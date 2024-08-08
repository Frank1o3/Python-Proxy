#!/bin/bash

#!/bin/bash

# List of URLs to download the files from
urls=(
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/DOCKERFILE"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/Config.json"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/LRU.py"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/requirements.txt"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/app/HTTP_Proxy.py"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/Download/cleanup.sh"
    "https://raw.githubusercontent.com/Frank1o3/Python-Proxy/main/Download/proxy.service"
)

download() {
    local url=$1
    local dir_name=$2
    local filename=$(basename "$url")
    mkdir -p "$dir_name"
    cd "$dir_name" || exit
    curl -O "$url"
    cd - > /dev/null
}

# Directory to save the files
DIR_NAME="Proxy"
APP_DIR="$DIR_NAME/app"

# Ensure the directories exist before downloading files
mkdir -p "$DIR_NAME"
mkdir -p "$APP_DIR"

# Download the files
for url in "${urls[@]}"; do
    download "$url" "$DIR_NAME"
done

# Move specific files to the app directory
mv "$DIR_NAME/HTTP_Proxy.py" "$APP_DIR"
mv "$DIR_NAME/LRU.py" "$APP_DIR"
mv "$DIR_NAME/Config.json" "$APP_DIR"

sleep 1

# Check if 'build-docker' argument is passed
if [[ "$*" == *build-docker* ]]; then
    sudo docker build -t python-proxy -f "$DIR_NAME/DOCKERFILE" .
    echo "Docker container built successfully."
else
    echo "Docker container not built. To build the container, run the script with the 'build-docker' argument."
fi

chmod +x "$DIR_NAME/cleanup.sh"

# Check if 'service-create' argument is passed
if [[ "$*" == *service-create* ]]; then
    sudo mv "$DIR_NAME/proxy.service" "/etc/systemd/system/"
    sudo mv "$DIR_NAME/cleanup.sh" "/etc/systemd/system/"
    sudo systemctl enable proxy.service
    echo "Service created and enabled to start on system boot."
else
    echo "No service created. To create a service, run the script with the 'service-create' argument."
fi
