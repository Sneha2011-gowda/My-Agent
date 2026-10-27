import os, random
from groq import Groq

client = Groq(api_key="")

def ask_groq(prompt):
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content

# --- FAKE DATABASE (for demo) ---
ORDERS = {
    "ORD123": {"status": "Shipped", "item": "Nike Shoes", "amount": 2999, "delivery": "Tomorrow"},
    "ORD124": {"status": "Delivered", "item": "iPhone Cover", "amount": 499, "delivery": "Delivered on Oct 10"},
    "ORD125": {"status": "Processing", "item": "Laptop Stand", "amount": 1299, "delivery": "In 3 days"},
}

FAQS = {
    "return": "You can return any product within 7 days. Go to My Orders > Return.",
    "refund": "Refund is processed in 3-5 business days to your original payment method.",
    "delivery": "Standard delivery takes 3-5 days. Express delivery takes 1-2 days.",
    "cancel": "You can cancel your order before it is shipped from My Orders > Cancel.",
    "warranty": "All electronics have 1 year warranty. Keep your invoice.",
}

# --- TOOLS ---
def tool_check_order(order_id: str):
    order_id = order_id.strip().upper()
    if order_id in ORDERS:
        o = ORDERS[order_id]
        return f"Order {order_id}: {o['item']} - Status: {o['status']}, Amount: Rs.{o['amount']}, Delivery: {o['delivery']}"
    return f"Order {order_id} not found. Please check ID. Try ORD123, ORD124, ORD125 for demo."

def tool_process_refund(order_id: str):
    order_id = order_id.strip().upper()
    if order_id in ORDERS:
        return f"Refund initiated for {order_id} of Rs.{ORDERS[order_id]['amount']}. It will reflect in 3-5 business days. Refund ID: REF{random.randint(1000,9999)}"
    return "Order not found, cannot process refund."

def tool_search_faq(query: str):
    query = query.lower()
    for key, ans in FAQS.items():
        if key in query:
            return ans
    return "FAQ: For return, refund, delivery, cancel, warranty - please ask specific question."

def tool_create_ticket(issue: str):
    ticket_id = f"TKT{random.randint(10000,99999)}"
    return f"Ticket created: {ticket_id} for issue: '{issue}'. Our team will contact you in 24 hours."

TOOLS = {
    "check_order": tool_check_order,
    "process_refund": tool_process_refund,
    "search_faq": tool_search_faq,
    "create_ticket": tool_create_ticket,
}

SYSTEM_PROMPT = """
You are a helpful Customer Support Agent for an e-commerce company.
You solve ALL customer support problems.

Tools:
1. check_order(order_id) - to check order status. e.g. check_order(ORD123)
2. process_refund(order_id) - to start refund
3. search_faq(query) - for return/refund/delivery/cancel/warranty policy
4. create_ticket(issue) - if problem is complex, complaint, or user is angry

Follow ReAct:
Thought:...
Action: tool_name(input)
Observation:...
Final Answer:...

Rules:
- Always be polite, empathetic, short.
- If user gives Order ID, ALWAYS use check_order first.
- If user wants refund, check order then process_refund.
- If user is angry / says 'talk to human' / 'not resolved' -> create_ticket.
- Ask for Order ID if missing and needed.
"""

def solve(problem: str):
    history = f"{SYSTEM_PROMPT}\n\nCustomer: {problem}\n"
    for step in range(5):
        resp = ask_groq(history + "\nThought:")
        history += "\nThought:" + resp
        if "Final Answer:" in resp:
            print(resp.split("Final Answer:")[-1].strip())
            return
        if "Action:" in resp:
            try:
                line = [l for l in resp.split("\n") if "Action:" in l][0]
                tool_name = line.split("Action:")[1].strip().split("(")[0].strip().replace("*", "").strip()
                tool_input = line[line.find("(")+1: line.rfind(")")].strip().strip("'\"")
                print(f"-> Using {tool_name}: {tool_input}")
                result = TOOLS[tool_name](tool_input)
                print(f"Observation: {result}")
                history += f"\nObservation: {result}\n"
            except Exception as e:
                history += f"\nObservation: Error {e}\n"
    print("Sorry, let me create a ticket for you.")


if __name__ == "__main__":
    print("=== CUSTOMER SUPPORT AGENT ===")
    print("Try: Where is my order ORD123? / I want refund for ORD124")
    while True:
        q = input("\nCustomer: ")
        if q.lower() == "exit": break
        solve(q)