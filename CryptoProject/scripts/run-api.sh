#!/bin/bash

docker build -t fastapi-restapi -f Dockerfile.restapi .

docker run --name fastapi-restapi --network crypto-network -p 8080:8080 fastapi-restapi
