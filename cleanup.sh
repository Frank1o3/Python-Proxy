#!/bin/bash

# Check if the container is running
if /usr/bin/docker inspect -f '{{.State.Running}}' python-proxy >/dev/null 2>&1; then
    # If running, stop the container
    echo "Stopping container"
    /usr/bin/docker stop python-proxy >/dev/null
fi

# Check if the container exists
if /usr/bin/docker ps -a --format '{{.Names}}' | grep -Eq "^python-proxy$"; then
    # If exists, remove the container
    echo "Deleting container"
    /usr/bin/docker rm python-proxy >/dev/null
fi
