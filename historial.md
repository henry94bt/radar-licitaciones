# Historial del Radar de Licitaciones

De dónde viene esta herramienta y qué ha cambiado en cada fase. Pensado para
que cualquiera del equipo (o tú, dentro de unos meses) entienda el porqué de
las decisiones sin tener que releer el código.

---

## Fase 0 — La demo (antes de entrar en La Pepa Studio)

Se construyó como pieza central de la presentación para el puesto en La Pepa
Studio: demostrar en concreto cómo la automatización ahorra horas de leer
pliegos. Se montó un esqueleto modular (`main.py` orquestando
`src/descarga.py → parseo.py → filtro.py → resumen.py → dashboard.py`) que:

- Descargaba el feed mensual de licitaciones de la PLACSP (formato ATOM/CODICE).
- Filtraba por Canarias (NUTS ES70) y por CPV/keywords de comunicación.
- Resumía cada licitación seleccionada con Claude Haiku en dos líneas.
- Publicaba un dashboard estático en GitHub Pages.

Objetivo cumplido: sirvió como pieza de portfolio y ayudó a conseguir el
puesto. Pero era una demo — el criterio de "relevante o no" era genérico
("¿podría una agencia de comunicación hacer esto?"), sin las reglas
específicas de negocio de La Pepa Studio, sin cálculo de viabilidad económica,
sin distinguir servicios core de descartes automáticos.

## Fase 1 — El salto de "demo" a "herramienta de verdad"

Ya dentro de La Pepa Studio, con el **GEM (Gestor de Licitaciones)** ya
redactado — el documento con el perfil completo de la empresa: servicios
core/secundarios/excluidos, semáforo de elegibilidad, estrategia de precio,
checklist de documentación — el objetivo cambió: que el radar no solo
detectara licitaciones, sino que aplicara el mismo criterio de negocio que ya
usa el equipo a mano.

Se revisó el pipeline real en uso (que resultó ser distinto del esqueleto
original de `src/` — ver nota en el `README.md`) y se hizo el primer cambio
de fondo:

- El prompt de evaluación de Claude pasó de "¿podría una agencia de
  comunicación hacer esto?" a aplicar explícitamente las reglas del GEM:
  servicios core (diseño, branding, RRSS, web, audiovisual, SEO), descartes
  automáticos (email marketing, gestión de prensa, eventos fuera de Gran
  Canaria salvo 100% digitales), y devolver un **semáforo** (🟢🟠🔴) con los
  motivos concretos, no solo un sí/no.
- El dashboard ganó un filtro por semáforo y un badge visual por tarjeta.
- Se investigó la estructura del XML de PLACSP y se confirmó que trae enlaces
  directos al PCAP y al PPT (`cac:LegalDocumentReference` /
  `cac:TechnicalDocumentReference`) — la base necesaria para el "Nivel 2"
  (leer el pliego de verdad, no solo el título). **Importante: solo se
  capturó DÓNDE están esos documentos** (la URL o el base64 embebido, guardado
  en `src/parseo.py`) — **no se ha descargado, decodificado ni leído ningún
  PCAP/PPT todavía.** El semáforo actual clasifica exclusivamente con los
  metadatos que ya trae el XML (título, órgano, importe, plazo, lugar, CPV);
  no sabe nada de lo que hay dentro del pliego (criterios de adjudicación,
  ISO, solvencia, lotes). El Nivel 2 real —descargar, extraer texto y hacer
  una segunda lectura con Claude— sigue sin empezar.

**Un hallazgo real en esta fase:** una licitación de PROEXCA con ejecución en
Península estaba entrando al dashboard como si nada, porque el filtro de
ubicación original solo miraba si el *nombre del órgano* sonaba canario, no
dónde se ejecutaba el servicio. El semáforo nuevo la habría marcado en rojo.

## Fase 2 — Depurar con datos reales (bugs y sobre-ajuste)

Al probarlo con un mes real de datos (58 candidatas), salieron dos problemas:

1. **Bug técnico:** el `max_tokens` de la llamada a Claude se quedó corto
   (300) para el JSON más largo que ahora se pedía (semáforo + motivos +
   resumen), y algunas respuestas se cortaban a mitad de frase, rompiendo el
   parseo. Se subió a 600 y se le pidió al modelo ser más conciso.
2. **Falso positivo de "está roto":** con las reglas nuevas, 39 de 40
   candidatas salieron descartadas. Al revisar el detalle (que antes no se
   veía — se añadió logging por consola de cada decisión), se confirmó que el
   semáforo estaba acertando: la mayoría eran obra pública, suministros de
   servidores, servicios sanitarios o sociales que habían colado por
   `KEYWORDS` demasiado genéricas (`"cultural"`, `"festival"`, `"sonido"`,
   `"prensa"`...). El problema real no era el semáforo, era el filtro de
   entrada (Fase 3 del pipeline) — queda anotado como pendiente de afinar.

## Fase 3 — No perder las descartadas

Antes, una licitación descartada simplemente desaparecía — ni se guardaba ni
se veía el motivo. El equipo ya tenía el hábito, con el GEM en papel, de
revisar por qué algo no encajaba. Se cambió para que **todas** las evaluadas
se guarden (con semáforo y motivo), y el dashboard por defecto solo muestra
oportunidades (🟢🟠) pero permite ver "Todas, incl. descartadas" cuando
interesa auditar el criterio. De paso se quitó el límite artificial de 40
candidatas (era un tope pensado para no alargar la demo original, ya sin
sentido con el volumen real).

## Fase 4 — Cómo se comparte hoy

Se evaluaron varias formas de que el equipo (Samira, Laura) vea el dashboard
a diario: carpeta compartida de Google Drive (descartado — Drive no
renderiza HTML con JS, lo muestra como código fuente), Google Sites
(descartado — sanea y elimina los `<script>`, se pierde toda la
interactividad), y finalmente **GitHub Pages**, que ya estaba montado y sí
ejecuta el HTML/JS tal cual. Dado que el contenido actual es información
pública de PLACSP (sin datos internos de la empresa), no hay problema en que
siga siendo público por ahora.

**Pendiente, aparcado a propósito:** el día que el dashboard incorpore datos
del GEM (márgenes calculados, estrategia de precio, informes de viabilidad
completos), hay que moverlo a algo con control de acceso — la opción evaluada
es Cloudflare Pages + Cloudflare Access.

---

## Qué falta para el objetivo final

El objetivo original, más allá de detectar licitaciones, es que el radar
agilice **todo** el proceso hasta tener una memoria técnica lista. Ahora mismo
cubre el filtrado y la priorización con metadatos (título, importe, plazo,
CPV, ubicación) — es decir, la parte de "encontrar y descartar lo obvio". La
parte que da más valor de negocio (leer el pliego real, calcular márgenes de
verdad, generar la memoria) no ha empezado más allá de saber dónde están los
documentos. En términos del propio GEM: cubrimos la Fase 2 de su protocolo
(Análisis de Encaje) con datos limitados; las Fases 3-6 (requisitos,
criterios de adjudicación, viabilidad económica real, informe completo)
siguen sin implementarse. Quedan, en orden:

1. **Afinar las keywords de entrada** — reducir el ruido antes de gastar
   llamadas a la IA en candidatas obviamente irrelevantes.
2. **Nivel 2 — lectura real del pliego** (PCAP + PPT): descargar/decodificar
   los documentos, extraer texto, y una segunda pasada de Claude que saque
   criterios de adjudicación, requisitos de solvencia/ISO/seguro RC, y genere
   el informe de viabilidad completo tal como lo define el GEM.
3. **Checklist de documentación** automático según lo que pida cada pliego.
4. **Borrador de memoria técnica** — generar un primer borrador siguiendo la
   estructura que ya define el GEM (análisis, proceso creativo, equipo,
   portfolio), a partir de lo extraído en el Nivel 2.

En paralelo, hay una lista de mejoras propuestas para el propio **documento
del GEM** (no el código) — matices sobre prensa vs. publicidad, umbral de
importe mínimo basado en datos reales, tratamiento de lotes, circuito de
aprendizaje de licitaciones ganadas/perdidas, umbral claro para UTE — pendientes
de comentar con dirección antes de tocar el documento.