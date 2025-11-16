import os
import json
import sys
import google.generativeai as genai
from langgraph.graph import StateGraph, END
import importlib
import io
import time
from algosdk.v2client import algod
from algosdk.transaction import ApplicationNoOpTxn, PaymentTxn, wait_for_confirmation
from algosdk import mnemonic, account

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN = ""
APP_ID = 749534825 
USE_MOCK_AI = False

EXPERT_MN = "father eye direct lava stay process tuna anger picture ahead differ hand habit hobby curious local book history trust arrow hidden broken bench abstract forward"
expert_pk = mnemonic.to_private_key(EXPERT_MN)
expert_addr = account.address_from_private_key(expert_pk)

AGENT_MN = "fluid vintage inspire matrix quarter paddle crater matrix wreck cube buddy opinion guess split erode teach base horse oxygen mouse decrease session icon absent memory"
agent_pk = mnemonic.to_private_key(AGENT_MN)
agent_addr = account.address_from_private_key(agent_pk)

client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

GEMINI_API_KEY = "AIzaSyBp7Tl7twQ0SMGOC2Ypjt2WAH6ORrO5Xmc"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")  # Use stable model

# Helper functions
def log_message(level: str, message: str, max_length: int = 100) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    prefix = f"{timestamp} [{level.upper()}]"
    
    if len(message) > max_length:
        message = message[:max_length] + "..."
        
    print(f"{prefix} {message}")

def call_gemini_safe(prompt: str, timeout_seconds: int = 30) -> tuple[bool, str | None]:
    if USE_MOCK_AI:
        log_message("info", f"Using mock response")
        return True, f"Mock response for: {prompt[:50]}..."
    
    log_message("debug", f"Calling Gemini...")
    start_time = time.time()
    
    try:
        response = model.generate_content(prompt)
        elapsed = time.time() - start_time
        
        if not response.text:
            raise ValueError("Empty response from Gemini API")
            
        log_message("info", f"Gemini API success ({elapsed:.2f}s)")
        return True, response.text.strip()
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Gemini API error: {str(e)[:50]}"
        log_message("error", error_msg)
        
        if "quota" in str(e).lower():
            log_message("warn", "API quota exceeded, using fallback")
            return True, f"[MOCK] Response for: {prompt[:50]}..."
            
        return False, None

# Blockchain functions
def register_task_on_chain(hash_value: str) -> dict:
    log_message("info", f"Registering task: {hash_value}")
    
    try:
        sp = client.suggested_params()
        
        txn = ApplicationNoOpTxn(
            sender=agent_addr,
            sp=sp,
            index=APP_ID,
            app_args=[b"register_task", hash_value.encode()],
        )
        
        signed = txn.sign(agent_pk)
        txid = client.send_transaction(signed)
        log_message("debug", f"TX submitted: {txid}")
        
        result = wait_for_confirmation(client, txid, 4)
        
        log_message("info", f"Registered in round {result['confirmed-round']}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to register: {str(e)}"
        log_message("error", error_msg)
        raise Exception(error_msg) from e

def get_agent_balance() -> float:
    try:
        agent_info = client.account_info(agent_addr)
        return agent_info['amount'] / 1_000_000
    except Exception as e:
        log_message("error", f"Failed to get balance: {str(e)}")
        return 0.0

def approve_and_release_payment() -> dict:
    log_message("info", "Releasing payment")
    
    try:
        initial_balance = get_agent_balance()
        log_message("debug", f"Agent balance: {initial_balance} ALGO")
        
        sp = client.suggested_params()
        
        txn = ApplicationNoOpTxn(
            sender=expert_addr,
            sp=sp,
            index=APP_ID,
            app_args=[b"approve_and_release"],
            accounts=[agent_addr]
        )
        
        signed = txn.sign(expert_pk)
        txid = client.send_transaction(signed)
        log_message("info", f"Payment TX: {txid}")
        
        result = wait_for_confirmation(client, txid, 4)
        
        final_balance = get_agent_balance()
        amount_sent = final_balance - initial_balance
        
        log_message("info", f"Payment of {amount_sent:.4f} ALGO sent. New balance: {final_balance} ALGO")
        
        return result
        
    except Exception as e:
        error_msg = f"Payment failed: {str(e)}"
        log_message("error", error_msg)
        raise Exception(error_msg) from e

# State definition
from typing import TypedDict

class ExpertState(TypedDict, total=False):
    task: str
    result: str
    understanding: str
    verdict: str
    feedback: str
    approved: bool
    result_hash: str
    blockchain_registered: bool
    payment_released: bool

# AI processing functions
def understand_task(state: ExpertState):
    print(f"\n Understanding task...")
    
    prompt = f"Briefly summarize this task in one sentence: {state['task']}"
    success, response = call_gemini_safe(prompt)
    
    if success:
        state["understanding"] = response
    else:
        state["understanding"] = f"Task involves {state['task'].split()[0]} service"
    
    print(f"   → {state['understanding'][:80]}...")
    return state

def get_agent_for_task(task_description: str) -> str:
    task_lower = task_description.lower()
    
    agent_mapping = [
        (["taxi", "cab", "uber", "ride", "car"], "taxi_agent"),
        (["hotel", "accommodation", "stay", "room"], "hotel_agent"),
        (["flight", "airline", "airport", "fly"], "flight_agent"),
        (["food", "restaurant", "dine", "eat", "meal"], "food_agent"),
    ]
    
    for keywords, agent_name in agent_mapping:
        if any(keyword in task_lower for keyword in keywords):
            return agent_name
    
    return "generic_agent"

def route_to_agent(state: ExpertState) -> ExpertState:
    print("\nRouting to agent...")
    
    mock_responses = {
        "taxi_agent": "Uber booked: Driver Raj, Toyota Innova, ETA: 15 mins, ₹450",
        "hotel_agent": "Hotel Taj booked: Deluxe Room, 2 nights, ₹8,500/night",
        "flight_agent": "Flight AI-101: Delhi→Mumbai, 3:30 PM, Seat 12A, ₹4,200",
        "food_agent": "Table for 2 at The Spice Route, 8:00 PM",
    }
    
    try:
        agent_name = get_agent_for_task(state["task"])
        print(f"   → {agent_name}")
        
        state["result"] = mock_responses.get(agent_name, f"Task processed by {agent_name}")
        
        print(f"   → {state['result'][:60]}...")
        return state
        
    except Exception as e:
        print(f"   → Error: {str(e)}")
        state["result"] = f"Error: {str(e)}"
        state["approved"] = False
        return state

def evaluate_result(state: ExpertState):
    print(f"\nEvaluating result...")
    
    prompt = f"Does this solve the task? Answer 'yes' or 'no'.\nTask: {state['task']}\nResult: {state['result']}"
    success, response = call_gemini_safe(prompt, timeout_seconds=15)
    
    if success:
        state["verdict"] = "yes" if "yes" in response.lower() else "no"
    else:
        state["verdict"] = "yes"
    
    print(f"   → Verdict: {state['verdict']}")
    return state

def generate_feedback(state: ExpertState):
    print(f"\nGenerating feedback...")
    
    prompt = f"Short feedback (max 20 words):\nTask: {state['task']}\nResult: {state['result']}"
    success, response = call_gemini_safe(prompt, timeout_seconds=15)
    
    if success:
        state["feedback"] = response
    else:
        state["feedback"] = "Result meets requirements."
    
    state["approved"] = state["verdict"] == "yes"
    
    print(f"   → Approved: {state['approved']}")
    print(f"   → {state['feedback'][:60]}...")
    
    return state

def blockchain_integration(state: ExpertState):
    if not state.get("approved"):
        return state
    
    print(f"\n{'='*60}")
    print(f" TASK APPROVED - BLOCKCHAIN INTEGRATION")
    print(f"{'='*60}")
    
    import hashlib
    result_str = str(state["result"])
    result_hash = hashlib.sha256(result_str.encode()).hexdigest()[:32]
    state["result_hash"] = result_hash
    print(f"Hash: {result_hash}")
    
    try:
        register_task_on_chain(result_hash)
        state["blockchain_registered"] = True
        
        approve_and_release_payment()
        state["payment_released"] = True
        
        print(f"\n{'='*60}")
        print(f"SUCCESS!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n Error: {str(e)[:100]}")
        state["blockchain_registered"] = False
        state["payment_released"] = False
    
    return state

# Graph building - FIXED
def build_graph() -> StateGraph:
    try:
        log_message("debug", "Building graph")
        
        graph = StateGraph(ExpertState)
        
        # Add nodes
        graph.add_node("understand", understand_task)
        graph.add_node("route", route_to_agent)
        graph.add_node("evaluate", evaluate_result)
        graph.add_node("feedback", generate_feedback)
        graph.add_node("blockchain", blockchain_integration)
        
        # Add edges
        graph.add_edge("understand", "route")
        graph.add_edge("route", "evaluate")
        graph.add_edge("evaluate", "feedback")
        
        # Conditional edge
        def should_continue(state: ExpertState) -> str:
            return "blockchain" if state.get("approved", False) else END
        
        graph.add_conditional_edges(
            "feedback",
            should_continue,
            {"blockchain": "blockchain", END: END}
        )
        
        graph.add_edge("blockchain", END)
        
        # *** CRITICAL: SET ENTRY POINT ***
        graph.set_entry_point("understand")
        
        log_message("debug", "Graph built successfully")
        return graph.compile()
        
    except Exception as e:
        log_message("error", f"Failed to build graph: {str(e)}")
        raise

# Main execution
def initialize_application() -> None:
    print(f"\n{'='*60}")
    print(f" AI EXPERT SYSTEM + BLOCKCHAIN")
    print(f"{'='*60}")
    print(f"Mode: {'MOCK' if USE_MOCK_AI else 'REAL AI'}")
    print(f"Expert: {expert_addr[:10]}...")
    print(f"Agent: {agent_addr[:10]}...")
    print(f"Contract: {APP_ID}")
    print(f"{'='*60}\n")

def get_task_input() -> str:
    task = input("Task: ")
    if not task:
        task = "Book a flight from Delhi to Mumbai and a taxi to hotel"
        print(f"Using default: {task}")
    return task

def display_final_results(state: ExpertState) -> None:
    print(f"\n{'='*60}")
    print(f" FINAL RESULTS")
    print(f"{'='*60}")
    print(f" Task: {state['task'][:50]}...")
    print(f" Result: {state['result'][:50]}...")
    print(f" Approved: {state['approved']}")
    print(f" Blockchain: {state.get('blockchain_registered', False)}")
    print(f" Payment: {state.get('payment_released', False)}")
    
    if state.get('result_hash'):
        print(f" Hash: {state['result_hash']}")
    
    print(f"\n🔗 https://lora.algokit.io/testnet/application/{APP_ID}")

if __name__ == "__main__":
    try:
        initialize_application()
        task = get_task_input()
        
        log_message("info", f"Processing: {task[:50]}...")
        
        workflow = build_graph()
        final_state = workflow.invoke({"task": task})
        
        display_final_results(final_state)
        
        # Save results
        with open("last_result.json", "w") as f:
            json.dump({k: str(v) for k, v in final_state.items()}, f, indent=2)
        print("\n Saved to: last_result.json")
        
        log_message("info", "Completed successfully")
        
    except KeyboardInterrupt:
        log_message("warning", "Interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        log_message("critical", f"Fatal error: {str(e)}")
        print(f"\n Error: {str(e)}")
        sys.exit(1)
