import streamlit as st
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# --- CONFIGURATION ---
st.set_page_config(page_title="ShopSmart AI Assistant", page_icon="🤖")

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

st.title("🤖 Info Bot")
st.caption("Powered by Qwen 2.5 (0.5B) • Symbolic RAG Architecture")

# Sidebar for System Status
with st.sidebar:
    st.header("System Status")
    if os.path.exists("data/flattened_notes.txt"):
        st.success("Database: Loaded")
        db_lines = get_flattened_data()
        st.info(f"Records: {len(db_lines)}")
    else:
        st.error("Database: Missing")
        st.warning("Please run smart_flatten.py first!")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Field
if prompt := st.chat_input("Ask about users, products, or nodes..."):
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Process Logic
    with st.chat_message("assistant"):
        with st.spinner("Searching database..."):
            db_lines = get_flattened_data()
            best_context = find_best_match(prompt, db_lines)
            
            if best_context:
                final_answer = generate_answer(prompt, best_context)
                response_text = f"{final_answer}"
                # Optional: Show the context used (for debugging/demo)
                # response_text += f"\n\n*Source: {best_context}*" 
            else:
                response_text = "I could not find that information in the database."
            
            st.markdown(response_text)
            
    # 3. Save Assistant Message
    st.session_state.messages.append({"role": "assistant", "content": response_text})