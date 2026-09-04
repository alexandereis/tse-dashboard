# -*- coding: utf-8 -*-
"""
VARREDURA — reabre as edições do DOU, dia a dia, e compara com o painel.

É a rede de segurança do coletor: ele só sabe o que o parser devolve, e um
formato novo faz a nomeação sumir em silêncio. A varredura reabre os atos da
Justiça Eleitoral de um período com o parser ATUAL e aponta:

  * nomeado de TI que o painel não tem       -> revisão humana (pode ser
    retificação de grafia do DOU; a base segue a versão corrigida)
  * anulação que o arquivo não tem            -> incorporada com --incorporar
  * ato "suspeito" (nomear + TI + 0 nomeados) -> revisão humana

Retomável: o progresso fica em collector/.varredura/ (fora do git); rodar de
novo continua de onde parou. Gentil com o in.gov.br: pausa entre atos e dias.
~1 minuto por dia útil.

Uso:
  python collector/varredura.py                       # últimos 45 dias, só reporta
  python collector/varredura.py --dias 90
  python collector/varredura.py --desde 2025-06-01    # desde uma data
  python collector/varredura.py --incorporar          # grava as anulações achadas e regenera a base
  python collector/varredura.py --reiniciar           # ignora o progresso salvo

Código de saída: 1 se sobrou algo para revisão humana (nomeado fora da base ou
ato suspeito), 0 se o período bate com o painel. É o que faz o workflow mensal
avisar por e-mail.
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect
import auditoria as aud

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".varredura")


def _ler(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def _gravar(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def varrer(desde, ate, pasta=PASTA, base=None, pausa_ato=0.8, pausa_dia=2.0):
    """Varre de `ate` para trás até `desde` (dates). Devolve o estado final:
    {"progresso", "nomeados", "anulacoes", "suspeitos"}."""
    os.makedirs(pasta, exist_ok=True)
    arq = {k: os.path.join(pasta, f"{k}.json") for k in ("progresso", "nomeados", "anulacoes", "suspeitos")}
    estado = {"progresso": _ler(arq["progresso"], {}), "nomeados": _ler(arq["nomeados"], []),
              "anulacoes": _ler(arq["anulacoes"], []), "suspeitos": _ler(arq["suspeitos"], [])}
    base = base or aud.Base.dos_arquivos()

    dia = ate
    while dia >= desde:
        iso = dia.isoformat()
        if dia.weekday() >= 5 or iso in estado["progresso"]:
            dia -= timedelta(days=1)
            continue
        je = aud.atos_je_do_dia(dia)
        if je is None:
            print(f"{iso}: edição indisponível (fica para a próxima rodada)", flush=True)
            dia -= timedelta(days=1)
            time.sleep(pausa_dia)
            continue
        n_nom = n_anul = n_falha = 0
        for item in je:
            r = aud.avaliar_ato(item, dia)
            if not r["avaliado"]:
                n_falha += 1
            for reg in r["nomeados"]:
                n_nom += 1
                if not base.nomeado_conhecido(reg):
                    print("   >>> NÃO ESTÁ NA BASE: " + aud.rotulo(reg), flush=True)
                    estado["nomeados"].append(reg)
            for a in r["anulacoes"]:
                n_anul += 1
                if not base.anulacao_conhecida(a):
                    print("   >>> ANULAÇÃO FORA DO ARQUIVO: " + aud.rotulo(a), flush=True)
                    estado["anulacoes"].append(a)
            if r["suspeito"]:
                s = {"uf": r["sigla"], "titulo": r["titulo"], "url": r["url"], "data": iso}
                print(f"   >>> SUSPEITO (nomear + TI e zero nomeados): {s['uf']} {s['titulo']} {s['url']}", flush=True)
                estado["suspeitos"].append(s)
            time.sleep(pausa_ato)
        estado["progresso"][iso] = {"atos_je": len(je), "nomeados": n_nom, "anulacoes": n_anul, "falhas": n_falha}
        print(f"{iso}: {len(je)} atos da JE, {n_nom} nomeados de TI, {n_anul} anulações, "
              f"{n_falha} falha(s) de download", flush=True)
        for k in arq:
            _gravar(arq[k], estado[k])
        time.sleep(pausa_dia)
        dia -= timedelta(days=1)
    return estado


def main(argv=None):
    ap = argparse.ArgumentParser(description="Reabre as edições do DOU e compara com o painel.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dias", type=int, default=45, help="quantos dias para trás (padrão 45)")
    g.add_argument("--desde", metavar="AAAA-MM-DD", help="data inicial")
    ap.add_argument("--ate", metavar="AAAA-MM-DD", help="data final (padrão: hoje)")
    ap.add_argument("--incorporar", action="store_true",
                    help="grava no arquivo as anulações achadas e regenera a base")
    ap.add_argument("--reiniciar", action="store_true", help="apaga o progresso salvo antes de começar")
    ap.add_argument("--pasta", default=PASTA, help="onde guardar progresso e achados")
    args = ap.parse_args(argv)

    ate = datetime.strptime(args.ate, "%Y-%m-%d").date() if args.ate else date.today()
    desde = (datetime.strptime(args.desde, "%Y-%m-%d").date() if args.desde
             else ate - timedelta(days=args.dias))
    if args.reiniciar and os.path.isdir(args.pasta):
        shutil.rmtree(args.pasta)

    print(f"Varredura de {desde:%d/%m/%Y} a {ate:%d/%m/%Y} (progresso em {args.pasta})\n", flush=True)
    collect.aquecer()
    estado = varrer(desde, ate, pasta=args.pasta)

    p = estado["progresso"]
    print(f"\n== {len(p)} dia(s) útil(eis), {sum(v['atos_je'] for v in p.values())} atos da JE, "
          f"{sum(v['nomeados'] for v in p.values())} nomeados de TI, "
          f"{sum(v['anulacoes'] for v in p.values())} anulações, "
          f"{sum(v['falhas'] for v in p.values())} falha(s) | "
          f"{len(estado['nomeados'])} nomeado(s) fora da base, "
          f"{len(estado['anulacoes'])} anulação(ões) fora do arquivo, "
          f"{len(estado['suspeitos'])} suspeito(s) ==", flush=True)

    if args.incorporar and estado["anulacoes"]:
        novas = aud.incorporar_anulacoes(estado["anulacoes"])
        for n in novas:
            print("   + incorporada: " + aud.rotulo(n), flush=True)
        if novas:
            import rebuild_data
            rebuild_data.main()
        else:
            print("   (todas já estavam no arquivo)", flush=True)

    pendentes = estado["nomeados"] or estado["suspeitos"]
    if pendentes:
        print("\nHá itens para revisão humana (nomeado fora da base ou ato suspeito) — veja acima.", flush=True)
    return 1 if pendentes else 0


if __name__ == "__main__":
    sys.exit(main())
