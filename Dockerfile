# syntax=docker/dockerfile:1.4
FROM ubuntu:22.04

# Install OS-level packages
RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get --yes upgrade && \
    apt-get --yes install --no-install-recommends \
    python3.10-full tini build-essential

# Create and activate virtual environment
ENV VIRTUAL_ENV="/root/.venv"
RUN python3.10 -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Update pip
RUN pip install --upgrade pip setuptools wheel

# Setup root home directory
WORKDIR /root/dashboard

# Install package
COPY . .
RUN pip install --requirement requirements.txt

#Define the run-app command
RUN echo "python ./app/dashboard.py" > /usr/local/bin/run-app && \
    chmod +x /usr/local/bin/run-app

ENTRYPOINT ["tini", "-v", "--"]
