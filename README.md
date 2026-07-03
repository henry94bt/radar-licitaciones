# 📡 Radar de Licitaciones — La Pepa Studio

Detecta automáticamente las licitaciones públicas de Canarias que le interesan
a una agencia de marketing/comunicación, las evalúa contra el perfil real de
**La Pepa Studio** (servicios core, ubicación, riesgos de descarte) y las deja
priorizadas en un dashboard, cada vez que lo ejecutas.

> Para el contexto completo de cómo ha evolucionado esta herramienta —de demo
> a algo que ya usa criterio de negocio real— ver [`HISTORIAL.md`](HISTORIAL.md).

---

## La idea en una frase

En vez de leer decenas de licitaciones cada semana para encontrar las 2-3 que
sirven de verdad, el radar las descarga, las filtra, las evalúa con un
**semáforo de viabilidad** (🟢🟠🔴) y las deja priorizadas — con el motivo de
cada decisión a la vista, no solo el resultado.

---

## Cómo funciona (pipeline real)

```
1. DESCARGA    → fichero mensual de licitaciones de la PLACSP (ATOM + CODICE)
2. PARSEO      → XML → filas con título, órgano, importe, plazo, CPV, lugar,
                 enlace al pliego, y (desde esta versión) enlaces al PCAP/PPT
3. FILTRO      → Canarias (NUTS ES70) + palabras clave del sector + en plazo
4. EVALUACIÓN  → cada candidata pasa por Claude, que aplica el perfil de
                 La Pepa Studio (servicios core/secundarios/descartados,
                 ubicación, riesgos) y devuelve semáforo + motivos + resumen
5. DASHBOARD   → docs/index.html — filtrable por semáforo, isla y texto libre
```

Los archivos que de verdad se ejecutan son los de la **raíz del repo**:

```powershell
python actualizar.py     # descarga, filtra, evalúa → data/relevantes.json
python dashboard.py      # data/relevantes.json → docs/index.html
```

`ANTHROPIC_API_KEY` tiene que estar en el entorno antes de ejecutar
`actualizar.py` (nunca en el código):
```powershell
$env:ANTHROPIC_API_KEY = "sk-..."
```

---

## El semáforo de viabilidad

Cada licitación evaluada recibe uno de estos tres colores, según las reglas
del **perfil de La Pepa Studio** (servicios core: diseño, branding, RRSS, web,
audiovisual, SEO; descartes automáticos: email marketing, gestión de prensa,
eventos fuera de Gran Canaria salvo que sean 100% digitales):

| Semáforo | Significado |
|---|---|
| 🟢 Prioridad | Encaje claro, sin riesgos detectados |
| 🟠 Valorar | Encaja pero con matices (servicio secundario, importe bajo, subcontratas) |
| 🔴 Descartar | No cumple los criterios del perfil — **se guarda igualmente**, con el motivo |

Las descartadas **no se tiran** — se guardan con su motivo para que el equipo
pueda revisarlas (filtro "Todas, incl. descartadas" en el dashboard). Por
defecto la vista solo muestra 🟢🟠, para no enterrar las oportunidades reales
entre el ruido.

Este semáforo aplica una versión reducida de las reglas del **GEM — Gestor de
Licitaciones** (el documento de instrucciones interno con el perfil completo
de la empresa: solvencia, márgenes, checklist documental). El GEM es un
documento aparte y **nunca debe subirse a este repo** — contiene datos
internos de la empresa (CIF, facturación, márgenes). El radar solo usa una
versión resumida de sus reglas de encaje, sin esos datos sensibles.

---

## Estructura del repo

```
radar-licitaciones/
├── README.md            ← este archivo
├── HISTORIAL.md          ← de dónde viene esto y qué ha cambiado en cada fase
├── requirements.txt
├── actualizar.py         ← ★ pipeline real: descarga + filtro + evaluación IA
├── dashboard.py           ← ★ pipeline real: genera docs/index.html
├── config.py               ← CPV, keywords, ámbito (usado por src/filtro.py)
├── data/
│   └── relevantes.json     ← salida de actualizar.py (todas las evaluadas)
├── docs/
│   └── index.html          ← salida de dashboard.py (esto sirve GitHub Pages)
└── src/
    ├── parseo.py          ← ★ usado: XML → filas (incluye enlaces PCAP/PPT)
    ├── descarga.py        ⚠ esqueleto sin usar (ver nota abajo)
    ├── filtro.py           ⚠ esqueleto sin usar
    ├── resumen.py          ⚠ esqueleto sin usar
    ├── dashboard.py         ⚠ esqueleto sin usar
    └── email_diario.py     ⚠ pendiente de implementar
```

> ⚠️ **Nota sobre `src/`:** este proyecto arrancó como un esqueleto modular
> (`main.py` orquestando `src/descarga.py → parseo.py → filtro.py → resumen.py
> → dashboard.py`, ver Fase 0 en `HISTORIAL.md`). En la práctica, el pipeline
> que se terminó de construir y usa datos reales vive en los dos archivos de
> la raíz (`actualizar.py`, `dashboard.py`), que son autocontenidos y más
> simples de mantener. El único archivo de `src/` que sigue en uso es
> `parseo.py`, importado directamente por `actualizar.py`. El resto de
> `src/*.py` y `main.py` han quedado obsoletos — se pueden borrar cuando se
> confirme que nada los referencia, o reaprovechar si en algún momento
> interesa volver a una arquitectura modular.

---

## Próximos pasos

- [ ] **Afinar `KEYWORDS`** en `actualizar.py` — entran muchas candidatas de
      obra pública/suministros que el semáforo descarta correctamente, pero
      que ni deberían llegar a consumir una llamada a la IA.
- [ ] **Nivel 2 — leer el pliego de verdad**: `src/parseo.py` ya captura los
      enlaces al PCAP y al PPT (URL externa o base64 embebido). Falta
      descargar/decodificar, extraer texto, y una segunda pasada de Claude
      que saque criterios de adjudicación reales (% precio vs. técnica),
      requisitos de solvencia/ISO/seguro RC, y arme el informe de viabilidad
      completo del GEM.
- [ ] **Email diario** (`src/email_diario.py`) — pendiente de implementar.
- [ ] **Automatización** (GitHub Actions o Programador de tareas de Windows)
      — pendiente, ligado a la decisión de hosting privado (ver abajo).
- [ ] **Hosting privado** — aparcado por ahora. El contenido actual (datos
      públicos de PLACSP) puede seguir en GitHub Pages público sin problema.
      El día que el dashboard muestre márgenes/estrategia de precio del GEM,
      hay que moverlo a algo cerrado — la opción evaluada es Cloudflare Pages
      + Cloudflare Access (gratis hasta 50 usuarios, login por email).
- [ ] **Borrador de memoria técnica** — objetivo final del proyecto: que el
      radar no solo detecte y priorice, sino que genere un primer borrador de
      la propuesta técnica siguiendo la estructura del GEM. Depende de tener
      el Nivel 2 funcionando primero.

---

## Fuente de datos

PLACSP (Plataforma de Contratación del Sector Público) — datos abiertos, uso
comercial permitido con atribución de la fuente. Las licitaciones canarias
modernas (Gobierno de Canarias, cabildos, ayuntamientos) publican su Perfil
del Contratante dentro de la PLACSP, así que una sola fuente cubre lo estatal
y lo canario sin tener que parsear el BOC en PDF.

---

## ⚠️ Notas de entorno (Windows)

- Repo fuera de OneDrive (`C:\dev\radar-licitaciones`) — sincronizar `.git`
  con OneDrive puede corromper el repo.
- Si `python` resuelve al stub de Microsoft Store (`WindowsApps\python.exe`),
  usa la ruta completa o desactiva los alias de ejecución de Python en
  *Configuración > Aplicaciones > Alias de ejecución de aplicaciones*.
- `ANTHROPIC_API_KEY` como variable de entorno en local; como **secret** el
  día que se automatice con GitHub Actions. Nunca commiteada.