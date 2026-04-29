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
