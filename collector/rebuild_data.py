# -*- coding: utf-8 -*-
"""
Regenera data/nomeacoes.json de forma SEGURA, sem perder nada.

Combina o seed (base curada) com o que já está em data/nomeacoes.json (as
adições que o coletor foi acumulando), sem duplicar — em conflito, o seed vence.
Se o data/nomeacoes.json estiver corrompido/ilegível (ex.: um merge do git
quebrou o arquivo), cai automaticamente para o seed sozinho (modo recuperação).

Use depois de um `git pull`/merge, ou sempre que a base ficar inconsistente.

Uso:  python collector/rebuild_data.py
"""
import json
import os
import re
import unicodedata
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")


def sem_acento(t):
    nfkd = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def chave(r):
    return (r.get("uf", ""), r.get("cargo", ""), sem_acento(r.get("nome", "")))


def data_iso(data_br):
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", data_br or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def _carregar(caminho):
    """Lê um JSON; retorna None se não existir ou estiver corrompido."""
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def main():
    seed = _carregar(ARQ_SEED) or []
    dados = _carregar(ARQ_DADOS)
    if dados is None:
        print("! data/nomeacoes.json ilegível/ausente — recuperando só do seed.")
        atuais = []
    else:
        atuais = dados.get("registros", []) if isinstance(dados, dict) else dados

    # UNIÃO: seed primeiro (vence em conflito), depois o que o coletor acumulou.
    base = {}
    for r in seed:
        r = dict(r)
        r.setdefault("data", data_iso(r.get("data_br", "")))
        base[chave(r)] = r
    add = 0
    for r in atuais:
        if chave(r) not in base:
            base[chave(r)] = r
            add += 1

    regs = sorted(base.values(),
                  key=lambda r: (r.get("data", ""), r.get("nome", "")),
                  reverse=True)
    saida = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(regs), "registros": regs,
    }
    os.makedirs(os.path.dirname(ARQ_DADOS), exist_ok=True)
    with open(ARQ_DADOS, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"data/nomeacoes.json regenerado: {len(regs)} registros "
          f"(seed {len(seed)} + {add} vindos da base/coletor).")


if __name__ == "__main__":
    main()
