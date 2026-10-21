# Amrtavani

Citas de Śrīla Prabhupāda («Words of Nectar»): una página web para leerlas y un bot de Telegram que publica una cita diaria en un canal. Las citas se extraen de un volcado en Markdown de Vedabase, se filtran y se guardan en `quotes.json`, cada una con su referencia (libro y pasaje) y una categoría.

## Estructura

- `index.html`: la página web (carga `quotes.json`); `index.html.backup` es una copia anterior.
- `quotes.json`: las citas ya curadas (campos `quote`, `source`, `reference`, `category`, `id`).
- `extract_quotes.py`: extrae frases citables del volcado de Vedabase (8 a 60 palabras).
- `extract_with_refs.py`: lo mismo, conservando la referencia de la fuente (10 a 55 palabras).
- `filter_quotes.py`: filtra y selecciona las mejores a partir de la extracción completa y escribe `quotes.json`.
- `telegram-worker/`: Cloudflare Worker `amrtavani-bot` (`worker.js`, `wrangler.toml`). Un cron diario (07:00 UTC) publica la siguiente cita en el canal de Telegram; el índice de la última publicada se guarda en un KV (`AMRTAVANI_KV`) y las citas se leen de `https://amrta.bhaktiyoga.es/quotes.json`.

## Uso

Los scripts de Python tienen rutas absolutas fijas, de la antigua ubicación `~/.emacs.d/git_projects/` (entrada `vedabase_gold_dia.md`, salidas `quotes_full.json`, etc.); hay que ajustarlas antes de ejecutarlos. Orden: `extract_quotes.py` o `extract_with_refs.py`, luego `filter_quotes.py`.

El token del bot no está en el repositorio: se guarda como secreto de Cloudflare.

```bash
cd telegram-worker
wrangler secret put BOT_TOKEN
wrangler deploy
```

## Estado

Último trabajo en el repositorio: octubre de 2026 (dejar de versionar la salida de máquina intermedia). No hay `PROGRESS.md`.
