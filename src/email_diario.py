"""
Paso 6 — EMAIL DIARIO
Mismo contenido que el dashboard, en formato email. Dos modos:
  - generar el .html del email (seguro para la demo: lo enseñas sin enviar nada)
  - enviarlo de verdad por SMTP (opcional, sin implementar todavia)
"""
import json
import smtplib
import os
from email.mime.text import MIMEText

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
    """
    Modo real (opcional): envía por SMTP.
    Credenciales por variable de entorno: SMTP_USER, SMTP_PASS.
    Con Gmail necesitas una 'contraseña de aplicación', no la normal.

    TODO: rellenar solo si decides enviarlo de verdad. Para la demo basta guardar.
    """
    raise NotImplementedError("Opcional — rellenar si quieres envío real por SMTP")


if __name__ == "__main__":
    with open("data/relevantes.json", encoding="utf-8") as f:
        items = json.load(f)
    guardar_email(items)