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