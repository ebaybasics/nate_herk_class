import os
import sys
import json
import requests


def send_newsletter(data: dict) -> dict:
    api_key = os.environ.get("BREVO_API_KEY")
    if not api_key:
        raise EnvironmentError("BREVO_API_KEY is not set")

    to_email = os.environ.get("BREVO_TEST_EMAIL")
    if not to_email:
        raise EnvironmentError("BREVO_TEST_EMAIL is not set")

    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "")
    sender_name = os.environ.get("BREVO_SENDER_NAME", "")

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
