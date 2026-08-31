# -*- coding: utf-8 -*-
"""
Testes das ANULAÇÕES: quando o tribunal publica um ato que TORNA SEM EFEITO uma
nomeação, o nomeado precisa sair do painel — antes disso o coletor só sabia
somar, e quem teve a nomeação anulada continuava aparecendo como convocado.

Caso que originou: PORTARIA 587/TRE-SE (DOU de 31/08/2026) tornou sem efeito a
PORTARIA 504, de 23/07/2026, que havia nomeado YTALLO AUGUSTO SANTOS LIMA — o
painel seguiu exibindo a nomeação por mais de um mês.

Rode com:  python3 test_anulacoes.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import extrair_anulacoes, extrair_nomeados

CASOS = {
 # --- DEVEM anular -------------------------------------------------------
 "SE 587 (real: tornar sem efeito ... referente a nomeacao do candidato)": (
    "PORTARIA N 587, DE 28 DE AGOSTO DE 2026 A PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE "
    "SERGIPE, no uso das atribuicoes que lhe sao conferidas pelo artigo 28, inciso XXXIV, do "
    "Regimento Interno; CONSIDERANDO o artigo 13, 1 e 6 da Lei n 8.112, de 11 de dezembro de "
    "1990, resolve: Art. 1 Tornar sem efeito a Portaria de Pessoal n 504, de 23 de Julho de "
    "2026, publicada no Diario Oficial da Uniao n 140, Secao 2, de 28 de Julho de 2026, "
    "referente a nomeacao do candidato YTALLO AUGUSTO SANTOS LIMA, para o cargo de Tecnico "
    "Judiciario, Area de Apoio Especializado, Especialidade Programacao de Sistemas. Art. 2 "
    "Esta Portaria entra em vigor na data de sua publicacao. Des. ANA LUCIA FREIRE DE ALMEIDA "
    "DOS ANJOS", ["Ytallo Augusto Santos Lima"]),

 "variante: tornar insubsistente a portaria que nomeou": (
    "Art. 1 Tornar insubsistente a Portaria n 312, de 4 de marco de 2026, que nomeou a candidata "
    "MARIANA COSTA PEREIRA para o cargo de Analista Judiciario, Area Apoio Especializado, "
    "Especialidade Analise de Sistemas de Informacao.", ["Mariana Costa Pereira"]),

 "variante: tornar sem efeito a nomeacao de FULANO": (
    "Art. 1 Tornar sem efeito a nomeacao de PAULO ROBERTO ALVES DE SOUZA, classificado em 3 lugar, "
    "para o cargo de Tecnico Judiciario, Apoio Especializado, Programacao de Sistemas, por nao ter "
    "tomado posse no prazo legal.", ["Paulo Roberto Alves de Souza"]),

 "variante: revogar a portaria ... que nomeou o(a) candidato(a)": (
    "Art. 1 Revogar a Portaria n 88, de 10 de fevereiro de 2026, que nomeou o(a) candidato(a) "
    "CARLA DE ANDRADE MENEZES, classificada em 4 lugar, para o cargo de Analista Judiciario, Area "
    "de Apoio Especializado - Tecnologia da Informacao.", ["Carla de Andrade Menezes"]),

 # --- NAO podem anular ---------------------------------------------------
 "nomeacao comum nao anula ninguem": (
    "Art. 1 NOMEAR o(a) candidato(a) JOAO PEDRO SANTOS DE MENDONCA, classificado(a) em 5 lugar, "
    "para ocupar o cargo de Tecnico Judiciario, Area de Apoio Especializado, Especialidade "
    "Programacao de Sistemas, Classe A, Padrao 1.", []),

 "exoneracao a pedido nao e anulacao (a pessoa foi mesmo nomeada)": (
    "Art. 1 EXONERAR, a pedido, RICARDO LIMA FERREIRA do cargo efetivo de Tecnico Judiciario, Area "
    "Apoio Especializado, Especialidade Programacao de Sistemas, a contar de 1 de setembro de 2026.",
    []),

 "tornar sem efeito de ato que nao e nomeacao (designacao) nao anula": (
    "Art. 1 Tornar sem efeito a Portaria n 45, de 2 de janeiro de 2026, que designou o servidor "
    "MARCELO AUGUSTO DIAS para responder pela Secao de Suporte Tecnico.", []),
}

# A portaria de anulacao NAO pode, ela mesma, virar uma nomeacao nova no painel.
NAO_NOMEIA = ["SE 587 (real: tornar sem efeito ... referente a nomeacao do candidato)"]


# O ato quase sempre diz POR QUE a nomeação foi desfeita. É a informação que o
# concurseiro mais quer ("desistiu" é muito diferente de "erro na portaria"), e
# sai de graça do mesmo texto. Quando o ato não declara, fica vazio — nunca
# chutamos um motivo.
MOTIVOS = {
 "desistencia": (
    "Art. 1 Tornar sem efeito, em razao de apresentacao de termo de desistencia, a nomeacao do "
    "candidato PEDRO HENRIQUE SOUZA, para o cargo de Analista Judiciario, Especialidade Tecnologia "
    "da Informacao.", "Desistência"),
 "nao tomou posse": (
    "Art. 1 Tornar sem efeito a nomeacao de MARIA CLARA DE ANDRADE, por nao ter tomado posse no "
    "prazo legal, no cargo de Tecnico Judiciario, Especialidade Programacao de Sistemas.",
    "Não tomou posse no prazo"),
 "pericia medica": (
    "Art. 1 TORNAR SEM EFEITO, por ausencia em pericia medica, a nomeacao de MARCOS ALVES DE "
    "OLIVEIRA, nomeado pela Portaria TRE-SP n. 209/2025, ao cargo de Analista Judiciario - Area "
    "Apoio Especializado - Especialidade Tecnologia da Informacao.", "Perícia médica"),
 "sem motivo declarado": (
    "Art. 1 Tornar sem efeito a Portaria de Pessoal n 504, de 23 de Julho de 2026, referente a "
    "nomeacao do candidato YTALLO AUGUSTO SANTOS LIMA, para o cargo de Tecnico Judiciario.", ""),
}


def main():
    ok = True
    for tag, (txt, esperado) in MOTIVOS.items():
        got = [a.get("motivo", "<sem campo>") for a in extrair_anulacoes(txt)]
        bateu = got == [esperado]
        if not bateu: ok = False
        print(f'[{"OK  " if bateu else "FALHA"}] motivo: {tag} -> {got!r}')
        if not bateu:
            print(f"       esperado: [{esperado!r}]")

    for tag, (txt, esperado) in CASOS.items():
        got = [a["nome"] for a in extrair_anulacoes(txt)]
        falta = [n for n in esperado if n not in got]
        extra = [n for n in got if n not in esperado]
        status = "OK  " if (not falta and not extra) else "FALHA"
        if falta or extra: ok = False
        print(f"[{status}] {tag}")
        print(f"       -> {got}")
        if falta: print(f"       faltou: {falta}")
        if extra: print(f"       FALSO POSITIVO: {extra}")

    for tag in NAO_NOMEIA:
        txt = CASOS[tag][0]
        nomes = [r["nome"] for r in extrair_nomeados(txt)]
        status = "OK  " if not nomes else "FALHA"
        if nomes: ok = False
        print(f"[{status}] ato de anulacao nao vira nomeacao: {tag[:30]} -> {nomes}")

    print("\n==> ANULACOES OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
