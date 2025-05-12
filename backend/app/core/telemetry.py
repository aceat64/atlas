from importlib.metadata import metadata

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.threading import ThreadingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased

from app.core.config import settings


def setup_telemetry() -> None:
    project_metadata = metadata("atlas")

    provider = TracerProvider(
        sampler=ParentBased(ALWAYS_ON),
        resource=Resource(
            attributes={"service.name": "atlas", "service.version": project_metadata["Version"]}
        ),
    )

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
