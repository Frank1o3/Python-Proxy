# Setup Instructions for Linux (with Docker support)

# Docker Download With the Tool

1. **Get The Downloader**: [Here](https://github.com/Frank1o3/Python-Proxy/releases/download/v1.5.0/Linux_Downloader.sh)

**Note**: The Tool Takes Some args the first one tells the Tool if it need to setup files so the docker runs on start up and the second arg tells the tool if it need to build the docker container so if you dont want to do those two thing run the tool with this command ./Linux_Downloader.sh "" ""

2. **Run the Tool**: The tool will download the files needed

3. **Build/Run**: if you ran the tool but did not tell it to build the docker container or do the startup config then run `bash docker build -t python-proxy -f "$(pwd)/DOCKERFILE" .` and after the container is build run `bash docker run -d --restart unless-stopped --network host -e PROXY_IP="0.0.0.0" -e PROXY_PORT=8080 --name python-proxy python-proxy .`