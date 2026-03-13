import os
import time
import re
import sympy as sp

# Gemini (safe fallback)
try:
    import google.genai as genai
    API_KEY = os.getenv("GEMINI_API_KEY", "")
    if API_KEY:
        genai.configure(api_key=API_KEY)
    HAS_GEMINI = True
except:
    HAS_GEMINI = False

MODEL_NAME = "gemini-2.0-flash"

def agent_sympy(problem_text: str):
    """Agent 1: SymPy - ALWAYS correct math"""
    print(f"SymPy solving: {problem_text}")
    try:
        clean = re.sub(r'[^\w\s\+\-\*/\.\=,x]', '', problem_text.lower())
        clean = ' '.join(clean.split())
        print(f"Cleaned: '{clean}'")
        
        if '=' not in clean:
            return {"final_answer": "No equation", "model": "SymPy"}
        
        left, right = clean.split('=', 1)
        left, right = left.strip(), right.strip()
        
        # Fix implicit multiplication
        left = re.sub(r'(\d)([a-z])', r'\1*\2', left)
        right = re.sub(r'(\d)([a-z])', r'\1*\2', right)
        
        x = sp.symbols('x')
        eq_left = sp.sympify(left)
        eq_right = sp.sympify(right)
        eq = sp.Eq(eq_left, eq_right)
        solution = sp.solve(eq, x)
        
        final = str(solution[0]) if solution else "No solution"
        return {
            "model": "SymPy ",
            "final_answer": final,
            "reasoning_steps": [f"{eq} → x={final}"],
        }
    except Exception as e:
        print(f"SymPy error: {e}")
        return {"final_answer": "0", "model": "SymPy-fail"}  # Safe number

def agent_llama3(problem_text: str):
    """Agent 2: LLM Mock (safe - no crash!)"""
    return {
        "model": "LLM-Mock (Llama3)",
        "final_answer": "0",  # Safe fallback
        "reasoning_steps": ["Mock reasoning"],
    }

def agent_gemini_safe(problem_text: str):
    """Agent 3: Gemini (safe)"""
    if not HAS_GEMINI or not os.getenv("GEMINI_API_KEY"):
        return {
            "model": "Gemini-Mock",
            "final_answer": "0",
            "reasoning_steps": ["No API key"],
        }
    
    time.sleep(2)
    try:
        full_prompt = f"""Solve: {problem_text}
Step-by-step. FINAL ANSWER: [number]"""
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(full_prompt)
        final_answer = "0"  # Safe default
        if response.text:
            match = re.search(r'FINAL ANSWER:\s*([0-9\-\.]+)', response.text, re.I)
            final_answer = match.group(1) if match else "0"
        return {
            "model": "Gemini",
            "final_answer": final_answer,
            "reasoning_steps": [response.text[:100]],
        }
    except:
        return {"final_answer": "0", "model": "Gemini-fail"}
def agent_gpt4(problem_text: str):
    """Agent 4: GPT-4o-mini (production LLM!)"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast/cheap math expert
            messages=[{
                "role": "user", 
                "content": f"""Solve this math equation step-by-step:
{problem_text}

Provide ONLY the numerical solution as FINAL ANSWER: [number]"""
            }],
            max_tokens=150,
            temperature=0.1  # Precise math
        )
        
        answer_text = response.choices[0].message.content
        print(f"GPT4 raw: {answer_text[:100]}")
        
        # Extract number
        match = re.search(r'FINAL ANSWER:\s*([0-9\-\.]+)', answer_text, re.I)
        final = match.group(1) if match else re.search(r'([0-9\-\.]+)', answer_text).group(1) if re.search(r'([0-9\-\.]+)', answer_text) else "0"
        
        return {
            "model": "GPT-4o-mini",
            "final_answer": final,
            "reasoning_steps": [answer_text[:80]],
            "raw_output": answer_text,
        }
    except Exception as e:
        print(f"GPT4 error: {e}")
        return {"final_answer": "0", "model": "GPT4-fail"}
