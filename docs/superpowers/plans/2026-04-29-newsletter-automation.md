# Newsletter Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully automated newsletter pipeline — type a topic into n8n chat, receive a complete HTML email sent via Brevo.

**Architecture:** n8n Chat Trigger → Perplexity API (research) → Claude API (HTML + structure) → QuickChart.io (chart embed, n8n-native) → Brevo transactional API (send). Python tools in `tools/` mirror each step as standalone testable scripts.

**Tech Stack:** n8n workflow, Perplexity `sonar` model, Claude `claude-sonnet-4-6`, QuickChart.io (chart in n8n), Brevo transactional email API, Python 3 + requests + matplotlib (standalone tools only)

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `.env.example` | Modify | Document all required keys |
| `.env` | Modify | Add real API key values |
| `requirements.txt` | Create | Python deps for standalone tools |
| `tools/perplexity_research.py` | Create | Standalone: research via Perplexity |
| `tools/generate_chart.py` | Create | Standalone: chart → base64 PNG |
| `tools/brevo_send.py` | Create | Standalone: inject chart + send via Brevo |
| `tests/test_tools.py` | Create | Smoke + unit tests for all three tools |
| `workflows/newsletter.md` | Create | SOP — steps, inputs, edge cases |

The n8n workflow is built directly in n8n (no JSON file). It calls all APIs natively via HTTP Request nodes — no Python inside n8n.

---

## Task 1: Environment Setup

**Files:**
- Modify: `.env.example`
- Modify: `.env`
- Create: `requirements.txt`

- [ ] **Step 1: Update `.env.example`**

Replace the contents of `.env.example` with:
```
# Perplexity — https://docs.perplexity.ai
PERPLEXITY_API_KEY=

# Anthropic — https://console.anthropic.com
CLAUDE_API_KEY=

# Brevo — https://app.brevo.com/settings/keys/api
BREVO_API_KEY=
BREVO_SENDER_EMAIL=
BREVO_SENDER_NAME=
BREVO_TEST_EMAIL=
```

- [ ] **Step 2: Populate `.env` with real values**

Copy example and fill in each key:
```bash
cp .env.example .env
```
Open `.env` and paste real values for each variable.

- [ ] **Step 3: Create `requirements.txt`**
```
requests==2.32.3
matplotlib==3.9.2
pytest==8.3.2
```

- [ ] **Step 4: Install dependencies**
```bash
pip install -r requirements.txt
```
Expected: Clean install, no errors.

- [ ] **Step 5: Commit**
```bash
git add .env.example requirements.txt
git commit -m "chore: add requirements and env template for newsletter tools"
```

---

## Task 2: Research Tool

**Files:**
- Create: `tools/perplexity_research.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_tools.py`:
```python
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
```

- [ ] **Step 2: Run test — confirm it fails**
```bash
source .env && pytest tests/test_tools.py::test_research_returns_valid_json -v
```
Expected: **FAIL** — `No such file or directory: 'tools/perplexity_research.py'`

- [ ] **Step 3: Create `tools/perplexity_research.py`**
```python
import os, sys, json, re, requests


def research(topic: str) -> dict:
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {os.environ['PERPLEXITY_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a research assistant. Given a newsletter topic, return ONLY a valid "
                        "JSON object with these keys: summary (string, 2-3 sentences), key_points "
                        "(list of 3-4 strings), stats (list of {label, value} objects with real data "
                        "points), sources (list of 2-3 source URLs). No markdown, no explanation — "
                        "JSON only."
                    ),
                },
                {"role": "user", "content": f"Research this topic: {topic}"},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in Perplexity response: {content[:300]}")
    return json.loads(match.group())


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else sys.stdin.read().strip()
    if not topic:
        print("Usage: python perplexity_research.py <topic>", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(research(topic), indent=2))
```

- [ ] **Step 4: Run test — confirm it passes**
```bash
source .env && pytest tests/test_tools.py::test_research_returns_valid_json -v
```
Expected: **PASS**

- [ ] **Step 5: Manual smoke test**
```bash
source .env && python tools/perplexity_research.py "newsletter automation for small business 2026"
```
Expected: JSON with `summary`, `key_points`, `stats`, `sources` printed to stdout.

- [ ] **Step 6: Commit**
```bash
git add tools/perplexity_research.py tests/test_tools.py
git commit -m "feat: add perplexity research tool"
```

---

## Task 3: Chart Tool

**Files:**
- Create: `tools/generate_chart.py`
- Modify: `tests/test_tools.py`

- [ ] **Step 1: Add failing test — append to `tests/test_tools.py`**
```python
import base64


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
```

- [ ] **Step 2: Run test — confirm it fails**
```bash
pytest tests/test_tools.py::test_chart_returns_valid_base64_png -v
```
Expected: **FAIL** — `No such file or directory: 'tools/generate_chart.py'`

- [ ] **Step 3: Create `tools/generate_chart.py`**
```python
import sys, json, base64, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_chart(chart_data: dict) -> str:
    labels = chart_data["labels"]
    values = chart_data["values"]
    title = chart_data.get("title", "")

    fig, ax = plt.subplots(figsize=(6, max(2.0, len(labels) * 0.65)))
    colors = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"]
    ax.barh(labels, values, color=colors[: len(labels)], height=0.5)
    ax.set_title(title, fontsize=11, fontweight="bold", pad=10)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(labelsize=9)
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    print(generate_chart(data))
```

- [ ] **Step 4: Run test — confirm it passes**
```bash
pytest tests/test_tools.py::test_chart_returns_valid_base64_png -v
```
Expected: **PASS**

- [ ] **Step 5: Commit**
```bash
git add tools/generate_chart.py tests/test_tools.py
git commit -m "feat: add matplotlib chart generator tool"
```

---

## Task 4: Brevo Send Tool

**Files:**
- Create: `tools/brevo_send.py`
- Modify: `tests/test_tools.py`

- [ ] **Step 1: Add failing test — append to `tests/test_tools.py`**
```python
import importlib.util
from unittest.mock import patch, MagicMock


def test_brevo_chart_injected_and_api_called():
    spec = importlib.util.spec_from_file_location("brevo_send", "tools/brevo_send.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {
        "subject": "Test Newsletter",
        "preview_text": "A quick preview",
        "html_body": "<h1>Hello</h1><p>{{CHART}}</p>",
        "plain_text": "Hello",
        "chart_base64": "iVBORw0KGgo=",
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"messageId": "abc-123"}
    mock_resp.raise_for_status = lambda: None

    with patch("requests.post", return_value=mock_resp) as mock_post:
        result = mod.send_newsletter(payload)

    sent_html = mock_post.call_args.kwargs["json"]["htmlContent"]
    assert "{{CHART}}" not in sent_html, "Placeholder was not replaced"
    assert "data:image/png;base64,iVBORw0KGgo=" in sent_html, "Chart not embedded"
    assert result["status"] == "sent"
```

- [ ] **Step 2: Run test — confirm it fails**
```bash
pytest tests/test_tools.py::test_brevo_chart_injected_and_api_called -v
```
Expected: **FAIL** — `No such file or directory: 'tools/brevo_send.py'`

- [ ] **Step 3: Create `tools/brevo_send.py`**
```python
import os, sys, json, requests


def send_newsletter(data: dict) -> dict:
    api_key = os.environ["BREVO_API_KEY"]
    to_email = os.environ["BREVO_TEST_EMAIL"]
    sender_email = os.environ["BREVO_SENDER_EMAIL"]
    sender_name = os.environ["BREVO_SENDER_NAME"]

    html = data["html_body"]
    if data.get("chart_base64"):
        img = (
            f'<img src="data:image/png;base64,{data["chart_base64"]}" '
            f'style="max-width:100%;height:auto;display:block;margin:1.5rem auto;" '
            f'alt="Data chart" />'
        )
        html = html.replace("{{CHART}}", img)

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json={
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": to_email}],
            "subject": data["subject"],
            "previewText": data.get("preview_text", ""),
            "htmlContent": html,
            "textContent": data.get("plain_text", ""),
        },
        timeout=15,
    )
    response.raise_for_status()
    return {"status": "sent", "messageId": response.json().get("messageId")}


if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    print(json.dumps(send_newsletter(data)))
```

- [ ] **Step 4: Run test — confirm it passes**
```bash
pytest tests/test_tools.py::test_brevo_chart_injected_and_api_called -v
```
Expected: **PASS**

- [ ] **Step 5: Run all tests**
```bash
source .env && pytest tests/ -v
```
Expected: All 3 tests PASS.

- [ ] **Step 6: Commit**
```bash
git add tools/brevo_send.py tests/test_tools.py
git commit -m "feat: add brevo send tool with chart injection"
```

---

## Task 5: n8n Workflow

Build the workflow directly in n8n. No JSON file — wire nodes via the UI.

The n8n workflow calls all APIs natively. Chart generation uses QuickChart.io (a free chart-as-URL service) — no Python needed inside n8n.

**Files:** None (built in n8n UI)

- [ ] **Step 1: Create a new workflow in n8n**

Go to `https://n8n.kccleancarpets.com` → New Workflow → Name it `Newsletter Automation`.

- [ ] **Step 2: Add Chat Trigger node**

Add node: **Chat Trigger**
- Leave all defaults.
- This outputs `{ chatInput: "<the topic the user typed>" }`.

- [ ] **Step 3: Add Perplexity HTTP Request node**

Add node: **HTTP Request** — name it `Research: Perplexity`
- Method: `POST`
- URL: `https://api.perplexity.ai/chat/completions`
- Authentication: **Header Auth** → Name: `Authorization`, Value: `Bearer YOUR_PERPLEXITY_API_KEY`
- Body: JSON
```json
{
  "model": "sonar",
  "messages": [
    {
      "role": "system",
      "content": "You are a research assistant. Given a newsletter topic, return ONLY a valid JSON object with these keys: summary (string, 2-3 sentences), key_points (list of 3-4 strings), stats (list of {label, value} objects with real data points), sources (list of 2-3 source URLs). No markdown, no explanation — JSON only."
    },
    {
      "role": "user",
      "content": "={{ 'Research this topic: ' + $json.chatInput }}"
    }
  ]
}
```
Connect from: Chat Trigger.

- [ ] **Step 4: Add Parse Research Code node**

Add node: **Code** — name it `Parse Research`
```javascript
const content = items[0].json.choices[0].message.content;
const match = content.match(/\{[\s\S]*\}/);
if (!match) throw new Error('No JSON in Perplexity response: ' + content.slice(0, 200));
const research = JSON.parse(match[0]);
return [{ json: { topic: $('Chat Trigger').first().json.chatInput, research } }];
```
Connect from: Research: Perplexity.

- [ ] **Step 5: Add Claude HTTP Request node**

Add node: **HTTP Request** — name it `Generate: Claude`
- Method: `POST`
- URL: `https://api.anthropic.com/v1/messages`
- Headers:
  - `x-api-key`: `YOUR_CLAUDE_API_KEY`
  - `anthropic-version`: `2023-06-01`
  - `content-type`: `application/json`
- Body: JSON
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "system": "You are a newsletter writer. Given research data as JSON, write a complete HTML email newsletter. Return ONLY a valid JSON object (no markdown, no code fences) with these exact keys:\n- subject: engaging email subject line\n- preview_text: 1 sentence shown in inbox preview\n- html_body: complete HTML email with inline CSS, 600px max-width, white background, system sans-serif fonts. Include the exact placeholder {{CHART}} once, where the data chart should appear.\n- plain_text: plain text fallback version\n- chart_data: {\"labels\": [...], \"values\": [...], \"title\": \"...\"} with 3-5 numeric data points from the research for visualization",
  "messages": [
    {
      "role": "user",
      "content": "={{ 'Topic: ' + $json.topic + '\\n\\nResearch:\\n' + JSON.stringify($json.research, null, 2) }}"
    }
  ]
}
```
Connect from: Parse Research.

- [ ] **Step 6: Add Parse Claude Output Code node**

Add node: **Code** — name it `Parse Claude Output`
```javascript
const content = items[0].json.content[0].text;
const match = content.match(/\{[\s\S]*\}/);
if (!match) throw new Error('No JSON in Claude response: ' + content.slice(0, 200));
const newsletter = JSON.parse(match[0]);
// Pass topic through for context
newsletter.topic = $('Parse Research').first().json.topic;
return [{ json: newsletter }];
```
Connect from: Generate: Claude.

- [ ] **Step 7: Add Embed Chart Code node**

Add node: **Code** — name it `Embed Chart`
```javascript
const data = items[0].json;
const cd = data.chart_data;

// Build QuickChart.io URL (free, no auth required)
const chartConfig = {
  type: 'horizontalBar',
  data: {
    labels: cd.labels,
    datasets: [{
      data: cd.values,
      backgroundColor: ['#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe'].slice(0, cd.labels.length),
    }]
  },
  options: {
    title: { display: true, text: cd.title, fontSize: 13 },
    legend: { display: false },
    scales: { xAxes: [{ gridLines: { display: false } }], yAxes: [{ gridLines: { display: false } }] }
  }
};

const chartUrl = 'https://quickchart.io/chart?w=500&h=220&bkg=white&c=' + encodeURIComponent(JSON.stringify(chartConfig));
const imgTag = `<img src="${chartUrl}" style="max-width:100%;height:auto;display:block;margin:1.5rem auto;" alt="${cd.title}" />`;

const html = data.html_body.replace('{{CHART}}', imgTag);
return [{ json: { ...data, html_body: html } }];
```
Connect from: Parse Claude Output.

- [ ] **Step 8: Add Brevo HTTP Request node**

Add node: **HTTP Request** — name it `Send: Brevo`
- Method: `POST`
- URL: `https://api.brevo.com/v3/smtp/email`
- Headers:
  - `api-key`: `YOUR_BREVO_API_KEY`
  - `content-type`: `application/json`
- Body: JSON
```json
{
  "sender": { "name": "YOUR_SENDER_NAME", "email": "YOUR_SENDER_EMAIL" },
  "to": [{ "email": "YOUR_TEST_EMAIL" }],
  "subject": "={{ $json.subject }}",
  "previewText": "={{ $json.preview_text }}",
  "htmlContent": "={{ $json.html_body }}",
  "textContent": "={{ $json.plain_text }}"
}
```
Connect from: Embed Chart.

- [ ] **Step 9: Save and activate the workflow**

Click **Save** → toggle **Active** on.

- [ ] **Step 10: Verify workflow is wired correctly**

Open the workflow. Confirm the chain:
```
Chat Trigger → Research: Perplexity → Parse Research → Generate: Claude
→ Parse Claude Output → Embed Chart → Send: Brevo
```

---

## Task 6: Workflow SOP

**Files:**
- Create: `workflows/newsletter.md`

- [ ] **Step 1: Create `workflows/newsletter.md`**
```markdown
# Newsletter Automation Workflow

## Objective
Send a researched, AI-written HTML newsletter email on any topic via a single chat message.

## Trigger
n8n Chat Trigger — type the topic directly into the n8n chat interface.

**Input format:** Plain text topic string.
Example: `"AI automation tools for small business in 2026"`

## Required Inputs
| Variable | Where set |
|---|---|
| PERPLEXITY_API_KEY | n8n HTTP node header |
| CLAUDE_API_KEY | n8n HTTP node header |
| BREVO_API_KEY | n8n HTTP node header |
| Sender name/email | n8n Brevo node body |
| Test recipient email | n8n Brevo node body |

## Tool Sequence
1. **Perplexity** — researches topic, returns summary + key points + stats + sources
2. **Claude** — writes full HTML email + chart data in one pass
3. **QuickChart.io** — chart data rendered as image URL, embedded inline
4. **Brevo** — sends transactional email to test address

## Outputs
- HTML email delivered to BREVO_TEST_EMAIL
- n8n execution log with each node's input/output

## Edge Cases
- Perplexity returns no JSON → Parse Research node throws, execution stops, check n8n error log
- Claude returns no JSON → Parse Claude Output node throws, check Claude response in node output
- `{{CHART}}` missing from Claude HTML → chart silently not embedded (check Claude system prompt)
- Brevo rejects email → raise_for_status fires, check API key and sender domain verification

## Standalone Tool Testing
Each tool can be run independently for debugging:
```bash
source .env

# Research only
python tools/perplexity_research.py "your topic here"

# Chart only (pipe in JSON)
echo '{"title":"Test","labels":["A","B"],"values":[10,20]}' | python tools/generate_chart.py > /tmp/chart.b64

# Send only (pipe in full payload)
cat payload.json | python tools/brevo_send.py
```
```

- [ ] **Step 2: Commit**
```bash
git add workflows/newsletter.md
git commit -m "docs: add newsletter workflow SOP"
```

---

## Task 7: End-to-End Test

- [ ] **Step 1: Run all unit tests one final time**
```bash
source .env && pytest tests/ -v
```
Expected: All 3 tests PASS.

- [ ] **Step 2: Trigger the workflow via n8n chat**

Go to `https://n8n.kccleancarpets.com` → open the Newsletter Automation workflow → click **Chat** → type:
```
AI automation tools for small business in 2026
```
Expected: Workflow executes all 7 nodes without error.

- [ ] **Step 3: Check your inbox**

Open `BREVO_TEST_EMAIL` inbox. Confirm:
- Email arrives within 1-2 minutes
- Subject line is present and relevant
- HTML renders correctly
- Chart image appears in body
- No raw `{{CHART}}` text visible

- [ ] **Step 4: Check n8n execution log**

In n8n → Executions → click the latest run. Verify:
- All nodes show green
- Parse Research node output contains `summary`, `key_points`, `stats`
- Parse Claude Output node output contains `subject`, `html_body`, `chart_data`
- Send: Brevo node output contains `messageId`

- [ ] **Step 5: Final commit**
```bash
git add .
git commit -m "feat: newsletter automation pipeline complete — e2e tested"
git push
```

---

## Spec Coverage Check

| Spec requirement | Covered in |
|---|---|
| n8n Chat Trigger | Task 5 Step 2 |
| Perplexity research | Task 2, Task 5 Step 3 |
| Claude HTML generation in one pass | Task 5 Step 5 |
| Chart generation | Task 3, Task 5 Step 7 |
| `{{CHART}}` placeholder injection | Task 4, Task 5 Step 7 |
| Brevo transactional send | Task 4, Task 5 Step 8 |
| `subject`, `preview_text`, `plain_text` | Task 5 Step 5 (Claude prompt) |
| WAT `workflows/newsletter.md` | Task 6 |
| `.env` / environment variables | Task 1 |
| All three Python tools as standalone scripts | Tasks 2–4 |
