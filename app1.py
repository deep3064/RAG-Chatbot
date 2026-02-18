import streamlit as st
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
# Added initial_sidebar_state="expanded" so it behaves like a chat app on load
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
        /* --- 1. GOOGLE FONT (Inter - Clean & Modern) --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* --- 2. CLEAN LAYOUT (ChatGPT Style) --- */
        /* We hide the footer and the "Deploy" menu, but we KEEP the header visible 
           so you can see the 'Minimize Sidebar' arrow (<) */
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Make the header transparent so it blends in, but keeps buttons clickable */
        header {
            background-color: transparent !important;
        }
        [data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 1;
        }
        
        /* Add padding to top so content breathes */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
        }

        /* --- 3. ADAPTIVE CHAT BUBBLES --- */
        /* We use 'rgba' for backgrounds so they work on BOTH Light & Dark themes automatically */
        
        /* General Message Style */
        .stChatMessage {
            background-color: transparent; /* Cleaner, no boxy look for AI */
            border: none;
        }

        /* USER MESSAGE: Distinct background (Like ChatGPT/Gemini user bubble) */
        /* Target messages where role is NOT assistant (i.e., user) */
        [data-testid="stChatMessage"]:nth-child(odd) {
            background-color: rgba(128, 128, 128, 0.08); /* Subtle gray tint */
            border-radius: 12px;
        }

        /* AVATARS: Round & Clean */
        .stChatMessage .st-emotion-cache-1p1nwyz {
            border-radius: 50%;
        }

        /* --- 4. FLOATING INPUT BOX (Gemini Style) --- */
        .stChatInputContainer {
            padding-bottom: 20px;
        }
        
        [data-testid="stChatInput"] {
            border-radius: 24px; /* Pill shape */
            border: 1px solid rgba(128, 128, 128, 0.3); /* Subtle border */
            background-color: transparent;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05); /* Soft shadow */
        }
        
        /* Input text focus color adaptation */
        .stTextInput input:focus {
            box-shadow: none;
            border-color: #4a90e2;
        }

        /* --- 5. SIDEBAR (Dark Mode Friendly) --- */
        [data-testid="stSidebar"] {
            background-color: rgba(128, 128, 128, 0.05); /* Very subtle contrast */
            border-right: 1px solid rgba(128, 128, 128, 0.1);
        }

        /* --- 6. TEXT COLORS (The "White Screen" Fix) --- */
        /* We force text to follow Streamlit's theme variables so it never vanishes */
        h1, h2, h3, p, div, span {
            color: var(--text-color);
        }
        
        /* Success/Error/Info boxes - Make them rounded */
        .stAlert {
            border-radius: 10px;
        }
        
        /* --- 7. SIDEBAR BOTTOM BUTTON FIX --- */
        /* This pushes the last container in the sidebar to the bottom if possible, 
           but since Streamlit is tricky, we use a spacer in Python. 
           Here we just style the button to look like a 'Danger' action. */
        .stButton button {
            width: 100%;
            border-radius: 8px;
        }
    </style>
    """, unsafe_allow_html=True)

init_custom_css()

# --- BACKEND LOGIC (Your "Symbolic" Engine) ---
def get_flattened_data():
    """Loads the flattened data into memory."""
    if not os.path.exists("data/flattened_notes.txt"):
        return []
    with open("data/flattened_notes.txt", 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def find_best_match(query, database_lines):
    """Finds the best matching line using keyword scoring."""
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    
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
    
    if not scored_results:
        return None
    return scored_results[0][1] # Return the text of the best line

def generate_answer(query, context):
    """Generates the final answer using Qwen 0.5B."""
    llm = ChatOllama(model="qwen2.5:0.5b", temperature=0, stop=["\n"])
    
    prompt = ChatPromptTemplate.from_template("""
    Context: {context}
    Question: {input}
    Answer the question using the Context. Be extremely brief.
    Answer:""")
    
    chain = prompt | llm
    response = chain.invoke({"input": query, "context": context})
    
    # Cleanup logic
    answer = response.content.strip()
    if answer.lower() == query.lower():
        answer = context.split("|")[-1].strip()
        
    return answer

# --- FRONTEND INTERFACE ---

# 1. SIDEBAR SETUP (ChatGPT Style)
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

    # Spacer to push the Clear button to the bottom
    st.markdown("<br>" * 10, unsafe_allow_html=True) 
    
    st.divider()
    
    # Clear Conversation Button (Full Width)
    if st.button("🗑️ Clear Conversation", type="primary"):
        st.session_state.messages = []
        st.rerun()

# 2. MAIN TITLE
st.title("Personal Chatbot Assistant")
# st.caption("Ask about Users, Products, or System Logs.")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Field
if prompt := st.chat_input("Ask your Questions..."):
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Process Logic
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            db_lines = get_flattened_data()
            best_context = find_best_match(prompt, db_lines)
            
            if best_context:
                final_answer = generate_answer(prompt, best_context)
                response_text = f"{final_answer}"
            else:
                response_text = "I could not find that information in the database."
            
            st.markdown(response_text)
            
    # 3. Save Assistant Message
    st.session_state.messages.append({"role": "assistant", "content": response_text})