## Pipeline actual vs legacy

**Pipeline real** (lo que ejecuta `.github/workflows/radar.yml`): `actualizar.py` (descarga + filtra + clasifica con Claude + extrae detalle de pliegos vía `src/pliegos.py`) → `dashboard.py` (genera `docs/index.html` y `docs/nacional.html`) → `src/email_diario.py` (envío por Resend).

**Legacy, no usado por el pipeline actual** (confirmado leyendo imports, no solo por el grafo): `main.py`, `filtrar.py`, `resumir.py`, `src/dashboard.py`. `main.py` es el único punto que importa `src/filtro.py` y `src/resumen.py` — hace de puente hacia esos dos módulos, que si no fuera por él estarían huérfanos igualmente. Nada de esto se ha borrado todavía; pendiente de investigar/decidir antes de eliminar.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
