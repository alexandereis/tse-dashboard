# -*- coding: utf-8 -*-
"""
Correção pontual (idempotente): remove da base os 5 registros gravados por engano
na execução de 08/06/2026 — eram da seção "Técnico Judiciário - Área Administrativa"
da PORTARIA TRE-SP nº 184 (NÃO são de TI). O parser já foi corrigido para não
repetir isso; este script só limpa o que já tinha sido publicado.

Uso:  python collector/corrigir_base.py
"""
import json, os, re, unicodedata
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = os.path.join(RAIZ, "data", "nomeacoes.json")

def sem_acento(t):
    nf = unicodedata.normalize("NFKD", t or "")
    return "".join(c for c in nf if not unicodedata.combining(c)).lower().strip()

INDEVIDOS = [
    ("SP", "laize fernanda pereira"),
    ("SP", "leticia mendonca rossetti silva"),
    ("SP", "eduardo cassoli ferraz"),
    ("SP", "aparecido santos tomazin junior"),
    ("SP", "adriana brandassi"),
]

def eh_indevido(r):
    nome = sem_acento(r.get("nome", ""))
    uf = r.get("uf", "")
    return any(uf == u and alvo in nome for (u, alvo) in INDEVIDOS)

def main():
    with open(ARQ, encoding="utf-8") as f:
        d = json.load(f)
    regs = d.get("registros", [])
    antes = len(regs)
    regs = [r for r in regs if not eh_indevido(r)]
    removidos = antes - len(regs)
    if removidos == 0:
        print(f"Nada a remover — base já está limpa ({antes} registros).")
        return
    regs.sort(key=lambda r: (r.get("data", ""), r.get("nome", "")), reverse=True)
    d["registros"] = regs
    d["total"] = len(regs)
    d["atualizado_em"] = datetime.now(timezone.utc).isoformat()
    with open(ARQ, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"Removidos {removidos} registros indevidos. Base agora: {len(regs)}.")

if __name__ == "__main__":
    main()
