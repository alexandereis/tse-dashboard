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
 "RN 277 (real: nome com 7 palavras nao pode ser descartado)": (
    "Art. 1 NOMEAR, com fundamento no inciso I do art. 9 da Lei n 8.112, de 11 de dezembro de 1990 e "
    "observada a ordem de classificacao, em razao de habilitacao no Concurso Publico Nacional "
    "Unificado da Justica Eleitoral, a candidata Indi Li da Silva Alves Moreira Tenorio, para "
    "exercer, em carater efetivo, neste Tribunal, o cargo de Tecnico Judiciario - Area Apoio "
    "Especializado - Programacao de Sistemas, Classe A, Padrao 1, criado pela Lei n 8.215/1991, "
    "vago em decorrencia da aposentadoria do servidor Epitacio Nunes da Silva Junior, conforme a "
    "Portaria PRES TRE/RN n. 12, de 24 de janeiro de 2025. Art. 2 A candidata nomeada tera o prazo "
    "de 30 (trinta) dias para tomar posse no cargo.", ["Indi Li da Silva Alves Moreira Tenorio"]),
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
 "SP (nome com 7 palavras sai inteiro, nao truncado)": (
    "NOMEAR, para o Cargo de Tecnico Judiciario, Area Apoio Especializado, Especialidade Programacao "
    "de Sistemas, os seguintes: Maria Aparecida da Conceicao de Oliveira Santos, 10a colocacao; "
    "Laize Pereira Santos, 11a colocacao.",
    ["Maria Aparecida da Conceicao de Oliveira Santos", "Laize Pereira Santos"]),
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
 "AM 1.090 (item numerado: o 'I -' nao faz parte do nome)": (
    "Art. 1. NOMEAR, em carater efetivo, no cargo de Tecnico Judiciario, Apoio Especializado, "
    "Programacao de Sistemas, classe A, padrao 1, para integrar o Quadro de Pessoal Permanente "
    "deste Tribunal Regional Eleitoral do Amazonas, o candidato habilitado no Concurso Publico "
    "Nacional Unificado da Justica Eleitoral: I - DIEGO AQUINO DE SOUSA Cargo: Tecnico Judiciario, "
    "Apoio Especializado, Programacao de Sistemas, classe A, padrao 1 Origem da vaga: Falecimento "
    "do servidor JOSE GALDINO DE MENEZES, vaga n 5.", ["Diego Aquino de Sousa"]),

 "PE 905 (real: tabela 'cargos de:' com Especialidade: e origem da vaga em cada linha)": (
    "O DESEMBARGADOR PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE PERNAMBUCO resolve: Art. 1 NOMEAR, "
    "em carater efetivo, observada a ordem de classificacao, em razao de habilitacao no Concurso "
    "Publico Nacional Unificado da Justica Eleitoral, as candidatas e os candidatos a seguir "
    "discriminadas e discriminados para exercerem, neste Tribunal, os cargos de: "
    "Analista Judiciario, Area de Apoio Especializado, Especialidade: Tecnologia da Informacao, "
    "Classe A, Padrao 1: Nome Classificacao/Lista Origem da Vaga "
    "LUCAS ARAUJO PAZ 2 lugar - Ampla concorrencia Provimento inicial do 1 cargo de Analista "
    "Judiciario criado pela Lei n 15.374, de 2 de Abril de 2026. "
    "UBIRACY DOS SANTOS REGO JUNIOR 2 lugar - Negro Provimento inicial do 2 cargo de Analista "
    "Judiciario criado pela Lei n 15.374. "
    "Analista Judiciario, Area Administrativa, Classe A, Padrao 1: Nome Classificacao/Lista Origem "
    "da Vaga ANNA CATHARINA QUEIROZ DO NASCIMENTO MALHEIROS 1 lugar - Negro Provimento inicial do 3 "
    "cargo de Analista Judiciario criado pela Lei. LENILTON CASSIANO DA SILVA 4 lugar - Ampla "
    "concorrencia Provimento inicial do 4 cargo de Analista Judiciario criado pela Lei. "
    "Tecnico Judiciario, Area de Apoio Especializado, Especialidade: Programacao de Sistemas, "
    "Classe A, Padrao 1: Nome Classificacao/Lista Origem da Vaga "
    "RODRIGO RAMGUND LEITE 5 lugar - Ampla concorrencia Provimento inicial do 7 cargo de Tecnico "
    "Judiciario criado pela Lei. LEANDRO CORREIA DA SILVA 6 lugar - Ampla concorrencia Provimento "
    "inicial do 8 cargo de Tecnico Judiciario criado pela Lei. "
    "Art. 2 Registrar que o candidato UBIRACY DOS SANTOS REGO JUNIOR, classificado em 2 lugar na "
    "lista de pessoas negras para o cargo de Analista Judiciario, Especialidade: Tecnologia da "
    "Informacao, esta sendo nomeado tendo em vista a desistencia formalizada pelo candidato "
    "WILLIAMS CALIXTO LEAO, classificado em 1 lugar na mesma lista. "
    "Art. 5 Salientar que, tendo em vista a desistencia do candidato HELDER MANOEL LIMA E SILVA, "
    "primeiro e unico classificado na lista de portadores de deficiencia para o cargo de Tecnico "
    "Judiciario, Especialidade: Programacao de Sistemas, seguiu-se a ordem das convocacoes.",
    ["Lucas Araujo Paz", "Ubiracy dos Santos Rego Junior", "Rodrigo Ramgund Leite",
     "Leandro Correia da Silva"]),
 "PA 25.151 (real: 435 caracteres entre o nome e o cargo)": (
    "Art. 1 TORNAR SEM EFEITO a nomeacao de MARCELO NASCIMENTO MOUTINHO, por intermedio da Portaria "
    "n 25.019/2026, publicada no DOU, em 24/07/2026, no cargo de Tecnico Judiciario, Area Apoio "
    "Especializado, Especialidade em Programacao de Sistemas, por desistencia provisoria expressa. "
    "Art. 2 NOMEAR as candidatas habilitadas em Concurso Publico Nacional Unificado da Justica "
    "Eleitoral de Provas realizado pelo Cebraspe, para provimento de cargos deste Tribunal, cujo "
    "resultado foi homologado pelo Edital n 38, de 01/07/2025, publicado no DOU, em 02/07/2025, "
    "para exercerem, em carater efetivo, nos termos do artigo 9, inciso I, da Lei n 8.112, de "
    "11/12/1990, o cargo de ANALISTA JUDICIARIO, AREA JUDICIARIA, NS, Classe A, Padrao 1, do Quadro "
    "de Pessoal Permanente: I - NAYANNE PEREIRA VENTURA GUAJAJARA, em vaga destinada a Pessoa "
    "Indigena; e II- ERICA FERREIRA DOS SANTOS, em vaga destinada a Pessoa Negra. "
    "Art. 3 NOMEAR o candidato THALES HENRIQUE GOMES LOBATO, habilitado em Concurso Publico Nacional "
    "Unificado da Justica Eleitoral de Provas realizado pelo Centro Brasileiro de Pesquisa em "
    "Avaliacao e Selecao e Promocao de Eventos - Cebraspe, para provimento de cargos deste Tribunal, "
    "cujo resultado foi homologado pelo Edital n 33, de 27/05/2025, publicado no DOU, em 28/05/2025, "
    "para exercer, em carater efetivo, nos termos do artigo 9, inciso I, da Lei n 8.112, de "
    "11/12/1990, o cargo de TECNICO JUDICIARIO, AREA APOIO ESPECIALIZADO, ESPECIALIDADE EM "
    "PROGRAMACAO DE SISTEMAS, NS, Classe A, Padrao 1, do Quadro de Pessoal Permanente, em vaga "
    "criada pela Lei n 15.374/2026.", ["Thales Henrique Gomes Lobato"]),
 "CE 691 (real: Nomear NOME, CPF ..., 330 caracteres ate o cargo)": (
    "A PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DO CEARA, no uso das atribuicoes que lhe confere o "
    "Regimento Interno deste Tribunal, com fundamento na Lei n. 8.112, de 11 de dezembro de 1990, "
    "considerando a homologacao do concurso publico realizado pelo Tribunal Superior Eleitoral, nos "
    "termos do Edital n. 33 - CPNUJE, resolve: Art. 1 Nomear RAUL RAMIRES LIMA OLIVEIRA, CPF n. "
    "***.815.633.**, aprovado em concurso publico e classificado em 3 lugar na lista especifica de "
    "candidatos cotistas, na vaga reservada aos candidatos autodeclarados pretos e pardos, indigenas "
    "e quilombolas, nos termos do Edital n. 1 - CPNUJE e da legislacao aplicavel, para exercer, em "
    "carater efetivo, o cargo de Tecnico Judiciario - Area Apoio Especializado - Especialidade "
    "Programacao de Sistemas, Classe A, Padrao 1, com exercicio na Assessoria de Ciberseguranca "
    "(CIBER), em cargo criado pela Lei n. 15.374, de 2 de abril de 2026, destinado ao primeiro "
    "provimento. Art. 2 Esta Portaria entra em vigor na data de sua publicacao.",
    ["Raul Ramires Lima Oliveira"]),
 "Dois nomeados num artigo so: o primeiro (Area Judiciaria) nao herda o cargo do segundo": (
    "Art. 1 NOMEAR: o candidato JOAO DA SILVA SANTOS, para exercer o cargo de Analista Judiciario, "
    "Area Judiciaria, Classe A, Padrao 1, do Quadro de Pessoal deste Tribunal; e a candidata MARIA "
    "DE SOUZA LIMA, habilitada no mesmo concurso, para exercer o cargo de Tecnico Judiciario, Area "
    "Apoio Especializado, Especialidade Programacao de Sistemas, Classe A.",
    ["Maria de Souza Lima"]),

 # --- NAO sao convocacao do concurso: nao podem entrar no painel -----------
 "MG 126 (servidor de TI trocando de FUNCAO COMISSIONADA)": (
    "O DESEMBARGADOR PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE MINAS GERAIS resolve: "
    "Art. 1 Dispensar ANDRE ALVES DE ALENCAR, Tecnico Judiciario, Area Apoio Especializado - "
    "Operacao de Computadores, do Quadro de Pessoal deste Tribunal, do exercicio da Funcao "
    "Comissionada FC-03, na Secao de Suporte Operacional. Art. 2 Exonerar, a pedido, JOAO PAULO "
    "FERREIRA PINTO, Tecnico Judiciario, Area Administrativa, do Quadro de Pessoal deste Tribunal, "
    "do exercicio do Cargo em Comissao CJ-2, na Coordenadoria de Suporte e Equipamentos. "
    "Art. 3 Nomear ANDRE ALVES DE ALENCAR, Tecnico Judiciario, Area Apoio Especializado - Operacao "
    "de Computadores, do Quadro de Pessoal deste Tribunal, para o exercicio do Cargo em Comissao "
    "CJ-2, na Coordenadoria de Suporte e Equipamentos.", []),

 "MG 206 (NOMEAR servidor efetivo para CARGO EM COMISSAO CJ-2)": (
    "Art. 1 Exonerar, a pedido, ANDRE ALVES DE ALENCAR, Tecnico Judiciario, Apoio Especializado - "
    "Operacao de Computadores, do exercicio do Cargo em Comissao CJ-2, na Coordenadoria de Suporte. "
    "Art. 2 Nomear FREDERICO GOMES JABBUR, Analista Judiciario, Apoio Especializado - Analise de "
    "Sistemas - Suporte, do Quadro de Pessoal deste Tribunal, para o exercicio do Cargo em Comissao "
    "CJ-2, na Coordenadoria de Suporte e Equipamentos.", []),

 "MG (CARGO EM COMISSAO com referencia a lei antes do CJ-2 nao vira convocacao)": (
    "Art. 1 Dispensar ANDRE ALVES DE ALENCAR da funcao. Art. 2 Nomear FREDERICO GOMES JABBUR, "
    "Analista Judiciario, Apoio Especializado - Analise de Sistemas, do Quadro de Pessoal deste "
    "Tribunal, nos termos do art. 9, inciso II, da Lei n 8.112/1990, para o exercicio do Cargo em "
    "Comissao CJ-2, na Coordenadoria de Suporte e Equipamentos.", []),

 "BA retificacao (real: so vale o 'Leia-se'; o 'Onde se le' tem a grafia errada)": (
    "RETIFICACAO Na PORTARIA N 488, DE 25 DE JULHO DE 2025, DO PRESIDENTE DO TRIBUNAL REGIONAL "
    "ELEITORAL DA BAHIA, que trata do ato de nomeacao de EVERTON SIMOES BARRETTO. Onde se le: "
    "\" Art. 1 Nomear o candidato EVERTON SIMOES BARRETO, 3 convocado, classificado em 1 lugar na "
    "lista de vagas reservadas, para ocupar o cargo de Tecnico Judiciario - Area: Apoio "
    "Especializado, Especialidade: Programacao de Sistemas, Classe A. \" Leia-se: \" Art. 1 Nomear "
    "o candidato EVERTON SIMOES BARRETTO, 3 convocado, classificado em 1 lugar na lista de vagas "
    "reservadas, para ocupar o cargo de Tecnico Judiciario - Area: Apoio Especializado, "
    "Especialidade: Programacao de Sistemas, Classe A. \"", ["Everton Simoes Barretto"]),

 "SP 108 (bloco de Area Administrativa nao herda a especialidade de TI)": (
    "Art. 1 TORNAR SEM EFEITO a nomeacao de HUGO SOUSA DA SILVA, nomeado pela Portaria TRE-SP "
    "n.95/2026, no cargo de Analista Judiciario - Area Apoio Especializado - Especialidade "
    "Tecnologia da Informacao. Art. 2 NOMEAR, por concurso, em estagio probatorio, para os cargos "
    "relacionados abaixo: Analista Judiciario - Area Administrativa, Classe A, Padrao 1: Nos termos "
    "do art. 9, inciso I, da Lei n. 8.112/1990 LUAN PUTINATI LORENCETTI, 10 colocacao, na vaga n. "
    "633, criada pela Lei n. 10842/2004.", []),

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

def caso_especialidade_caixa_alta_sai_igual_a_dos_outros():
    """O TRE-PA escreve o cargo inteiro em CAIXA ALTA. A especialidade guardada
    tem de sair como a dos outros tribunais — senão a mesma especialidade vira
    duas na exportação do painel."""
    txt = CASOS["PA 25.151 (real: 435 caracteres entre o nome e o cargo)"][0]
    esps = [r["especialidade"] for r in extrair_nomeados(txt)]
    # (o texto dos casos é sem acento, como o resto deste arquivo)
    return [] if esps == ["Programacao de Sistemas"] else [f"veio {esps}"]


def main():
    ok = True
    problemas = caso_especialidade_caixa_alta_sai_igual_a_dos_outros()
    if problemas:
        ok = False
        print("[FALHA] especialidade em CAIXA ALTA sai capitalizada")
        for p in problemas:
            print(f"        {p}")
    else:
        print("[OK  ] especialidade em CAIXA ALTA sai capitalizada")
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
