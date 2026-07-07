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


def _bloque_oportunidades(items: list[dict], titulo_seccion: str) -> str:
    """Lista en HTML de las oportunidades (verde/naranja) de un ambito
    (Canarias o resto de Espana). Cadena vacia si no hay ninguna, para que
    el llamante decida si mostrar la seccion."""
    oportunidades = [it for it in items if it.get("relevante", True)]
    if not oportunidades:
        return ""
    filas = "\n".join(
        f"<li><b>{it.get('titulo','')}</b> — {it.get('organo','')}<br>"
        f"{it.get('resumen','')}<br>"
        f"<a href='{it.get('enlace','#')}'>Ver pliego</a> · Plazo: {it.get('plazo','')} "
        f"· {'🟢' if it.get('semaforo') == 'verde' else '🟠'}</li>"
        for it in oportunidades
    )
    return f"<h3>{titulo_seccion}</h3><ul>{filas}</ul>"


def construir_email_html(items_canarias: list[dict], items_nacional: list[dict] | None = None) -> str:
    """Devuelve el cuerpo HTML del email a partir de las licitaciones de
    Canarias y (si se pasan) del resto de España. Solo incluye las
    relevantes (verde/naranja) -- las descartadas se quedan fuera."""
    items_nacional = items_nacional or []
    bloques = [
        _bloque_oportunidades(items_canarias, "Canarias"),
        _bloque_oportunidades(items_nacional, "Resto de España (remoto)"),
    ]
    bloques = [b for b in bloques if b]
    cuerpo = "".join(bloques) if bloques else "<p>Sin oportunidades nuevas hoy.</p>"
    return f"<h2>{config.EMAIL_ASUNTO}</h2>{cuerpo}"


def guardar_email(items_canarias: list[dict], items_nacional: list[dict] | None = None,
                   ruta: str = "docs/email_preview.html") -> None:
    """Modo demo: guarda el email como HTML para enseñarlo sin enviar."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(construir_email_html(items_canarias, items_nacional))
    print(f"Preview del email guardado en {ruta}")


def enviar_email(items_canarias: list[dict], items_nacional: list[dict] | None = None) -> None:
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
            "html": construir_email_html(items_canarias, items_nacional),
        },
        timeout=30,
    )
    resp.raise_for_status()
    print(f"Email enviado a {', '.join(config.EMAIL_DESTINO)}")


def _cargar(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


if __name__ == "__main__":
    items_canarias = _cargar("data/relevantes.json")
    items_nacional = _cargar("data/relevantes_nacional.json")
    guardar_email(items_canarias, items_nacional)
    enviar_email(items_canarias, items_nacional)