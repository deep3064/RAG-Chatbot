import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

def run_choice_a_bot():
    # 1. Load Data directly into Memory (No Vector DB needed for this size)
    # This is "Symbolic RAG" - perfect for 0.5B models
    if not os.path.exists("data/flattened_notes.txt"):
        print("❌ Run smart_flatten.py first!")
        return

    with open("data/flattened_notes.txt", 'r', encoding='utf-8') as f:
        database_lines = [line.strip() for line in f if line.strip()]

    # 2. Setup Model
    llm = ChatOllama(model="qwen2.5:0.5b", temperature=0, stop=["\n"])

    # 3. Simple Q&A Prompt
    prompt = ChatPromptTemplate.from_template("""
    Context: {context}
    
    Question: {input}
    
    Answer the question using the Context. Be extremely brief.
    Answer:""")

    print("\n✅ Choice A Bot Active. (Symbolic Search)")
    
    while True:
        user_input = input("\nQuery: ")
        if user_input.lower() in ["quit", "exit"]: break
        
        # --- SYMBOLIC RETRIEVAL (The Logic Fix) ---
        # 1. Split user query into keywords (ignore small words)
        keywords = [w.lower() for w in user_input.split() if len(w) > 2]
        
        # 2. Score every line in the file
        # If a line has "Bob" and "Currency", it gets a high score.
        scored_results = []
        for line in database_lines:
            score = 0
            line_lower = line.lower()
            for kw in keywords:
                if kw in line_lower:
                    score += 1
            if score > 0:
                scored_results.append((score, line))
        
        # 3. Sort by score (highest match first)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # 4. Pick Top Match
        if not scored_results:
            print("Bot: Data not found.")
            continue
            
        best_line = scored_results[0][1]
        
        # DEBUG: Uncomment this to see exactly which line it picked!
        # print(f"[DEBUG] Using line: {best_line}")

        # 5. Generate
        chain = prompt | llm
        response = chain.invoke({"input": user_input, "context": best_line})
        
        # Final cleanup to remove parroting
        answer = response.content.strip()
        if answer.lower() == user_input.lower(): # If it just repeated the question
             answer = best_line.split("|")[-1].strip()

        print(f"Bot: {answer}")

if __name__ == "__main__":
    run_choice_a_bot()