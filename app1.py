import streamlit as st
import os
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
st.set_page_config(
    page_title="RAG Chatbot AI", 
    page_icon="🤖", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- UI CSS ---
def init_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        header {
            background-color: transparent !important;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        .stChatMessage {
            background-color: transparent;
            border: none;
        }

        [data-testid="stChatMessage"]:nth-child(odd) {
            background-color: rgba(128, 128, 128, 0.08);
            border-radius: 12px;
        }

        .stChatInputContainer {
            padding-bottom: 20px;
        }
        
        [data-testid="stChatInput"] {
            border-radius: 24px;
            border: 1px solid rgba(128, 128, 128, 0.3);
            background-color: transparent;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        }

        [data-testid="stSidebar"] {
            background-color: rgba(128, 128, 128, 0.05);
            border-right: 1px solid rgba(128, 128, 128, 0.1);
        }

        h1, h2, h3, p, div, span {
            color: var(--text-color);
        }

        .stAlert {
            border-radius: 10px;
        }

        .stButton button {
            width: 100%;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

init_custom_css()

# --- BACKEND LOGIC ---

def get_flattened_data():
    """Loads the flattened data into memory."""
    if not os.path.exists("data/flattened_notes.txt"):
        return []
    with open("data/flattened_notes.txt", 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


# ✅ UPDATED: Retrieve TOP 5 matches instead of 1
def find_best_matches(query, database_lines, top_k=5):
    keywords = re.findall(r"\w+", query.lower())
    
    scored_results = []
    for line in database_lines:
        score = 0
        line_lower = line.lower()
        
        for kw in keywords:
            if kw in line_lower:
                score += 1
        
        if score > 0:
            scored_results.append((score, line))
    
    scored_results.sort(key=lambda x: x[0], reverse=True)
    
    top_results = [line for score, line in scored_results[:top_k]]
    
    if not top_results:
        return None
    
    return "\n".join(top_results)


# ✅ UPDATED: Improved grounding prompt
def generate_answer(query, context):
    llm = ChatOllama(model="qwen2.5:0.5b", temperature=0)

    prompt = ChatPromptTemplate.from_template("""
You are a database reasoning assistant.

Use ONLY the information in the Context.
If the question asks for highest, lowest, total, or comparison:
Carefully compare all relevant numbers before answering.

If the answer is not found, respond exactly with:
"I could not find that information in the database."

Context:
{context}

Question:
{input}

Answer briefly and precisely.
Answer:
""")

    chain = prompt | llm
    response = chain.invoke({"input": query, "context": context})
    
    return response.content.strip()


# --- FRONTEND INTERFACE ---

with st.sidebar:
    st.title("🤖 Info Bot")
    st.caption("v1.0 • Symbolic RAG")
    
    st.divider()
    
    st.subheader("System Status")
    if os.path.exists("data/flattened_notes.txt"):
        st.success("🟢 Online")
        db_lines = get_flattened_data()
        st.markdown(f"**Records Loaded:** `{len(db_lines)}`")
    else:
        st.error("🔴 Offline")
        st.warning("Run `smart_flatten.py`")

    st.markdown("<br>" * 10, unsafe_allow_html=True) 
    
    st.divider()
    
    if st.button("🗑️ Clear Conversation", type="primary"):
        st.session_state.messages = []
        st.rerun()


st.title("Personal Chatbot Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Ask your Questions..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            db_lines = get_flattened_data()
            best_context = find_best_matches(prompt, db_lines, top_k=5)
            
            if best_context:
                final_answer = generate_answer(prompt, best_context)
                response_text = final_answer
            else:
                response_text = "I could not find that information in the database."
            
            st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
