#!/bin/bash

docker build -t bitmex-websocket-to-kafka .

docker run --name bitmex-websocket-to-kafka --network crypto-network bitmex-websocket-to-kafka
