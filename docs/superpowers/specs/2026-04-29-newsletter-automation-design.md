# Newsletter Automation — Design Spec

**Date:** 2026-04-29
**Status:** Approved
**Project:** nate_herk_projects_n8n (WAT framework)

---

## Overview

Fully automated newsletter pipeline triggered by typing a topic into n8n's chat interface. Claude researches the topic via Perplexity, writes and formats a complete HTML email in one pass, generates an inline chart, and sends via Brevo. No human review step. Built for testing and learning n8n/WAT patterns.

---

## Architecture

```
n8n Chat Trigger (topic input)
        ↓
perplexity_research.py
  — calls Perplexity API with topic
  — returns: summary, key points, stats, sources
        ↓
Claude API (n8n HTTP Request node)
  — input: research JSON + topic
  — output: { html_body, subject, preview_text, plain_text, chart_data }
        ↓
generate_chart.py
  — input: chart_data (labels + values from Claude)
  — output: base64 PNG embedded in HTML
        ↓
brevo_send.py
  — injects chart into HTML
  — sends to Brevo list via API
```

---

## Components

### Trigger
- **Type:** n8n Chat Trigger node
- **Input:** Free-text topic string (e.g. "AI trends in small business 2026")
- **Output:** `{ topic: string }` passed downstream

### Tool: `tools/perplexity_research.py`
- **Input:** `topic` (string via CLI arg or stdin)
- **API:** Perplexity `sonar` model (online search-enabled)
- **Output:** JSON to stdout
  ```json
  {
    "summary": "...",
    "key_points": ["...", "...", "..."],
    "stats": [{ "label": "...", "value": "..." }],
    "sources": ["url1", "url2"]
  }
  ```
- **Error handling:** Exits non-zero on API failure; n8n stops the chain

### Claude API Call (n8n HTTP Request)
- **Endpoint:** Anthropic Messages API
- **Model:** `claude-sonnet-4-6`
- **Prompt:** System prompt defines HTML email structure + brand style; user message contains research JSON + topic
- **Output format:** JSON with these keys:
  ```json
  {
    "subject": "...",
    "preview_text": "...",
    "html_body": "...",
    "plain_text": "...",
    "chart_data": { "labels": [], "values": [], "title": "..." }
  }
  ```
- **Response mode:** JSON mode (structured output)

### Tool: `tools/generate_chart.py`
- **Input:** `chart_data` JSON (stdin)
- **Library:** matplotlib (horizontal bar chart, clean palette for white email background)
- **Output:** base64-encoded PNG string to stdout (chart not yet injected)

### Tool: `tools/brevo_send.py`
- **Input:** subject, preview_text, html_body, plain_text, chart_base64 — all via stdin JSON
- **Chart injection:** Replaces `{{CHART}}` placeholder in `html_body` with `<img src="data:image/png;base64,..."/>`
- **API:** Brevo Transactional Email API (`/v3/smtp/email`)
- **List:** Configured via `BREVO_LIST_ID` env var
- **Includes:** Brevo unsubscribe tag in footer (CAN-SPAM compliance, automatic)

---

## HTML Email Structure

Claude generates within this skeleton:

```
[Header — topic as title]
[Lead paragraph — hook/summary]
[3–4 key insight sections with subheadings]
[Chart — inline base64 PNG]
[Source callout — 2–3 linked sources]
[Footer — unsubscribe tag]
```

- **Width:** 600px max (email standard)
- **Font:** System sans-serif stack
- **Style:** Inline CSS only (email client compatibility)
- **Images:** Only the chart — no external image hosting dependencies

---

## Environment Variables

```
PERPLEXITY_API_KEY=
CLAUDE_API_KEY=
BREVO_API_KEY=
BREVO_LIST_ID=
BREVO_SENDER_EMAIL=
BREVO_SENDER_NAME=
```

---

## WAT Files

| File | Purpose |
|---|---|
| `workflows/newsletter.md` | SOP — objective, inputs, tool sequence, edge cases |
| `tools/perplexity_research.py` | Perplexity research call |
| `tools/generate_chart.py` | matplotlib chart → base64 |
| `tools/brevo_send.py` | Brevo send |
| `.env` | All API keys |

---

## Out of Scope (testing phase)

- Subscriber list management / signup forms
- Subject line A/B testing
- Newsletter archive page
- Scheduling / topic queue
- Open rate / click tracking
