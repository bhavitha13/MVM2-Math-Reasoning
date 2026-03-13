import cv2
from mvm2.ocr_preprocess import preprocess_image, run_ocr
from mvm2.representation import build_representation
from mvm2.agents import agent_sympy, agent_llama3, agent_gemini_safe, agent_gpt4
from mvm2.verification import verify_agent_answer, compute_consensus
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.makedirs("data/images", exist_ok=True)

os.environ["GEMINI_API_KEY"] = "YOUR_GEMINI_KEY"
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_KEY"


def main():
    image_filename = sys.argv[1] if len(sys.argv) > 1 else "math_problem1.png"
    image_path = os.path.join("data", "images", image_filename)

    print("MVM2 - 4-AGENT VERIFICATION")
    print(f"Image: {image_path}")

    if not os.path.exists(image_path):
        print(f"ERROR: Image not found at {image_path}")
        sys.exit(1)

    try:
        preprocessed = preprocess_image(image_path)
        preprocessed_name = f"preprocessed_{image_filename}"
        cv2.imwrite(os.path.join("data", "images", preprocessed_name), preprocessed)
        print("Preprocessing")

        ocr_output = run_ocr(image_path)
        print(f"OCR: {ocr_output['tokens']} conf: {ocr_output['ocr_conf']:.3f}")

        representation = build_representation(ocr_output["tokens"])
        print(f"Problem: {representation['problem_text']}")

        print("\n1. SymPy (symbolic)")
        agent1 = agent_sympy(representation["problem_text"])

        print("\n2. Gemini Derivation")
        agent2 = agent_llama3(representation["problem_text"])

        print("\n3. Gemini Verification")
        agent3 = agent_gemini_safe(representation["problem_text"])

        print("\n4. GPT-4o (OpenAI)")
        agent4 = agent_gpt4(representation["problem_text"])

        print("\nAgents:")
        for i, a in enumerate([agent1, agent2, agent3, agent4], 1):
            model_name = a.get("model", "Unknown")
            final_answer = a.get("final_answer", "N/A")
            print(f"{i}: {model_name} -> {final_answer}")

        consensus_result = compute_consensus(agent1, agent4)

        verification = verify_agent_answer({
            "final_answer": consensus_result["chosen_answer"]
        })

        ocr_penalty = 0.9 + 0.1 * ocr_output["ocr_conf"]
        final_conf = round(
            consensus_result["score"] * verification["verification_score"] * ocr_penalty,
            3
        )

        print("=" * 80)
        print(f"VERIFIED ANSWER: {consensus_result['chosen_answer']}")
        print(f"OCR: {round(ocr_output['ocr_conf'], 3)}")
        print(f"Consensus: {consensus_result['consensus']}")
        print(f"Confidence: {final_conf}")
        print(f"SymPy Valid: {verification['sympy_valid']}")
        print("=" * 80)

    except Exception as e:
        print(f"ERROR: {e}")
        print("Chosen answer: Error - check keys/image")
        sys.exit(1)


if __name__ == "__main__":
    main()
