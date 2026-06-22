# 📡 Radar de Licitaciones — demo para La Pepa Studio

Detecta de forma automática las licitaciones públicas que le interesan a una
agencia de marketing/comunicación en Canarias, las resume con un LLM y las
presenta en un **dashboard HTML** y un **email diario**.

> Demo de proceso, no producto. El objetivo es enseñar en concreto cómo se
> ahorran las horas de leer pliegos. Lo de "esto corre solo cada mañana" se
> cuenta y se deja montado, pero no necesita estar en producción para convencer.

---

## La idea en una frase

> En vez de leer decenas de licitaciones cada semana para encontrar las 3 que os
> sirven, un script las filtra, las resume y os las deja servidas cada mañana.

---

## Cómo funciona (pipeline)

```
1. DESCARGA   → fichero de licitaciones de la PLACSP (formato ATOM + CODICE)
2. PARSEO     → XML → DataFrame de pandas (título, órgano, importe, plazo, CPV, enlace)
3. FILTRO     → solo Canarias + CPV de comunicación/diseño/web + estado EN PLAZO
4. RESUMEN    → cada pliego seleccionado → 2 líneas con un LLM (API de Anthropic)
5. SALIDA     → dashboard HTML (GitHub Pages) + email diario
6. (opcional) → GitHub Actions lo ejecuta solo cada mañana
```

## Por qué una sola fuente (PLACSP) y no el BOC

Las licitaciones canarias modernas (post Ley 9/2017) — Gobierno de Canarias,
Cabildo de Gran Canaria, ayuntamientos — **alojan su Perfil del Contratante
dentro de la PLACSP**. Así que la PLACSP ya cubre lo estatal *y* lo canario en
formato de datos abiertos reutilizables. El BOC publica el anuncio legal, pero
obligaría a parsear PDFs para conseguir un dato que ya está estructurado en otro
sitio. → **BOC queda como ampliación futura, fuera del MVP.**

Reutilización permitida (incluido uso comercial) con atribución de la fuente —
cero riesgo legal, que es justo la ventaja de esta demo.

---

## Estructura del repo

```
radar-licitaciones/
├── README.md               ← este archivo (el plan)
├── requirements.txt        ← dependencias
├── config.py               ← CPV, keywords, ámbito, parámetros (TÚ ajustas esto)
├── main.py                 ← orquestador: ejecuta el pipeline de principio a fin
├── src/
│   ├── descarga.py         ← baja el fichero de la PLACSP
│   ├── parseo.py           ← XML ATOM/CODICE → DataFrame
│   ├── filtro.py           ← aplica CPV + Canarias + EN PLAZO
│   ├── resumen.py          ← resúmenes con la API de Anthropic
│   ├── dashboard.py        ← genera docs/index.html
│   └── email_diario.py     ← genera/envía el email
├── docs/                   ← salida del dashboard (GitHub Pages sirve desde aquí)
└── .github/workflows/
    └── radar.yml           ← ejecución diaria automática
```

---

## Plan de relleno (orden recomendado)

El esqueleto está montado. Vamos hueco por hueco en este orden — cada paso
produce algo verificable antes de pasar al siguiente:

- [ ] **1. `descarga.py`** — Confirmar la URL exacta del fichero de licitaciones
      en el portal de datos abiertos y bajarlo. *Entregable: el .zip/.atom en disco.*
- [ ] **2. `parseo.py`** — Abrir UNA licitación real y mapear los campos CODICE
      a columnas. *Entregable: un DataFrame con 5 columnas bien pobladas.*
      ⚠️ Los xpath del esqueleto son la estructura esperada — hay que
      confirmarlos contra una muestra real antes de fiarse.
- [ ] **3. `filtro.py`** — Ajustar CPV y keywords en `config.py` y filtrar.
      *Entregable: pasar de miles de filas a ~10 relevantes de Canarias.*
- [ ] **4. `resumen.py`** — Resumir esas ~10 con la API. *Entregable: columna
      `resumen` con 2 líneas por licitación.*
- [ ] **5. `dashboard.py`** — Volcar a HTML bonito. *Entregable: docs/index.html.*
- [ ] **6. `email_diario.py`** — Mismo contenido en formato email.
- [ ] **7. `radar.yml`** — Automatizar (el toque final de "corre solo").

---

## Cómo ejecutarlo (cuando esté relleno)

```bash
pip install -r requirements.txt
# La API key NUNCA va en el código. Variable de entorno:
#   PowerShell:  $env:ANTHROPIC_API_KEY="sk-..."
python main.py
```

El dashboard queda en `docs/index.html`. Para publicarlo: GitHub Pages → rama
`main`, carpeta `/docs`.

---

## ⚠️ Notas para tu entorno (Windows / OneDrive)

- Tienes los repos dentro de OneDrive. OneDrive sincronizando la carpeta `.git`
  puede corromper el repo o dar conflictos raros. Si puedes, **clona este fuera
  de OneDrive** (p. ej. `C:\dev\radar-licitaciones`).
- La `ANTHROPIC_API_KEY` va como variable de entorno en local y como **secret**
  en GitHub Actions. Nunca commiteada.
