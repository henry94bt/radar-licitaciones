"""
Paso 3 — FILTRO
De miles de licitaciones a las ~10 que le sirven a una agencia de comunicación
en Canarias y que aún están en plazo.
"""
import pandas as pd

import config


def es_canarias(fila) -> bool:
    """¿La licitación es de ámbito canario? (por NUTS o por nombre del órgano)."""
    # TODO: comprobar NUTS contra config.NUTS_CANARIAS si el campo existe,
    #       y como respaldo buscar config.PISTAS_ORGANO_CANARIAS en el órgano.
    organo = str(fila.get("organo", "")).lower()
    return any(p in organo for p in config.PISTAS_ORGANO_CANARIAS)


def cpv_relevante(cpv: str) -> bool:
    """¿El CPV empieza por alguno de los prefijos que nos interesan?"""
    if not cpv:
        return False
    return any(str(cpv).startswith(pref.replace("x", "")) for pref in config.CPV_RELEVANTES)


def titulo_relevante(titulo: str) -> bool:
    """Respaldo: ¿el título menciona algo de comunicación/diseño/web?"""
    t = str(titulo).lower()
    return any(k in t for k in config.KEYWORDS_TITULO)


def en_plazo(fila) -> bool:
    """¿Sigue abierta para presentarse?"""
    # TODO: combinar estado válido + plazo > hoy
    return str(fila.get("estado", "")).upper() in [e.upper() for e in config.ESTADOS_VALIDOS]


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica los tres filtros (ámbito + temática + plazo) y devuelve el subconjunto.

    Lógica de temática: relevante si (CPV cuadra) O (título cuadra). El OR sube
    el recall porque muchos órganos clasifican mal el CPV.
    """
    canarias = df.apply(es_canarias, axis=1)
    tematica = df["cpv"].apply(cpv_relevante) | df["titulo"].apply(titulo_relevante)
    abierta = df.apply(en_plazo, axis=1)

    resultado = df[canarias & tematica & abierta].copy()
    # TODO: ordenar por plazo más cercano y resetear índice
    return resultado


if __name__ == "__main__":
    # prueba rápida con un DataFrame ya parseado
    pass
