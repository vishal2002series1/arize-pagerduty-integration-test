import os
import requests
import json
import time
import boto3
from datetime import datetime, timezone

# Environment variables
ARIZE_SPACE_ID = "U3BhY2U6MTgwMjk6NG9NWQ=="
ARIZE_API_KEY = "ak-b0c26b37-fd3d-4e0c-931c-1ff47ebde4df-5E2bBB6-vUwtMcQJ7ihqIBRSrXRpz_xi"
PAGERDUTY_ROUTING_KEY = "c28663bb4b544e05d03ca534813ea6eb"
PROJECT_NAME = "WAM-agent-monitoring"
AGENT_ID = "BCNKRENPZS"
AGENT_ALIAS_ID = "EALQASLM4U"

# Arize GraphQL endpoint
ARIZE_GRAPHQL_ENDPOINT = "https://app.arize.com/graphql"

def create_evaluator_and_monitor():
    """
    Step 1: Create evaluation task
    Step 2: Create monitor with PagerDuty integration
    """
    
    headers = {
        "Authorization": f"Bearer {ARIZE_API_KEY}",
        "Content-Type": "application/json",
        "space-id": ARIZE_SPACE_ID
    }
    
    # Step 1: Create evaluation task
    create_eval_mutation = """
    mutation CreateOnlineEvalTask {
      createEvalTask(input: {
        modelId: "WAM-agent-monitoring"
        samplingRate: 100
        queryFilter: "attributes.openinference.span.kind = 'AGENT'"
        name: "WAM Agent Quality Evaluator"
        templateEvaluators: {
          name: "response_quality",
          rails: ["poor","good","excellent"],
          template: "Rate the quality of this wealth management response on a scale: poor, good, excellent. Consider accuracy, helpfulness, and professionalism.",
          position: 1,
          includeExplanations: true,
          useFunctionCallingIfAvailable: false
        }
        runContinuously: true
        llmConfig: {
          modelName: GPT_4o,
          provider: openAI,
          temperature: 0
        }
      }) {
        evalTask {
          id
          name
          samplingRate 
          queryFilter
        }
      }
    }
    """
    
    print("🔧 Creating evaluation task...")
    response = requests.post(
        ARIZE_GRAPHQL_ENDPOINT,
        headers=headers,
        json={"query": create_eval_mutation}
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' in result:
            print(f"❌ GraphQL errors: {result['errors']}")
            return None
        
        eval_task = result['data']['createEvalTask']['evalTask']
        print(f"✅ Created evaluation task: {eval_task['name']} (ID: {eval_task['id']})")
        
        # Step 2: Create monitor for the evaluation
        create_monitor_mutation = f"""
        mutation CreateMonitor {{
          createMonitor(input: {{
            modelId: "WAM-agent-monitoring"
            name: "WAM Agent Quality Monitor"
            monitorType: EVALUATION
            evaluationName: "response_quality"
            threshold: {{
              operator: LESS_THAN
              value: 0.7
            }}
            notifications: [{{
              type: PAGERDUTY
              settings: {{
                routingKey: "{PAGERDUTY_ROUTING_KEY}"
                severity: "error"
              }}
            }}]
            schedule: {{
              interval: HOURLY
            }}
          }}) {{
            monitor {{
              id
              name
              monitorType
            }}
          }}
        }}
        """
        
        print("🔧 Creating monitor with PagerDuty integration...")
        monitor_response = requests.post(
            ARIZE_GRAPHQL_ENDPOINT,
            headers=headers,
            json={"query": create_monitor_mutation}
        )
        
        if monitor_response.status_code == 200:
            monitor_result = monitor_response.json()
            if 'errors' in monitor_result:
                print(f"❌ Monitor creation errors: {monitor_result['errors']}")
                return eval_task['id']
            
            monitor = monitor_result['data']['createMonitor']['monitor']
            print(f"✅ Created monitor: {monitor['name']} (ID: {monitor['id']})")
            return eval_task['id']
        else:
            print(f"❌ Monitor creation failed: {monitor_response.status_code}")
            return eval_task['id']
    else:
        print(f"❌ Evaluation task creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def trigger_evaluation_scenarios():
    """
    Step 3: Send various test scenarios to trigger evaluations
    """
    
    # Initialize Bedrock client
    bedrock_agent = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    
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
        }
    ]
    
    print("\n🧪 Running test scenarios to trigger evaluations...")
    
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
            
            # Wait between tests
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error in scenario {i}: {str(e)}")
    
    print(f"\n✅ Completed {len(test_scenarios)} test scenarios")
    print("🔍 Evaluations should start processing shortly...")
    print("📧 Check PagerDuty for alerts if quality thresholds are breached!")

def run_historical_evaluation(task_id):
    """
    Step 4: Run evaluation on historical data
    """
    if not task_id:
        print("❌ No task ID available for historical run")
        return
    
    headers = {
        "Authorization": f"Bearer {ARIZE_API_KEY}",
        "Content-Type": "application/json",
        "space-id": ARIZE_SPACE_ID
    }
    
    # Run on last hour of data
    end_time = datetime.now(timezone.utc)
    start_time = end_time.replace(hour=end_time.hour-1)
    
    run_task_mutation = f"""
    mutation RunOnlineTask {{
      runOnlineTask(
        input: {{
          onlineTaskId: "{task_id}",
          dataStartTime: "{start_time.isoformat()}",
          dataEndTime: "{end_time.isoformat()}",
          maxSpans: 100
        }}
      ) {{
        result {{
          ... on CreateTaskRunResponse {{
            runId
          }}
          ... on TaskError {{
            message
            code
          }}
        }}
      }}
    }}
    """
    
    print(f"\n🔄 Running historical evaluation on task {task_id}...")
    response = requests.post(
        ARIZE_GRAPHQL_ENDPOINT,
        headers=headers,
        json={"query": run_task_mutation}
    )
    
    if response.status_code == 200:
        result = response.json()
        if 'errors' in result:
            print(f"❌ Historical run errors: {result['errors']}")
        else:
            run_result = result['data']['runOnlineTask']['result']
            if 'runId' in run_result:
                print(f"✅ Historical evaluation started: Run ID {run_result['runId']}")
            else:
                print(f"❌ Historical run failed: {run_result.get('message', 'Unknown error')}")
    else:
        print(f"❌ Historical run request failed: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Starting Arize-PagerDuty Integration Test")
    print("=" * 50)
    
    # Step 1 & 2: Create evaluator and monitor
    task_id = create_evaluator_and_monitor()
    
    if task_id:
        print(f"\n⏳ Waiting 30 seconds for setup to complete...")
        time.sleep(30)
        
        # Step 3: Trigger evaluation scenarios
        trigger_evaluation_scenarios()
        
        print(f"\n⏳ Waiting 60 seconds for evaluations to process...")
        time.sleep(60)
        
        # Step 4: Run historical evaluation
        run_historical_evaluation(task_id)
        
        print("\n" + "=" * 50)
        print("🎯 Test Complete! Next Steps:")
        print("1. Check Arize dashboard for evaluation results")
        print("2. Monitor PagerDuty for alerts")
        print("3. Review evaluation quality scores")
        print("4. Test monitor threshold adjustments")
    else:
        print("❌ Setup failed - cannot proceed with testing")