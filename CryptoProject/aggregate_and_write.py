from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, window, count, sum
from pyspark.sql.types import StructType, StringType, TimestampType, IntegerType, FloatType

spark = SparkSession \
    .builder \
    .appName("Write to Cassandra and Redis") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,com.datastax.spark:spark-cassandra-connector_2.12:3.1.0") \
    .config("spark.cassandra.connection.host", "cassandra-node") \
    .getOrCreate()

kafka_bootstrap_servers = "kafka-server:9092"
transactions_topic_name = "transactions"

schema = StructType() \
    .add("timestamp", StringType()) \
    .add("symbol", StringType()) \
    .add("side", StringType()) \
    .add("size", IntegerType()) \
    .add("price", FloatType())

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
    .option("subscribe", transactions_topic_name) \
    .option("startingOffsets", "earliest") \
    .load()

df_json = df.select(from_json(col("value").cast("string"), schema).alias("data"))

selected_df = df_json.select(
    to_timestamp(col("data.timestamp")).alias("made_at"),
    col("data.symbol").alias("symbol"),
    col("data.side").alias("side"),
    col("data.size").alias("size"),
    col("data.price").alias("price")
).filter(
    (col("made_at").isNotNull()) &
    (col("symbol").isNotNull()) &
    (col("side").isNotNull()) &
    (col("size").isNotNull()) &
    (col("price").isNotNull())
)


minute_aggregates_df = selected_df \
    .withWatermark("made_at", "1 minute") \
    .groupBy(
        "symbol",
        window(col("made_at"), "1 minute")
    ).agg(
        count("symbol").alias("num_transactions"),
        sum("size").alias("total_volume")
    ).select(
        col("window.start").alias("minute"),
        col("symbol"),
        col("num_transactions"),
        col("total_volume")
    )

minute_aggregates_query = minute_aggregates_df \
    .writeStream \
    .foreachBatch(lambda batch_df, batch_id: batch_df.write \
                  .format("org.apache.spark.sql.cassandra") \
                  .options(keyspace="crypto_data", table="minute_aggregates") \
                  .mode("append") \
                  .save()) \
    .option("checkpointLocation", "/opt/app/cassandra-checkpoint/minute_aggregates") \
    .start()

hour_aggregates_df = selected_df \
    .withWatermark("made_at", "1 hour") \
    .groupBy(
        "symbol",
        window(col("made_at"), "1 hour")
    ).agg(
        count("symbol").alias("num_transactions"),
        sum("size").alias("total_volume")
    ).select(
        col("window.start").alias("hour"),
        col("symbol"),
        col("num_transactions"),
        col("total_volume")
    )

hour_aggregates_query = hour_aggregates_df \
    .writeStream \
    .foreachBatch(lambda batch_df, batch_id: batch_df.write \
                  .format("org.apache.spark.sql.cassandra") \
                  .options(keyspace="crypto_data", table="hour_aggregates") \
                  .mode("append") \
                  .save()) \
    .option("checkpointLocation", "/opt/app/cassandra-checkpoint/hour_aggregates") \
    .start()

spark.streams.awaitAnyTermination()