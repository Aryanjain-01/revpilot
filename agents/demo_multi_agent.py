import os
import sys
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from agents.orchestrator import create_multi_agent_graph
from agents.content_utils import extract_text_content

def run_multi_agent(question: str):
    """Run the multi-agent workflow, log trajectory, and print output."""
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not configured. Add it to .env before running the agent.")
        return
        
    print("-" * 50)
    print("USER QUESTION")
    print("-" * 50)
    print(f"{question}\n")
    
    print("-" * 50)
    print("ORCHESTRATOR ACTIVITY")
    print("-" * 50)
    
    app = create_multi_agent_graph()
    
    inputs = {
        "user_question": question,
        "messages": []
    }
    
    trajectory_log = {
        "timestamp": datetime.now().isoformat(),
        "user_question": question,
        "investigation_plan": {},
        "specialists_activity": [],
        "verification_results": {},
        "decision_result": {},
        "errors": {},
        "synthesis_result": "",
        "execution_success": False
    }
    
    try:
        final_state = None
        for step in app.stream(inputs, stream_mode="values"):
            # Update trajectory with latest state
            final_state = step
            if "investigation_plan" in step and not trajectory_log["investigation_plan"]:
                trajectory_log["investigation_plan"] = step["investigation_plan"]
                print("Orchestrator Decision:")
                print(f"Selected Agents: {step['investigation_plan'].get('selected_agents')}")
                print(f"Reason: {step['investigation_plan'].get('reason')}\n")
                
        if final_state:
            # Gather findings for the log
            if final_state.get("sales_findings"):
                trajectory_log["specialists_activity"].append(final_state["sales_findings"])
            if final_state.get("inventory_findings"):
                trajectory_log["specialists_activity"].append(final_state["inventory_findings"])
            if final_state.get("customer_findings"):
                trajectory_log["specialists_activity"].append(final_state["customer_findings"])

            trajectory_log["verification_results"] = final_state.get("verification_results", {})
            trajectory_log["decision_result"] = final_state.get("decision_result", {})
                
            trajectory_log["errors"] = final_state.get("agent_errors", {})
            trajectory_log["synthesis_result"] = extract_text_content(final_state.get("final_answer", ""))
            
        trajectory_log["execution_success"] = True
        
    except Exception as e:
        print(f"\nWorkflow execution failed.")
        trajectory_log["errors"] = {"workflow": str(e)}
        trajectory_log["execution_success"] = False
        
    if trajectory_log["synthesis_result"]:
        print("-" * 50)
        print("SYNTHESIS RESULT")
        print("-" * 50)
        print(f"{trajectory_log['synthesis_result']}\n")
        
    os.makedirs('logs/agent_runs', exist_ok=True)
    filename = f"logs/agent_runs/multi_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(trajectory_log, f, indent=2)
        
    print(f"(Trajectory logged to {filename})")

def main():
    questions = [
        "Did profit change differently from revenue between September and October 2023?"
    ]
    
    for q in questions:
        run_multi_agent(q)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
