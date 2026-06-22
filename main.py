"""
Orquestador del Radar de Licitaciones.
Ejecuta el pipeline de principio a fin:

    descarga → parseo → filtro → resumen → dashboard + email

Uso:
    python main.py
"""
from src import descarga, parseo, filtro, resumen, dashboard, email_diario


def main():
    print("1/6 · Descargando fichero de la PLACSP...")
    ruta_zip = descarga.descargar_fichero()
    ficheros_atom = descarga.descomprimir_si_hace_falta(ruta_zip)

    print("2/6 · Parseando XML...")
    import pandas as pd
    df = pd.concat([parseo.parsear_atom(str(f)) for f in ficheros_atom], ignore_index=True)
    print(f"      {len(df)} licitaciones en el fichero.")

    print("3/6 · Filtrando (Canarias + comunicación + en plazo)...")
    df = filtro.filtrar(df)
    print(f"      {len(df)} relevantes.")

    print("4/6 · Resumiendo con LLM...")
    df = resumen.resumir(df)

    print("5/6 · Generando dashboard...")
    dashboard.generar_dashboard(df)

    print("6/6 · Generando email...")
    email_diario.guardar_email(df)

    print("✅ Listo.")


if __name__ == "__main__":
    main()
