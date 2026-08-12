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
 "A/DF (inline c/ classificacao)": (
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
 "RN (preambulo longo)": (
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
 "AM (multi-area, Cargo:; exclui Administrativa e servidora)": (
    "NOMEAR, no cargo de Tecnico Judiciario, Area Administrativa, bem como de Apoio Especializado, "
    "os seguintes candidatos DANIEL RODRIGUES CHAGAS JUNIOR Cargo: Tecnico Judiciario, Area "
    "Administrativa, classe A Origem da vaga Redistribuicao da servidora SOLANGE MADEIRO DA COSTA, "
    "vaga 112. MARCOS CARDOSO WAGNER Cargo: Tecnico Judiciario, Apoio Especializado, Programacao de "
    "Sistemas classe A. PEDRO MELLO DAUER Cargo: Tecnico Judiciario, Apoio Especializado, "
    "Programacao de Sistemas classe A.", ["Marcos Cardoso Wagner", "Pedro Mello Dauer"]),
 "GO (lista 1. NOME - 1o lugar; exclui servidora)": (
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
 "PE (NOME No lugar; bloco nao-TI ignorado; exclui aposentada)": (
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
 "SP 2 secoes (Programacao=TI + Administrativa=nao-TI)": (
    "NOMEAR, por concurso publico, os candidatos: Cargo de Tecnico Judiciario, Area Apoio "
    "Especializado, Especialidade Programacao de Sistemas, Classe A, Padrao 1 Hibernon Olegario da "
    "Silva Junior, 116a colocacao, na vaga n. 99, criada pela Lei. Cargo de Tecnico Judiciario - "
    "Area Administrativa, Classe A, Padrao 1 Nos termos do art. 9 inciso I da Lei 8.112/1990 "
    "Laize Fernanda Pereira, 117a colocacao, na vaga n. 140, decorrente de aposentadoria de Roberto "
    "Jorge Raya em 19/08/2025. Leticia Mendonca Rossetti Silva, 118a colocacao, decorrente de "
    "aposentadoria de Rosangela Aparecida Ribeiro. Adriana Brandassi, 119a colocacao. Eduardo "
    "Cassoli Ferraz, 120a colocacao. Aparecido Santos Tomazin Junior, 121a colocacao.",
    ["Hibernon Olegario da Silva Junior"]),
 "SP (Fulano, Na colocacao)": (
    "NOMEAR, para o Cargo de Tecnico Judiciario, Area Apoio Especializado, Especialidade Programacao "
    "de Sistemas, os seguintes: Hibernon Olegario da Silva Junior, 10a colocacao; Laize Pereira "
    "Santos, 11a colocacao.", ["Hibernon Olegario da Silva Junior", "Laize Pereira Santos"]),
 "DF 152 multi-art (Formato A nao cruza artigo; exclui Eng. Mecanica)": (
    "Art. 8 Tornar sem efeito a nomeacao do candidato Fulano de Tal, Especialidade Tecnologia da "
    "Informacao, em razao de termo de desistencia. Art. 9 Nomear o candidato Joao Batista Grigorio "
    "de Almeida, classificado em 10 lugar, na vaga n. 5, criada pela Lei n. 15.374 2026, decorrente "
    "de aposentadoria de Sicrano. Art. 10 Nomear o candidato Marcos Antonio Pinheiro Silva, "
    "classificado em 12 lugar, para exercer o cargo de Analista Judiciario, Area Apoio Especializado, "
    "Especialidade Tecnologia da Informacao, criado pela Lei n. 15.374 2026.",
    ["Marcos Antonio Pinheiro Silva"]),
 "MG PRE multi-art (ocupar na Secretaria; exclui servidores anteriores)": (
    "Art. 1 NOMEAR o candidato JHEFFREY THULYO DOS SANTOS, classificado em 1 lugar, no Concurso "
    "Publico Nacional Unificado da Justica Eleitoral, para ocupar na Secretaria o cargo de Analista "
    "Judiciario, Area Apoio Especializado - Especialidade Tecnologia da Informacao, Classe A, vago "
    "em decorrencia de aposentadoria do servidor Sergio Ubiratan Jeronimo Silva Araujo. Art. 2 "
    "NOMEAR a candidata LUCIANA LORENA RODRIGUES, classificada em 3 lugar, no Concurso Publico "
    "Nacional Unificado da Justica Eleitoral, para ocupar na Secretaria o cargo de Analista "
    "Judiciario, Area Apoio Especializado - Especialidade Tecnologia da Informacao, vago em "
    "decorrencia de posse de Marcelo Mascarenhas Ribeiro de Araujo.",
    ["Jheffrey Thulyo dos Santos", "Luciana Lorena Rodrigues"]),
 "PA 25019 multi-art (romanos I-, Especialidade EM; so Art.3 e TI)": (
    "Art. 1 NOMEAR as(os) candidatas(os) habilitadas(os) em Concurso Publico Nacional Unificado da "
    "Justica Eleitoral, para exercerem o cargo de ANALISTA JUDICIARIO, AREA JUDICIARIA, NS, Classe A: "
    "I - GIULIANA FIDELLES MARANHAO MARINHO, em vaga criada pela Lei 15.374/2026; "
    "II - HADRIA DO SOCORRO PINTO CORREA, em vaga destinada a Pessoa Negra. "
    "Art. 2 NOMEAR os candidatos habilitados, para exercer o cargo de ANALISTA JUDICIARIO, AREA "
    "ADMINISTRATIVA, ESPECIALIDADE EM CONTABILIDADE, NS, Classe A: "
    "I - JOHN LINCON DA SILVA NEVES, em vaga destinada a Pessoa Negra; e "
    "II - CARLOS EDUARDO BANDEIRA DOS SANTOS, em vaga criada pela Lei. "
    "Art. 3 NOMEAR os candidatos habilitados em Concurso Publico Nacional Unificado da Justica "
    "Eleitoral, para exercer o cargo de TECNICO JUDICIARIO, AREA APOIO ESPECIALIZADO, ESPECIALIDADE "
    "EM PROGRAMACAO DE SISTEMAS, NS, Classe A, Padrao 1: "
    "I - MARCELO NASCIMENTO MOUTINHO em vaga criada pela Lei 15.374/2026; e "
    "II - HEALLEY ARDASSE MONTEIRO, em vaga destinada a Pessoa Negra.",
    ["Marcelo Nascimento Moutinho", "Healley Ardasse Monteiro"]),
 "Especialidade limpa (Apoio Especializado, Especialidade X)": (
    "NOMEAR o(a) candidato(a) JOAO TESTE DA SILVA, classificado(a) em 1 lugar, para ocupar o cargo "
    "de Analista Judiciario, Area de Apoio Especializado, Especialidade Analise de Sistemas de "
    "Informacao, Classe A.", ["Joao Teste da Silva"]),
 "Area longa entre cargo e Especialidade": (
    "NOMEAR o(a) candidato(a) MARIA TESTE SOUZA, classificado(a) em 1 lugar, para ocupar o cargo de "
    "Analista Judiciario, Area de Apoio Especializado em Tecnologia da Informacao e Comunicacao, "
    "Especialidade Analise de Sistemas de Informacao, Classe A, Padrao 1, do Quadro de Pessoal.",
    ["Maria Teste Souza"]),
 "SE 512 (preambulo longo + Apoio Especializado - Especialidade X)": (
    "A PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE SERGIPE, no exercicio de suas atribuicoes, "
    "CONSIDERANDO a Portaria TSE n 229, de 20 de maio de 2026, que autoriza o provimento dos cargos "
    "efetivos criados pela Lei n 15.374; e CONSIDERANDO a Resolucao Normativa TRE/SE n 76, de 18 de "
    "junho de 2026, que dispoe sobre a implementacao dos cargos efetivos, resolve: "
    "Art. 1 NOMEAR o(a) candidato(a) VICTOR COSTA DE ALEMAO CISNEIROS, classificado(a) em 1 lugar no "
    "Concurso Publico de Provas, destinado ao provimento das vagas deste Tribunal, para ocupar o cargo "
    "de Analista Judiciario, Area Apoio Especializado - Especialidade Tecnologia da Informacao, "
    "Classe A, Padrao 1, do Quadro de Pessoal deste Tribunal.",
    ["Victor Costa de Alemao Cisneiros"]),
 "SE 535 (sub judice + typo do DOU: candidaDo(a))": (
    "A PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE SERGIPE, CONSIDERANDO a Portaria TSE n 229; e "
    "CONSIDERANDO a Resolucao Normativa TRE/SE n 76; CONSIDERANDO o Processo Judicial da 1a Vara "
    "Federal, resolve: Art. 1 NOMEAR, na condicao de sub judice, o(a) candidado(a) JEIRLAN CORREIA "
    "PALMEIRA, classificado(a) em 2 lugar na lista da ampla concorrencia no Concurso Publico de Provas "
    "e Titulos, destinado ao provimento das vagas deste Tribunal, para ocupar o cargo de Analista "
    "Judiciario, Area Apoio Especializado - Especialidade Tecnologia da Informacao, Classe A, Padrao 1.",
    ["Jeirlan Correia Palmeira"]),
 "PR 266 (alineas a) e b) - dois nomeados num NOMEAR so)": (
    "Art. 1 NOMEAR, em virtude de habilitacao em Concurso Publico regido pelo Edital n. 01 - CPNUJE, "
    "de 27 de maio de 2024: a) o candidato JOSE HENRIQUE DOMETERCO, classificado em 2 lugar no concurso "
    "destinado ao provimento das vagas deste Tribunal, para ocupar o cargo de Analista Judiciario, Area "
    "de Apoio Especializado - Tecnologia da Informacao, Classe A, Padrao 01, do Quadro de Pessoal deste "
    "Tribunal, no cargo criado pela Lei n. 15.374, nunca provido. b) a candidata AMANDA MONTEIRO GALVAO, "
    "classificada em 1 lugar (na lista prevista pelo item 5.2 do Edital n. 1/2024), no concurso destinado "
    "ao provimento das vagas deste Tribunal, para ocupar o cargo de Analista Judiciario, Area de Apoio "
    "Especializado - Tecnologia da Informacao, Classe A, Padrao 01, do Quadro de Pessoal.",
    ["Jose Henrique Dometerco", "Amanda Monteiro Galvao"]),
}

def main():
    ok = True
    for tag, (txt, esperado) in CASOS.items():
        got = [r["nome"] for r in extrair_nomeados(txt)]
        falta = [n for n in esperado if n not in got]
        extra = [n for n in got if n not in esperado]
        status = "OK  " if (not falta and not extra) else "FALHA"
        if falta or extra: ok = False
        print(f"[{status}] {tag}")
        print(f"       -> {got}")
        if falta: print(f"       faltou: {falta}")
        if extra: print(f"       FALSO POSITIVO: {extra}")
    print("\n==> TODOS OS FORMATOS OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
