import os
import datetime
import json
import dateutil.parser as parser

from flask import Flask
from flask import render_template, request

import plotly
import plotly.express as px
import pandas as pd
import psycopg2

def get_database_connection():
    """Initiate connection to PostgreSQL database"""
    return psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=os.environ['POSTGRES_PORT']
    )

def get_cursor(connection):
    return connection.cursor()

app = Flask(__name__)
conn = get_database_connection()

@app.route("/")
def dashboard() -> str:
    return render_template("dashboardtemplate.html")

def getTableData(tableName: str) -> list:
    """
    Fetch all rows from specified table in connected PostgreSQL, return as list of dictionaries
    
        Args:
            tableName (str): Name of table

        Returns:
            table_data (list): List of dictionaries, each representing a row from the table
    """
    with get_cursor(conn) as cursor:
        cursor.execute(f"SELECT * FROM {tableName}")
        results: list = cursor.fetchall()
        table_data: list = []
        for row in results:
            table_data.append({
                "time": row[0],
                "value": row[1]
            })
        cursor.close()
    return table_data

@app.route("/data")
def getDashboardData() -> str:
    """
    Fetch data for multiple series from different tables in connected PostgreSQL, generates a line plot for each series using Plotly,
    returns all plot data as a JSON string. Data starts at specified time window and extends to current date.

        Args:
            request.args.get("from_date") (str): JSON string passed from front end representing start time window for data

        Returns:
            graphJSONs (str): A JSON string with 4 root elements, each containing the JSON Plotly data to construct plots on front-end
    """
    data: dict = {}

    # Fetch and aggregate data for each series
    temperature_data: list = getTableData("\"CM_HAM_DO_AI1/Temp_value\"")
    data["Temperature"] = temperature_data

    ph_data: list = getTableData("\"CM_HAM_PH_AI1/pH_value\"")
    data["pH"] = ph_data

    distilledox_data: list = getTableData("\"CM_PID_DO/Process_DO\"")
    data["Distilled Oxygen"] = distilledox_data

    pressure_data: list = getTableData("\"CM_PRESSURE/Output\"")
    data["Pressure"] = pressure_data

    # Get selected starting time window from request args, parse into datetime
    from_date: str = request.args.get("from_date")
    from_date_obj: datetime = None
    try:
        from_date_obj = parser.parse(json.loads(from_date))
    except:
        pass
        
    # Dict to store Plotly JSON for each series
    graphJSONs: dict = {}

    # For each series, build the Plotly plot and convert to JSON, store in graphJSONs
    for series in data:
        seriesData: list = data[series]
        xData: list = []
        yData: list = []
        # For the data in this series, extract the X values (time) and Y values into seperate lists only if data is within time slot
        for row in seriesData:
            if (from_date_obj != None and row["time"] > from_date_obj) or from_date_obj == None:
                xData.append(row["time"])
                yData.append(row["value"])

        df: pd.DataFrame = pd.DataFrame(dict(
            Time = xData,
            Value = yData
        ))
        fig = px.line(df, x="Time", y="Value", title=series)
        graphJSON: str = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) 
        graphJSONs[series] = graphJSON
    
    return json.dumps(graphJSONs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)