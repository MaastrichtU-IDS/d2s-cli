#!/bin/bash

docker build -t publish-d2s-cli .

docker run -it publish-d2s-cli
