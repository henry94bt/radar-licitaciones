"""
Configuración del Radar. Es el único archivo que tocas para afinar QUÉ se
considera "relevante para La Pepa". Todo lo demás lee de aquí.
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. FUENTE DE DATOS
# ─────────────────────────────────────────────────────────────────────────────
# TODO(descarga): confirmar la URL exacta del fichero de licitaciones publicadas
# en el portal de datos abiertos. Punto de partida para localizarla:
#   https://contrataciondelsectorpublico.gob.es/wps/portal/DatosAbiertos
#   (conjunto: "Licitaciones publicadas en los perfiles del contratante",
#    excluyendo contratos menores). Suele ser un .zip mensual con ficheros .atom.
URL_FICHERO_LICITACIONES = "https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_202606.zip"

# Carpeta temporal de descarga
DIR_DESCARGA = "data"


# ─────────────────────────────────────────────────────────────────────────────
# 2. FILTRO POR ÁMBITO (Canarias)
# ─────────────────────────────────────────────────────────────────────────────
# Estrategia de filtrado geográfico (combinar varias da más recall):
#  - código de provincia / NUTS en el campo de lugar de ejecución (ES70 = Canarias)
#  - nombre del órgano de contratación contiene estas pistas
NUTS_CANARIAS = ["ES70", "ES701", "ES702"]  # Canarias / Las Palmas / S.C. Tenerife

PISTAS_ORGANO_CANARIAS = [
    "canarias", "gran canaria", "tenerife", "lanzarote", "fuerteventura",
    "la palma", "la gomera", "el hierro", "las palmas", "cabildo",
]


# ─────────────────────────────────────────────────────────────────────────────
# 3. FILTRO POR CPV  (lo que de verdad le sirve a una agencia)
# ─────────────────────────────────────────────────────────────────────────────
# Códigos CPV (Common Procurement Vocabulary). Filtramos por prefijo, así que
# "7934" captura toda la familia de publicidad y marketing.
# TODO(tú): revisa con lo que hace EXACTAMENTE La Pepa y añade/quita.
CPV_RELEVANTES = [
    "7934",      # Servicios de publicidad y de marketing
    "794xx",     # (ver abajo) eventos, ferias, relaciones públicas
    "79822500",  # Servicios de diseño gráfico
    "79823000",  # Servicios de diseño e impresión
    "92111",     # Producción de películas/vídeos de promoción
    "72400000",  # Servicios de internet
    "72413000",  # Servicios de diseño de sitios web (WWW)
    "79416",     # Relaciones públicas
    "98390000",  # Otros servicios (a veces cuelgan campañas aquí; revisar ruido)
]

# Keywords de respaldo: si el título contiene esto, entra aunque el CPV no cuadre.
# Útil porque a veces los órganos clasifican mal el CPV.
KEYWORDS_TITULO = [
    "publicidad", "campaña", "comunicación", "diseño", "branding", "marca",
    "redes sociales", "social media", "web", "página web", "sitio web",
    "audiovisual", "vídeo", "imagen corporativa", "marketing", "difusión",
    "promoción", "evento",
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. FILTRO POR ESTADO
# ─────────────────────────────────────────────────────────────────────────────
# Solo interesan las que aún se pueden presentar.
ESTADOS_VALIDOS = ["EN PLAZO", "PUB", "PUBLICADA"]  # confirmar el literal en CODICE


# ─────────────────────────────────────────────────────────────────────────────
# 5. RESUMEN LLM
# ─────────────────────────────────────────────────────────────────────────────
MODELO_LLM = "claude-haiku-4-5-20251001"  # rápido y barato para resúmenes cortos
MAX_LICITACIONES_A_RESUMIR = 15           # tope para la demo (controla coste/tiempo)


# ─────────────────────────────────────────────────────────────────────────────
# 6. SALIDA
# ─────────────────────────────────────────────────────────────────────────────
RUTA_DASHBOARD = "docs/index.html"
TITULO_DASHBOARD = "Radar de Licitaciones · Canarias · Comunicación & Marketing"

# Email
EMAIL_REMITENTE = "henry@lapepastudio.com"
EMAIL_DESTINO = ["hola@lapepastudio.com", "administracion@lapepastudio.com"]
EMAIL_ASUNTO = "📡 Licitaciones del día que os pueden interesar"

# SMTP de IONOS. Usuario/contraseña vienen de variables de entorno
# (SMTP_USER / SMTP_PASS), nunca hardcodeadas aquí.
SMTP_HOST = "smtp.ionos.es"
SMTP_PORT = 587
