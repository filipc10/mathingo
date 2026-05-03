import html

import httpx

from app.config import settings

RESEND_ENDPOINT = "https://api.resend.com/emails"
SUBJECT = "Tvůj přihlašovací odkaz do Mathingo"
FROM = "Mathingo <noreply@mathingo.cz>"


def _render(magic_url: str) -> tuple[str, str]:
    safe_url = html.escape(magic_url, quote=True)
    html_body = f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><title>Mathingo</title></head>
<body style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;background:#fff;padding:32px;color:#171717;">
  <div style="max-width:480px;margin:0 auto;">
    <h1 style="font-size:28px;font-weight:700;margin:0 0 24px;">Mathingo</h1>
    <p style="line-height:1.5;margin:0 0 24px;">Klikni na tlačítko níže pro přihlášení do aplikace.</p>
    <p style="margin:0 0 24px;">
      <a href="{safe_url}" style="display:inline-block;background:#171717;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;">Přihlásit se</a>
    </p>
    <p style="color:#737373;font-size:14px;line-height:1.5;margin:0 0 32px;">Odkaz je platný 15 minut. Pokud jsi se nepřihlašoval/a, tento email ignoruj.</p>
    <p style="color:#a3a3a3;font-size:13px;margin:0;border-top:1px solid #e5e5e5;padding-top:16px;"><a href="https://mathingo.cz" style="color:#a3a3a3;">mathingo.cz</a></p>
  </div>
</body>
</html>"""

    plain = (
        "Mathingo\n\n"
        "Klikni na odkaz níže pro přihlášení do aplikace:\n"
        f"{magic_url}\n\n"
        "Odkaz je platný 15 minut. Pokud jsi se nepřihlašoval/a, tento email ignoruj.\n\n"
        "mathingo.cz"
    )

    return html_body, plain


async def send_magic_link(email: str, token: str) -> None:
    """Send the magic-link email through Resend.

    Raises httpx.HTTPStatusError if Resend returns non-2xx.
    """
    magic_url = f"{settings.app_url}/auth/click?token={token}"
    html_body, plain = _render(magic_url)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            RESEND_ENDPOINT,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": FROM,
                "to": [email],
                "subject": SUBJECT,
                "html": html_body,
                "text": plain,
            },
        )
        response.raise_for_status()
