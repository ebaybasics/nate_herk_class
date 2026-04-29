import subprocess
import json
import os
import sys
import base64


def run_tool(script, input_text=None, args=None):
    """Helper: runs a tool script, returns CompletedProcess."""
    cmd = [sys.executable, f"tools/{script}"]
    if args:
        cmd.extend(args)
    return subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ},
    )


def test_research_returns_valid_json():
    result = run_tool("perplexity_research.py", args=["AI trends in small business"])
    assert result.returncode == 0, f"Tool failed:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert "summary" in data
    assert "key_points" in data and isinstance(data["key_points"], list)
    assert len(data["key_points"]) >= 2
    assert "stats" in data and isinstance(data["stats"], list)
    assert all("label" in s and "value" in s for s in data["stats"])
    assert "sources" in data and isinstance(data["sources"], list)
    assert len(data["sources"]) >= 1


def test_research_fails_without_api_key():
    env_without_key = {k: v for k, v in os.environ.items() if k != "PERPLEXITY_API_KEY"}
    result = subprocess.run(
        [sys.executable, "tools/perplexity_research.py", "test topic"],
        capture_output=True,
        text=True,
        timeout=10,
        env=env_without_key,
    )
    assert result.returncode != 0
    assert "PERPLEXITY_API_KEY" in result.stderr or "PERPLEXITY_API_KEY" in result.stdout


def test_chart_returns_valid_base64_png():
    chart_data = json.dumps({
        "title": "Top Automation Tools",
        "labels": ["n8n", "Zapier", "Make"],
        "values": [72, 58, 44],
    })
    result = run_tool("generate_chart.py", input_text=chart_data)
    assert result.returncode == 0, f"Tool failed:\n{result.stderr}"
    raw = base64.b64decode(result.stdout.strip())
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "Output is not a valid PNG"
