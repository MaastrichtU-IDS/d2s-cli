#!/bin/bash

docker build -f Dockerfile.publish -t publish-d2s-cli .

docker run -it publish-d2s-cli
