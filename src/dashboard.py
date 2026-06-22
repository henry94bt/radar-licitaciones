"""
Paso 5 — DASHBOARD
Vuelca las licitaciones resumidas a un HTML estático bonito (docs/index.html),
listo para publicar en GitHub Pages. Mismo patrón que el Gas Tracker.
"""
import pandas as pd

import config


def generar_dashboard(df: pd.DataFrame, ruta: str = config.RUTA_DASHBOARD) -> None:
    """
    Genera el HTML del dashboard a partir del DataFrame con columna 'resumen'.

    TODO:
      - Diseño: reutiliza tu tema (paleta, tipografía) para que parezca tuyo.
      - Cada licitación = una tarjeta: título, órgano, importe, badge de plazo
        (rojo si quedan <5 días), el resumen del LLM, y botón "Ver pliego".
      - Cabecera con fecha de actualización y nº de licitaciones encontradas.
      - Pie con atribución a la PLACSP (obligatorio por la licencia de reutilización).
    """
    # Esqueleto mínimo para tener algo que abrir desde ya:
    filas_html = "\n".join(
        f"<article class='card'>"
        f"<h2>{row.get('titulo','')}</h2>"
        f"<p class='org'>{row.get('organo','')}</p>"
        f"<p class='plazo'>Plazo: {row.get('plazo','')}</p>"
        f"<p class='resumen'>{row.get('resumen','')}</p>"
        f"<a href='{row.get('enlace','#')}'>Ver pliego</a>"
        f"</article>"
        for _, row in df.iterrows()
    )

    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>{config.TITULO_DASHBOARD}</title>
<!-- TODO: pegar aquí tus estilos (el tema azul/coral que ya usas) -->
</head><body>
<header><h1>{config.TITULO_DASHBOARD}</h1></header>
<main>{filas_html}</main>
<footer>Datos: Plataforma de Contratación del Sector Público (reutilización con atribución)</footer>
</body></html>"""

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generado en {ruta}")


if __name__ == "__main__":
    pass
