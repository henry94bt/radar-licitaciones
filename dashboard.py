import json
import html
import os
from datetime import date

ENTRADA = "data/relevantes.json"
SALIDA = "docs/index.html"
ENTRADA_NACIONAL = "data/relevantes_nacional.json"
SALIDA_NACIONAL = "docs/nacional.html"

MESES = ["", "ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def formatear_importe(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "—"
    entero = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{entero} €"


def formatear_fecha(plazo):
    try:
        d = date.fromisoformat(str(plazo)[:10])
    except (TypeError, ValueError):
        return "—"
    return f"{d.day} {MESES[d.month]} {d.year}"


def dias_restantes(plazo):
    try:
        d = date.fromisoformat(str(plazo)[:10])
    except (TypeError, ValueError):
        return None
    return (d - date.today()).days


def urgencia(dias):
    if dias is None:
        return "sin", "Sin plazo"
    if dias < 0:
        return "cerrado", "Cerrado"
    if dias == 0:
        return "urgente", "Hoy"
    if dias <= 5:
        return "urgente", f"{dias} días"
    if dias <= 15:
        return "media", f"{dias} días"
    return "holgado", f"{dias} días"


SEMAFORO_ETIQUETA = {"verde": "🟢 Prioridad", "naranja": "🟠 Valorar", "rojo": "🔴 Descartar"}

CAMPOS_DETALLE = [
    ("criterios_valoracion", "Criterios de valoración"),
    ("solvencia", "Solvencia exigida"),
    ("garantia", "Garantía"),
    ("plazo_ejecucion", "Plazo de ejecución"),
    ("lotes", "Lotes"),
]


def bloque_detalle_pliego(detalle):
    """Devuelve el HTML del desplegable con el detalle del pliego (Fase 2),
    o cadena vacía si no hay nada que mostrar."""
    if not isinstance(detalle, dict):
        return ""
    filas = []
    for clave, etiqueta in CAMPOS_DETALLE:
        valor = detalle.get(clave)
        if valor and isinstance(valor, str):
            filas.append(f"<dt>{html.escape(etiqueta)}</dt><dd>{html.escape(valor)}</dd>")
    if not filas:
        return ""
    return f"""
          <details class="op__pliego">
            <summary>Detalle del pliego</summary>
            <dl>{"".join(filas)}</dl>
          </details>"""


def tarjeta_html(item):
    dias = dias_restantes(item.get("plazo"))
    clase, etiqueta = urgencia(dias)
    isla = item.get("lugar") or ""
    if not isinstance(isla, str):
        isla = ""  # por si llega None/NaN/lo que sea en vez de texto
    titulo = item.get("titulo") or ""
    organo = item.get("organo") or ""
    resumen = item.get("resumen") or ""
    if not isinstance(titulo, str):
        titulo = ""
    if not isinstance(organo, str):
        organo = ""
    if not isinstance(resumen, str):
        resumen = ""
    try:
        imp = float(item.get("importe"))
    except (TypeError, ValueError):
        imp = 0
    semaforo = item.get("semaforo") or "naranja"
    sem_etiqueta = SEMAFORO_ETIQUETA.get(semaforo, SEMAFORO_ETIQUETA["naranja"])
    motivos = item.get("motivos") or []
    sem_tooltip = " · ".join(motivos)
    detalle_html = bloque_detalle_pliego(item.get("detalle_pliego"))
    return f"""
      <article class="op" data-isla="{html.escape(isla)}" data-dias="{dias if dias is not None else 99999}" data-importe="{imp}" data-semaforo="{html.escape(semaforo)}" data-relevante="{str(bool(item.get('relevante', True))).lower()}" data-texto="{html.escape((titulo + ' ' + organo + ' ' + resumen).lower())}">
        <div class="op__clock op__clock--{clase}">
          <span class="op__days">{html.escape(etiqueta)}</span>
          <span class="op__deadline">{html.escape(formatear_fecha(item.get("plazo")))}</span>
        </div>
        <div class="op__body">
          <div class="op__semaforo op__semaforo--{html.escape(semaforo)}" title="{html.escape(sem_tooltip)}">{html.escape(sem_etiqueta)}</div>
          <h2 class="op__title">{html.escape(titulo)}</h2>
          <p class="op__org">{html.escape(organo)}{(" · " + html.escape(isla)) if isla else ""}</p>
          <p class="op__summary">{html.escape(resumen)}</p>
          {f'<p class="op__motivos">{html.escape(sem_tooltip)}</p>' if sem_tooltip else ""}
          {detalle_html}
          <div class="op__meta">
            <span class="op__amount">{html.escape(formatear_importe(item.get("importe")))}</span>
            <a class="op__link" href="{html.escape(item.get("enlace") or "#")}" target="_blank" rel="noopener">Ver pliego →</a>
          </div>
        </div>
      </article>"""


CABECERA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>@@TITULO_PAGINA@@</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#eef1f2;--card:#fff;--ink:#0b2a3a;--ink-soft:#54676f;
    --teal:#00857a;--coral:#e0563b;--amber:#d68a1e;--green:#2e8b6e;--line:#dde3e5;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);
    font-family:"Inter",system-ui,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:880px;margin:0 auto;padding:48px 24px 80px;}
  header{border-bottom:2px solid var(--ink);padding-bottom:24px;}
  .nav{margin:0 0 14px;}
  .nav a{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;
    color:var(--teal);text-decoration:none;letter-spacing:.02em;}
  .nav a:hover,.nav a:focus-visible{text-decoration:underline;}
  .eyebrow{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;
    letter-spacing:.22em;text-transform:uppercase;color:var(--teal);margin:0 0 12px;}
  h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;
    font-size:clamp(34px,6vw,56px);line-height:1.02;letter-spacing:-.02em;margin:0;}
  .sub{margin:14px 0 0;color:var(--ink-soft);font-size:16px;max-width:48ch;}
  .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:24px 0 8px;}
  .controls input,.controls select{
    font-family:"Inter",sans-serif;font-size:14px;color:var(--ink);
    background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 12px;}
  .controls input{flex:1;min-width:180px;}
  .controls input:focus,.controls select:focus{outline:2px solid var(--teal);outline-offset:1px;}
  .count{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--ink-soft);margin:14px 0 28px;}
  .count strong{color:var(--ink);}
  .ops{display:flex;flex-direction:column;gap:16px;}
  .op{display:grid;grid-template-columns:128px 1fr;background:var(--card);
    border:1px solid var(--line);border-radius:14px;overflow:hidden;}
  .op__clock{display:flex;flex-direction:column;justify-content:center;gap:6px;
    padding:22px 18px;color:#fff;text-align:center;}
  .op__clock--urgente{background:var(--coral);}
  .op__clock--media{background:var(--amber);}
  .op__clock--holgado{background:var(--green);}
  .op__clock--cerrado{background:#9aa7ac;}
  .op__clock--sin{background:var(--ink-soft);}
  .op__days{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:22px;line-height:1;}
  .op__deadline{font-size:11px;opacity:.9;}
  .op__body{padding:20px 22px;}
  .op__semaforo{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:11px;
    font-weight:600;letter-spacing:.04em;padding:3px 9px;border-radius:20px;margin:0 0 10px;
    cursor:default;}
  .op__semaforo--verde{background:#e3f3ec;color:#1f6b50;}
  .op__semaforo--naranja{background:#fbeed9;color:#95611a;}
  .op__semaforo--rojo{background:#fbe2dc;color:#a6402a;}
  .op__motivos{font-size:12.5px;color:var(--ink-soft);margin:-8px 0 14px;font-style:italic;}
  .op__pliego{margin:0 0 16px;font-size:13px;}
  .op__pliego summary{cursor:pointer;font-weight:600;color:var(--teal);}
  .op__pliego dl{margin:10px 0 0;}
  .op__pliego dt{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:600;
    color:var(--ink-soft);text-transform:uppercase;letter-spacing:.03em;margin:10px 0 2px;}
  .op__pliego dd{margin:0 0 0 0;color:#28424d;}
  .op[data-relevante="false"]{opacity:.6;}
  .op[data-relevante="false"] .op__title{font-size:17px;}
  .op__title{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;
    font-size:19px;line-height:1.22;margin:0 0 6px;letter-spacing:-.01em;}
  .op__org{font-size:13px;color:var(--ink-soft);margin:0 0 12px;}
  .op__summary{font-size:14.5px;margin:0 0 16px;color:#28424d;}
  .op__meta{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;}
  .op__amount{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:15px;}
  .op__link{font-weight:600;font-size:14px;color:var(--teal);text-decoration:none;
    border-bottom:2px solid transparent;transition:border-color .15s;}
  .op__link:hover,.op__link:focus-visible{border-color:var(--teal);outline:none;}
  .empty{background:var(--card);border:1px dashed var(--line);border-radius:14px;
    padding:40px;text-align:center;color:var(--ink-soft);}
  footer{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);
    font-size:12px;color:var(--ink-soft);font-family:"IBM Plex Mono",monospace;}
  @media (max-width:560px){
    .op{grid-template-columns:1fr;}
    .op__clock{flex-direction:row;justify-content:flex-start;gap:10px;align-items:baseline;padding:14px 22px;}
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="nav">@@NAV@@</p>
    <p class="eyebrow">Radar de Licitaciones</p>
    <h1>@@TITULO_H1@@</h1>
    <p class="sub">@@SUBTITULO@@</p>
  </header>
  <div class="controls">
    <input id="q" type="search" placeholder="Buscar: redes sociales, diseño, vídeo...">
    <select id="isla">
      <option value="">@@FILTRO_LUGAR@@</option>
    </select>
    <select id="semaforo">
      <option value="">Oportunidades (verde/naranja)</option>
      <option value="todas">Todas, incl. descartadas</option>
      <option value="verde">🟢 Prioridad</option>
      <option value="naranja">🟠 Valorar</option>
      <option value="rojo">🔴 Descartadas</option>
    </select>
    <select id="orden">
      <option value="plazo">Vence antes</option>
      <option value="importe">Mayor importe</option>
    </select>
  </div>
  <p class="count"><strong id="visibles">@@RECOMENDADAS@@</strong> de @@TOTAL@@ analizadas · @@RECOMENDADAS@@ oportunidades · Actualizado @@FECHA@@</p>
  <main class="ops" id="ops">
@@TARJETAS@@
  </main>
  <footer>
    Fuente: Plataforma de Contratación del Sector Público (datos abiertos, reutilización con atribución). Resúmenes generados con IA.
  </footer>
</div>
<script>
  const ops = Array.from(document.querySelectorAll('.op'));
  const q = document.getElementById('q');
  const isla = document.getElementById('isla');
  const semaforo = document.getElementById('semaforo');
  const orden = document.getElementById('orden');
  const cont = document.getElementById('ops');
  const visiblesLabel = document.getElementById('visibles');

  // Rellenar islas a partir de los datos
  const islas = [...new Set(ops.map(o => o.dataset.isla).filter(Boolean))].sort();
  for (const i of islas){ const opt=document.createElement('option'); opt.value=i; opt.textContent=i; isla.appendChild(opt); }

  function aplicar(){
    const texto = q.value.trim().toLowerCase();
    const islaSel = isla.value;
    const semSel = semaforo.value;
    let visibles = 0;
    for (const o of ops){
      const okTexto = !texto || o.dataset.texto.includes(texto);
      const okIsla = !islaSel || o.dataset.isla === islaSel;
      const okSemaforo = semSel === '' ? o.dataset.semaforo !== 'rojo'
        : semSel === 'todas' ? true
        : o.dataset.semaforo === semSel;
      const mostrar = okTexto && okIsla && okSemaforo;
      o.style.display = mostrar ? '' : 'none';
      if (mostrar) visibles++;
    }
    visiblesLabel.textContent = visibles;
    ordenar();
  }
  function ordenar(){
    const vis = ops.filter(o => o.style.display !== 'none');
    vis.sort((a,b) => orden.value === 'importe'
      ? (parseFloat(b.dataset.importe||0) - parseFloat(a.dataset.importe||0))
      : (parseInt(a.dataset.dias) - parseInt(b.dataset.dias)));
    for (const o of vis) cont.appendChild(o);
  }
  q.addEventListener('input', aplicar);
  isla.addEventListener('change', aplicar);
  semaforo.addEventListener('change', aplicar);
  orden.addEventListener('change', aplicar);
  aplicar();
</script>
</body>
</html>"""


def generar_html(items, salida, titulo_pagina, titulo_h1, subtitulo, nav_html, filtro_lugar):
    if items:
        tarjetas = "\n".join(tarjeta_html(it) for it in items)
    else:
        tarjetas = '<div class="empty">No hay oportunidades abiertas ahora mismo. El radar seguira mirando.</div>'
    hoy = date.today()
    fecha_txt = f"{hoy.day} {MESES[hoy.month]} {hoy.year}"
    total = len(items)
    recomendadas = sum(1 for it in items if it.get("relevante", True))
    doc = (CABECERA
           .replace("@@TOTAL@@", str(total))
           .replace("@@RECOMENDADAS@@", str(recomendadas))
           .replace("@@FECHA@@", fecha_txt)
           .replace("@@TARJETAS@@", tarjetas)
           .replace("@@TITULO_PAGINA@@", titulo_pagina)
           .replace("@@TITULO_H1@@", titulo_h1)
           .replace("@@SUBTITULO@@", subtitulo)
           .replace("@@NAV@@", nav_html)
           .replace("@@FILTRO_LUGAR@@", filtro_lugar))
    os.makedirs("docs", exist_ok=True)
    with open(salida, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"Dashboard generado en {salida}")


def _cargar(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def main():
    items_canarias = _cargar(ENTRADA)
    items_nacional = _cargar(ENTRADA_NACIONAL)

    if items_canarias is None and items_nacional is None:
        print(f"No encuentro {ENTRADA} ni {ENTRADA_NACIONAL}. Ejecuta primero:  python actualizar.py")
        return

    if items_canarias is not None:
        generar_html(
            items_canarias, SALIDA,
            titulo_pagina="Radar de Licitaciones · Canarias",
            titulo_h1="Lo que se cuece en lo público.",
            subtitulo="Concursos de comunicación, diseño y eventos en Canarias, filtrados y resumidos para no leerse un solo pliego.",
            nav_html='<a href="nacional.html">Ver oportunidades de toda España (remoto) →</a>',
            filtro_lugar="Todas las islas",
        )
    if items_nacional is not None:
        generar_html(
            items_nacional, SALIDA_NACIONAL,
            titulo_pagina="Radar de Licitaciones · Resto de España",
            titulo_h1="Lo que se cuece, en remoto.",
            subtitulo="Concursos de diseño, web, branding y comunicación en toda España ejecutables 100% en remoto.",
            nav_html='<a href="index.html">← Ver oportunidades de Canarias</a>',
            filtro_lugar="Todas las provincias",
        )


if __name__ == "__main__":
    main()