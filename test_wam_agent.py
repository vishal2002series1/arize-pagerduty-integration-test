import os
from dotenv import load_dotenv
from wam_agent_instrumented import WAMAgentInstrumented

# Load environment variables
load_dotenv()
# export no_proxy=otlp.arize.com

def quick_test():
    """Quick test of the WAM agent"""
    print("🧪 Running Quick WAM Agent Test")
    print("=" * 40)
    
    try:
        # Initialize agent
        agent = WAMAgentInstrumented()
        
        # Single test query
        test_query = "What is a mutual fund and how does it differ from an ETF?"
        print(f"\n🔍 Testing query: {test_query}")
        
        # Test foundation model
        print("\n🤖 Testing Foundation Model...")
        fm_response = agent.invoke_foundation_model(test_query)
        
        # Test WAM agent
        print("\n🏦 Testing WAM Agent...")
        agent_response = agent.invoke_wam_agent(test_query)
        
        print("\n" + "=" * 40)
        print("✅ Quick test completed successfully!")
        print("📊 Check your Arize dashboard for traces!")
        print("🔗 URL: https://app.arize.com")
        print("=" * 40)
        
        return {
            "foundation_model": fm_response,
            "wam_agent": agent_response
        }
        
    except Exception as e:
        print(f"❌ Quick test failed: {str(e)}")
        raise
    finally:
        # ❗️ IMPORTANT: Shutdown the tracer to flush all pending traces
        if agent and hasattr(agent, 'tracer_provider'):
            print("👋 Shutting down OpenTelemetry tracer...")
            agent.tracer_provider.shutdown()
            print("✅ Tracer shut down successfully.")

if __name__ == "__main__":
    quick_test()