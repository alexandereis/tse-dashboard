# -*- coding: utf-8 -*-
"""
Testes de regressão do parser: um trecho real (resumido) de cada FORMATO de
portaria que os órgãos publicam, com os nomes que devem (e que NÃO devem) sair.
Rode com:  python3 test_parser.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import extrair_nomeados

CASOS = {
 "A/DF (inline c/ classificação)": (
    "Nomear o candidato Fabio Henrique da Silva, classificado em 1o lugar, para ocupar o cargo "
    "efetivo de Analista Judiciario, Area Apoio Especializado, Especialidade: Tecnologia da "
    "Informacao, do Quadro de Pessoal.", ["Fabio Henrique da Silva"]),
 "AP (texto entre Nomear e o nome)": (
    "Art. 1 NOMEAR, em carater efetivo, em virtude de habilitacao em concurso publico, o candidato "
    "ROBERTO BRUNO PONTES DOS SANTOS, classificado em 5o lugar, para exercer o cargo de Tecnico "
    "Judiciario, Area Apoio Especializado, Especialidade Programacao de Sistemas.",
    ["Roberto Bruno Pontes dos Santos"]),
 "ES (o Sr. Fulano, para o cargo de)": (
    "Nomear, com fundamento no artigo 8, o Sr. Bruno Siqueira Andrade, para o cargo de Tecnico "
    "Judiciario - Area Apoio Especializado - Especialidade Programacao de Sistemas, Classe A.",
    ["Bruno Siqueira Andrade"]),
 "MS (sem palavra Especialidade)": (
    "NOMEAR, nos termos do art. 9, a candidata CINTIA STSUKO OGATHA, classificada em 1 lugar, para "
    "exercer o cargo da carreira judiciaria de Tecnico Judiciario - Apoio Especializado - "
    "Programacao de Sistemas.", ["Cintia Stsuko Ogatha"]),
 "PB (Apoio Especializado - X)": (
    "Art. 1 Nomear o candidato KELSON SARMENTO DUARTE, classificado em 1 lugar da lista geral, para "
    "exercer o cargo de Tecnico Judiciario - Apoio Especializado - Programacao de Sistemas, Classe A.",
    ["Kelson Sarmento Duarte"]),
 "SC (Nomear NOME direto)": (
    "Art. 1 Nomear RAFAEL SILVEIRA DA SILVA, em virtude de habilitacao, para exercer o cargo da "
    "categoria funcional de Analista Judiciario, Area Apoio Especializado, Especialidade Tecnologia "
    "da Informacao.", ["Rafael Silveira da Silva"]),
 "SE (o(a) candidato(a))": (
    "NOMEAR o(a) candidato(a) RAFAEL SOUZA SANTOS, classificado(a) em 2 lugar de candidatos negros, "
    "para ocupar o cargo de Tecnico Judiciario, Area de Apoio Especializado, Especialidade "
    "Programacao de Sistemas, Classe A.", ["Rafael Souza Santos"]),
 "RN (preâmbulo longo)": (
    "Art. 1 NOMEAR, com fundamento no inciso I do art. 9 da Lei 8.112, de 11 de dezembro de 1990 e "
    "observada a ordem de classificacao, em razao de habilitacao no Concurso Publico Nacional "
    "Unificado da Justica Eleitoral, a candidata ADRIANA BENICIO GALVAO, para exercer, em carater "
    "efetivo, o cargo de Analista Judiciario, Area Apoio Especializado, Especialidade Analise de "
    "Sistemas de Informacao, Classe A.", ["Adriana Benicio Galvao"]),
 "AC (caixa alta; exclui servidor anterior)": (
    "NOMEAR os candidatos abaixo mencionados, os cargos de Tecnico Judiciario - Area Apoio "
    "Especializado, Especialidade Programacao de Sistemas, respectivamente JONATHAN MESSIAS E SILVA "
    "Tecnico Judiciario - Area Apoio Especializado, Especialidade Programacao de Sistemas, cargo "
    "criado pela Lei 11.202, vago em razao da redistribuicao do servidor Frankley Francalino da "
    "Rocha; e FELIPE BEZERRA LIMA Tecnico Judiciario - Area Apoio Especializado, Especialidade "
    "Programacao de Sistemas.", ["Jonathan Messias e Silva", "Felipe Bezerra Lima"]),
 "AM (multi-área, Cargo: ...; exclui Administrativa e servidora)": (
    "NOMEAR, no cargo de Tecnico Judiciario, Area Administrativa, bem como de Apoio Especializado, "
    "os seguintes candidatos DANIEL RODRIGUES CHAGAS JUNIOR Cargo: Tecnico Judiciario, Area "
    "Administrativa, classe A Origem da vaga Redistribuicao da servidora SOLANGE MADEIRO DA COSTA, "
    "vaga 112. MARCOS CARDOSO WAGNER Cargo: Tecnico Judiciario, Apoio Especializado, Programacao de "
    "Sistemas classe A. PEDRO MELLO DAUER Cargo: Tecnico Judiciario, Apoio Especializado, "
    "Programacao de Sistemas classe A.", ["Marcos Cardoso Wagner", "Pedro Mello Dauer"]),
 "GO (lista 1. NOME - 1º lugar; exclui servidora)": (
    "NOMEAR os candidatos abaixo relacionados, o cargo de Tecnico Judiciario - Area Apoio "
    "Especializado - Programacao de Sistemas. 1. JULIO CESAR FREITAS BUENO DE MORAES - 1 lugar da "
    "lista de cotas. Vaga 207. Cargo criado pela Lei 10.842, ocupado pela servidora Samyle Santos "
    "do Carmo. 2. ARTHUR ABREU DE ANDRADE - 2 lugar.",
    ["Julio Cesar Freitas Bueno de Moraes", "Arthur Abreu de Andrade"]),
 "MA (tabela; exclui ocupantes anteriores)": (
    "Cargo de Tecnico Judiciario, Area de Atividade Apoio Especializado, Especialidade Programacao "
    "de Sistemas Ordem de Convocacao Nome 1 ANDRE BORBA NETTO ASSIS 1 Lugar - AMPLA Vaga 141, "
    "decorrente de vacancia por posse de LUIZ GONZAGA DE ALBUQUERQUE NETO, em 02 12 2022. 2 "
    "DOUGLLAS MOREIRA DINIZ 2 Lugar - AMPLA Vaga 17, decorrente de vacancia de SILVIO LACK LENZ "
    "CESAR.", ["Andre Borba Netto Assis", "Dougllas Moreira Diniz"]),
 "PE (NOME Nº lugar; bloco não-TI ignorado; exclui aposentada)": (
    "os cargos de Analista Judiciario, Especialidade Arquivologia, Nome Classificacao LUCAS LIMA "
    "SANTOS 1 lugar - Ampla concorrencia Cargo criado pela Lei 10.842, vago em decorrencia da "
    "aposentadoria de BENISE MARIA DE SOUZA. os cargos de Tecnico Judiciario, Especialidade "
    "Programacao de Sistemas, Nome Classificacao PEDRO HENRIQUE ALVES 1 lugar - Ampla concorrencia "
    "Cargo criado pela Lei. JOAO VITOR LIMA 2 lugar - Ampla Cargo criado pela Lei.",
    ["Pedro Henrique Alves", "Joao Vitor Lima"]),
 "TSE (NOME Cargo criado pela Lei; exclui exonerado)": (
    "Nomear, para exercer o cargo de Tecnico Judiciario, Area Apoio Especializado, Especialidade "
    "Programacao de Sistemas, Classe A, candidata candidato origem da vaga Matheus Martins do "
    "Nascimento Cargo criado pela Lei 7.385, vago em decorrencia da exoneracao de Rodrigo Augusto "
    "de Oliveira Paes Borges Bione, em 5 de maio de 2025. Gabriel Dantas de Oliveira Cargo criado "
    "pela Lei 11.202, vago.", ["Matheus Martins do Nascimento", "Gabriel Dantas de Oliveira"]),
 "SP (Fulano, Nª colocação)": (
    "NOMEAR, para o Cargo de Tecnico Judiciario, Area Apoio Especializado, Especialidade Programacao "
    "de Sistemas, os seguintes: Hibernon Olegario da Silva Junior, 10a colocacao; Laize Pereira "
    "Santos, 11a colocacao.", ["Hibernon Olegario da Silva Junior", "Laize Pereira Santos"]),
}

def main():
    ok = True
    for tag, (txt, esperado) in CASOS.items():
        got = [r["nome"] for r in extrair_nomeados(txt)]
        falta = [n for n in esperado if n not in got]
        extra = [n for n in got if n not in esperado]
        st = "OK  " if (not falta and not extra) else "FALHA"
        if falta or extra: ok = False
        print(f"[{st}] {tag}")
        print(f"       -> {got}")
        if falta: print(f"       faltou: {falta}")
        if extra: print(f"       FALSO POSITIVO: {extra}")
    print("\n==> TODOS OS FORMATOS OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
