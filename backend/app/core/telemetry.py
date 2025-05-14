from importlib.metadata import metadata

import structlog
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased
from prometheus_client import start_http_server

from app.core.config import settings

log = structlog.stdlib.get_logger("telemetry")


def setup_telemetry() -> None:
    project_metadata = metadata("atlas")

    resource = Resource(
        attributes={"service.name": "atlas", "service.version": project_metadata["Version"]}
    )

    provider = TracerProvider(sampler=ParentBased(ALWAYS_ON), resource=resource)

    if settings.telemetry.endpoint:
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=str(settings.telemetry.endpoint)))
        provider.add_span_processor(processor)
    if settings.telemetry.console:
        # TODO: Use a formatter to make the spans look better
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)

    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    # Instrument requests made by HTTPX
    HTTPXClientInstrumentor().instrument()

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(enable_commenter=True)

    # Propagate OpenTelemetry context across threads
    ThreadingInstrumentor().instrument()

    if settings.metrics.host:
        start_http_server(port=settings.metrics.port, addr=settings.metrics.host)
        log.info(
            f"Metrics available at http://{settings.metrics.host}:{settings.metrics.port}/metrics"
        )

    reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader], resource=resource))
