# -*- coding: utf-8 -*-
"""
CONFERIR AS ANULAÇÕES — reabre cada ato de data/anulacoes.json e compara com
o que o parser de HOJE lê nele.

Por que: toda mudança no parser pode mudar o que ele lê dos atos antigos. Foi
esta conferência que pegou, em 04/09/2026, um ato do TRE-ES sem "Art. 1º" cujo
número de portaria passou a ser lido do cabeçalho — regressão que a suite de
testes não via. Rode ANTES de publicar qualquer mudança em parser.py.

O que compara, registro a registro:
  * o nome ainda é reconhecido no ato?                  -> "NÃO RECONHECIDO"
  * portaria desfeita e motivo continuam iguais?        -> "DIFERENÇA"
  * o parser vê no mesmo ato alguém que o arquivo não tem? -> "EXTRA"

Uso:
  python collector/conferir_anulacoes.py              # só reporta; sai 1 se houver algo
  python collector/conferir_anulacoes.py --atualizar  # grava portaria/motivo novos,
                                                      # acrescenta os EXTRAs e regenera a base
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect
import anulacoes as anul
import auditoria as aud
from parser import extrair_anulacoes, sem_acento


def conferir(anulacoes, pausa=0.8):
    """Devolve (diferencas, extras, falhas). Não grava nada.

    'diferencas' são pares (registro, leitura_atual) — leitura_atual é None
    quando o nome não foi reconhecido; 'extras' são anulações novas já no
    formato do arquivo; 'falhas' são urls que não abriram.
    """
    por_url = {}
    for a in anulacoes:
        por_url.setdefault(a.get("url", ""), []).append(a)
    diferencas, extras, falhas = [], [], []
    for url, regs in sorted(por_url.items()):
        if not url:
            continue
        texto, _ = collect.baixar_texto_portaria(url.replace(collect.BASE_ARTIGO, ""))
        if not texto:
            falhas.append(url)
            continue
        atual = extrair_anulacoes(texto)
        mapa = {sem_acento(x["nome"]): x for x in atual}
        conhecidos = {sem_acento(a["nome"]) for a in regs}
        for a in regs:
            n = mapa.get(sem_acento(a["nome"]))
            if n is None:
                diferencas.append((a, None))
            elif (anul._numero(n["portaria"]) != anul._numero(a.get("portaria_desfeita"))
                  or (n["motivo"] or "") != (a.get("motivo") or "")):
                diferencas.append((a, n))
        modelo = regs[0]
        for x in atual:
            if sem_acento(x["nome"]) not in conhecidos:
                extras.append({"uf": modelo["uf"], "nome": x["nome"],
                               "portaria_desfeita": x["portaria"], "motivo": x["motivo"],
                               "data": modelo.get("data", ""), "data_br": modelo.get("data_br", ""),
                               "ato": modelo.get("ato", ""), "url": url})
        time.sleep(pausa)
    return diferencas, extras, falhas


def main(argv=None):
    ap = argparse.ArgumentParser(description="Reabre os atos de data/anulacoes.json com o parser atual.")
    ap.add_argument("--atualizar", action="store_true",
                    help="grava as diferenças e os extras no arquivo e regenera a base")
    args = ap.parse_args(argv)

    anulacoes = anul.carregar(aud.ARQ_ANULACOES)
    print(f"{len(anulacoes)} registro(s) em {len({a.get('url') for a in anulacoes})} ato(s)…")
    collect.aquecer()
    diferencas, extras, falhas = conferir(anulacoes)

    for a, n in diferencas:
        if n is None:
            print(f"   >>> NÃO RECONHECIDO: {aud.rotulo(a)}")
        else:
            print(f"   >>> DIFERENÇA: {a['uf']} {a['nome']} — portaria {a.get('portaria_desfeita')!r} -> "
                  f"{n['portaria']!r}, motivo {a.get('motivo') or ''!r} -> {n['motivo']!r} ({a.get('ato')})")
    for x in extras:
        print(f"   >>> EXTRA (nome que o arquivo não tem): {aud.rotulo(x)}")
    for u in falhas:
        print(f"   ! download falhou: {u}")
    print(f"\n== {len(anulacoes)} registros: {len(diferencas)} diferença(s), {len(extras)} extra(s), "
          f"{len(falhas)} falha(s) de download ==")

    if not args.atualizar:
        return 1 if (diferencas or extras) else 0

    nao_reconhecidos = [a for a, n in diferencas if n is None]
    if nao_reconhecidos:
        print("\nNão atualizo enquanto houver nome NÃO RECONHECIDO: isso é regressão do parser, "
              "não dado a corrigir.")
        return 1
    for a, n in diferencas:
        a["portaria_desfeita"], a["motivo"] = n["portaria"], n["motivo"]
    total = anul.salvar(aud.ARQ_ANULACOES, anulacoes + extras)
    print(f"\nArquivo atualizado: {len(anulacoes)} -> {total} registro(s).")
    if diferencas or extras:
        import rebuild_data
        rebuild_data.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
