import logging
import os

import pika
from pika.exceptions import AMQPConnectionError, ProbableAuthenticationError

logger = logging.getLogger(__name__)


def get_pika_connection() -> pika.connection.Connection:
    """Returns pika connection to RabbitMQ consumer.

    Raises:
        ValueError: Raised if RabbitMQ host environment variable is missing.
        ValueError: Raised if RabbitMQ username environment variable is missing.
        ValueError: Raised if RabbitMQ password environment variable is missing.

    Returns:
        pika.connection.Connection: Connection to RabbitMQ consumer.
    """
    host = os.environ.get("RABBITMQ_HOST")
    username = os.environ.get("RABBITMQ_USERNAME")
    password = os.environ.get("RABBITMQ_PASSWORD")

    if not host:
        raise ValueError("Must provide RABBITMQ_HOST with host in .backend.env")

    if not username:
        raise ValueError("Must provide RABBITMQ_USERNAME with username in .backend.env")

    if not password:
        raise ValueError("Must provide RABBITMQ_PASSWORD with password in .backend.env")

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host, credentials=pika.PlainCredentials(username, password)
            )
        )
    except AMQPConnectionError as e:
        print(
            "Failed to connect to RabbitMQ consumer - check if service running on host"
        )
        raise
    except ProbableAuthenticationError as e:
        print(
            "Failed to connect to RabbitMQ consumer - check username and password credentials"
        )
        raise
    except Exception as e:
        logger.exception("Failed to connect to RabbitMQ consumer")
        raise

    return connection
