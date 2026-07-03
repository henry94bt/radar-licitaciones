import requests
import pandas as pd
from lxml import etree

URL = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3.atom"
ATOM = "{http://www.w3.org/2005/Atom}"

RUTAS = {
    "titulo": "entry/ContractFolderStatus/ProcurementProject/Name",
    "organo": "entry/ContractFolderStatus/LocatedContractingParty/Party/PartyName/Name",
    "importe": "entry/ContractFolderStatus/ProcurementProject/BudgetAmount/TotalAmount",
    "plazo": "entry/ContractFolderStatus/TenderingProcess/TenderSubmissionDeadlinePeriod/EndDate",
    "estado": "entry/ContractFolderStatus/ContractFolderStatusCode",
    "nuts": "entry/ContractFolderStatus/ProcurementProject/RealizedLocation/CountrySubentityCode",
    "lugar": "entry/ContractFolderStatus/ProcurementProject/RealizedLocation/CountrySubentity",
    "enlace": "entry/link@href",
}
RUTA_CPV = "entry/ContractFolderStatus/ProcurementProject/RequiredCommodityClassification/ItemClassificationCode"

# Documentos del pliego: pueden venir como URL externa (ExternalReference/URI) o
# embebidos en base64 (EmbeddedDocumentBinaryObject). Guardamos ambas rutas y nos
# quedamos con la que tenga contenido.
RUTA_PCAP_URL = "entry/ContractFolderStatus/LegalDocumentReference/Attachment/ExternalReference/URI"
RUTA_PCAP_B64 = "entry/ContractFolderStatus/LegalDocumentReference/Attachment/EmbeddedDocumentBinaryObject"
RUTA_PPT_URL = "entry/ContractFolderStatus/TechnicalDocumentReference/Attachment/ExternalReference/URI"
RUTA_PPT_B64 = "entry/ContractFolderStatus/TechnicalDocumentReference/Attachment/EmbeddedDocumentBinaryObject"
RUTA_ANEXOS_URL = "entry/ContractFolderStatus/AditionalDocumentReference/Attachment/ExternalReference/URI"


def _documento(idx, ruta_url, ruta_b64):
    """Devuelve (tipo, valor) para un documento: ('url', str) o ('base64', str) o (None, None)."""
    urls = idx.get(ruta_url, [])
    if urls:
        return "url", urls[0]
    b64 = idx.get(ruta_b64, [])
    if b64:
        return "base64", b64[0]
    return None, None


def _indexar(entry):
    idx = {}
    def rec(elem, ruta=""):
        nombre = elem.tag.split("}")[-1]
        ruta_actual = f"{ruta}/{nombre}" if ruta else nombre
        texto = (elem.text or "").strip()
        if texto:
            idx.setdefault(ruta_actual, []).append(texto)
        for k, v in elem.attrib.items():
            kn = k.split("}")[-1]
            idx.setdefault(f"{ruta_actual}@{kn}", []).append(v)
        for hijo in elem:
            rec(hijo, ruta_actual)
    rec(entry)
    return idx


def parsear_bytes(contenido):
    root = etree.fromstring(contenido)
    filas = []
    for entry in root.findall(f"{ATOM}entry"):
        idx = _indexar(entry)
        fila = {col: idx.get(ruta, [None])[0] for col, ruta in RUTAS.items()}
        fila["cpv"] = ", ".join(idx.get(RUTA_CPV, []))
        fila["pcap_tipo"], fila["pcap_valor"] = _documento(idx, RUTA_PCAP_URL, RUTA_PCAP_B64)
        fila["ppt_tipo"], fila["ppt_valor"] = _documento(idx, RUTA_PPT_URL, RUTA_PPT_B64)
        fila["anexos_urls"] = idx.get(RUTA_ANEXOS_URL, [])
        filas.append(fila)
    return pd.DataFrame(filas)


def parsear_atom(ruta):
    with open(ruta, "rb") as f:
        return parsear_bytes(f.read())


if __name__ == "__main__":
    print("Descargando el feed... (un momento)")
    resp = requests.get(URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    df = parsear_bytes(resp.content)
    print(f"\nParseadas {len(df)} licitaciones.\n")

    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.width", 200)
    print(df[["titulo", "organo", "importe", "plazo", "nuts"]].head(10).to_string(index=False))

    canarias = df[df["nuts"].fillna("").str.startswith("ES70")]
    print(f"\nDe esas {len(df)}, {len(canarias)} son de Canarias.")
    if len(canarias):
        print(canarias[["titulo", "organo", "lugar", "plazo"]].to_string(index=False))