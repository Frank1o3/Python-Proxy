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

# Ensure the directory exists before looping through URLs
mkdir -p "$DIR_NAME"

for url in "${urls[@]}"; do
    download "$url" "$DIR_NAME"
done

cd "$DIR_NAME"
mkdir -p "app"
mv "$(pwd)/Proxy.py" "$(pwd)/app"

sleep 1

sudo docker build -t python-proxy -f "$(pwd)/DOCKERFILE" .

chmod +x cleanup.sh

sudo mv "$(pwd)/proxy.service" "/etc/systemd/system/"
sudo mv "$(pwd)/cleanup.sh" "/etc/systemd/system/"