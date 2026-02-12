import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Instrumentation packages
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
#from opentelemetry.instrumentation.django import DjangoInstrumentor
# from opentelemetry.instrumentation.pymongo import PymongoInstrumentor # Uncomment if using Djongo

def setup_instrumentation():
    # 1. Define Resource (Service Name)
    resource = Resource.create(attributes={
        "service.name": os.getenv("OTEL_SERVICE_NAME", "djongo-agent-service")
    })

    # 2. Configure the Tracer Provider
    tracer_provider = TracerProvider(resource=resource)
    
    # 3. Configure Exporter to point to Phoenix (Docker service name)
    # The endpoint comes from docker-compose env var: http://phoenix:4317
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True # Docker internal traffic is usually HTTP/insecure gRPC
    )

    # 4. Add Processor
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # 5. Set Global Tracer
    trace.set_tracer_provider(tracer_provider)

    # 6. Instrument Libraries
    # Instrument Django
    #DjangoInstrumentor().instrument()
    
    # Instrument Smolagents (The Key Step)
    SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)
    
    # If using Djongo, instrument Pymongo to see DB queries
    # PymongoInstrumentor().instrument()
    
    print("🔭 OpenTelemetry instrumentation setup complete. Sending traces to Phoenix.")