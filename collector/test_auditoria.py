# -*- coding: utf-8 -*-
"""
Testes da AUDITORIA (auditoria.py): a biblioteca que sustenta auditar_dia.py,
conferir_anulacoes.py e varredura.py.

O que ela precisa acertar:
  * o "cheiro" de nomeação perdida — ato com "nomear" + termo de TI e zero
    nomeados (foi assim que a nomeação do TRE-RN de 04/09/2026 foi achada);
  * dizer se um nomeado ou uma anulação já são conhecidos, sem se enganar com
    acento, caixa ou número de portaria;
  * avaliar um ato inteiro (download + parser) devolvendo tudo num só lugar.

Rode com:  python3 test_auditoria.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect
import auditoria as aud

TEXTO_RN = (
    "Art. 1 NOMEAR, com fundamento no inciso I do art. 9 da Lei n 8.112, a candidata Indi Li da "
    "Silva Alves Moreira Tenorio, para exercer, em carater efetivo, o cargo de Tecnico Judiciario - "
    "Area Apoio Especializado - Programacao de Sistemas, Classe A. Art. 2 Esta Portaria entra em vigor."
)
# nome de UMA palavra: o parser não aceita, e o cheiro precisa acusar
TEXTO_NOME_ILEGIVEL = TEXTO_RN.replace("Indi Li da Silva Alves Moreira Tenorio", "Madonna")
TEXTO_CESSAO = (
    "Art. 1 CEDER o servidor DIONE SANTOS DE ALMEIDA, ocupante do cargo de Tecnico Judiciario, "
    "Especialidade Operacao de Computadores, para o Tribunal Superior do Trabalho."
)
TEXTO_CONTABILIDADE = (
    "Art. 1 NOMEAR o candidato ELIONAI COSTA FERREIRA, classificado em 1 lugar, para ocupar o cargo "
    "de Analista Judiciario, Area Administrativa, Especialidade Contabilidade, Classe A."
)
TEXTO_COMISSAO = (
    "Art. 2 Nomear FREDERICO GOMES JABBUR, Analista Judiciario, Apoio Especializado - Analise de "
    "Sistemas, para o exercicio do Cargo em Comissao CJ-2, na Coordenadoria de Suporte."
)
# "nomear" + "suporte" sem nada de concurso/cargo efetivo: chefia, nao convocacao
TEXTO_CHEFIA = (
    "Art. 1 Nomear MARIA DA SILVA para responder pela Secao de Suporte Tecnico durante as ferias "
    "do titular."
)

REGISTROS = [
    {"uf": "RN", "cargo": "Técnico Judiciário", "nome": "Indi Li da Silva Alves Moreira Tenorio"},
    {"uf": "RJ", "cargo": "Técnico Judiciário", "nome": "Gabriel Binda Lima"},
]
SEED = [{"uf": "SP", "cargo": "Analista Judiciário", "nome": "Marcos de Oliveira Coelho"}]
ANULACOES = [
    {"uf": "RJ", "nome": "Gabriel Binda Lima", "portaria_desfeita": "148", "data": "2026-07-08",
     "url": "https://www.in.gov.br/web/dou/-/ato-pr-n-215"},
]

ITEM = {
    "hierarchyStr": "Poder Judiciário/Tribunal Regional Eleitoral do Rio Grande do Norte",
    "title": "PORTARIA PRES Nº 277, DE 3 DE SETEMBRO DE 2026",
    "urlTitle": "portaria-pres-n-277-de-3-de-setembro-de-2026-730129751",
    "content": "",
    "pubDate": "04/09/2026",
}


def _com_download(resposta):
    original = collect.baixar_texto_portaria
    collect.baixar_texto_portaria = lambda ut, tentativas=3: resposta
    return original


def caso_cheiro_de_nomeacao_perdida():
    p = []
    if not aud.cheira_a_nomeacao_perdida(TEXTO_NOME_ILEGIVEL, []):
        p.append("nomear + TI + 0 nomeados NAO acusou")
    if aud.cheira_a_nomeacao_perdida(TEXTO_RN, [{"nome": "Indi Li da Silva Alves Moreira Tenorio"}]):
        p.append("acusou mesmo com nomeado extraido")
    if aud.cheira_a_nomeacao_perdida(TEXTO_CESSAO, []):
        p.append("cessao (sem 'nomear') acusou")
    if aud.cheira_a_nomeacao_perdida(TEXTO_CONTABILIDADE, []):
        p.append("nomeacao de Contabilidade (sem termo de TI) acusou")
    if aud.cheira_a_nomeacao_perdida(TEXTO_COMISSAO, []):
        p.append("cargo em comissao acusou")
    if aud.cheira_a_nomeacao_perdida(TEXTO_CHEFIA, []):
        p.append("'nomear ... Secao de Suporte' sem concurso/efetivo acusou")
    return p


def caso_base_reconhece_nomeado():
    base = aud.Base(REGISTROS, SEED, ANULACOES)
    p = []
    if not base.nomeado_conhecido({"uf": "RN", "nome": "INDI LI DA SILVA ALVES MOREIRA TENÓRIO"}):
        p.append("nao reconheceu o mesmo nome em caixa alta e com acento")
    if not base.nomeado_conhecido({"uf": "SP", "nome": "Marcos de Oliveira Coelho"}):
        p.append("nao reconheceu nome que so esta no seed")
    if base.nomeado_conhecido({"uf": "SP", "nome": "Marcos Oliveira Coelho"}):
        p.append("reconheceu grafia diferente como se fosse a mesma (deve acusar para revisao humana)")
    if base.nomeado_conhecido({"uf": "PB", "nome": "Gabriel Binda Lima"}):
        p.append("reconheceu o nome em OUTRO tribunal")
    return p


def caso_base_reconhece_anulacao():
    base = aud.Base(REGISTROS, SEED, ANULACOES)
    p = []
    mesma = {"uf": "RJ", "nome": "Gabriel Binda Lima", "portaria_desfeita": "148", "data": "2026-07-08",
             "url": "https://www.in.gov.br/web/dou/-/ato-pr-n-215"}
    if not base.anulacao_conhecida(mesma):
        p.append("nao reconheceu anulacao identica")
    # mesmo ato (url) e mesma pessoa, numero da portaria lido diferente: e a MESMA anulacao
    if not base.anulacao_conhecida(dict(mesma, portaria_desfeita="215")):
        p.append("mesmo ato + mesma pessoa com numero diferente virou anulacao nova")
    # outro ato, mesma pessoa: e outra anulacao (gente nomeada duas vezes existe)
    if base.anulacao_conhecida(dict(mesma, url="https://www.in.gov.br/web/dou/-/ato-pr-n-300", data="2026-09-01")):
        p.append("anulacao de OUTRO ato foi dada como conhecida")
    return p


def caso_avaliar_ato_suspeito():
    original = _com_download((TEXTO_NOME_ILEGIVEL, "https://www.in.gov.br/x"))
    try:
        r = aud.avaliar_ato(ITEM)
    finally:
        collect.baixar_texto_portaria = original
    p = []
    if r["sigla"] != "RN":
        p.append(f"sigla {r['sigla']} (esperado RN)")
    if r["nomeados"]:
        p.append(f"extraiu {r['nomeados']} de um nome ilegivel")
    if not r["suspeito"]:
        p.append("nao marcou como suspeito")
    if not r["avaliado"]:
        p.append("nao marcou como avaliado, mas o texto veio inteiro")
    return p


def caso_avaliar_ato_normal():
    original = _com_download((TEXTO_RN, "https://www.in.gov.br/x"))
    try:
        r = aud.avaliar_ato(ITEM)
    finally:
        collect.baixar_texto_portaria = original
    p = []
    nomes = [n["nome"] for n in r["nomeados"]]
    if nomes != ["Indi Li da Silva Alves Moreira Tenorio"]:
        p.append(f"nomeados {nomes}")
    if r["suspeito"]:
        p.append("marcou como suspeito um ato lido com sucesso")
    if r["nomeados"][0].get("uf") != "RN" or r["nomeados"][0].get("data") != "2026-09-04":
        p.append("registro sem uf/data no formato do coletor")
    return p


CASOS = {
    "cheiro de nomeacao perdida (nomear + TI + 0 nomeados)": caso_cheiro_de_nomeacao_perdida,
    "Base reconhece nomeado (acento/caixa; grafia diferente acusa)": caso_base_reconhece_nomeado,
    "Base reconhece anulacao (mesmo ato = mesma; outro ato = outra)": caso_base_reconhece_anulacao,
    "avaliar_ato: nome ilegivel vira suspeito": caso_avaliar_ato_suspeito,
    "avaliar_ato: ato normal sai no formato do coletor": caso_avaliar_ato_normal,
}


def main():
    ok = True
    for tag, funcao in CASOS.items():
        problemas = funcao()
        if problemas:
            ok = False
            print(f"[FALHA] {tag}")
            for x in problemas:
                print(f"        {x}")
        else:
            print(f"[OK  ] {tag}")
    print("\n==> AUDITORIA OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
