#!/bin/bash

export DOCKER_IMAGE_ID="localhost/tasmota-shelly:test"
docker-compose -f docker-compose.build.yml build
