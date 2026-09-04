# -*- coding: utf-8 -*-
"""
AUDITAR UM DIA DO DOU — confere o painel contra a edição do dia.

Abre TODOS os atos da Justiça Eleitoral da Seção 2 daquela data, roda o parser
em cada um e mostra o que saiu — e, mais importante, o que NÃO saiu:

  * nomeado de TI que o painel ainda não tem            -> "NÃO ESTÁ NA BASE"
  * anulação que o arquivo ainda não tem                -> "FORA DO ARQUIVO"
  * ato com "nomear" + termo de TI e ZERO nomeados      -> "SUSPEITO" (abra e olhe)

Uso:
  python collector/auditar_dia.py                 # hoje
  python collector/auditar_dia.py 04-09-2026      # uma data
  python collector/auditar_dia.py 04-09-2026 --salvar /tmp/atos   # guarda os textos

Sai com código 1 quando há algo para olhar, 0 quando o dia bate com o painel.
Só lê; não grava nada no projeto.
"""
import argparse
import os
import re
import sys
import time
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect
import auditoria as aud


def _parse_data(s):
    return datetime.strptime(s, "%d-%m-%Y").date()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Confere o painel contra um dia do DOU.")
    ap.add_argument("data", nargs="?", default=date.today().strftime("%d-%m-%Y"),
                    help="DD-MM-AAAA (padrão: hoje)")
    ap.add_argument("--salvar", metavar="PASTA", help="guarda o texto de cada ato nessa pasta")
    args = ap.parse_args(argv)
    dia = _parse_data(args.data)

    base = aud.Base.dos_arquivos()
    collect.aquecer()
    je = aud.atos_je_do_dia(dia)
    if je is None:
        print(f"{dia:%d/%m/%Y}: edição indisponível no in.gov.br (tente de novo mais tarde).")
        return 2
    print(f"{dia:%d/%m/%Y}: {len(je)} ato(s) da Justiça Eleitoral na Seção 2\n")
    if args.salvar:
        os.makedirs(args.salvar, exist_ok=True)

    pendencias = []
    for i, item in enumerate(je):
        r = aud.avaliar_ato(item, dia)
        marcas = []
        if not r["avaliado"]:
            marcas.append("SEM TEXTO (download falhou)")
        if r["suspeito"]:
            marcas.append("SUSPEITO: nomear + TI e zero nomeados")
        print(f"[{i:02d}] {r['sigla'] or '??':>3} | {r['titulo'][:70]:<70} | "
              f"nomeados={len(r['nomeados'])} anulações={len(r['anulacoes'])}"
              + (f"  <<< {'; '.join(marcas)}" if marcas else ""))
        for reg in r["nomeados"]:
            novo = not base.nomeado_conhecido(reg)
            print(f"       + {reg['nome']} — {reg['cargo']} / {reg['especialidade']}"
                  + ("   <<< NÃO ESTÁ NA BASE" if novo else ""))
            if novo:
                pendencias.append("nomeado fora da base: " + aud.rotulo(reg))
        for a in r["anulacoes"]:
            novo = not base.anulacao_conhecida(a)
            print(f"       - {a['nome']} (desfaz {a.get('portaria_desfeita') or '?'}"
                  f"{', ' + a['motivo'] if a.get('motivo') else ''})"
                  + ("   <<< FORA DO ARQUIVO" if novo else ""))
            if novo:
                pendencias.append("anulação fora do arquivo: " + aud.rotulo(a))
        if r["suspeito"]:
            pendencias.append(f"suspeito: {r['sigla']} {r['titulo']} {r['url']}")
        if args.salvar and r["texto"]:
            nome = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{i:02d}_{r['sigla'] or 'XX'}_{r['titulo'][:50]}") + ".txt"
            with open(os.path.join(args.salvar, nome), "w", encoding="utf-8") as f:
                f.write(f"{r['titulo']}\n{r['url']}\n\n{r['texto']}\n")
        time.sleep(0.5)

    print()
    if not pendencias:
        print("OK: tudo que o parser leu nesse dia já está no painel, e nenhum ato ficou suspeito.")
        return 0
    print(f"{len(pendencias)} pendência(s) para olhar:")
    for p in pendencias:
        print("   >>> " + p)
    return 1


if __name__ == "__main__":
    sys.exit(main())
