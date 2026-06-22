import json
import io
import os
import zipfile
import unicodedata
from datetime import date
import requests
import pandas as pd
from anthropic import Anthropic
from src.parseo import parsear_bytes

# Mes a consultar, en formato AAAAMM. Cambia esto cuando quieras otro mes.
ANIO_MES = "202606"
URL = f"https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_{ANIO_MES}.zip"
MODELO = "claude-haiku-4-5-20251001"
SALIDA_JSON = "data/relevantes.json"
MAX_CANDIDATAS = 40  # tope de seguridad para no disparar tiempo/coste de IA

KEYWORDS = [
    "publicidad", "comunicacion", "campana", "marketing", "difusion",
    "promocion", "diseno", "branding", "marca", "redes sociales",
    "social media", "contenido", "web", "audiovisual", "video", "imagen",
    "iluminacion", "sonido", "grabacion", "streaming", "evento", "patrocinio",
    "artistic", "produccion", "prensa", "medios", "grafic", "espectaculo",
    "festival", "feria", "cultural", "dinamizacion",
]

cliente = Anthropic()

SYSTEM = (
    "Eres un asistente de una agencia de marketing y comunicacion en Canarias "
    "(branding, diseno grafico, SEO, redes sociales, campanas, eventos, audiovisual, web). "
    "Te paso los datos de una licitacion publica. Decide si es un trabajo que una agencia "
    "asi podria ejecutar de verdad. Se ESTRICTO: obras, asfaltado, catering, limpieza, "
    "suministro de equipos o material, informatica/servidores y mantenimiento NO son "
    "relevantes, aunque mencionen un evento o una feria. "
    "Responde SOLO con un JSON valido, sin markdown ni texto extra, con esta forma exacta: "
    '{"relevante": true, "resumen": "..."}. '
    "En 'resumen' pon dos frases en espanol: que piden y por que le encaja a la agencia. "
    "Si no es relevante, pon \"relevante\": false y \"resumen\": \"\"."
)


def sin_tildes(s):
    s = s or ""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def es_candidata(titulo):
    t = sin_tildes(titulo)
    return any(k in t for k in KEYWORDS)


def evaluar(row):
    datos = (
        f"Titulo: {row['titulo']}\n"
        f"Organo: {row['organo']}\n"
        f"Importe: {row['importe']}\n"
        f"Plazo: {row['plazo']}\n"
        f"CPV: {row['cpv']}"
    )
    resp = cliente.messages.create(
        model=MODELO, max_tokens=300, system=SYSTEM,
        messages=[{"role": "user", "content": datos}],
    )
    texto = resp.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)


def main():
    print(f"Descargando el fichero del mes {ANIO_MES} (puede tardar un poco)...")
    resp = requests.get(URL, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    dfs = []
    for nombre in z.namelist():
        if nombre.lower().endswith(".atom"):
            dfs.append(parsear_bytes(z.read(nombre)))
    df = pd.concat(dfs, ignore_index=True)
    print(f"{len(df)} licitaciones en el mes.")

    # Filtro 1: Canarias
    df = df[df["nuts"].fillna("").str.startswith("ES70")]
    # Filtro 2: tematica (titulo con keyword)
    df = df[df["titulo"].apply(es_candidata)]
    # Filtro 3: en plazo (fecha de cierre futura). Las fechas ISO se comparan como texto.
    hoy = date.today().isoformat()
    df = df[df["plazo"].fillna("") >= hoy]
    # Quitar duplicados (un expediente aparece varias veces al actualizarse)
    df = df.drop_duplicates(subset=["organo", "titulo"])
    print(f"{len(df)} candidatas de Canarias, abiertas y del sector.")

    if len(df) > MAX_CANDIDATAS:
        df = df.head(MAX_CANDIDATAS)
        print(f"(limito a {MAX_CANDIDATAS} para no alargar la demo)")

    print("Pasandolas por la IA...")
    items = []
    descartadas = 0
    for _, row in df.iterrows():
        try:
            v = evaluar(row)
        except Exception as e:
            print(f"(salto una por un error: {e})")
            continue
        if v.get("relevante"):
            items.append({
                "titulo": row["titulo"], "organo": row["organo"],
                "importe": row["importe"], "plazo": row["plazo"],
                "lugar": row.get("lugar"), "enlace": row["enlace"],
                "resumen": v.get("resumen", ""),
            })
        else:
            descartadas += 1

    print(f"La IA descarto {descartadas}. Quedan {len(items)} recomendadas.")
    os.makedirs("data", exist_ok=True)
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Guardado en {SALIDA_JSON}. Ahora ejecuta:  python dashboard.py")


if __name__ == "__main__":
    main()
