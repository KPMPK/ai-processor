#!/bin/bash

# Remove any existing container named 'patternred'
echo "Removing any existing container named 'patternred'..."
sudo docker rm -f patternred
echo "Container removed (if it existed)."

# Build the Docker image from the current directory with the tag 'patternred'
echo "Building Docker image named 'patternred'..."
sudo docker build -t patternred .
echo "Docker image 'patternred' built successfully."

# Run the Docker container in detached mode with the specified settings
echo "Running the Docker container in detached mode..."
sudo docker run -d --name patternred --restart unless-stopped -p 9999:9999 patternred
echo "Docker container 'patternred' is now running."

# Display the list of running Docker containers to verify that 'patternred' is running
echo "Displaying the list of running Docker containers:"
sudo docker ps --format "table {{.Image}}\t{{.Ports}}\t{{.Names}}\t{{.RunningFor}}"
