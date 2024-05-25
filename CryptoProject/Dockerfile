FROM python:3.9-slim

WORKDIR /app

COPY ws_to_kafka.py /app/ws_to_kafka.py

RUN pip install websocket-client kafka-python redis

CMD ["python", "ws_to_kafka.py"]
