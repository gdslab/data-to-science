import uuid
from typing import Optional

import pika

from app.utils.rabbitmq import get_pika_connection


class RpcClient:
    def __init__(self, routing_key: str) -> None:
        self.connection = get_pika_connection()
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
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

    def call(self, message: str) -> Optional[str]:
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key=self.routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=message,
        )
        while self.response is None:
            self.connection.process_data_events()

        # check if response is an error
        if self.response.decode("utf-8").startswith("Error:"):
            return None

        return self.response.decode("utf-8")
