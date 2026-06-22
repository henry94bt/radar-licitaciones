"""
Paso 1 — DESCARGA
Baja el fichero de licitaciones publicadas de la PLACSP a disco.
"""
from pathlib import Path
import requests

import config


def descargar_fichero(url: str = config.URL_FICHERO_LICITACIONES,
                      dir_destino: str = config.DIR_DESCARGA) -> Path:
    """
    Descarga el fichero de licitaciones y lo guarda en disco.

    Returns:
        Path al fichero descargado (probablemente un .zip con .atom dentro).

    TODO:
      - Confirmar URL real en config.URL_FICHERO_LICITACIONES.
      - El recurso suele ser un .zip mensual. Si es así, descomprimir aquí o en parseo.
      - Añadir cabecera User-Agent decente y un timeout generoso.
      - (de cara a producción) lógica de reintentos con backoff — la copias tal
        cual del Gas Tracker, que ya la tienes resuelta.
    """
    Path(dir_destino).mkdir(parents=True, exist_ok=True)

    # raise NotImplementedError("Rellenar: descarga del fichero PLACSP")
    resp = requests.get(url, timeout=60, headers={"User-Agent": "radar-licitaciones-demo"})
    resp.raise_for_status()

    destino = Path(dir_destino) / "licitaciones.zip"  # TODO: nombre/extensión reales
    destino.write_bytes(resp.content)
    return destino


def descomprimir_si_hace_falta(ruta: Path) -> list[Path]:
    """
    Si el fichero es un .zip, descomprime y devuelve la lista de .atom.
    Si ya es un .atom, lo devuelve en una lista de un elemento.

    TODO: implementar con zipfile cuando confirmemos el formato real.
    """
    raise NotImplementedError("Rellenar tras confirmar si es zip o atom suelto")


if __name__ == "__main__":
    f = descargar_fichero()
    print(f"Descargado en: {f}  ({f.stat().st_size / 1_000_000:.1f} MB)")
