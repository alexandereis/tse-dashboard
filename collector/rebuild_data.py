# -*- coding: utf-8 -*-
"""
Regenera data/nomeacoes.json a partir do seed/seed.json (fonte de verdade).

Use quando o data/nomeacoes.json ficar inconsistente — por exemplo depois de um
`git pull`/merge, já que JSON não mescla bem linha a linha. É determinístico:
ordena por data (mais recente primeiro) e recalcula o total.

Uso:  python collector/rebuild_data.py
"""
import json, os, re
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")


def data_iso(br):
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", br or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def main():
    seed = json.load(open(ARQ_SEED, encoding="utf-8"))
    regs = []
    for r in seed:
        r = dict(r)
        r.setdefault("data", data_iso(r.get("data_br", "")))
        regs.append(r)
    regs.sort(key=lambda r: (r.get("data", ""), r.get("nome", "")), reverse=True)
    out = {"atualizado_em": datetime.now(timezone.utc).isoformat(),
           "total": len(regs), "registros": regs}
    json.dump(out, open(ARQ_DADOS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"data/nomeacoes.json regenerado a partir do seed: {len(regs)} registros.")


if __name__ == "__main__":
    main()
