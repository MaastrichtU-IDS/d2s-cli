#!/bin/bash 
set -e

docker build -f publish.Dockerfile -t publish-d2s-cli .

docker run -it publish-d2s-cli
