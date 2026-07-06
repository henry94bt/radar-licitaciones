"""
Fase 2 — PLIEGOS
Descarga y extrae el texto de los documentos PCAP (administrativo) y PPT
(técnico) de una licitación, para poder pasarlos por la IA y sacar detalle
que no viene en el feed (criterios de valoración, solvencia, garantía,
plazo de ejecución, lotes...).

Cada documento puede venir de dos formas en el feed (ver src/parseo.py):
  - "url": hay que descargarlo con requests
  - "base64": ya viene embebido en el propio XML

Cualquier fallo (documento no disponible, PDF ilegible, demasiado grande)
se traduce en devolver None: quien llama decide si sigue sin detalle.
"""
import base64
import io

import requests
from pypdf import PdfReader

TAMANO_MAX_BYTES = 15_000_000  # 15 MB, para no colgarnos con un pliego enorme
# Tope de texto que mandamos a la IA por documento. Los primeros miles de
# caracteres de un PCAP suelen ser solo el indice (paginas de sumario), asi
# que un tope bajo se queda sin llegar al contenido real (solvencia,
# garantia, criterios). 30000 caracteres (~7-8k tokens) da margen de sobra
# para pasar el indice y llegar al cuerpo, con coste todavia bajo en Haiku.
CARACTERES_MAX_POR_DOC = 30000


def _descargar(tipo, valor):
    if tipo == "url" and valor:
        resp = requests.get(valor, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return resp.content
    if tipo == "base64" and valor:
        return base64.b64decode(valor)
    return None


def _texto_pdf(contenido):
    if not contenido or len(contenido) > TAMANO_MAX_BYTES:
        return None
    lector = PdfReader(io.BytesIO(contenido))
    paginas = [p.extract_text() or "" for p in lector.pages]
    texto = "\n".join(paginas).strip()
    return texto or None


def _texto_documento(tipo, valor):
    try:
        contenido = _descargar(tipo, valor)
        return _texto_pdf(contenido)
    except Exception:
        return None


def obtener_texto_pliego(row) -> str | None:
    """Combina el texto del PCAP y del PPT de una fila (dict o pandas Series
    con las claves pcap_tipo/pcap_valor/ppt_tipo/ppt_valor). Devuelve None si
    no se pudo sacar nada de ninguno de los dos."""
    partes = []
    pcap = _texto_documento(row.get("pcap_tipo"), row.get("pcap_valor"))
    if pcap:
        partes.append("=== PLIEGO ADMINISTRATIVO (PCAP) ===\n" + pcap[:CARACTERES_MAX_POR_DOC])
    ppt = _texto_documento(row.get("ppt_tipo"), row.get("ppt_valor"))
    if ppt:
        partes.append("=== PLIEGO TÉCNICO (PPT) ===\n" + ppt[:CARACTERES_MAX_POR_DOC])
    return "\n\n".join(partes) if partes else None
