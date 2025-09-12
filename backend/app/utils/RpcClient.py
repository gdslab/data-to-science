import time
import uuid
from typing import Optional

import pika
from pika.exceptions import AMQPError

from app.utils.rabbitmq import get_pika_connection


class RpcClient:
    def __init__(self, routing_key: str) -> None:
        self.connection = get_pika_connection()
        self.channel = self.connection.channel()

        # transient, exclusive reply queue
        result = self.channel.queue_declare(queue="", exclusive=True, auto_delete=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response: Optional[bytes] = None
        self.corr_id: Optional[str] = None
        self.routing_key = routing_key

    def on_response(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, message: str, rpc_timeout_sec: int = 900) -> Optional[str]:
        self.response = None
        self.corr_id = str(uuid.uuid4())

        self.channel.basic_publish(
            exchange="",
            routing_key=self.routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                content_type="text/plain; charset=utf-8",
                delivery_mode=1,
            ),
            body=message.encode("utf-8"),
        )

        start_time = time.time()

        # Pump I/O so heartbeats are sent and replies received
        while self.response is None:
            self.connection.process_data_events(time_limit=1.0)

            if time.time() - start_time > rpc_timeout_sec:
                return None

            if self.connection.is_closed:
                raise AMQPError("Connection closed while waiting for RPC reply")

        text = self.response.decode("utf-8", errors="replace")
        if text.startswith("Error:"):
            return None
        return text
