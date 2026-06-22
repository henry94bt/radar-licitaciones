import requests
from lxml import etree

URL = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"

print("Descargando el feed... (un momento)")
resp = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()

root = etree.fromstring(resp.content)
ATOM = "{http://www.w3.org/2005/Atom}"

entries = root.findall(f"{ATOM}entry")
print(f"El feed trae {len(entries)} licitaciones. Te muestro la primera:\n")
entry = entries[0]

def localname(tag):
    return tag.split("}")[-1] if "}" in tag else tag

def recorrer(elem, ruta=""):
    nombre = localname(elem.tag)
    ruta_actual = f"{ruta}/{nombre}" if ruta else nombre
    texto = (elem.text or "").strip()
    if texto:
        print(f"{ruta_actual}: {texto}")
    for k, v in elem.attrib.items():
        print(f"{ruta_actual}[@{localname(k)}]: {v}")
    for hijo in elem:
        recorrer(hijo, ruta_actual)

print("=" * 70)
recorrer(entry)
print("=" * 70)
print("\nListo. Copia toda esta lista y pegasela a Claude.")