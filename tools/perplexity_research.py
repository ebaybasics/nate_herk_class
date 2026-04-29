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
