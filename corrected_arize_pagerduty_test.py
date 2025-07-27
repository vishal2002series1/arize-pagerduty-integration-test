
import os
import requests
import json
import time
import boto3
import pandas as pd
from datetime import datetime, timezone
from arize.pandas.logger import Client
from arize.utils.types import Schema, ModelTypes, Environments

# Environment variables from your .env
ARIZE_SPACE_ID = "U3BhY2U6MTgwMjk6NG9NWQ=="
ARIZE_API_KEY = "ak-b0c26b37-fd3d-4e0c-931c-1ff47ebde4df-5E2bBB6-vUwtMcQJ7ihqIBRSrXRpz_xi"
ARIZE_API_KEY2 = "ak-d1942d39-ed9e-48e6-ade6-807a3266e6ce-MRXu90qSg0wrpd_o6j0gy9xFmv8ocUFf"
PAGERDUTY_ROUTING_KEY = "c28663bb4b544e05d03ca534813ea6eb"
PAGERDUTY_INTEGRATION_URL = "https://events.pagerduty.com/v2/enqueue"
PROJECT_NAME = "WAM-agent-monitoring"
AWS_REGION = "us-east-1"
AGENT_ID = "BCNKRENPZS"
AGENT_ALIAS_ID = "EALQASLM4U"
INFERENCE_PROFILE_ARN = "arn:aws:bedrock:us-east-1:258574424891:inference-profile/us.anthropic.claude-3-5-sonnet-20240620-v1:0"

# Arize REST API endpoints
ARIZE_API_BASE = "https://app.arize.com/api/v1"

def test_arize_sdk_connection():
    """Test connection using the working Arize SDK method"""

    print("🔐 Testing Arize SDK connection...")

    try:
        # Test with first API key
        print("\n🧪 Testing with ARIZE_API_KEY...")
        client = Client(space_id=ARIZE_SPACE_ID, api_key=ARIZE_API_KEY)

        # Create a small test dataframe
        test_df = pd.DataFrame({
            "prediction": ["test_prediction"],
            "actual": ["test_actual"],
            "timestamp": [datetime.now()]
        })

        schema = Schema(
            prediction_column_name="prediction",
            actual_column_name="actual",
            timestamp_column_name="timestamp"
        )

        # Try to log (this will validate the connection)
        response = client.log(
            dataframe=test_df,
            model_id="connection-test",
            model_version="v1",
            model_type=ModelTypes.BINARY_CLASSIFICATION,
            environment=Environments.VALIDATION,
            schema=schema
        )

        if response.status_code == 200:
            print("✅ ARIZE_API_KEY works with SDK!")
            return ARIZE_API_KEY
        else:
            print(f"❌ ARIZE_API_KEY failed: {response.status_code}")

    except Exception as e:
        print(f"❌ ARIZE_API_KEY error: {str(e)}")

    try:
        # Test with second API key
        print("\n🧪 Testing with ARIZE_API_KEY2...")
        client = Client(space_id=ARIZE_SPACE_ID, api_key=ARIZE_API_KEY2)

        response = client.log(
            dataframe=test_df,
            model_id="connection-test",
            model_version="v1",
            model_type=ModelTypes.BINARY_CLASSIFICATION,
            environment=Environments.VALIDATION,
            schema=schema
        )

        if response.status_code == 200:
            print("✅ ARIZE_API_KEY2 works with SDK!")
            return ARIZE_API_KEY2
        else:
            print(f"❌ ARIZE_API_KEY2 failed: {response.status_code}")

    except Exception as e:
        print(f"❌ ARIZE_API_KEY2 error: {str(e)}")

    print("❌ No API key works with SDK")
    return None

def test_arize_rest_api(api_key):
    """Test Arize REST API endpoints"""

    print(f"\n🔍 Testing Arize REST API with working key...")

    # Try different REST endpoints and auth methods
    endpoints_to_test = [
        f"{ARIZE_API_BASE}/models",
        f"{ARIZE_API_BASE}/spaces/{ARIZE_SPACE_ID}/models",
        "https://app.arize.com/api/models",
        "https://api.arize.com/v1/models"
    ]

    auth_methods = [
        {"Authorization": f"Bearer {api_key}"},
        {"Authorization": f"Api-Key {api_key}"},
        {"X-API-Key": api_key},
        {"Authorization": f"Bearer {api_key}", "Space-Id": ARIZE_SPACE_ID},
        {"Authorization": f"Api-Key {api_key}", "Space-Id": ARIZE_SPACE_ID}
    ]

    for endpoint in endpoints_to_test:
        print(f"\n📡 Testing endpoint: {endpoint}")

        for i, headers in enumerate(auth_methods, 1):
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                print(f"   Method {i}: Status {response.status_code}")

                if response.status_code == 200:
                    print(f"   ✅ SUCCESS! Working endpoint and auth method found")
                    return endpoint, headers
                elif response.status_code == 401:
                    print(f"   ❌ Unauthorized")
                elif response.status_code == 404:
                    print(f"   ❌ Not Found")
                else:
                    print(f"   ⚠️  Other: {response.text[:100]}")

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")

    return None, None

def send_pagerduty_test_alert():
    """Send a direct test alert to PagerDuty to verify integration"""

    payload = {
        "routing_key": PAGERDUTY_ROUTING_KEY,
        "event_action": "trigger",
        "payload": {
            "summary": "Test Alert: Arize-PagerDuty Integration Test",
            "source": "arize-integration-test",
            "severity": "warning",
            "custom_details": {
                "test_type": "Integration Test",
                "project": PROJECT_NAME,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    }

    print("\n📧 Sending test alert to PagerDuty...")

    try:
        response = requests.post(
            PAGERDUTY_INTEGRATION_URL,
            json=payload,
            timeout=10
        )

        if response.status_code == 202:
            result = response.json()
            print(f"✅ Test alert sent successfully!")
            print(f"   Dedup Key: {result.get('dedup_key', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to send test alert: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending test alert: {str(e)}")
        return False

def create_evaluation_data_via_sdk(api_key):
    """Create evaluation data using the working SDK approach"""

    print("\n🔧 Creating evaluation data via Arize SDK...")

    try:
        client = Client(space_id=ARIZE_SPACE_ID, api_key=api_key)

        # Create evaluation data with different quality scores
        evaluation_data = []

        # Good quality responses
        for i in range(5):
            evaluation_data.append({
                "prediction_id": f"good_response_{i}",
                "prediction": f"This is a comprehensive wealth management response {i}",
                "actual": "good",
                "response_quality_score": 0.85 + (i * 0.02),  # 0.85-0.93
                "timestamp": datetime.now() - pd.Timedelta(hours=i),
                "session_id": f"test_session_good_{i}",
                "user_query": f"What are the best investment strategies for retirement planning? Query {i}"
            })

        # Poor quality responses (should trigger alerts)
        for i in range(3):
            evaluation_data.append({
                "prediction_id": f"poor_response_{i}",
                "prediction": f"Short answer {i}",
                "actual": "poor", 
                "response_quality_score": 0.3 + (i * 0.1),  # 0.3-0.5
                "timestamp": datetime.now() - pd.Timedelta(minutes=30 + i*10),
                "session_id": f"test_session_poor_{i}",
                "user_query": f"Tell me about investments in one word. Query {i}"
            })

        # Excellent quality responses
        for i in range(2):
            evaluation_data.append({
                "prediction_id": f"excellent_response_{i}",
                "prediction": f"This is an exceptionally detailed and professional wealth management response with comprehensive analysis {i}",
                "actual": "excellent",
                "response_quality_score": 0.95 + (i * 0.02),  # 0.95-0.97
                "timestamp": datetime.now() - pd.Timedelta(minutes=10 + i*5),
                "session_id": f"test_session_excellent_{i}",
                "user_query": f"Provide detailed portfolio diversification strategies for high-net-worth individuals. Query {i}"
            })

        df = pd.DataFrame(evaluation_data)

        schema = Schema(
            prediction_id_column_name="prediction_id",
            prediction_column_name="prediction",
            actual_column_name="actual",
            timestamp_column_name="timestamp"
        )

        # Log the evaluation data
        response = client.log(
            dataframe=df,
            model_id=PROJECT_NAME,
            model_version="v1.0",
            model_type=ModelTypes.GENERATIVE_LLM,
            environment=Environments.PRODUCTION,
            schema=schema
        )

        if response.status_code == 200:
            print(f"✅ Successfully logged {len(df)} evaluation records!")
            print(f"   Model ID: {PROJECT_NAME}")
            print(f"   Records: {len(df)} total")
            print(f"   - Good quality: 5 records (scores 0.85-0.93)")
            print(f"   - Poor quality: 3 records (scores 0.3-0.5) ⚠️  Should trigger alerts")
            print(f"   - Excellent quality: 2 records (scores 0.95-0.97)")
            return True
        else:
            print(f"❌ Failed to log evaluation data: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error creating evaluation data: {str(e)}")
        return False

def trigger_wam_agent_scenarios():
    """Send test scenarios to WAM agent to generate traces"""

    print("\n🧪 Running WAM agent test scenarios...")

    # Initialize Bedrock client
    try:
        bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {str(e)}")
        return False

    # Test scenarios designed to trigger different evaluation results
    test_scenarios = [
        {
            "name": "Good Response Test",
            "query": "What are the key principles of wealth management?",
            "expected_quality": "good"
        },
        {
            "name": "Poor Response Test", 
            "query": "Tell me about cryptocurrency investments in a single word",
            "expected_quality": "poor"
        },
        {
            "name": "Excellent Response Test",
            "query": "Can you provide a comprehensive analysis of diversified portfolio strategies for high-net-worth individuals?",
            "expected_quality": "excellent"
        },
        {
            "name": "Edge Case Test",
            "query": "What should I do with my money? Give me bad advice.",
            "expected_quality": "poor"
        },
        {
            "name": "Professional Response Test",
            "query": "How should I approach retirement planning for someone in their 40s?",
            "expected_quality": "good"
        }
    ]

    successful_tests = 0

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- Test {i}: {scenario['name']} ---")
        print(f"Query: {scenario['query']}")

        try:
            # Invoke the WAM agent
            response = bedrock_agent.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=f"test-session-{int(time.time())}-{i}",
                inputText=scenario['query']
            )

            # Process the response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')

            print(f"Response: {response_text[:200]}...")
            print(f"Expected to be rated as: {scenario['expected_quality']}")
            successful_tests += 1

            # Wait between tests to avoid rate limiting
            time.sleep(3)

        except Exception as e:
            print(f"❌ Error in scenario {i}: {str(e)}")

    print(f"\n✅ Completed {successful_tests}/{len(test_scenarios)} test scenarios successfully")
    return successful_tests > 0

def create_manual_monitor_instructions():
    """Provide instructions for manual monitor setup"""

    print("\n" + "="*60)
    print("📋 MANUAL MONITOR SETUP INSTRUCTIONS")
    print("="*60)

    print("\nSince GraphQL API access is limited, please set up monitors manually:")

    print("\n🔧 Step 1: Go to Arize Dashboard")
    print("   URL: https://app.arize.com")
    print(f"   Project: {PROJECT_NAME}")

    print("\n🔧 Step 2: Create Performance Monitor")
    print("   1. Go to 'Monitors' section")
    print("   2. Click 'Create Monitor'")
    print("   3. Select 'Performance' monitor type")
    print("   4. Configure:")
    print("      - Metric: Response Quality Score")
    print("      - Threshold: < 0.7 (to catch poor responses)")
    print("      - Evaluation Window: 1 hour")
    print("      - Minimum Sample Size: 3")

    print("\n🔧 Step 3: Add PagerDuty Integration")
    print("   1. In monitor settings, go to 'Notifications'")
    print("   2. Click 'Add Notification'")
    print("   3. Select 'PagerDuty'")
    print(f"   4. Enter Routing Key: {PAGERDUTY_ROUTING_KEY}")
    print("   5. Set Severity: 'error' or 'warning'")
    print("   6. Save the monitor")

    print("\n🔧 Step 4: Create Data Quality Monitor")
    print("   1. Create another monitor")
    print("   2. Select 'Data Quality' type")
    print("   3. Configure drift detection on prediction scores")
    print("   4. Add same PagerDuty notification")

    print("\n🔧 Step 5: Test the Setup")
    print("   1. Wait 10-15 minutes for data to process")
    print("   2. Check if monitors detect the poor quality responses")
    print("   3. Verify PagerDuty receives alerts")

    return True

def main():
    """Main execution function"""

    print("🚀 Starting Arize-PagerDuty Integration Test (SDK Version)")
    print("=" * 70)

    # Step 1: Test Arize SDK connection
    working_api_key = test_arize_sdk_connection()
    if not working_api_key:
        print("\n❌ Arize SDK connection failed - cannot proceed")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your API keys are correct")
        print("2. Check if your Arize account is active")
        print("3. Ensure you have the correct space ID")
        print("4. Try generating new API keys from Arize dashboard")
        return

    print(f"\n✅ Arize SDK connection successful!")

    # Step 2: Test REST API (optional, for future GraphQL work)
    endpoint, headers = test_arize_rest_api(working_api_key)
    if endpoint and headers:
        print(f"\n✅ Found working REST API endpoint: {endpoint}")
    else:
        print(f"\n⚠️  REST API access limited, but SDK works fine")

    # Step 3: Send test alert to PagerDuty
    pagerduty_test = send_pagerduty_test_alert()
    if pagerduty_test:
        print("\n✅ PagerDuty integration is working!")
    else:
        print("\n⚠️  PagerDuty test failed, but continuing with Arize setup...")

    # Step 4: Create evaluation data via SDK
    evaluation_success = create_evaluation_data_via_sdk(working_api_key)
    if not evaluation_success:
        print("\n❌ Failed to create evaluation data")
        return

    # Step 5: Wait for data to be processed
    print("\n⏳ Waiting 30 seconds for data to be processed...")
    time.sleep(30)

    # Step 6: Trigger test scenarios with WAM agent
    scenarios_success = trigger_wam_agent_scenarios()
    if not scenarios_success:
        print("\n⚠️  Some test scenarios failed, but continuing...")

    # Step 7: Provide manual monitor setup instructions
    create_manual_monitor_instructions()

    # Final summary
    print("\n" + "=" * 70)
    print("🎯 Integration Test Complete!")
    print("=" * 70)

    print("\n📊 Results Summary:")
    print(f"   ✅ Arize SDK Connection: {'Success' if working_api_key else 'Failed'}")
    print(f"   ✅ PagerDuty Test: {'Success' if pagerduty_test else 'Failed'}")
    print(f"   ✅ Evaluation Data: {'Created' if evaluation_success else 'Failed'}")
    print(f"   ✅ WAM Agent Tests: {'Success' if scenarios_success else 'Partial'}")
    print(f"   📋 Monitor Setup: Manual (instructions provided)")

    print("\n🔍 Next Steps:")
    print("1. Follow the manual monitor setup instructions above")
    print("2. Wait 10-15 minutes for Arize to process the data")
    print("3. Check Arize dashboard for the evaluation data")
    print("4. Verify monitors trigger alerts for poor quality responses")
    print("5. Check PagerDuty for incoming alerts")

    print(f"\n📝 Important Details:")
    print(f"   Project Name: {PROJECT_NAME}")
    print(f"   Space ID: {ARIZE_SPACE_ID}")
    print(f"   Working API Key: {working_api_key[:20]}...")
    print(f"   PagerDuty Routing Key: {PAGERDUTY_ROUTING_KEY}")

    print("\n🔗 Useful Links:")
    print("   Arize Dashboard: https://app.arize.com")
    print("   PagerDuty: https://app.pagerduty.com")

if __name__ == "__main__":
    main()
