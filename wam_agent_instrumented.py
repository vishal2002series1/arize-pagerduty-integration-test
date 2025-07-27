import boto3
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from arize.otel import register
from openinference.instrumentation.bedrock import BedrockInstrumentor

# Load environment variables from .env file
load_dotenv()
# export no_proxy=otlp.arize.com

class WAMAgentInstrumented:
    def __init__(self):
        """Initialize the WAM Agent with Arize instrumentation"""
        print("🚀 Initializing WAM Agent with Arize instrumentation...")
        
        # Load configuration from environment variables
        self.load_config()
        
        # Step 1: Set up Arize tracing BEFORE creating any AWS clients
        self.setup_arize_tracing()
        
        # Step 2: Initialize AWS clients AFTER instrumentation
        self.setup_aws_clients()
        
        print("✅ WAM Agent initialized successfully!")
    
    def load_config(self):
        """Load configuration from environment variables"""
        print("📋 Loading configuration from .env file...")
        
        # Arize Configuration
        self.arize_space_id = os.getenv("ARIZE_SPACE_ID")
        self.arize_api_key = os.getenv("ARIZE_API_KEY")
        self.project_name = os.getenv("PROJECT_NAME", "WAM-agent-monitoring")
        
        # AWS Configuration
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.agent_id = os.getenv("AGENT_ID")
        self.agent_alias_id = os.getenv("AGENT_ALIAS_ID")
        
        # Inference Profile Configuration
        self.inference_profile_arn = os.getenv("INFERENCE_PROFILE_ARN")
        
        # PagerDuty Configuration (for future use)
        self.pagerduty_routing_key = os.getenv("PAGERDUTY_ROUTING_KEY")
        self.pagerduty_integration_url = os.getenv("PAGERDUTY_INTEGRATION_URL")
        
        # Validate required configuration
        if not self.arize_space_id or not self.arize_api_key:
            raise ValueError("❌ ARIZE_SPACE_ID and ARIZE_API_KEY must be set in .env file")
        
        if not self.agent_id or not self.agent_alias_id:
            raise ValueError("❌ AGENT_ID and AGENT_ALIAS_ID must be set in .env file")
        
        if not self.inference_profile_arn:
            raise ValueError("❌ INFERENCE_PROFILE_ARN must be set in .env file")
        
        print("✅ Configuration loaded successfully!")
        print(f"   Project: {self.project_name}")
        print(f"   AWS Region: {self.aws_region}")
        print(f"   Agent ID: {self.agent_id}")
        print(f"   Agent Alias: {self.agent_alias_id}")
        print(f"   Inference Profile: {self.inference_profile_arn}")
    
    def setup_arize_tracing(self):
        """Set up Arize tracing and instrumentation"""
        print("📊 Setting up Arize tracing...")
        
        # Register with Arize
        self.tracer_provider = register(
            space_id=self.arize_space_id,
            api_key=self.arize_api_key,
            project_name=self.project_name
        )
        
        # Instrument Bedrock calls
        BedrockInstrumentor().instrument(tracer_provider=self.tracer_provider)
        
        print("✅ Arize tracing configured!")
        print(f"   Space ID: {self.arize_space_id[:10]}...")
        print(f"   Project: {self.project_name}")
    
    def setup_aws_clients(self):
        """Initialize AWS Bedrock clients"""
        print("🔧 Setting up AWS clients...")
        
        # Create AWS session (will use default credentials from AWS CLI/environment)
        self.session = boto3.Session(region_name=self.aws_region)
        
        # Create Bedrock clients
        self.bedrock_runtime = self.session.client("bedrock-runtime")
        self.bedrock_agent_runtime = self.session.client("bedrock-agent-runtime")
        
        print("✅ AWS clients configured!")
        print(f"   Region: {self.aws_region}")
    
    def invoke_foundation_model(self, prompt):
        """Invoke a foundation model directly using inference profile"""
        print(f"🤖 Invoking foundation model using inference profile")
        print(f"   Prompt: {prompt[:50]}...")
        print(f"   Using ARN: {self.inference_profile_arn}")
        
        # Prepare the request body for Claude
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })
        
        try:
            start_time = time.time()
            
            # This call will be automatically traced by Arize
            response = self.bedrock_runtime.invoke_model(
                modelId=self.inference_profile_arn,
                body=body
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Parse response
            response_body = json.loads(response.get("body").read())
            content = response_body.get("content", [{}])[0].get("text", "")
            
            print(f"✅ Model invocation successful! (Latency: {latency:.2f}s)")
            print(f"   Response: {content[:100]}...")
            
            return {
                "content": content,
                "latency": latency,
                "model_id": self.inference_profile_arn,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error invoking model: {str(e)}")
            raise
    
    def invoke_wam_agent(self, user_input):
        """Invoke the WAM agent"""
        print(f"🏦 Invoking WAM Agent...")
        print(f"   Input: {user_input[:50]}...")
        
        session_id = f"wam-session-{int(time.time())}"
        
        try:
            start_time = time.time()
            
            # This call will be automatically traced by Arize
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=user_input,
                enableTrace=True
            )
            
            # Collect response
            output_text = ""
            trace_data = []
            
            for event in response.get("completion", []):
                if "chunk" in event:
                    chunk = event["chunk"]
                    if "bytes" in chunk:
                        output_text += chunk["bytes"].decode("utf-8")
                elif "trace" in event:
                    trace_data.append(event["trace"])
            
            end_time = time.time()
            latency = end_time - start_time
            
            print(f"✅ WAM Agent invocation successful! (Latency: {latency:.2f}s)")
            print(f"   Response: {output_text[:100]}...")
            
            return {
                "content": output_text,
                "latency": latency,
                "session_id": session_id,
                "trace_data": trace_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error invoking WAM agent: {str(e)}")
            raise
    
    def test_wealth_management_queries(self):
        """Test the WAM agent with sample wealth management queries"""
        print("\n" + "="*60)
        print("🧪 Testing WAM Agent with Wealth Management Queries")
        print("="*60)
        
        test_queries = [
            "What is a mutual fund and how does it work?",
            "Explain the difference between growth and value investing strategies",
            "What are the main risks associated with investing in corporate bonds?",
            "How should a 30-year-old diversify their investment portfolio?",
            "What is the expense ratio in mutual funds and why does it matter?"
        ]
        
        results = []
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test Query {i}/{len(test_queries)} ---")
            print(f"Query: {query}")
            
            try:
                # Test with foundation model
                print("\n🤖 Testing with Foundation Model...")
                fm_result = self.invoke_foundation_model(query)
                
                # Test with WAM agent
                print("\n🏦 Testing with WAM Agent...")
                agent_result = self.invoke_wam_agent(query)
                
                results.append({
                    "query_number": i,
                    "query": query,
                    "foundation_model": fm_result,
                    "wam_agent": agent_result,
                    "test_timestamp": datetime.now().isoformat()
                })
                
                # Small delay between requests to avoid rate limiting
                print("⏳ Waiting 3 seconds before next query...")
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error with query {i}: {str(e)}")
                results.append({
                    "query_number": i,
                    "query": query,
                    "error": str(e),
                    "test_timestamp": datetime.now().isoformat()
                })
        
        print(f"\n✅ Completed {len(results)} test queries!")
        return results
    
    def generate_test_summary(self, results):
        """Generate a summary of test results"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        successful_tests = [r for r in results if "error" not in r]
        failed_tests = [r for r in results if "error" in r]
        
        print(f"✅ Successful tests: {len(successful_tests)}")
        print(f"❌ Failed tests: {len(failed_tests)}")
        
        if successful_tests:
            # Calculate average latencies
            fm_latencies = [r["foundation_model"]["latency"] for r in successful_tests if "foundation_model" in r]
            agent_latencies = [r["wam_agent"]["latency"] for r in successful_tests if "wam_agent" in r]
            
            if fm_latencies:
                avg_fm_latency = sum(fm_latencies) / len(fm_latencies)
                print(f"\n📈 Performance Metrics:")
                print(f"   Average Foundation Model Latency: {avg_fm_latency:.2f}s")
            
            if agent_latencies:
                avg_agent_latency = sum(agent_latencies) / len(agent_latencies)
                print(f"   Average WAM Agent Latency: {avg_agent_latency:.2f}s")
        
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   Query {test['query_number']}: {test['error']}")
        
        print(f"\n🔗 Check your Arize dashboard:")
        print(f"   Project: {self.project_name}")
        print(f"   URL: https://app.arize.com")

def main():
    """Main function to run the instrumented WAM agent"""
    print("=" * 60)
    print("🏦 WAM Agent with Arize Instrumentation")
    print("=" * 60)
    
    try:
        # Initialize the instrumented agent
        wam_agent = WAMAgentInstrumented()
        
        # Run test queries
        results = wam_agent.test_wealth_management_queries()
        
        # Generate summary
        wam_agent.generate_test_summary(results)
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("📊 All traces should now be visible in your Arize dashboard!")
        print("🔗 Go to https://app.arize.com to view your traces")
        print("=" * 60)
        
        return results
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        raise

if __name__ == "__main__":
    main()