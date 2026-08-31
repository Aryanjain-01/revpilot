import os
import sys
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from agents.analyst_agent import create_agent_graph
from agents.content_utils import extract_text_content

def run_agent(question: str):
    """Run the agent, log the trajectory, and print the demo output."""
    
    # Ensure environment variables are loaded
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is not configured. Add it to .env before running the agent.")
        return
        
    print("-" * 50)
    print("USER QUESTION")
    print("-" * 50)
    print(f"{question}\n")
    
    print("-" * 50)
    print("AGENT ACTIVITY")
    print("-" * 50)
    
    # Initialize the graph
    app = create_agent_graph()
    
    # Setup initial state
    inputs = {
        "user_question": question,
        "messages": [HumanMessage(content=question)]
    }
    
    trajectory_log = {
        "timestamp": datetime.now().isoformat(),
        "user_question": question,
        "tool_calls": [],
        "execution_success": False,
        "final_answer": "",
        "error": None
    }
    
    final_state = None
    try:
        # Stream the graph execution to observe intermediate steps
        for event in app.stream(inputs, stream_mode="values"):
            messages = event.get("messages", [])
            if not messages:
                continue
                
            last_message = messages[-1]
            
            # If the LLM made a tool call
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    print(f"Tool: {tool_call['name']}")
                    print(f"Input: {tool_call['args']}\n")
                    
                    trajectory_log["tool_calls"].append({
                        "tool": tool_call['name'],
                        "arguments": tool_call['args'],
                        "result": None # Will be filled in the next step
                    })
                    
            # If this is a tool message (result from the tool)
            elif last_message.type == "tool":
                result_str = last_message.content
                # Truncate for terminal display
                display_result = result_str[:200] + "..." if len(result_str) > 200 else result_str
                print(f"Tool Result:\n{display_result}\n")
                
                # Update the last recorded tool call in the trajectory with the result
                if trajectory_log["tool_calls"]:
                    trajectory_log["tool_calls"][-1]["result"] = result_str
                    
            final_state = event
            
        trajectory_log["execution_success"] = True
        
    except Exception as e:
        print(f"\nAgent execution failed.")
        trajectory_log["error"] = str(e)
        trajectory_log["execution_success"] = False
        
    if trajectory_log["execution_success"] and final_state and "messages" in final_state:
        # The last message is the final answer from the LLM
        final_answer = extract_text_content(final_state["messages"][-1].content)
        trajectory_log["final_answer"] = final_answer
        
        print("-" * 50)
        print("FINAL ANSWER")
        print("-" * 50)
        print(f"{final_answer}\n")
    elif trajectory_log["error"]:
        print("-" * 50)
        print("ERROR")
        print("-" * 50)
        print(f"{trajectory_log['error']}\n")
        
    # Save the trace
    os.makedirs('logs/agent_runs', exist_ok=True)
    filename = f"logs/agent_runs/trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(trajectory_log, f, indent=2)
        
    print(f"(Trajectory logged to {filename})")

def main():
    questions = [
        "How did revenue change between September and October 2023?",
        "Which products experienced significant stockouts?",
        "Are there customers whose revenue dropped significantly between September and October 2023?",
        "Did profit change differently from revenue between September and October 2023?"
    ]
    
    for q in questions:
        run_agent(q)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
