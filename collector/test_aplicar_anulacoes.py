# -*- coding: utf-8 -*-
"""
Testes de COMO a anulação é aplicada à base.

Achar o nome no ato é metade do trabalho; a outra metade é acertar QUAL registro
sai. Errar aqui apaga do painel alguém que foi mesmo nomeado — pior do que o bug
original. As regras que estes testes travam:

  * só sai registro do MESMO tribunal (homônimo em outro TRE não é a mesma pessoa);
  * só sai nomeação ANTERIOR ao ato — quem foi nomeado de novo depois continua;
  * quando o ato cita a portaria desfeita, só aquela nomeação sai (caso real do
    TSE: o mesmo candidato teve duas nomeações, anuladas em atos diferentes).

Rode com:  python3 test_aplicar_anulacoes.py
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anulacoes import aplicar_anulacoes, carregar, salvar


def reg(uf, nome, data, portaria, cargo="Técnico Judiciário"):
    return {"uf": uf, "nome": nome, "data": data, "portaria": portaria, "cargo": cargo}


def anul(uf, nome, data, portaria_desfeita=""):
    return {"uf": uf, "nome": nome, "data": data, "portaria_desfeita": portaria_desfeita}


CASOS = [
    ("remove a nomeacao anulada",
     [reg("SE", "Ytallo Augusto Santos Lima", "2026-07-28", "PORTARIA Nº 504")],
     [anul("SE", "Ytallo Augusto Santos Lima", "2026-08-31", "504")],
     []),

    ("nao remove homonimo de outro tribunal",
     [reg("SE", "Jonas da Silva", "2026-07-28", "PORTARIA Nº 504"),
      reg("MG", "Jonas da Silva", "2025-08-25", "PORTARIA Nº 188")],
     [anul("MG", "Jonas da Silva", "2025-11-17", "188")],
     ["SE/Jonas da Silva"]),

    ("nao remove nomeacao POSTERIOR ao ato (renomeado depois)",
     [reg("MG", "Daniel Jardim Cordeiro", "2025-11-17", "PORTARIA Nº 288"),
      reg("MG", "Daniel Jardim Cordeiro", "2026-03-10", "PORTARIA Nº 40")],
     [anul("MG", "Daniel Jardim Cordeiro", "2025-12-29", "288")],
     ["MG/Daniel Jardim Cordeiro"]),

    ("com portaria citada, sai so a nomeacao daquela portaria (TSE, 2 anulacoes)",
     [reg("TSE", "Marcus Vinicius Alves de Sousa Amaro", "2026-03-11", "PORTARIA Nº 85",
          "Analista Judiciário"),
      reg("TSE", "Marcus Vinicius Alves de Sousa Amaro", "2026-04-24", "PORTARIA Nº 163")],
     [anul("TSE", "Marcus Vinicius Alves de Sousa Amaro", "2026-03-25", "85")],
     ["TSE/Marcus Vinicius Alves de Sousa Amaro"]),   # sobra a da portaria 163

    ("anulacao sem correspondencia na base nao remove nada",
     [reg("BA", "Fulano de Tal Silva", "2026-01-05", "PORTARIA Nº 10")],
     [anul("BA", "Ciclano Souza Lima", "2026-02-01", "99")],
     ["BA/Fulano de Tal Silva"]),

    ("nome com acento diferente ainda casa",
     [reg("PI", "Heanes José de Sousa Silva", "2026-03-02", "PORTARIA Nº 137")],
     [anul("PI", "HEANES JOSE DE SOUSA SILVA", "2026-03-16", "")],
     []),
]


def caso_salvar_sem_novidade_nao_mexe_no_arquivo():
    """Regravar a mesma lista não pode mudar o arquivo.

    O robô roda ~20x por dia. Se o 'atualizado_em' mudasse a cada execução, o
    GitHub Actions abriria um commit por rodada, sem nada de novo dentro.
    """
    caminho = os.path.join(tempfile.mkdtemp(), "anulacoes.json")
    lista = [anul("SE", "Ytallo Augusto Santos Lima", "2026-08-31", "504")]
    salvar(caminho, lista)
    antes = open(caminho, encoding="utf-8").read()
    salvar(caminho, lista)                      # mesma lista, de novo
    depois = open(caminho, encoding="utf-8").read()
    problemas = []
    if antes != depois:
        problemas.append("regravou o arquivo mesmo sem anulação nova")
    salvar(caminho, lista + [anul("MG", "Jonas da Silva", "2025-11-17", "188")])
    if len(carregar(caminho)) != 2:
        problemas.append("não gravou a anulação nova")
    return problemas


def main():
    ok = True
    problemas = caso_salvar_sem_novidade_nao_mexe_no_arquivo()
    if problemas:
        ok = False
        print("[FALHA] salvar sem novidade nao mexe no arquivo")
        for p in problemas:
            print(f"        {p}")
    else:
        print("[OK  ] salvar sem novidade nao mexe no arquivo")

    for tag, registros, anuls, esperado in CASOS:
        ficaram, removidos = aplicar_anulacoes(registros, anuls)
        got = sorted(f'{r["uf"]}/{r["nome"]}' for r in ficaram)
        esp = sorted(esperado)
        status = "OK  " if got == esp else "FALHA"
        if got != esp:
            ok = False
        print(f"[{status}] {tag}")
        print(f"       ficaram={got} (removidos={len(removidos)})")
        if got != esp:
            print(f"       esperado={esp}")
    print("\n==> APLICACAO DE ANULACOES OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
