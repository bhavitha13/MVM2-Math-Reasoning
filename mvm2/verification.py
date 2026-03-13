import sympy as sp
import re

def extract_number(text):
    """Extract numerical expression from LLM text."""
    text = str(text).strip()

    prefixes = ["FINAL ANSWER:", "Final answer:", "Answer:", "answer:"]
    for prefix in prefixes:
        if prefix.upper() in text.upper():
            text = text.split(prefix, 1)[1].strip()
            break

    # Keep digits, operators, decimal, comma, x, spaces, equals
    text = re.sub(r"[^0-9\+\-\*\/\.\,x=\s]", "", text)
    text = text.split("=")[-1].strip()

    try:
        return sp.sympify(text)
    except Exception:
        return None

def answers_equal(ans1, ans2):
    """Check if two answers are mathematically equal."""
    try:
        expr1 = extract_number(ans1)
        expr2 = extract_number(ans2)
        if expr1 is None or expr2 is None:
            return str(ans1).strip().lower() == str(ans2).strip().lower()
        return sp.simplify(expr1 - expr2) == 0
    except Exception:
        return False

def verify_agent_answer(agent_output):
    """SymPy-based verification + simple score."""
    final_answer = agent_output.get("final_answer", "")
    parsed = extract_number(final_answer)
    sympy_valid = parsed is not None

    return {
        "original_answer": final_answer,
        "sympy_valid": sympy_valid,
        "parsed_value": str(parsed) if sympy_valid else None,
        "verification_score": 1.0 if sympy_valid else 0.5,
    }

def compute_consensus(agent1, agent2):
    """Consensus between two agents using equivalence check."""
    ans1 = agent1["final_answer"]
    ans2 = agent2["final_answer"]

    equal = answers_equal(ans1, ans2)

    if equal:
        return {
            "consensus": "HIGH AGREEMENT",
            "score": 0.9,
            "chosen_answer": ans1,
            "match": True,
        }
    else:
        chosen = ans1 if len(str(ans1)) >= len(str(ans2)) else ans2
        return {
            "consensus": "DISAGREEMENT",
            "score": 0.4,
            "chosen_answer": chosen,
            "match": False,
        }
