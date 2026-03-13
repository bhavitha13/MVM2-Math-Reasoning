import gradio as gr
import os
import shutil
import tempfile
import re
import subprocess
import sys
import time
from pathlib import Path
import html

PROJECT_ROOT = Path(r"C:\Users\yarag\MVM2 project")
MAIN_PY = PROJECT_ROOT / "main.py"
DATA_DIR = PROJECT_ROOT / "data" / "images"


def parse_pipeline_output(output_text: str):
    final_answer = "No valid answer extracted"
    ocr_conf = "N/A"
    consensus_val = "N/A"
    final_conf_val = "N/A"

    m = re.search(r"VERIFIED ANSWER\s*:\s*(.+)", output_text, re.IGNORECASE)
    if m:
        final_answer = m.group(1).strip()

    m = re.search(r"\nOCR\s*:\s*([0-9.]+)", output_text, re.IGNORECASE)
    if m:
        ocr_conf = m.group(1).strip()

    m = re.search(r"\nConsensus\s*:\s*(.+)", output_text, re.IGNORECASE)
    if m:
        consensus_val = m.group(1).strip()

    m = re.search(r"\nConfidence\s*:\s*([0-9.]+)", output_text, re.IGNORECASE)
    if m:
        final_conf_val = m.group(1).strip()

    return final_answer, ocr_conf, consensus_val, final_conf_val


def solve_math_image(image):
    if image is None:
        return """
        <div style='padding:20px; color:#e74c3c; text-align:center; font-family:Segoe UI,sans-serif;'>
            <h2>No Image</h2>
            <p>Please upload a math problem image.</p>
        </div>
        """

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time() * 1000)
        image_filename = f"upload_{timestamp}.png"
        target_image = DATA_DIR / image_filename

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            temp_path = Path(tmp.name)

        shutil.copy(str(temp_path), str(target_image))

        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        result = subprocess.run(
            [sys.executable, str(MAIN_PY), image_filename],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=120,
            env=env
        )

        output = result.stdout or ""

        full_output = (
            f"PROJECT_ROOT: {PROJECT_ROOT}\n"
            f"MAIN_PY: {MAIN_PY}\n"
            f"TARGET_IMAGE: {target_image}\n"
            f"IMAGE_FILENAME: {image_filename}\n"
            f"PYTHON_USED: {sys.executable}\n"
            f"RETURN_CODE: {result.returncode}\n"
            f"{'=' * 70}\n"
            f"{output}"
        )

        final_answer, ocr_conf, consensus_val, final_conf_val = parse_pipeline_output(full_output)

        if result.returncode != 0:
            safe_debug = html.escape(full_output[:6000])
            return f"""
<div style="font-family:'Segoe UI',sans-serif; padding:20px; max-width:900px; margin:0 auto;">
  <h1 style="text-align:center; color:#c0392b;">Pipeline Error</h1>
  <div style="background:#2d3748; color:#e2e8f0; padding:20px; border-radius:12px;
              margin-top:10px; font-family:'Courier New', monospace; font-size:13px;
              max-height:600px; overflow-y:auto; white-space:pre-wrap;">{safe_debug}</div>
</div>
            """

        safe_output = html.escape(full_output[:6000])
        safe_answer = html.escape(final_answer)
        safe_ocr = html.escape(ocr_conf)
        safe_consensus = html.escape(consensus_val)
        safe_conf = html.escape(final_conf_val)

        return f"""
<div style="font-family:'Segoe UI',sans-serif; padding:20px; max-width:900px; margin:0 auto;">
  <h1 style="color:#2c3e50; text-align:center;">MVM² - Mathematical Reasoning Verification</h1>
  <p style="text-align:center; color:#7f8c8d; font-size:16px;">
    Multi-Modal Multi-Model System | Neuro-Symbolic Verification | IEEE Paper Prototype
  </p>

  <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
              color:white; padding:25px; border-radius:20px; text-align:center; margin:25px 0;">
    <h2 style="margin:0 0 15px 0; font-size:28px;">VERIFIED FINAL ANSWER</h2>
    <div style="background:rgba(255,255,255,0.95); padding:20px; border-radius:15px;
                font-size:32px; font-weight:bold; color:#2c3e50; min-height:50px;">
      {safe_answer}
    </div>
  </div>

  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:20px; margin:25px 0;">
    <div style="padding:20px; background:#e8f4fd; border-radius:15px; text-align:center;">
      <h4 style="color:#2980b9; margin:0 0 10px 0;">OCR Confidence</h4>
      <div style="font-size:26px; font-weight:bold; color:#2980b9;">{safe_ocr}</div>
    </div>
    <div style="padding:20px; background:#d5f4e6; border-radius:15px; text-align:center;">
      <h4 style="color:#27ae60; margin:0 0 10px 0;">Agent Consensus</h4>
      <div style="font-size:26px; font-weight:bold; color:#27ae60;">{safe_consensus}</div>
    </div>
    <div style="padding:20px; background:#fdf2e9; border-radius:15px; text-align:center;">
      <h4 style="color:#e67e22; margin:0 0 10px 0;">Final Confidence</h4>
      <div style="font-size:26px; font-weight:bold; color:#e67e22;">{safe_conf}</div>
    </div>
  </div>

  <details style="margin-top:25px;">
    <summary style="padding:15px; background:#f8f9fa; border:2px solid #dee2e6; border-radius:12px;
                    cursor:pointer; font-weight:600; font-size:16px;">
      Debug: Full Pipeline Output
    </summary>
    <div style="background:#2d3748; color:#e2e8f0; padding:20px; border-radius:12px;
                margin-top:10px; font-family:'Courier New', monospace; font-size:13px;
                max-height:500px; overflow-y:auto; white-space:pre-wrap;">{safe_output}</div>
  </details>
</div>
        """

    except subprocess.TimeoutExpired:
        return """
        <div style='color:#e74c3c; padding:20px; text-align:center; font-family:Segoe UI,sans-serif;'>
            <h2>Timeout</h2>
            <p>main.py took more than 120 seconds to finish.</p>
        </div>
        """
    except Exception as e:
        return f"""
        <div style='color:#e74c3c; padding:20px; text-align:center; font-family:Segoe UI,sans-serif;'>
            <h2>Error</h2>
            <p>{html.escape(str(e))}</p>
        </div>
        """


demo = gr.Interface(
    fn=solve_math_image,
    inputs=gr.Image(type="pil", label="Upload Math Problem (handwritten/printed OK)", height=400),
    outputs=gr.HTML(label="MVM² Results"),
    title="MVM² - Multi-Modal Math Reasoning Verifier",
    description="""Upload any math image -> OCR + Multi-LLM agents + SymPy verification -> Confidence-calibrated answer.
    <br><small>Prototype for IEEE/Springer publication | Handles noisy/handwritten inputs</small>""",
    theme=gr.themes.Soft(),
)

if __name__ == "__main__":
    demo.launch(server_port=8080, share=True, show_error=True, debug=True)
