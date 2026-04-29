import os
import requests


def send_email_resend(to_email: str, subject: str, text: str):
    api_key = os.getenv("RESEND_API_KEY", "")
    from_email = os.getenv("RESEND_FROM", "")
    if not api_key or not from_email:
        raise Exception("Missing RESEND_API_KEY or RESEND_FROM in .env")

    dev_to = os.getenv("RESEND_DEV_TO", "").strip()
    original_to = to_email
    if dev_to and to_email.lower() != dev_to.lower():
        to_email = dev_to
        subject = f"[DEV to={original_to}] {subject}"
        text = f"[DEV MODE]\nIntended recipient: {original_to}\n\n{text}"

    url = "https://api.resend.com/emails"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"from": from_email, "to": [to_email], "subject": subject, "text": text}

    r = requests.post(url, headers=headers, json=payload, timeout=15)
    if r.status_code >= 400:
        raise Exception(f"Resend error {r.status_code}: {r.text}")
    out = r.json()
    if dev_to:
        out["_dev"] = {"original_to": original_to, "actual_to": to_email}
    return out

