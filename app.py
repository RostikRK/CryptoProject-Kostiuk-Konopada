from fastapi import FastAPI, Query
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, timedelta
import redis

app = FastAPI()


cluster = Cluster(['cassandra-node'])
session = cluster.connect('crypto_data')

redis_client = redis.StrictRedis(host='redis-server', port=6379, db=0)


def get_current_minute():
    now = datetime.utcnow()
    return now.replace(second=0, microsecond=0)


def get_current_hour():
    now = datetime.utcnow()
    return now.replace(minute=0, second=0, microsecond=0)


@app.get("/transactions/last_6_hours")
def get_transactions_last_6_hours():
    current_hour = get_current_hour()
    start_time = current_hour - timedelta(hours=7)  # Excluding the previous hour
    end_time = current_hour - timedelta(hours=1)

    query = SimpleStatement("""
        SELECT hour, symbol, num_transactions 
        FROM hour_aggregates 
        WHERE hour >= %s AND hour < %s
    """, fetch_size=None)

    result = session.execute(query, (start_time, end_time))
    data = {}
    for row in result:
        if row.symbol not in data:
            data[row.symbol] = []
        data[row.symbol].append({
            "hour": row.hour,
            "num_transactions": row.num_transactions
        })

    return data


@app.get("/volume/last_6_hours")
def get_volume_last_6_hours():
    current_hour = get_current_hour()
    start_time = current_hour - timedelta(hours=7)  # Excluding the previous hour
    end_time = current_hour - timedelta(hours=1)

    query = SimpleStatement("""
        SELECT hour, symbol, total_volume 
        FROM hour_aggregates 
        WHERE hour >= %s AND hour < %s
    """, fetch_size=None)

    result = session.execute(query, (start_time, end_time))
    data = {}
    for row in result:
        if row.symbol not in data:
            data[row.symbol] = []
        data[row.symbol].append({
            "hour": row.hour,
            "total_volume": row.total_volume
        })

    return data


@app.get("/aggregated_stats/last_12_hours")
def get_aggregated_stats_last_12_hours():
    current_hour = get_current_hour()
    start_time = current_hour - timedelta(hours=12)
    end_time = current_hour  # Excluding the current hour

    query = SimpleStatement("""
        SELECT hour, symbol, num_transactions, total_volume 
        FROM hour_aggregates 
        WHERE hour >= %s AND hour < %s
    """, fetch_size=None)

    result = session.execute(query, (start_time, end_time))
    data = {}
    for row in result:
        if row.symbol not in data:
            data[row.symbol] = []
        data[row.symbol].append({
            "hour": row.hour,
            "num_transactions": row.num_transactions,
            "total_volume": row.total_volume
        })

    return data


@app.get("/trades/last_n_minutes")
def get_trades_last_n_minutes(symbol: str, minutes: int = Query(..., ge=1)):
    current_minute = get_current_minute()
    start_time = current_minute - timedelta(minutes=minutes+1)
    end_time = current_minute - timedelta(minutes=1)

    query = SimpleStatement("""
        SELECT minute, num_transactions 
        FROM minute_aggregates 
        WHERE symbol = %s AND minute >= %s AND minute < %s
    """, fetch_size=None)

    result = session.execute(query, (symbol, start_time, end_time))
    total_trades = sum(row.num_transactions for row in result)

    return {"symbol": symbol, "num_trades": total_trades}


@app.get("/top_cryptos_last_hour")
def get_top_cryptos_last_hour(top_n: int = Query(..., ge=1)):
    current_hour = get_current_hour()
    start_time = current_hour - timedelta(hours=1)
    end_time = current_hour

    query = SimpleStatement("""
        SELECT symbol, sum(total_volume) as total_volume 
        FROM hour_aggregates 
        WHERE hour >= %s AND hour < %s
        GROUP BY symbol
        ORDER BY total_volume DESC
        LIMIT %s
    """, fetch_size=None)

    result = session.execute(query, (start_time, end_time, top_n))
    data = [{"symbol": row.symbol, "total_volume": row.total_volume} for row in result]

    return {"top_cryptocurrencies": data}


@app.get("/current_price")
def get_current_price(symbol: str):
    buy_price = redis_client.get(f"{symbol}_Buy")
    sell_price = redis_client.get(f"{symbol}_Sell")

    return {
        "symbol": symbol,
        "buy_price": float(buy_price) if buy_price else None,
        "sell_price": float(sell_price) if sell_price else None
    }
