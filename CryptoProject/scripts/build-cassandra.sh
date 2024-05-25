#!/bin/bash

docker run --name cassandra-node --network crypto-network -p 9042:9042 -d cassandra:3.11.14

sleep 35

docker exec -i cassandra-node cqlsh < schema.cql
