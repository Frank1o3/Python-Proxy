# Setup Instructions for Linux (with Docker support)

# Docker Download With The Tool

1. **Get The Downloader**: [Here](https://github.com/Frank1o3/Python-Proxy/releases/download/v1.5.0/Linux_Downloader.sh)

**Note**: The Tool Takes Some args (service-create, build-docker) the first one tells the Tool if it need to setup files so the docker runs on start up and the second arg tells the tool if it need to build the docker container so if you dont want to do those two thing run the tool with this command ./Linux_Downloader.sh "" ""

2. **Run The Tool**: The tool will download the files needed

3. **Build/Run**: if you ran the tool but did not tell it to build the docker container or do the startup config then run `bash docker build -t python-proxy -f "$(pwd)/DOCKERFILE" .` and after the container is build run `bash docker run -d --restart unless-stopped --network host -e PROXY_IP="0.0.0.0" -e PROXY_PORT=8080 --name python-proxy python-proxy .`

# Download & Install The Proxy Without The Tool

1. **Clone the repository**: Clone this repository to your local machine.

2. **Build Docker/Run the Container**:To build the docker container  run `bash docker build -t python-proxy -f "$(pwd)/DOCKERFILE" .` and after the container is build run `bash docker run -d --restart unless-stopped --network host -e PROXY_IP="0.0.0.0" -e PROXY_PORT=8080 --name python-proxy python-proxy .`

3. **Se Logs**: To see the logs of the proxy run `bash docker logs -f python-proxy`

# Download & Run The Proxy Without The Tool And Docker

1. **Clone the repository**: Clone this repository to your local machine.

2. **Create The Virtual Envirement**: Navigate to the project directory and run the following command to Create the virtual envirement:
   `bash python -m venv venv`

3. **Install dependencies**: Navigate to the project directory and run the following command to install the required Python packages:
   `bash pip install -r requirements.txt`

4. **Run The Application Directly**:
    To run the application directly using Python, follow these steps:
    1. Ensure you have Python 3.12.3 or higher installed on your system.
    2. Navigate to the project directory in your terminal. 3.
    If you're using a virtual environment (which is recommended), activate it. If you haven't created a virtual environment yet, you can do so by running:

      ````
      bash python -m venv venv

              And then activate it with:
              - On Windows:
                ```

      bash pip install -r requirements.txt

             Start the application by running:
              ```

      bash python app/HTTP_Proxy.py
