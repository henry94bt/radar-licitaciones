"""
Paso 4 — RESUMEN
Por cada licitación seleccionada, pide a la API de Anthropic un resumen de 2
líneas: qué piden y a quién le encaja. Esto es el "wow" de la demo — lo que de
verdad ahorra las horas de lectura.

La API key se lee de la variable de entorno ANTHROPIC_API_KEY. NUNCA en el código.
"""
import os
import pandas as pd
from anthropic import Anthropic

import config

cliente = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PROMPT_SISTEMA = (
    "Eres un asistente de una agencia de marketing y comunicación. Te paso datos "
    "de una licitación pública. Devuelve EXACTAMENTE dos líneas en español: "
    "(1) qué se está contratando, en cristiano; "
    "(2) por qué le encaja (o no) a una agencia de comunicación, y plazo. "
    "Sin preámbulos, sin markdown."
)


def resumir_una(fila) -> str:
    """Resume una licitación. Devuelve el texto del resumen."""
    contenido = (
        f"Título: {fila.get('titulo')}\n"
        f"Órgano: {fila.get('organo')}\n"
        f"Importe: {fila.get('importe')}\n"
        f"Plazo: {fila.get('plazo')}\n"
        f"CPV: {fila.get('cpv')}"
    )
    # TODO: manejar errores de la API y reintentos suaves.
    resp = cliente.messages.create(
        model=config.MODELO_LLM,
        max_tokens=200,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": contenido}],
    )
    return resp.content[0].text.strip()


def resumir(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade una columna 'resumen' al DataFrame filtrado.
    Limita a config.MAX_LICITACIONES_A_RESUMIR para controlar coste/tiempo.
    """
    df = df.head(config.MAX_LICITACIONES_A_RESUMIR).copy()
    df["resumen"] = df.apply(resumir_una, axis=1)
    return df


if __name__ == "__main__":
    pass
