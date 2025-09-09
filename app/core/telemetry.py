from importlib.metadata import metadata

import structlog
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.sdk.metrics import MeterProvider, TraceBasedExemplarFilter
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased
from prometheus_client import start_http_server

from app.core.config import settings

log = structlog.stdlib.get_logger("telemetry")


def setup_telemetry() -> bool:
    if not (
        settings.telemetry.otel_endpoint
        or settings.telemetry.console
        or settings.metrics.otel_endpoint
        or settings.metrics.prometheus.host
    ):
        log.info("Telemetry is NOT enabled")
        return False
    log.info("Setting up telemetry")

    project_metadata = metadata("atlas")

    resource = Resource(attributes={"service.name": "atlas", "service.version": project_metadata["Version"]})

    provider = TracerProvider(sampler=ParentBased(ALWAYS_ON), resource=resource)

    if settings.telemetry.otel_endpoint:
        processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=str(settings.telemetry.otel_endpoint)))
        provider.add_span_processor(processor)
        log.info("Sending traces to OTLP endpoint", endpoint=str(settings.telemetry.otel_endpoint))
    if settings.telemetry.console:
        # TODO: Use a formatter to make the spans look better
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        log.info("Dumping traces to console")

    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    # Instrument requests made by HTTPX
    HTTPXClientInstrumentor().instrument()

    # Instrument SQLAlchemy
    SQLAlchemyInstrumentor().instrument(enable_commenter=True)

    # Instrument Jinja2
    Jinja2Instrumentor().instrument()

    # Propagate OpenTelemetry context across threads
    ThreadingInstrumentor().instrument()

    metric_readers: list[MetricReader] = []

    if settings.metrics.prometheus.host:
        start_http_server(port=settings.metrics.prometheus.port, addr=settings.metrics.prometheus.host)
        log.info(
            f"Metrics available at http://{settings.metrics.prometheus.host}:{settings.metrics.prometheus.port}/metrics"
        )
        metric_readers.append(PrometheusMetricReader())

    if settings.metrics.otel_endpoint:
        metric_readers.append(
            PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=str(settings.metrics.otel_endpoint)))
        )
        log.info("Sending metrics to OTLP endpoint", endpoint=str(settings.metrics.otel_endpoint))

    if len(metric_readers) > 0:
        metrics.set_meter_provider(
            MeterProvider(
                metric_readers=metric_readers,
                resource=resource,
                exemplar_filter=TraceBasedExemplarFilter(),
            )
        )
    return True
