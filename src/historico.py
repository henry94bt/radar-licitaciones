"""
Bucle de aprendizaje: registra el desenlace real de cada expediente en
data/historico.csv, indexado por id_evl (ver notas/CONVENCION.md).

Uso desde otro script:
    from src.historico import actualizar_fila
    actualizar_fila("BzszOPWAEUpLAIVZdUs8KA==", resultado="ganada", adjudicatario="...")

Uso desde terminal (un campo por argumento, solo los que quieras tocar):
    python -m src.historico BzszOPWAEUpLAIVZdUs8KA== resultado=ganada adjudicatario="La Pepa Studio"
"""
import csv
import sys

RUTA_CSV = "data/historico.csv"

COLUMNAS = [
    "id_evl", "expediente", "organo_contratacion", "objeto", "lotes",
    "presupuesto_base", "fecha_limite", "clasificacion_radar",
    "nos_presentamos", "motivo", "puntuacion_pepa", "puntuacion_ganador",
    "adjudicatario", "importe_adjudicacion", "resultado", "aprendizaje",
]

RESULTADOS_VALIDOS = {"pendiente", "ganada", "perdida", "desierta", "no_presentada"}


def _leer_filas():
    with open(RUTA_CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _escribir_filas(filas):
    with open(RUTA_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNAS)
        writer.writeheader()
        writer.writerows(filas)


def actualizar_fila(id_evl: str, **campos) -> None:
    """Crea la fila de ese id_evl si no existe, o actualiza los campos dados
    si ya existe. Nunca toca las demás columnas de una fila existente."""
    if not id_evl:
        raise ValueError("id_evl es obligatorio")
    campos_desconocidos = set(campos) - set(COLUMNAS)
    if campos_desconocidos:
        raise ValueError(f"Columna(s) desconocida(s): {', '.join(campos_desconocidos)}")
    if "resultado" in campos and campos["resultado"] not in RESULTADOS_VALIDOS:
        raise ValueError(
            f"resultado debe ser uno de {sorted(RESULTADOS_VALIDOS)}, "
            f"recibido: {campos['resultado']!r}"
        )

    filas = _leer_filas()
    for fila in filas:
        if fila["id_evl"] == id_evl:
            fila.update(campos)
            break
    else:
        nueva = {col: "" for col in COLUMNAS}
        nueva["id_evl"] = id_evl
        nueva["resultado"] = nueva["resultado"] or "pendiente"
        nueva.update(campos)
        filas.append(nueva)

    _escribir_filas(filas)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m src.historico <id_evl> [columna=valor ...]")
        raise SystemExit(1)
    id_evl = sys.argv[1]
    campos = dict(arg.split("=", 1) for arg in sys.argv[2:])
    actualizar_fila(id_evl, **campos)
    print(f"Fila de {id_evl} actualizada en {RUTA_CSV}")
