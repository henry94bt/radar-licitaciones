# Contexto del proyecto — Radar de Licitaciones

> Este documento resume todo el histórico e ideas de este proyecto para que cualquier sesión de Claude Code arranque con contexto completo, sin tener que re-explicar nada. Colócalo en la raíz de `C:\dev\radar-licitaciones`.

## Qué es

Herramienta de radar de licitaciones públicas para **La Pepa Studio** (agencia de marketing/comunicación en Telde, Gran Canaria). Nació como proyecto de portfolio para impresionar a Samira (co-fundadora) en la entrevista, y acabó convirtiéndose en herramienta real de la agencia.

Repo: `github.com/henry94bt/radar-licitaciones`
Demo pública: `henry94bt.github.io/radar-licitaciones`
Ruta local: `C:\dev\radar-licitaciones` (fuera de OneDrive a propósito, para evitar corrupción de git por sincronización)

## Objetivo de negocio

Samira mencionó como pain point que la agencia pierde mucho tiempo leyendo licitaciones públicas manualmente para encontrar las relevantes (contratos de comunicación/marketing en Canarias). El radar automatiza esa lectura y clasificación.

## Pipeline técnico

1. **`actualizar.py`** (o similar según fase): descarga el ZIP mensual de la Plataforma de Contratación del Sector Público (PLACSP):
   - URL patrón: `https://contrataciondelsectorpublico.gob.es/sindicacion/sindicacion_643/licitacionesPerfilesContratanteCompleto3_AAAAMM.zip`
   - Formato ATOM/XML con namespaces CODICE.
   - Es open data: reutilización permitida, incluso uso comercial, con atribución.
   - Los organismos canarios publican su perfil de contratante directamente en PLACSP → no hace falta scrapear el BOC.

2. **Parseo XML** (`src/parseo.py`): extrae campos desde rutas confirmadas en un feed real:
   - Título: `entry/ContractFolderStatus/ProcurementProject/Name`
   - Órgano: `entry/ContractFolderStatus/LocatedContractingParty/Party/PartyName/Name`
   - Presupuesto: `entry/ContractFolderStatus/ProcurementProject/BudgetAmount/TotalAmount`
   - Plazo: `entry/ContractFolderStatus/TenderingProcess/TenderSubmissionDeadlinePeriod/EndDate`
   - Código NUTS (ubicación): `entry/ContractFolderStatus/ProcurementProject/RealizedLocation/CountrySubentityCode` (Canarias = ES70)
   - Enlace: `entry/link@href`
   - Ampliado para capturar también enlaces a documentos **PCAP y PPT** (pliegos), pensado para una Fase 2.

3. **Filtrado** (`src/filtro.py`): por Canarias (NUTS ES70) + palabras clave de comunicación/marketing + exclusiones + plazo vigente. Capas de keywords/exclusiones afinadas varias veces para reducir falsos positivos. Cap de candidatos subido a 150.

4. **Clasificación/resumen con LLM** (`src/resumen.py` o similar): pasa los candidatos filtrados por **Claude Haiku vía API de Anthropic** para clasificar con semáforo:
   - 🟢 verde: muy relevante
   - 🟠 naranja: dudoso/revisar
   - 🔴 rojo: descartado (se guarda igual, con motivo)

5. **Salida**: se guarda en `data/relevantes.json`.

6. **Dashboard** (`dashboard.py`): genera `docs/index.html` — panel interactivo con:
   - Buscador
   - Filtro por isla (autopoblado desde los datos)
   - Ordenar por plazo o presupuesto
   - Tarjetas con color según urgencia (coral = urgente, ámbar = medio, verde = cómodo, gris = cerrado)

7. **Email diario** (`src/email_diario.py`): módulo para mandar resumen por correo. Envío real vía **API de Resend** (no SMTP: IONOS bloquea logins desde las IPs de los runners de GitHub Actions, confirmado probando el mismo login desde un PC normal vs desde Actions). Pendiente: verificar el dominio `lapepastudio.com` en Resend y crear el secret `RESEND_API_KEY` (bloqueado por 2FA que gestiona el superior de Henry).

8. **Fase 2 — detalle de pliegos** (`src/pliegos.py`): para candidatas verde/naranja, descarga el PCAP/PPT (URL o base64) y extrae su texto con `pypdf`. Ese texto se pasa por una segunda llamada a Claude (`evaluar_detalle` en `actualizar.py`) que saca criterios de valoración, solvencia, garantía, plazo de ejecución y lotes — se muestra en un desplegable "Detalle del pliego" en cada tarjeta del dashboard. Probado con un pliego real: el límite inicial de 8.000 caracteres por documento solo llegaba al índice, subido a 30.000 para llegar al contenido real.

9. **Ámbito nacional (remoto)**: además de Canarias, el radar ahora también mira licitaciones del resto de España que sean 100% ejecutables en remoto (diseño, web, branding, RRSS) — filtro más estricto (`KEYWORDS_REMOTO_NACIONAL`, sin comodín de CPV) para no disparar el volumen/coste. Se guarda en `data/relevantes_nacional.json` y se publica en `docs/nacional.html`, con navegación cruzada con `docs/index.html`. El email diario incluye ambos ámbitos en secciones separadas.

## Bug ya resuelto (por si reaparece)

`dashboard.py` petaba con `AttributeError: 'float' object has no attribute 'replace'` en `html.escape()`. Causa: licitaciones reales sin campo "lugar" llegan como `NaN` (float especial de pandas), no como texto vacío — algo que no salía en los datos de prueba porque siempre tenían ese campo relleno. Solución: función `limpio()` que convierte cualquier `NaN`/float raro a `None` antes de guardar en el JSON, aplicada tanto en la generación del dato como en el consumo (dashboard), para blindar por los dos lados.

## GitHub Actions (automatización diaria)

`.github/workflows/radar.yml`:
- Cron diario (`0 6 * * *`, ajustable) + `workflow_dispatch` para lanzarlo a mano.
- **Importante**: se detectó que el workflow llamaba al orquestador obsoleto `main.py` en vez del pipeline real (`actualizar.py` + `dashboard.py`) — ya corregido.
- El mes se calculaba con un hardcode `"202606"` — corregido a cálculo dinámico del mes actual.
- Usa `actions/checkout@v4` y `actions/setup-python@v5` (da un warning cosmético de Node.js deprecado, forzado a Node 24 en vez de 20 — no bloqueante, ignorar).
- La `ANTHROPIC_API_KEY` de este proyecto se gestiona como **GitHub Secret**, separada de cualquier key personal.
- El commit final usa `git pull --rebase --autostash` antes del push para evitar el conflicto ya conocido de otro proyecto (Gas Tracker).

## Seguridad / privacidad

- El **GEM** (documento interno de perfil de negocio de La Pepa, con márgenes y estrategia de precios) se mantiene **fuera del repo público**, siempre.
- El dashboard está en GitHub Pages público de momento porque solo contiene datos abiertos de la PLACSP, sin nada sensible de la agencia. Se decidió aplazar el trabajo de control de acceso/privacidad hasta que se incorporen datos internos del GEM (márgenes, estrategia de precios).
- Se intentó compartir el dashboard por Google Drive (descartado: Drive muestra el HTML como código fuente en vez de renderizarlo) y Google Sites (descartado: elimina el JavaScript y se pierde la interactividad). Por ahora, GitHub Pages sigue siendo el método de compartición con Samira y Laura.

## Próximos pasos pendientes

- Añadir email diario automatizado (parcialmente hecho, revisar estado real).
- Terminar de afinar la automatización vía GitHub Actions.
- Pequeños arreglos de UI.
- Fase 2: aprovechar los enlaces a documentos PCAP/PPT ya capturados para extraer más detalle de los pliegos.
- Roadmap del proyecto ya volcado como tareas en Bitrix24 (importado vía CSV, delimitado por `;`; los campos Estado y Prioridad quedaron sin mapear por incompatibilidad de tipos de campo en Bitrix — pendiente revisar si se quiere corregir el import).
- Mejoras propuestas para discutir con el responsable sobre el propio documento GEM (para pulir después, no técnico pero relevante para cómo debe evolucionar el radar):
  - Aclarar la distinción entre compra de medios (servicio core) y gestión de prensa/periodismo (descarte automático).
  - Sustituir el umbral cualitativo de mínimo 20.000€ por un suelo calculado según tarifa/hora.
  - Añadir lógica de evaluación a nivel de lote.
  - Definir un bucle estructurado de aprendizaje de licitaciones ganadas/perdidas.
  - Fijar umbrales explícitos para plantear UTEs (uniones temporales de empresas).

## Entorno técnico de Henry (para que Claude Code no la líe)

- Windows, PowerShell, VS Code con terminal integrado de PowerShell.
- Python en `C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\` — el Scripts folder NO está en el PATH, así que pip siempre se llama como `python -m pip`, nunca `pip` a secas.
- Repos siempre en `C:\dev\...`, nunca dentro de OneDrive.
- Prefiere español informal, comandos copy-paste con valores reales (nunca placeholders), un paso a la vez, sin encadenar tareas.
- Ojo con el vocabulario: "correr" un script es un anglicismo — el término correcto es "ejecutar".
- La API key de Anthropic de este proyecto vive en su propio `.env` dentro del repo (confirmado), completamente separada de cualquier variable de entorno global del sistema o de la suscripción personal de Claude Pro.
