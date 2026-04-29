import subprocess, json, os, sys


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
    assert "sources" in data
