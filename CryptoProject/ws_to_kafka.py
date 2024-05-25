import json
import websocket
from kafka import KafkaProducer
import redis
import time
import threading


def on_message(ws, message):
    producer = KafkaProducer(
        bootstrap_servers='kafka-server:9092',
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    redis_client = redis.StrictRedis(host='redis', port=6379, db=0)

    try:
        message_data = json.loads(message)
        if message_data.get('table') == 'trade':
            for trade in message_data['data']:
                trade_info = {
                    'timestamp': trade['timestamp'],
                    'symbol': trade['symbol'],
                    'side': trade['side'],
                    'size': trade['size'],
                    'price': trade['price']
                }
                producer.send('transactions', value=trade_info)
                print(f"Published: {trade_info}")

                redis_key = f"{trade['symbol']}_{trade['side']}"
                redis_client.set(redis_key, trade['price'])
                print(f"Stored in Redis: {redis_key} -> {trade['price']}")
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")


def on_error(ws, error):
    print(f"Error: {error}")


def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: {close_msg}")


def on_open(ws):
    def run():
        subscribe_message = {
            "op": "subscribe",
            "args": ["trade:ETHUSD", "trade:ADAUSD", "trade:DOGEUSD", "trade:SOLUSD"]
        }
        ws.send(json.dumps(subscribe_message))
    thread = threading.Thread(target=run)
    thread.start()


def main():
    websocket_url = "wss://www.bitmex.com/realtime"
    while True:
        ws = websocket.WebSocketApp(websocket_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        ws.on_open = on_open
        ws.run_forever()
        time.sleep(10)


if __name__ == "__main__":
    main()
