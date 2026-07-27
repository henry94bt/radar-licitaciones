# Convención de seguimiento (id_evl)

`id_evl` es el identificador persistente de cada licitación y la clave que une
todo lo demás: los enlaces de PLACSP con sesión codificada caducan, así que
nunca se guardan como referencia a largo plazo.

- **`pliegos/<id_evl>/`**: carpeta con los anexos de ese expediente (PCAP, PPT,
  notas). Los `.pdf` NO van a git (pesan y son redescargables desde PLACSP);
  los `.md` sí van, son las notas/resúmenes que aportan valor versionado.
- **`data/historico.csv`**: una fila por expediente, indexada por `id_evl`.
  Registra lo que el radar predijo (`clasificacion_radar`, verde/ámbar/rojo) y
  lo que pasó de verdad al final (`resultado`: pendiente/ganada/perdida/
  desierta/no_presentada), más datos de la adjudicación cuando se sepan
  (adjudicatario, importe, puntuaciones).

El objetivo es que el radar deje de ser una caja negra que solo clasifica y
nunca aprende: hoy no hay forma de saber si un verde era de verdad una buena
oportunidad. Comparando `clasificacion_radar` contra `resultado` fila a fila,
en cuanto haya ~20 casos reales, se podrá ver qué patrones se le escapan al
prompt de `evaluar()` en `actualizar.py` (falsos verdes que se pierden,
falsos rojos que eran ganables) y afinarlo con datos en vez de intuición.

No se rellena nada de esto automáticamente todavía — es la base para que,
según se vayan cerrando expedientes, alguien (Henry, o un paso futuro del
pipeline) añada la fila correspondiente a mano o semi-automatizado.

## Cómo registrar un desenlace

En vez de editar `data/historico.csv` a mano, usar `src/historico.py` — crea la
fila si no existe, o actualiza solo los campos indicados si ya existe. Valida
que `resultado` sea uno de los 5 valores permitidos.

```bash
python -m src.historico BzszOPWAEUpLAIVZdUs8KA== resultado=ganada adjudicatario="La Pepa Studio" importe_adjudicacion=59000
```
