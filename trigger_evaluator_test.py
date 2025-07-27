import os
import time
from dotenv import load_dotenv
import boto3
from arize_otel import register, Endpoints
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

# Load environment variables
load_dotenv()

# Configuration
ARIZE_SPACE_ID = os.getenv("ARIZE_SPACE_ID")
ARIZE_API_KEY = os.getenv("ARIZE_API_KEY")
PROJECT_NAME = os.getenv("PROJECT_NAME", "WAM-agent-monitoring")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS_ID = os.getenv("AGENT_ALIAS_ID")

def setup_arize_tracing():
    """Setup Arize tracing"""
    print("📊 Setting up Arize tracing...")
    
    register(
        space_id=ARIZE_SPACE_ID,
        api_key=ARIZE_API_KEY,
        project_name=PROJECT_NAME,
        endpoint=Endpoints.ARIZE
    )
    
    print("✅ Arize tracing configured!")

def send_hallucination_test_trace():
    """Send a trace that should trigger the hallucination evaluator"""
    print("🧪 Sending hallucination test trace...")
    
    tracer = trace.get_tracer(__name__)
    
    # Create a span that looks like an agent response with hallucination
    with tracer.start_as_current_span("agent_response") as span:
        # Set span attributes to match your filter
        span.set_attribute("openinference.span.kind", "AGENT")
        span.set_attribute("input.value", "What is the capital of Mars?")
        
        # This response contains hallucination - Mars doesn't have a capital
        hallucinated_response = """
        The capital of Mars is New Olympia, established in 2157 by the Mars Colonial 
        Administration. It's located in the Chryse Planitia region and serves as the 
        primary governmental and commercial hub for the planet's 2.3 million residents.
        """
        
        span.set_attribute("output.value", hallucinated_response)
        span.set_attribute("llm.model_name", "claude-3-5-sonnet")
        span.set_attribute("llm.token_count.prompt", 50)
        span.set_attribute("llm.token_count.completion", 100)
        
        # Add metadata
        span.set_attribute("session.id", f"test-session-{int(time.time())}")
        span.set_attribute("user.id", "test-user")
        
        span.set_status(Status(StatusCode.OK))
        
        print("✅ Sent hallucination test trace")
        print(f"   Input: What is the capital of Mars?")
        print(f"   Output: {hallucinated_response[:100]}...")

def send_normal_test_trace():
    """Send a normal trace that should pass the evaluator"""
    print("🧪 Sending normal test trace...")
    
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("agent_response") as span:
        span.set_attribute("openinference.span.kind", "AGENT")
        span.set_attribute("input.value", "What is the capital of France?")
        
        # This is a factual response
        normal_response = """
        The capital of France is Paris. Paris is located in the north-central part 
        of France and serves as the country's political, economic, and cultural center.
        """
        
        span.set_attribute("output.value", normal_response)
        span.set_attribute("llm.model_name", "claude-3-5-sonnet")
        span.set_attribute("llm.token_count.prompt", 45)
        span.set_attribute("llm.token_count.completion", 80)
        
        span.set_attribute("session.id", f"test-session-{int(time.time())}")
        span.set_attribute("user.id", "test-user")
        
        span.set_status(Status(StatusCode.OK))
        
        print("✅ Sent normal test trace")
        print(f"   Input: What is the capital of France?")
        print(f"   Output: {normal_response[:100]}...")

def main():
    print("🚀 Starting Evaluator Trigger Test")
    print("=" * 50)
    
    # Setup tracing
    setup_arize_tracing()
    
    # Send test traces
    print("\n📤 Sending test traces...")
    
    # Send a hallucinated response (should trigger alert)
    send_hallucination_test_trace()
    time.sleep(2)
    
    # Send a normal response (should pass)
    send_normal_test_trace()
    time.sleep(2)
    
    print("\n" + "=" * 50)
    print("✅ Test traces sent!")
    print("\n📋 What happens next:")
    print("1. Arize will process these traces")
    print("2. The hallucination evaluator will analyze them")
    print("3. If hallucination is detected, monitor will trigger")
    print("4. PagerDuty should receive an alert")
    print("\n⏰ Wait 5-10 minutes, then check:")
    print("   • Arize dashboard for evaluation results")
    print("   • PagerDuty for alerts")

if __name__ == "__main__":
    main()