## Crypto project
### By Rostyslav Kostiuk & Oleksii Konopada

## Introduction
In this project our task was to design the system that will process the real time stream of cryptocurrency data, transform this data efficiently and store into the DB. Also system should provide the API with endpoints to complete 6 requests stated in the task.

## Our architecture to solve the problem

Here we would like to provide a diagram of our system:
![architecture.png](CryptoProject%2Freadme_images%2Farchitecture.png)

Let's dive in details on how it works by each element:

- Bitmex website - it is the source from which we can get the real time data that we need
- Bitmex Reader service - it is a service that makes a connection with the site via the websockets.
Then it processes the messages that come from the tables of our interest and writes the new messages but into the kafka
topic to interact asynchronously with the spark service. This service will do a further processing and saves into the Redis DB data that should be updated close to real time - current buy price for each cryptocurrency and current sell price for each cryptocurrency.
- Kafka message queue - service that provides the management of the topic needed for further processing.
- Spark service - service that reads the messages from the kafka topic and do the aggregation transformation to efficiently store the data about each cryptocurrency during the time period. Then saves it in Cassandra DB.
- Redis DB - storage where we store close to real time data
- Cassandra DB - storage where we store aggregated data about cryptocurrencies performance
- User
- REST API service - service with which user interacts. It provides the answers to the tasks of interest using the queries to databases.

## DB\schema

As a main DB we have selected a Cassandra DB. Using it we can get the robustness for our data, also it is efficient in storing and performing queries on huge amount of data (potentially if our system will run for months and years than we will need to work with terabytes of data).

Also, we have used a Redis to give our system ability to efficiently perform last request. That's why just when the message arrive into the websocket we update the value of price in the db for the symbol and the side (SELL, BUY) of this transaction.

Our Cassandra schema looks like this:

![schema.png](CryptoProject%2Freadme_images%2Fschema.png)
                                                              

As you can see it is pretty simple - just aggregates for each cryptocurrency symbol by minutes and hours. However, this schema covers the need for all request as they all depend either on minute periods or on hours.

## Files description
Now lets move on to the code and let us provide the description for all the files and directories you can find in this project:
- readme_images dir - directory where we store all the images that where used for readme
- scripts - here are all the scripts that we will use to configure and build the containers for the needed services (build-cassandra.sh, build-kafka.sh, build-ws-kafka.sh (this script build the container with the Bitmex reader))
- aggregate_and_write.py - script that we run on spark server and that reads from kafka, aggregates the data over the minutes and hours periods and then saves those aggregated values into the cassandra
- app.py - file that configures the REST API and its endpoints
- docker-compose.yaml - file that set-ups the spark cluster, redis and REST API
- Dockerfile - dockerfile with which we configure the image for the Bitmex Reader service
- Dockerfile.restapi - dockerfile with which we configure the image for the REST API service
- schema.cql - file in which we define the schema for our Cassandra DB
- ws_to_kafka.py - the main script of Bitmex Reader service that reads messages from the Bitmex website via websockets and then writes the preprocessed messages into kafka topic

## Usage 

- Clone the project into directory
- Open the terminal and using the `cd` command move into CryptoProject directory
- Set up the kafka cluster using the command `.\scripts\build-kafka.sh`
- Set up the cassandra cluster using the command `.\scripts\build-cassandra.sh`
- Set up the Bitmex Reader container using the command `.\scripts\build-ws-kafka.sh`
- Set up rest of containers using the docker compose running this command `docker-compose up -d`
- The last step is to run on the spark cluster the program that will aggregate the data, so firstly run this command adjusting the PROJECT_PATH with the absolute path to directory where you cloned this repo `docker run --rm -it --network crypto-network --name spark-submit -v PROJECT_PATH\CryptoProject-Kostiuk-Konopada\CryptoProject:/opt/app bitnami/spark:3 /bin/bash`
- Now run those commands: `cd /opt/app`, `spark-submit  --conf spark.jars.ivy=/opt/app --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0" --master spark://cryptoproject-spark-1:7077 --deploy-mode client aggregate_and_write.py`

## Results

As a result after execution of those command in your docker containers list you should see those 6 items running:
![containers.png](CryptoProject%2Freadme_images%2Fcontainers.png)

The system has been running for the 4 hours and was scraping the info about the 4 cryptocurrencies. Now lets first of look either everything has been written into the DBs as supposed:

![db_minutes.png](CryptoProject%2Freadme_images%2Fdb_minutes.png)
![db_hours.png](CryptoProject%2Freadme_images%2Fdb_hours.png)

As we can see everything has been writen good. 

Now lets move on to the REST API and check either all of the asked in the task endpoints actually work:

#### Category A

1.	Return the aggregated statistics containing the number of transactions for each cryptocurrency for each hour in the last 6 hours, excluding the previous hour.
You should send such a request to get the result GET`http://localhost:8080/transactions/last_6_hours`:
![6_hours_transactions.png](CryptoProject%2Freadme_images%2F6_hours_transactions.png)
2.	Return the statistics about the total trading volume for each cryptocurrency for the last 6 hours, excluding the previous hour.
You should send such a request to get the result GET`http://localhost:8080/volume/last_6_hours`:
![6_hours_volume.png](CryptoProject%2Freadme_images%2F6_hours_volume.png)
3.	Return aggregated statistics containing the number of trades and their total volume for each hour in the last 12 hours, excluding the current hour. 
You should send such a request to get the result GET`http://localhost:8080/aggregated_stats/last_12_hours`:
![12_hours.png](CryptoProject%2Freadme_images%2F12_hours.png)

#### Category B

1.	Return the number of trades processed in a specific cryptocurrency in the last N minutes, excluding the last minute.
You should send such a request to get the result GET`http://localhost:8080/trades/last_n_minutes?symbol={YOUR_SYMBOL}&minutes={MINUTES}`:
![trades_by_minutes.png](CryptoProject%2Freadme_images%2Ftrades_by_minutes.png)
2.	Return the top N cryptocurrencies with the highest trading volume in the last hour. 
You should send such a request to get the result GET`http://localhost:8080/top_cryptos_last_hour?top_n={YOUR_NUMBER}`:
![top_n.png](CryptoProject%2Freadme_images%2Ftop_n.png)
3.	Return the cryptocurrency’s current price for «Buy» and «Sell» sides based on its symbol. 
You should send such a request to get the result GET`http://localhost:8080/transactions/last_6_hours`:
![curr_price.png](CryptoProject%2Freadme_images%2Fcurr_price.png)
