CREATE KEYSPACE IF NOT EXISTS crypto_data WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 1};

CREATE TABLE IF NOT EXISTS crypto_data.minute_aggregates (
    minute timestamp,
    symbol text,
    num_transactions int,
    total_volume int,
    PRIMARY KEY (symbol, minute)
);

CREATE TABLE IF NOT EXISTS crypto_data.hour_aggregates (
    hour timestamp,
    symbol text,
    num_transactions int,
    total_volume int,
    PRIMARY KEY (symbol, hour)
);