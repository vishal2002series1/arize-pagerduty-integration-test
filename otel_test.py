from arize.otel import register
from opentelemetry import trace

tracer_provider = register(
    space_id="YOUR_SPACE_ID",
    api_key="YOUR_API_KEY",
    project_name="test-project",
    endpoint="https://otlp.arize.com:443",  # Use full URL!
    batch=False,  # Use SimpleSpanProcessor for debugging
    verbose=True
)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("test-span"):
    print("Span created")