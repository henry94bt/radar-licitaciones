import json
import requests
import unicodedata
from anthropic import Anthropic
from src.parseo import parsear_bytes

URL = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
MODELO = "claude-haiku-4-5-20251001"

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
        model=MODELO,
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": datos}],
    )
    texto = resp.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)


print("Descargando y parseando... (un momento)")
resp = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
df = parsear_bytes(resp.content)

df = df[df["nuts"].fillna("").str.startswith("ES70")]
df = df[df["titulo"].apply(es_candidata)]

print(f"{len(df)} candidatas de Canarias. Pasandolas por la IA...\n")

relevantes = []
descartadas = 0
for _, row in df.iterrows():
    try:
        veredicto = evaluar(row)
    except Exception as e:
        print(f"(salto una por un error: {e})")
        continue
    if veredicto.get("relevante"):
        relevantes.append((row, veredicto.get("resumen", "")))
    else:
        descartadas += 1

print(f"La IA descarto {descartadas} por no encajar de verdad.\n")
print(f"{len(relevantes)} licitaciones recomendadas para la agencia:\n")
for row, resumen in relevantes:
    print("-" * 70)
    print(f"TITULO : {row['titulo']}")
    print(f"ORGANO : {row['organo']}")
    print(f"IMPORTE: {row['importe']}  |  PLAZO: {row['plazo']}")
    print(f"RESUMEN: {resumen}")
    print(f"ENLACE : {row['enlace']}")