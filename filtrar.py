import requests
import unicodedata
from src.parseo import parsear_bytes

URL = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"

KEYWORDS = [
    "publicidad", "comunicacion", "campana", "marketing", "difusion",
    "promocion", "diseno", "branding", "marca", "redes sociales",
    "social media", "contenido", "web", "audiovisual", "video", "imagen",
    "iluminacion", "sonido", "grabacion", "streaming", "evento", "patrocinio",
    "artistic", "produccion", "prensa", "medios", "grafic", "espectaculo",
    "festival", "feria", "cultural", "dinamizacion",
]

def sin_tildes(s):
    s = s or ""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()

print("Descargando y parseando... (un momento)")
resp = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
df = parsear_bytes(resp.content)

df = df[df["nuts"].fillna("").str.startswith("ES70")]

def es_relevante(titulo):
    t = sin_tildes(titulo)
    return any(k in t for k in KEYWORDS)

relevantes = df[df["titulo"].apply(es_relevante)]

print(f"\n{len(relevantes)} licitaciones de Canarias relevantes para una agencia:\n")
for _, row in relevantes.iterrows():
    print("-" * 70)
    print(f"TITULO : {row['titulo']}")
    print(f"ORGANO : {row['organo']}")
    print(f"IMPORTE: {row['importe']}  |  PLAZO: {row['plazo']}")
    print(f"ENLACE : {row['enlace']}")
print("-" * 70)