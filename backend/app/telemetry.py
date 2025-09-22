import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)  # <-- change
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(
    service_name: str = "fastapi-api",
    otlp_endpoint: str = "http://otel-collector:4318/v1/traces",  # <-- HTTP endpoint + path
):
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.namespace": "d2s",
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENV", "dev"),
        }
    )
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=otlp_endpoint)
    )  # no insecure flag for HTTP
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
