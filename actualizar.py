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
    "Eres el analista de licitaciones de LA PEPA STUDIO, agencia de marketing y comunicacion "
    "de Telde, Gran Canaria. Te paso los datos de una licitacion publica (titulo, organo, "
    "importe, plazo, CPV, lugar de ejecucion). Aplica este criterio para decidir relevancia "
    "y semaforo:\n"
    "\n"
    "SERVICIOS CORE (si son >=80% del objeto -> encaja bien): diseno grafico, editorial, "
    "branding/identidad corporativa, gestion de redes sociales, desarrollo web, tiendas "
    "online, produccion audiovisual/shooting, estrategia de contenido/marketing, SEO.\n"
    "SERVICIOS SECUNDARIOS (encaja pero con cautela): Meta/Google Ads como servicio "
    "principal sin diseno; gestion de eventos EN GRAN CANARIA que impliquen subcontratar "
    "iluminacion/sonido.\n"
    "DESCARTAR SIEMPRE (no relevante, semaforo rojo): email marketing como servicio "
    "principal; ruedas de prensa, gabinete de prensa o relaciones con medios de "
    "comunicacion (no periodismo, no gestion informativa institucional) como objeto "
    "principal; eventos con presencia fisica FUERA de Gran Canaria (Tenerife, Lanzarote, "
    "Fuerteventura, La Palma, La Gomera, El Hierro o Peninsula), salvo que el servicio "
    "sea 100% digital/remoto (diseno, web, RRSS, contenido); tambien descarta obras, "
    "asfaltado, catering, limpieza, suministro de equipos/material, informatica/servidores "
    "y mantenimiento aunque mencionen un evento o feria.\n"
    "\n"
    "SEMAFORO (solo si relevante=true):\n"
    "- verde: >=80% servicios core, ubicacion Gran Canaria o 100% digital, sin senales de "
    "riesgo, importe razonable para dedicar recursos.\n"
    "- naranja: encaja pero hay un servicio secundario dominante, o eventos con "
    "subcontratas en Gran Canaria, o importe bajo (<20.000EUR, valorar si compensa el "
    "esfuerzo), o duda real sobre si el trabajo es presencial fuera de Gran Canaria.\n"
    "- rojo: no se cumple ninguno de los anteriores pero aun asi decides relevante=true "
    "por algun motivo puntual (raro; normalmente rojo va con relevante=false).\n"
    "\n"
    "Responde SOLO con un JSON valido, sin markdown ni texto extra, con esta forma exacta: "
    '{"relevante": true, "semaforo": "verde", "motivos": ["..."], "resumen": "..."}. '
    "En 'motivos' pon SIEMPRE 1-3 frases cortas en espanol citando la regla concreta "
    "aplicada, tanto si es relevante como si no (ej: 'Evento en Tenerife, fuera de Gran "
    "Canaria' o 'Diseno y RRSS, encaje core'). Se breve: cada motivo debe caber en una "
    "linea, no expliques de mas. "
    "En 'resumen' pon dos frases: que piden y por que le encaja (o no) a la agencia. "
    "Si no es relevante, pon \"relevante\": false, \"semaforo\": \"rojo\" y \"resumen\": \"\"."
)

SEMAFORO_ICONO = {"verde": "🟢", "naranja": "🟠", "rojo": "🔴"}


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
        f"Lugar de ejecucion: {row.get('lugar') or '(no especificado)'}\n"
        f"CPV: {row['cpv']}"
    )
    resp = cliente.messages.create(
        model=MODELO, max_tokens=600, system=SYSTEM,
        messages=[{"role": "user", "content": datos}],
    )
    texto = resp.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON invalido para «{row['titulo'][:60]}...»")
        print(f"      Error: {e}")
        print(f"      Respuesta cruda: {texto[:500]}")
        raise


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
        titulo_corto = row["titulo"][:70]
        if v.get("relevante"):
            items.append({
                "titulo": row["titulo"], "organo": row["organo"],
                "importe": row["importe"], "plazo": row["plazo"],
                "lugar": row.get("lugar"), "enlace": row["enlace"],
                "resumen": v.get("resumen", ""),
                "semaforo": v.get("semaforo", "naranja"),
                "motivos": v.get("motivos", []),
            })
            print(f"  {SEMAFORO_ICONO.get(v.get('semaforo'), '⚪')} {titulo_corto}")
        else:
            descartadas += 1
            motivos = "; ".join(v.get("motivos", []))
            print(f"  ⛔ {titulo_corto}  →  {motivos}")

    # Orden: primero verdes, luego naranjas, dentro de cada grupo por plazo mas cercano.
    orden_semaforo = {"verde": 0, "naranja": 1, "rojo": 2}
    items.sort(key=lambda it: (orden_semaforo.get(it.get("semaforo"), 1), it.get("plazo") or ""))

    print(f"La IA descarto {descartadas}. Quedan {len(items)} recomendadas.")
    os.makedirs("data", exist_ok=True)
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Guardado en {SALIDA_JSON}. Ahora ejecuta:  python dashboard.py")


if __name__ == "__main__":
    main()