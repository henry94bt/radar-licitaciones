import json
import io
import os
import zipfile
import unicodedata
from datetime import date
import requests
import pandas as pd
from anthropic import Anthropic
from src.parseo import parsear_bytes
from src.pliegos import obtener_texto_pliego

# Mes a consultar, en formato AAAAMM. Se calcula solo (mes actual) para que
# la automatización diaria siempre pida el mes correcto. Si necesitas forzar
# un mes concreto para pruebas, pon aqui el valor fijo en vez de la linea de
# abajo (ej: ANIO_MES = "202606").
ANIO_MES = date.today().strftime("%Y%m")
URL = f"https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_{ANIO_MES}.zip"
MODELO = "claude-haiku-4-5-20251001"
SALIDA_JSON = "data/relevantes.json"
MAX_CANDIDATAS = 150  # tope de seguridad, no limitacion real (antes 40, era para la demo)

KEYWORDS = [
    "publicidad", "comunicacion", "campana", "marketing", "difusion",
    "promocion", "diseno", "branding", "marca", "redes sociales",
    "social media", "contenido", "web", "audiovisual", "video", "imagen",
    "grafic", "evento",
]
# Quitados respecto a la version anterior por traer demasiado ruido (obra
# publica, sanidad, servicios sociales, telecom disfrazados de "cultural" o
# "dinamizacion"): iluminacion, sonido, cultural, festival, feria, artistic,
# espectaculo, dinamizacion, patrocinio, streaming, prensa, medios,
# produccion. Si una candidata legitima se pierde por esto, es mas barato
# recuperarla a mano puntualmente que pagar el ruido de tenerlas todas.

# CPV cuyo prefijo, si aparece, mete la candidata igual aunque el titulo no
# tenga ninguna KEYWORD (a veces el organo clasifica mal el titulo).
CPV_RELEVANTES = [
    "7934", "79822500", "79823000", "92111", "72400000", "72413000", "79416",
]

# Si el titulo contiene cualquiera de estos, se descarta ANTES de llamar a la
# IA, aunque haya matcheado una keyword o CPV (ahorra la llamada y el ruido).
# Son objetos que el GEM descarta siempre: obra civil, suministro de equipos/
# material, mantenimiento tecnico, sanidad, servicios sociales, telecom.
EXCLUSIONES = [
    "obra de", "obras de", "edificacion", "vivienda", "asfaltado",
    "servidor", "servidores", "software especifico", "radiocomunicaciones",
    "telecomunicaciones", "mantenimiento electrico", "instalacion electrica",
    "reparacion de iluminacion", "resonancia", "diagnostico por imagen",
    "desratizacion", "desinsectacion", "legionella", "tarima", "tarimas",
    "suministro e instalacion", "suministro de", "catering", "limpieza",
    "transporte regular", "certificacion iso", "iso 9001", "fluido electrico",
]

cliente = Anthropic()

SYSTEM = (
    "Eres el analista de licitaciones de LA PEPA STUDIO, agencia de marketing y comunicacion "
    "de Telde, Gran Canaria. Te paso los datos de una licitacion publica (titulo, organo, "
    "importe, plazo, CPV, lugar de ejecucion). Aplica este criterio para decidir relevancia "
    "y semaforo:\n"
    "\n"
    "SERVICIOS CORE (si son >=80% del objeto -> encaja bien): diseno grafico, editorial, "
    "branding/identidad corporativa, gestion de redes sociales, desarrollo web, tiendas "
    "online, produccion audiovisual/shooting, estrategia de contenido/marketing, SEO.\n"
    "SERVICIOS SECUNDARIOS (encaja pero con cautela): Meta/Google Ads como servicio "
    "principal sin diseno; gestion de eventos EN GRAN CANARIA que impliquen subcontratar "
    "iluminacion/sonido.\n"
    "DESCARTAR SIEMPRE (no relevante, semaforo rojo): email marketing como servicio "
    "principal; ruedas de prensa, gabinete de prensa o relaciones con medios de "
    "comunicacion (no periodismo, no gestion informativa institucional) como objeto "
    "principal; eventos con presencia fisica FUERA de Gran Canaria (Tenerife, Lanzarote, "
    "Fuerteventura, La Palma, La Gomera, El Hierro o Peninsula), salvo que el servicio "
    "sea 100% digital/remoto (diseno, web, RRSS, contenido); tambien descarta obras, "
    "asfaltado, catering, limpieza, suministro de equipos/material, informatica/servidores "
    "y mantenimiento aunque mencionen un evento o feria.\n"
    "\n"
    "SEMAFORO (solo si relevante=true):\n"
    "- verde: >=80% servicios core, ubicacion Gran Canaria o 100% digital, sin senales de "
    "riesgo, importe razonable para dedicar recursos.\n"
    "- naranja: encaja pero hay un servicio secundario dominante, o eventos con "
    "subcontratas en Gran Canaria, o importe bajo (<20.000EUR, valorar si compensa el "
    "esfuerzo), o duda real sobre si el trabajo es presencial fuera de Gran Canaria.\n"
    "- rojo: no se cumple ninguno de los anteriores pero aun asi decides relevante=true "
    "por algun motivo puntual (raro; normalmente rojo va con relevante=false).\n"
    "\n"
    "En 'resumen' pon SIEMPRE dos frases en espanol, sea o no relevante: que se esta "
    "contratando (en cristiano) y, si no es relevante, por que no encaja. "
    "Ejemplo si no relevante: 'Suministro e instalacion de servidores para el "
    "ayuntamiento. No es un servicio de marketing ni comunicacion.'"
    "\n\n"
    "Responde SOLO con un JSON valido, sin markdown ni texto extra, con esta forma exacta: "
    '{"relevante": true, "semaforo": "verde", "motivos": ["..."], "resumen": "..."}. '
    "En 'motivos' pon SIEMPRE 1-3 frases cortas en espanol citando la regla concreta "
    "aplicada, tanto si es relevante como si no (ej: 'Evento en Tenerife, fuera de Gran "
    "Canaria' o 'Diseno y RRSS, encaje core'). Se breve: cada motivo debe caber en una "
    "linea, no expliques de mas. "
    "Si no es relevante, pon \"relevante\": false y \"semaforo\": \"rojo\"."
)

SEMAFORO_ICONO = {"verde": "🟢", "naranja": "🟠", "rojo": "🔴"}

SYSTEM_DETALLE = (
    "Eres el analista de licitaciones de LA PEPA STUDIO. Te paso el texto extraido "
    "del PCAP (pliego administrativo) y/o PPT (pliego tecnico) de una licitacion. "
    "Extrae SOLO lo que encuentres explicitamente en el texto; si un dato no aparece, "
    "pon null (no lo inventes).\n\n"
    "Responde SOLO con un JSON valido, sin markdown ni texto extra, con esta forma "
    "exacta:\n"
    '{"criterios_valoracion": "...", "solvencia": "...", "garantia": "...", '
    '"plazo_ejecucion": "...", "lotes": "..."}\n\n'
    "- criterios_valoracion: como se puntua (ej. '60% precio, 40% memoria tecnica').\n"
    "- solvencia: requisitos de solvencia tecnica/economica exigidos para presentarse.\n"
    "- garantia: importe o porcentaje de garantia provisional/definitiva, si se exige.\n"
    "- plazo_ejecucion: duracion del contrato una vez adjudicado.\n"
    "- lotes: si se divide en lotes, cuales y de que trata cada uno; si no hay lotes, "
    "pon 'Sin lotes'.\n"
    "Cada campo, 1-2 frases cortas en espanol. Si no hay texto suficiente para "
    "extraer nada de un campo, pon null en ese campo."
)


def evaluar_detalle(texto_pliego):
    resp = cliente.messages.create(
        model=MODELO, max_tokens=500, system=SYSTEM_DETALLE,
        messages=[{"role": "user", "content": texto_pliego}],
    )
    texto = resp.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)


def sin_tildes(s):
    s = s or ""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def limpio(v):
    """Convierte NaN de pandas (o cualquier float 'raro') a None; deja el
    resto tal cual. Evita que un hueco vacio del XML (ej. lugar sin
    especificar) llegue al JSON como NaN y rompa luego el HTML."""
    if isinstance(v, float) and v != v:  # el truco clasico: NaN != NaN
        return None
    return v


def es_candidata(row):
    t = sin_tildes(row.get("titulo", ""))
    if any(ex in t for ex in EXCLUSIONES):
        return False
    if any(k in t for k in KEYWORDS):
        return True
    cpv = str(row.get("cpv") or "")
    return any(cpv.startswith(pref) for pref in CPV_RELEVANTES)


def evaluar(row):
    datos = (
        f"Titulo: {row['titulo']}\n"
        f"Organo: {row['organo']}\n"
        f"Importe: {row['importe']}\n"
        f"Plazo: {row['plazo']}\n"
        f"Lugar de ejecucion: {limpio(row.get('lugar')) or '(no especificado)'}\n"
        f"CPV: {row['cpv']}"
    )
    resp = cliente.messages.create(
        model=MODELO, max_tokens=600, system=SYSTEM,
        messages=[{"role": "user", "content": datos}],
    )
    texto = resp.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON invalido para «{row['titulo'][:60]}...»")
        print(f"      Error: {e}")
        print(f"      Respuesta cruda: {texto[:500]}")
        raise


def main():
    print(f"Descargando el fichero del mes {ANIO_MES} (puede tardar un poco)...")
    resp = requests.get(URL, timeout=180, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    z = zipfile.ZipFile(io.BytesIO(resp.content))
    dfs = []
    for nombre in z.namelist():
        if nombre.lower().endswith(".atom"):
            dfs.append(parsear_bytes(z.read(nombre)))
    df = pd.concat(dfs, ignore_index=True)
    print(f"{len(df)} licitaciones en el mes.")

    # Filtro 1: Canarias
    df = df[df["nuts"].fillna("").str.startswith("ES70")]
    # Filtro 2: tematica (keyword de titulo O cpv relevante, vetado por exclusiones)
    df = df[df.apply(es_candidata, axis=1)]
    # Filtro 3: en plazo (fecha de cierre futura). Las fechas ISO se comparan como texto.
    hoy = date.today().isoformat()
    df = df[df["plazo"].fillna("") >= hoy]
    # Quitar duplicados (un expediente aparece varias veces al actualizarse)
    df = df.drop_duplicates(subset=["organo", "titulo"])
    print(f"{len(df)} candidatas de Canarias, abiertas y del sector.")

    if len(df) > MAX_CANDIDATAS:
        df = df.head(MAX_CANDIDATAS)
        print(f"(tope de seguridad: limito a {MAX_CANDIDATAS})")

    print("Pasandolas por la IA...")
    items = []
    for _, row in df.iterrows():
        try:
            v = evaluar(row)
        except Exception as e:
            print(f"(salto una por un error: {e})")
            continue
        titulo_corto = row["titulo"][:70]
        semaforo = v.get("semaforo") or ("verde" if v.get("relevante") else "rojo")

        detalle_pliego = None
        if semaforo in ("verde", "naranja"):
            texto_pliego = obtener_texto_pliego(row)
            if texto_pliego:
                try:
                    detalle_pliego = evaluar_detalle(texto_pliego)
                except Exception as e:
                    print(f"    (sin detalle de pliego, fallo al analizarlo: {e})")

        items.append({
            "titulo": limpio(row["titulo"]), "organo": limpio(row["organo"]),
            "importe": limpio(row["importe"]), "plazo": limpio(row["plazo"]),
            "lugar": limpio(row.get("lugar")), "enlace": limpio(row["enlace"]),
            "resumen": v.get("resumen", ""),
            "relevante": bool(v.get("relevante")),
            "semaforo": semaforo,
            "motivos": v.get("motivos", []),
            "detalle_pliego": detalle_pliego,
        })
        icono = "⛔" if not v.get("relevante") else SEMAFORO_ICONO.get(semaforo, "⚪")
        extra = " 📄" if detalle_pliego else ""
        print(f"  {icono} {titulo_corto}{extra}")

    # Orden: primero verdes, luego naranjas, luego rojas; dentro de cada grupo por plazo.
    orden_semaforo = {"verde": 0, "naranja": 1, "rojo": 2}
    items.sort(key=lambda it: (orden_semaforo.get(it.get("semaforo"), 1), it.get("plazo") or ""))

    recomendadas = sum(1 for it in items if it["relevante"])
    print(f"{len(items)} analizadas. {recomendadas} recomendadas, {len(items) - recomendadas} descartadas (guardadas igualmente con motivo).")
    os.makedirs("data", exist_ok=True)
    with open(SALIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Guardado en {SALIDA_JSON}. Ahora ejecuta:  python dashboard.py")


if __name__ == "__main__":
    main()