import os, random
import streamlit as st
from groq import Groq

# --- 1. GROQ SETUP ---
# Option A: Put key in sidebar (easiest for demo)
# Option B: Set env var GROQ_API_KEY
api_key = st.sidebar.text_input("Enter Groq API Key (gsk_...)", type="password", value=os.getenv("GROQ_API_KEY", ""))
if not api_key:
    st.warning("Please enter your Groq API Key in the sidebar to start.")
    st.stop()

client = Groq(api_key=api_key)

def ask_groq(prompt):
    resp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message.content

st.set_page_config(page_title="Customer Support Agent", page_icon="🎧", layout="centered")
st.title("🎧 Customer Support Agent")
st.write("Hi! I can help with Order Tracking, Refund, Returns, Cancellation & Complaints.")

ORDERS = {
    "ORD123": {"status": "Shipped", "item": "Nike Shoes", "amount": 2999, "delivery": "Tomorrow"},
    "ORD124": {"status": "Delivered", "item": "iPhone Cover", "amount": 499, "delivery": "Delivered on Oct 10"},
    "ORD125": {"status": "Processing", "item": "Laptop Stand", "amount": 1299, "delivery": "In 3 days"},
}
FAQS = {
    "return": "You can return any product within 7 days. Go to My Orders > Return.",
    "refund": "Refund is processed in 3-5 business days to your original payment method.",
    "delivery": "Standard delivery takes 3-5 days. Express takes 1-2 days.",
    "cancel": "You can cancel your order before it is shipped from My Orders > Cancel.",
    "warranty": "All electronics have 1 year warranty. Keep your invoice.",
}

def check_order(order_id):
    order_id = order_id.strip().upper()
    if order_id in ORDERS:
        o = ORDERS[order_id]
        return f"Order {order_id}: {o['item']} - Status: {o['status']}, Amount: Rs.{o['amount']}, Delivery: {o['delivery']}"
    return f"Order {order_id} not found. Try ORD123, ORD124, ORD125 for demo."
def process_refund(order_id):
    order_id = order_id.strip().upper()
    if order_id in ORDERS:
        return f"Refund initiated for {order_id} of Rs.{ORDERS[order_id]['amount']}. Refund ID: REF{random.randint(1000,9999)}. Will reflect in 3-5 days."
    return "Order not found."
def search_faq(q):
    q=q.lower()
    for k,v in FAQS.items():
        if k in q: return v
    return "For return, refund, delivery, cancel, warranty - please ask specific question."
def create_ticket(issue):
    return f"Ticket created: TKT{random.randint(10000,99999)} for '{issue}'. Team will contact you in 24 hrs."

TOOLS = {"check_order": check_order, "process_refund": process_refund, "search_faq": search_faq, "create_ticket": create_ticket}
SYSTEM_PROMPT = """You are Customer Support Agent. Tools: 1.check_order(order_id) 2.process_refund(order_id) 3.search_faq(query) 4.create_ticket(issue)
Follow: Thought: Action: tool_name(input) Observation: Final Answer:
Rules: If Order ID given, use check_order. If refund, check then process_refund. If angry/human, create_ticket. Be polite, short. Do NOT use ** or markdown in Action line."""

def solve(problem, box):
    history = f"{SYSTEM_PROMPT}\n\nCustomer: {problem}\n"
    for _ in range(5):
        resp = ask_groq(history + "\nThought:")
        history += "\nThought:" + resp
        box.write(f"💭 {resp[:250]}")
        if "Final Answer:" in resp:
            return resp.split("Final Answer:")[-1].strip()
        if "Action:" in resp:
            try:
                line = [l for l in resp.split("\n") if "Action:" in l][0]
                # FIX: remove ** that was breaking TOOLS lookup
                tool = line.split("Action:")[1].strip().split("(")[0].strip().replace("*", "").strip()
                inp = line[line.find("(")+1: line.rfind(")")].strip().strip("'\"")
                box.info(f"🛠️ Tool: {tool} -> {inp}")
                res = TOOLS[tool](inp)
                box.write(f"👀 {res}")
                history += f"\nObservation: {res}\n"
            except Exception as e:
                history += f"\nObservation: Error {e}\n"
    return "Let me create a ticket for you."

if "messages" not in st.session_state:
    st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Type your issue... e.g. Where is my order ORD123?"):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        box = st.expander("See how Agent thinks...", expanded=True)
        with st.spinner("Solving..."):
            ans = solve(prompt, box)
        st.markdown(f"**{ans}**")
        st.session_state.messages.append({"role":"assistant","content":ans})

with st.sidebar:
    st.header("Demo - Try these")
    st.code("Where is my order ORD123?")
    st.code("I want refund for ORD124")
    st.code("What is your return policy?")
    st.code("My product is damaged, I am angry")
    st.info("Demo Order IDs: ORD123, ORD124, ORD125")

