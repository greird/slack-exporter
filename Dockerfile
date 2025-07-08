# Use Ubuntu as base image
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Update package list and install Python 3, pip, and other essentials
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install MEGAcmd using the official MEGA repository
RUN wget -O- https://mega.nz/linux/repo/xUbuntu_22.04/Release.key | apt-key add - && \
    echo "deb https://mega.nz/linux/repo/xUbuntu_22.04/ ./" > /etc/apt/sources.list.d/megasync.list && \
    apt-get update && \
    apt-get install -y megacmd && \
    rm -rf /var/lib/apt/lists/*

# Create a symbolic link for python command
RUN ln -s /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY slack_exporter slack_exporter
COPY .env .env
# Google Drive credentials file – remove if not needed
COPY credentials.json credentials.json

# run main.py
CMD ["python", "-m", "slack_exporter.main"]