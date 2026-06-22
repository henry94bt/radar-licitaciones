"""
Paso 6 — EMAIL DIARIO
Mismo contenido que el dashboard, en formato email. Dos modos:
  - generar el .html del email (seguro para la demo: lo enseñas sin enviar nada)
  - enviarlo de verdad por SMTP (opcional)
"""
import smtplib
import os
from email.mime.text import MIMEText
import pandas as pd

import config


def construir_email_html(df: pd.DataFrame) -> str:
    """Devuelve el cuerpo HTML del email a partir del DataFrame resumido."""
    # TODO: versión compacta del dashboard. En email, estilos inline y simples
    #       (los clientes de correo se comen el CSS de <head>).
    items = "\n".join(
        f"<li><b>{row.get('titulo','')}</b> — {row.get('organo','')}<br>"
        f"{row.get('resumen','')}<br>"
        f"<a href='{row.get('enlace','#')}'>Ver pliego</a> · Plazo: {row.get('plazo','')}</li>"
        for _, row in df.iterrows()
    )
    return f"<h2>{config.EMAIL_ASUNTO}</h2><ul>{items}</ul>"


def guardar_email(df: pd.DataFrame, ruta: str = "docs/email_preview.html") -> None:
    """Modo demo: guarda el email como HTML para enseñarlo sin enviar."""
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(construir_email_html(df))
    print(f"Preview del email guardado en {ruta}")


def enviar_email(df: pd.DataFrame) -> None:
    """
    Modo real (opcional): envía por SMTP.
    Credenciales por variable de entorno: SMTP_USER, SMTP_PASS.
    Con Gmail necesitas una 'contraseña de aplicación', no la normal.

    TODO: rellenar solo si decides enviarlo de verdad. Para la demo basta guardar.
    """
    raise NotImplementedError("Opcional — rellenar si quieres envío real por SMTP")


if __name__ == "__main__":
    pass
