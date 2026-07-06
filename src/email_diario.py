"""
Paso 6 — EMAIL DIARIO
Mismo contenido que el dashboard, en formato email. Dos modos:
  - generar el .html del email (seguro para la demo: lo enseñas sin enviar nada)
  - enviarlo de verdad vía API de Resend (SMTP de IONOS no vale: bloquea
    logins desde las IPs de datacenter de GitHub Actions)
"""
import json
import os
import requests

import config


def construir_email_html(items: list[dict]) -> str:
    """Devuelve el cuerpo HTML del email a partir de la lista de licitaciones
    (mismo formato que data/relevantes.json). Solo incluye las relevantes
    (verde/naranja) -- las descartadas se quedan fuera del email."""
    oportunidades = [it for it in items if it.get("relevante", True)]
    if not oportunidades:
        cuerpo = "<p>Sin oportunidades nuevas hoy.</p>"
    else:
        cuerpo = "<ul>" + "\n".join(
            f"<li><b>{it.get('titulo','')}</b> — {it.get('organo','')}<br>"
            f"{it.get('resumen','')}<br>"
            f"<a href='{it.get('enlace','#')}'>Ver pliego</a> · Plazo: {it.get('plazo','')} "
            f"· {'🟢' if it.get('semaforo') == 'verde' else '🟠'}</li>"
            for it in oportunidades
        ) + "</ul>"
    return f"<h2>{config.EMAIL_ASUNTO}</h2>{cuerpo}"


def guardar_email(items: list[dict], ruta: str = "docs/email_preview.html") -> None:
    """Modo demo: guarda el email como HTML para enseñarlo sin enviar."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(construir_email_html(items))
    print(f"Preview del email guardado en {ruta}")


def enviar_email(items: list[dict]) -> None:
    """Envía el resumen vía API de Resend (HTTPS, no SMTP). Credenciales
    por variable de entorno: RESEND_API_KEY."""
    api_key = os.environ["RESEND_API_KEY"]
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": config.EMAIL_REMITENTE,
            "to": config.EMAIL_DESTINO,
            "subject": config.EMAIL_ASUNTO,
            "html": construir_email_html(items),
        },
        timeout=30,
    )
    resp.raise_for_status()
    print(f"Email enviado a {', '.join(config.EMAIL_DESTINO)}")


if __name__ == "__main__":
    with open("data/relevantes.json", encoding="utf-8") as f:
        items = json.load(f)
    guardar_email(items)
    enviar_email(items)