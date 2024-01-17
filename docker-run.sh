#!/bin/bash

# The name of the Docker image to update
image_name="glichtner/celida-recommendation-server"

# Pull the latest version of the image
echo "Pulling latest image for $image_name..."
docker pull $image_name:latest

# Get the IDs of all running containers that are using the image
container_ids=$(docker ps -q --filter ancestor=$image_name)

# If any such containers are found, stop and remove them
if [ -n "$container_ids" ]; then
    echo "Stopping and removing containers for $image_name..."
    for id in $container_ids; do
        container_name=$(docker ps -a --format "{{.Names}}" -f id=$id)
        echo "Stopping container $container_name ($id)..."
        docker stop $id
        echo "Removing container $container_name ($id)..."
        docker rm $id
    done
else
    echo "No running containers found for $image_name."
fi

# Start a new container using the latest version of the image
echo "Starting new container for $image_name..."
docker run   --restart=unless-stopped -e "GH_RELEASE_BASE=https://github.com/CODEX-CELIDA/celida-recommendations/releases"    -e "PACKAGE_NAME_TEMPLATE=recommendations.celida.codex.netzwerk-universitaetsmedizin.de-{version}.tgz"    -dp 8000:80 --name celida-recommendation-server $image_name:latest
echo "Container started"
