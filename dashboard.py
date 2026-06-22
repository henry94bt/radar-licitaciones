import json
import html
import os
from datetime import date

ENTRADA = "data/relevantes.json"
SALIDA = "docs/index.html"

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


def tarjeta_html(item):
    dias = dias_restantes(item.get("plazo"))
    clase, etiqueta = urgencia(dias)
    isla = item.get("lugar") or ""
    try:
        imp = float(item.get("importe"))
    except (TypeError, ValueError):
        imp = 0
    return f"""
      <article class="op" data-isla="{html.escape(isla)}" data-dias="{dias if dias is not None else 99999}" data-importe="{imp}" data-texto="{html.escape((item.get('titulo','') + ' ' + item.get('organo','') + ' ' + item.get('resumen','')).lower())}">
        <div class="op__clock op__clock--{clase}">
          <span class="op__days">{html.escape(etiqueta)}</span>
          <span class="op__deadline">{html.escape(formatear_fecha(item.get("plazo")))}</span>
        </div>
        <div class="op__body">
          <h2 class="op__title">{html.escape(item.get("titulo") or "")}</h2>
          <p class="op__org">{html.escape(item.get("organo") or "")}{(" · " + html.escape(isla)) if isla else ""}</p>
          <p class="op__summary">{html.escape(item.get("resumen") or "")}</p>
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
<title>Radar de Licitaciones · Canarias</title>
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
    <p class="eyebrow">Radar de Licitaciones</p>
    <h1>Lo que se cuece en lo público.</h1>
    <p class="sub">Concursos de comunicación, diseño y eventos en Canarias, filtrados y resumidos para no leerse un solo pliego.</p>
  </header>
  <div class="controls">
    <input id="q" type="search" placeholder="Buscar: redes sociales, diseño, vídeo...">
    <select id="isla">
      <option value="">Todas las islas</option>
    </select>
    <select id="orden">
      <option value="plazo">Vence antes</option>
      <option value="importe">Mayor importe</option>
    </select>
  </div>
  <p class="count"><strong id="visibles">@@RECUENTO@@</strong> de @@RECUENTO@@ oportunidades · Actualizado @@FECHA@@</p>
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
  const orden = document.getElementById('orden');
  const cont = document.getElementById('ops');
  const visiblesLabel = document.getElementById('visibles');

  // Rellenar islas a partir de los datos
  const islas = [...new Set(ops.map(o => o.dataset.isla).filter(Boolean))].sort();
  for (const i of islas){ const opt=document.createElement('option'); opt.value=i; opt.textContent=i; isla.appendChild(opt); }

  function aplicar(){
    const texto = q.value.trim().toLowerCase();
    const islaSel = isla.value;
    let visibles = 0;
    for (const o of ops){
      const okTexto = !texto || o.dataset.texto.includes(texto);
      const okIsla = !islaSel || o.dataset.isla === islaSel;
      const mostrar = okTexto && okIsla;
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
  orden.addEventListener('change', aplicar);
  aplicar();
</script>
</body>
</html>"""


def generar_html(items):
    if items:
        tarjetas = "\n".join(tarjeta_html(it) for it in items)
    else:
        tarjetas = '<div class="empty">No hay oportunidades abiertas ahora mismo. El radar seguira mirando.</div>'
    hoy = date.today()
    fecha_txt = f"{hoy.day} {MESES[hoy.month]} {hoy.year}"
    doc = (CABECERA
           .replace("@@RECUENTO@@", str(len(items)))
           .replace("@@FECHA@@", fecha_txt)
           .replace("@@TARJETAS@@", tarjetas))
    os.makedirs("docs", exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"Dashboard generado en {SALIDA}")


def main():
    try:
        with open(ENTRADA, encoding="utf-8") as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"No encuentro {ENTRADA}. Ejecuta primero:  python actualizar.py")
        return
    generar_html(items)


if __name__ == "__main__":
    main()
