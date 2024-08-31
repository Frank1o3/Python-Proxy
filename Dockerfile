# Use official Python image
FROM python:3.12.3

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m venv /venv
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy the proxy script
COPY app/HTTP_Proxy.py .
COPY app/LRU.py .
COPY app/Config.json .
COPY example/Database_Example ./Database_Example/

# Set args
ARG DEFAULT_IP="0.0.0.0"
ARG DEFAULT_PORT=8080

# Set environment variables
ENV IP $DEFAULT_IP
ENV PORT $DEFAULT_PORT

EXPOSE $PORT

# Run the proxy with signal handling

RUN chmod +x HTTP_Proxy.py

CMD ["/venv/bin/python", "HTTP_Proxy.py"]
