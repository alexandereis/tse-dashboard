# Histórico de versões

Este arquivo registra as mudanças do painel ao longo do tempo. A versão atual
também aparece no rodapé do site.

O número segue o formato **MAIOR.MENOR.CORREÇÃO**:
- **MAIOR**: mudança grande, que altera bastante o funcionamento.
- **MENOR**: recurso novo, sem quebrar o que já existia.
- **CORREÇÃO**: pequenos ajustes e correções.

> Dica: no GitHub você pode marcar cada versão em **Releases → Create a new
> release**, criando uma "tag" (ex.: `v1.1.0`). Assim fica fácil voltar a uma
> versão anterior se precisar.

---

## [1.17.5] — 2026-09-04

**Duas nomeações do TRE-AM desfeitas em setembro de 2025 constavam como
válidas há quase um ano**

A varredura chegou a 12/09/2025 (256 dias úteis, 3.548 atos da Justiça
Eleitoral, 212 nomeados de TI, **nenhum fora da base**) e encontrou a
Portaria 917 do **TRE-AM**, de 25/09/2025: "TORNAR SEM EFEITO a nomeação de
**Leonardo Silva Almeida e de Francisco Adalberto Rocha Junior**, no cargo de
Técnico Judiciário … Programação de Sistemas … nomeados por meio da Portaria
nº 727/2025". Os dois estavam no painel como **convocados válidos desde
30/07/2025**. É exatamente o formato "Fulano e de Ciclano" que a 1.17.4
ensinou o parser a separar — na época da 1.16.0 o bloco de 9 palavras era
descartado inteiro, e ninguém saía. O ato não declara motivo.

Também entrou a Portaria 2.582 do **TRE-RS** (30/01/2026), que desfaz uma
nomeação de Técnico da Área Administrativa (fora de TI) "conforme disposto no
**§ 6º do art. 13** da Lei 8.112": a fórmula legal na ordem invertida agora
também conta como motivo "Não tomou posse no prazo".

**Dados**
- **284** nomeações em vigor (eram 286), **315** convocações publicadas,
  **31** tornadas sem efeito (eram 29). Arquivo de anulações: 95 → 98.
- Reparsagem dos 98 registros de anulação com o parser final: zero diferenças.
- Testes: +1 caso de motivo (ordem invertida, texto real do TRE-RS).

## [1.17.4] — 2026-09-04

**Anulação em lista e "Fulana e de Ciclano": o parser lia só o primeiro nome**

A varredura da 1.17.3 continuou para trás (até 18/03: 123 dias úteis, 1.912
atos da Justiça Eleitoral, 127 nomeados de TI, **nenhum fora da base**) e
trouxe dois formatos de ato de anulação que o parser não lia inteiros:

- **Lista num único "tornar sem efeito"** (TSE, Portaria 146 de 15/04/2026):
  "…a nomeação dos candidatos: **I -** Fulano, constante da Portaria nº 100…;
  **II -** Ciclano, …". Só o primeiro nome saía, e ainda com o "I -" colado.
  Agora cada item é lido por conta própria, com a portaria que **ele** cita.
- **Duas pessoas numa frase** (TRE-SP, Portaria 207 de 01/09/2025): "a
  nomeação de **Letícia … e de Jonathan …**". Antes o bloco de 10 palavras era
  descartado e ninguém entrava; com o limite novo da 1.17.1 entraria como uma
  pessoa que não existe. Agora "e de/da/do" separa os dois.

Nenhum dos quatro é de TI (Polícia Judicial e Área Administrativa), então o
painel não muda — mas o formato existe, e da próxima vez pode ser alguém de
TI. Reparsagem dos 91 registros de anulação conhecidos: zero diferenças.

**Dados**
- Arquivo de anulações: 91 → 95 (2 do TSE, 2 do TRE-SP). Base inalterada:
  286 em vigor, 315 publicadas, 29 sem efeito.
- Testes: +2 casos de anulação com texto real (TSE 146 e TRE-SP 207).

## [1.17.3] — 2026-09-04

**Duas nomeações do TRE-RJ estavam no painel como válidas, mas tinham sido
desfeitas em julho**

A correção do divisor de artigos (1.17.1) foi posta à prova numa **varredura
edição por edição do DOU**, de trás para frente a partir de 04/09, com o parser
novo. Até 02/07 (47 dias úteis, 823 atos da Justiça Eleitoral), ela encontrou
**quatro atos que tornam sem efeito uma nomeação** e que o parser antigo tinha
perdido — todos pelo mesmo motivo: "Tornar sem efeito, **com fundamento no
art. 13, § 6º**, da Lei 8.112…" ou "Tornar sem efeito **o art. 3º** da Portaria
135…". A referência ao artigo de lei partia o texto e separava o "tornar sem
efeito" do nome.

Dois deles atingem nomeações de TI que **estavam no painel como válidas há
quase dois meses**:

- **Anderson Alves Pereira** — TRE-RJ, Técnico Judiciário (Programação de
  Sistemas), nomeado pelo Ato 149 de 29/05/2026; nomeação tornada sem efeito
  pelo Ato 216 de 08/07/2026.
- **Gabriel Binda Lima** — TRE-RJ, Técnico Judiciário (TI), nomeado pelo Ato
  148 de 29/05/2026; nomeação tornada sem efeito pelo Ato 215 de 08/07/2026.
  Ele foi **nomeado de novo como Analista** pelo Ato 278 de 21/08/2026, e essa
  nomeação **continua valendo** — a regra da portaria exata (1.16.0) fez o que
  prometia.

Os outros dois (TRE-RJ, Ato 217; TRE-MS, Portaria 161) são de candidatos de
outras áreas e entram só no arquivo de anulações.

**Motivo por fórmula legal.** Esses atos não escrevem "não tomou posse": citam
o **art. 13, § 6º, da Lei 8.112/90**, que é exatamente a regra que torna sem
efeito a nomeação de quem não toma posse no prazo. O parser agora reconhece
a citação e registra o motivo, em vez de "motivo não declarado".

**Dados**
- **286** nomeações em vigor (eram 288), **315** convocações publicadas, **29**
  tornadas sem efeito (eram 27). Arquivo de anulações: 87 → 91.
- A varredura segue rodando para trás até junho de 2025; o que mais aparecer
  entra num próximo ajuste de dados.
- Testes: +1 caso de motivo (art. 13, § 6º, texto real do TRE-RJ).

## [1.17.2] — 2026-09-04

**Correção — número da portaria desfeita e motivo da anulação**

Ao conferir a 1.17.1 contra todo o histórico de anulações (87 registros, 59
atos reabertos), apareceram dois problemas — um criado pela própria 1.17.1 e
um antigo:

**1) Ato sem "Art. 1º" lia o número errado.** O TRE-ES publica atos sem
artigos: cabeçalho, preâmbulo e "Tornar sem efeito…" num bloco só. Com o
divisor de artigos corrigido na 1.17.1, o número da portaria desfeita passou a
ser lido do **cabeçalho do próprio ato** (Ato 289 "desfazia" o Ato 289) — antes
só dava certo por acidente, porque a referência à lei no preâmbulo partia o
texto no lugar conveniente. Esse número é o que decide **qual** nomeação sai
quando a mesma pessoa foi nomeada duas vezes, então não pode estar errado.
Agora o parser procura o número **depois** do "tornar sem efeito" e, só se não
houver, a citação mais próxima antes dele; e "candidato" deixou de contar como
"ato" (um "candidato FULANO, classificado em 3º lugar" rendia portaria "3").

**2) O robô não gravava o motivo.** A 1.17.0 prometeu o motivo da anulação na
aba Movimentações, mas só a varredura daquela versão o gravava — as anulações
que o robô pegava depois saíam sem o campo, e a aba mostrava "motivo não
declarado" mesmo quando o ato dizia "desistência" com todas as letras. Foi o
caso das três do TRE-RS de 04/09. Corrigido nos dois caminhos do coletor (DOU e
Escavador), com teste.

**Dados**
- `data/anulacoes.json` reprocessado a partir dos próprios atos com o parser
  corrigido: 9 registros atualizados (2 do TRE-MT ganharam o número da portaria
  desfeita; 6 ganharam o motivo "Desistência"; 1 ganhou o campo vazio). Nenhum
  registro entrou ou saiu, e nenhuma nomeação de TI mudou de situação.
- Testes: 3 casos novos de número da portaria desfeita e 1 caso novo do
  coletor (motivo e portaria da anulação).

## [1.17.1] — 2026-09-04

**Correção — a nomeação do TRE-RN de 04/09 não apareceu**

A PORTARIA PRES 277 do **TRE-RN** (DOU de 04/09/2026) nomeou **Indi Li da Silva
Alves Moreira Tenorio** para Técnico Judiciário (Programação de Sistemas), e ela
não entrou no painel — a convocação do TRE-AP do mesmo dia entrou normalmente.

**O que aconteceu.** O parser lia a portaria certinho: achava o nome, o cargo e
a especialidade. Quem descartava era o **filtro de "nome válido"** — ele existe
para jogar fora trechos de texto capturados por engano, e só aceitava nomes de
**até 6 palavras**. Esse tem **7** (sobrenome composto mais o "da"). A nomeação
sumia em silêncio, sem erro nenhum. Doze nomes já na base têm exatamente 6
palavras; o limite estava no fio da navalha.

Agora o limite é **10 palavras** — os padrões de leitura já limitam o nome a
~70 caracteres e a lista de palavras proibidas continua barrando o que não é
nome de gente, então a folga não abre a porta para frase inteira. O mesmo teto
de 6 estava escondido em mais dois lugares, corrigidos juntos:

- No formato do **TRE-SP** ("Fulano, Nª colocação") um nome de 7 palavras não
  sumia: entrava **sem a primeira palavra**.
- Nos atos que **tornam sem efeito** uma nomeação, um nome de 7 palavras não era
  reconhecido — e a pessoa continuaria no painel como convocada.

**De quebra, mais um erro achado no caminho.** Uma referência a artigo de lei
dentro de um artigo da portaria ("…nos termos do **art. 13** da Lei 8.112…") era
tratada como se fosse o começo de um novo artigo, e o texto era partido no meio.
Para nomeação não fazia diferença (os pedaços são juntados de novo), mas para os
atos que **tornam sem efeito** fazia: o "tornar sem efeito" ficava num pedaço e o
nome no outro, e a anulação se perdia. Também fechava uma porta para falso
positivo: um servidor nomeado para **cargo em comissão** podia entrar como
convocado se a referência à lei viesse antes do "CJ-2". Agora só conta como
artigo da portaria o "Art. Nº" que vem depois do "resolve:" ou do ponto final
do artigo anterior — conferido nas 66 ocorrências dos 18 atos da Justiça
Eleitoral publicados em 04/09.

**Dados**
- +Indi Li da Silva Alves Moreira Tenorio — **TRE-RN**, Técnico Judiciário
  (Programação de Sistemas), PORTARIA PRES 277, 04/09/2026. **288** nomeações em
  vigor, **315** convocações publicadas (27 tornadas sem efeito).
- Seed sincronizado com a base (+10 registros desde 21/08).
- Auditoria de tudo que a busca do DOU alcança (17/08 a 04/09: 101 portarias
  da Justiça Eleitoral, 19 nomeados de TI): nenhuma outra nomeação havia sido
  perdida por esse motivo nesse período.
- Testes: 31 formatos de portaria (3 novos), 9 casos de anulação (2 novos) e
  4 de motivo, 6 de aplicação de anulação, 3 do coletor, 12 de órgão.

## [1.17.0] — 2026-08-31

**Os dois números, e o que aconteceu com quem saiu**

A 1.16.0 tirou do painel as nomeações que os tribunais tornaram sem efeito — o
que estava certo, mas criou um efeito colateral: quem comparasse o painel com
outra fonte veria **menos convocações do que realmente houve**, e quem procurasse
o nome de alguém que teve a nomeação desfeita não encontraria nada, sem nenhuma
explicação. Sumir é pior do que aparecer errado.

**Agora o painel mostra os dois números:**

- **Nomeações em vigor** (as que valem hoje) — é o que alimenta o mapa, os
  gráficos e as contagens por estado e cargo.
- **Convocações já publicadas** (tudo que saiu no DOU) — é o número que diz até
  onde a fila do concurso andou, e o que costuma bater com outras fontes.

A diferença entre os dois são exatamente as nomeações tornadas sem efeito, e
agora ela fica visível em vez de virar dúvida.

**Nova aba "Movimentações"**, com todas elas: quem saiu, de qual tribunal, em que
cargo, quando foi nomeado, quando a nomeação foi desfeita, **por quê** e o link
das duas portarias. O motivo sai do próprio texto do ato — hoje 11 desistências,
1 perícia médica e 14 sem motivo declarado.

**Na Lista Completa**, uma caixa "incluir nomeações tornadas sem efeito" traz
essas pessoas de volta à lista, com o nome riscado e a etiqueta *sem efeito*.
E se você buscar um nome que só existe entre as desfeitas, o painel avisa em vez
de devolver tela vazia. O CSV exportado ganhou as colunas de situação, data,
motivo e ato que desfez — um CSV onde a nomeação desfeita se confunde com a
válida vira dado errado assim que sai daqui.

**O que o painel NÃO faz — de propósito:** dizer quem entrou no lugar de quem.
O Diário Oficial não publica esse vínculo. Dos 55 atos de anulação encontrados,
só 8 também nomeiam alguém no mesmo documento — e nem nesses a conta fecha um a
um (numa portaria do TRE-MG saíram 5 e entraram 7; numa do TRE-DF saíram 8 e
entrou 1). Dava para adivinhar pela classificação, mas seria palpite nosso
apresentado como informação oficial, e num painel que as pessoas usam para
decidir a vida isso é pior do que não ter o dado.

---

## [1.16.0] — 2026-08-31

**Nomeação tornada sem efeito agora sai do painel**

Até aqui o coletor só sabia **somar**. Quando um tribunal desfazia uma nomeação
— o candidato não tomou posse no prazo, desistiu, ou a portaria saiu com erro —
ele publicava um ato novo ("**Tornar sem efeito** a Portaria nº 504 … referente à
nomeação do candidato FULANO"), e o painel simplesmente **ignorava**. A pessoa
continuava aparecendo como convocada, para sempre.

O problema apareceu em 31/08/2026, quando o **TRE-SE** tornou sem efeito a
nomeação de um Técnico Judiciário de Programação de Sistemas publicada em
28/07/2026. Ao investigar, varremos **todas as edições da Seção 2 do DOU desde
junho de 2025** (326 dias, 4.352 atos da Justiça Eleitoral) e encontramos **83
nomeações tornadas sem efeito** — **26 delas estavam no painel indevidamente**,
algumas havia mais de um ano.

**O que mudou:**

- O coletor agora lê os atos de anulação ("tornar sem efeito", "tornar
  insubsistente", "revogar/anular a nomeação de…") e os separa por **artigo** —
  o TRE-MG publica portarias que anulam umas nomeações e fazem outras nos
  artigos alternados da mesma peça, e os dois grupos não podem se misturar.
- As anulações ficam num arquivo próprio e permanente, **`data/anulacoes.json`**.
  Apagar o registro do `nomeacoes.json` não bastaria: o seed e o histórico o
  trariam de volta na execução seguinte, porque a portaria que anulou já teria
  saído da janela dos últimos dias que o robô varre.
- **Exoneração não é anulação.** Quem foi exonerado tomou posse e depois saiu —
  a convocação aconteceu de verdade e continua no painel como histórico.

**Cuidado para não apagar quem não devia:** uma nomeação só sai se for do
**mesmo tribunal**, com data **anterior** ao ato, e — quando o ato cita a
portaria desfeita — apenas a daquela portaria. Isso não é teoria: o TRE-MG
anulou a nomeação de **Técnico** de um candidato que também tinha sido nomeado
**Analista** dias antes; sem a regra da portaria, o painel teria perdido a
nomeação válida dele. O mesmo vale para quem é nomeado de novo depois da
anulação: a nomeação nova permanece.

**Três outros erros apareceram na mesma varredura e foram corrigidos:**

- **Função comissionada não é convocação.** Quando um servidor que já é do
  quadro assume uma Função Comissionada (FC-03) ou Cargo em Comissão (CJ-2), o
  DOU escreve igualzinho a uma nomeação de concurso — "Nomear FULANO, Analista
  Judiciário, Apoio Especializado - Análise de Sistemas…". O TRE-MG publica
  esses atos toda semana, e o painel os teria tratado como gente nova sendo
  chamada.
- **Cabeçalho de lista do TRE-SP.** O TRE-SP abre cada bloco da lista com
  "Analista Judiciário - Área Administrativa, Classe A, Padrão 1:". O painel não
  reconhecia esse formato de cabeçalho, e os nomes da seção **Administrativa**
  herdavam a especialidade de TI citada antes, no artigo anterior.
- **"I -" não faz parte do nome.** Numa lista numerada ("I - DIEGO AQUINO DE
  SOUSA"), o marcador do item entrava colado no nome.

Também acertamos a grafia de **dois nomes** que estavam diferentes do texto
oficial do DOU. Não é só estética: um deles ("Brandãoo", com dois "o") impedia o
painel de reconhecer que aquela nomeação tinha sido tornada sem efeito pelo
TRE-SP em janeiro.

Total do painel: de 311 para **285** nomeações de TI.

---

## [1.15.1] — 2026-08-21

**Correção — as nomeações do TRE-MS de 20/08 não apareciam**

A PORTARIA 196 do **TRE-MS** (publicada em 20/08/2026) nomeou **duas Técnicas
Judiciárias de TI** e nenhuma das duas entrou no painel. Foram **duas falhas em
sequência**, e as duas foram corrigidas:

**1) O DOU escreve o nome do TRE-MS de um jeito e o painel esperava outro.**
Na hierarquia do Diário o tribunal aparece como "Tribunal Regional Eleitoral
**do** Mato Grosso do Sul"; o nome oficial (o que o painel usava) é "…**de** Mato
Grosso do Sul". Por causa de uma única preposição, o coletor não reconhecia o
órgão. Agora a comparação ignora as preposições (de/do/da/dos/das) e passa a
valer para os 28 órgãos — há teste que troca a preposição de cada um dos 27 TREs
e confere se todos continuam se identificando.

De quebra, a comparação agora vale por **palavra inteira**, o que fecha um erro
irmão do que foi corrigido na 1.15.0: "…Eleitoral do **Pará**" casava dentro de
"…Eleitoral do **Paraíba**" (PB viraria PA).

**2) Uma portaria que falhava numa etapa nunca era tentada de novo.** O coletor
procura as portarias por dois caminhos (a busca do DOU e a edição do dia). O
resumo que a **busca** devolve é recortado em volta do termo procurado e quase
nunca traz o nome do tribunal — mesmo assim a portaria já era marcada como "já
vista", e a etapa seguinte, que teria dado certo, a pulava. Agora: (a) quando o
resumo não identifica o órgão, o coletor **abre a portaria inteira** e tenta de
novo (o nome do tribunal está sempre no preâmbulo); e (b) só é marcado como
"visto" o ato **realmente avaliado** — se o download falhar, ele continua na fila
para as etapas e execuções seguintes.

**Dados**
- +Larissa Ribeiro Lopes e +Raissa Rinaldi Yoshioka — **TRE-MS**, Técnico
  Judiciário (Programação de Sistemas), PORTARIA 196, 20/08/2026. Total **305**
  (121 Analistas + 184 Técnicos), em 28 órgãos.
- Auditoria de todo o histórico da busca do DOU: nenhuma outra nomeação havia
  sido perdida por esse motivo.
- Testes: 24 formatos de portaria, 12 casos de identificação de órgão + a
  varredura de preposições, e 2 casos novos do coletor (`test_coletor.py`).

## [1.15.0] — 2026-08-12

**Duas correções a partir da PORTARIA 266 do TRE-PR (12/08)**

**1) Nomeação registrada no estado errado (PR virava PA).** A identificação do
órgão procurava o nome do tribunal dentro do texto e ficava com o primeiro que
encontrasse — e "…Eleitoral do Pará" **está contido em** "…Eleitoral do Paraná".
Resultado: nomeação do **Paraná** foi gravada como **Pará**. O mesmo valia para
"…de Mato Grosso" dentro de "…de Mato Grosso do Sul" (MS viraria MT). Agora vale
sempre o **nome mais longo** (o mais específico), e há um teste que confere os
**28 órgãos**, um a um. Conferimos também o histórico: nenhum registro antigo
tinha sido afetado.

**2) Só 1 de 2 nomeados era capturado.** A portaria traz um único "NOMEAR" no
caput e os nomeados em **alíneas** ("a) o candidato…; b) a candidata…"). O parser
só alcançava o primeiro item. Agora cada alínea é lida separadamente, com o cargo
e a especialidade do próprio item.

**Dados**
- Corrigido: José Henrique Dometerco (estava em PA) e adicionada Amanda Monteiro
  Galvão — ambos **TRE-PR**, Analista de TI, PORTARIA 266.
- Testes: 24 formatos de portaria + 10 casos de identificação de órgão.

## [1.14.1] — 2026-08-07

**Correção (parser) — erro de digitação no próprio DOU**

A nomeação de Analista de TI do TRE-SE (PORTARIA 535, 06/08) não entrou porque o
texto publicado no Diário traz **"o(a) candida*d*o(a)"** — com **D** no lugar do
**T**. Como o parser procurava exatamente "candidato/candidata", a portaria não
casava com nenhum padrão e o nomeado sumia.

Agora o parser aceita as duas grafias, então esse tipo de erro de digitação na
fonte não faz mais a nomeação desaparecer. (A expressão "NOMEAR, **na condição de
sub judice**, …", também presente nessa portaria, já era tratada corretamente.)

**Dados**
- +Jeirlan Correia Palmeira (TRE-SE, PORTARIA 535, 06/08) — total **266**
  (101 Analistas + 165 Técnicos). Testes de regressão: 23 casos.

## [1.14.0] — 2026-07-28

**Correção importante (coletor) — portarias com preâmbulo longo eram descartadas**

Uma nomeação de Analista de TI do TRE-SE (PORTARIA 512, 28/07) não apareceu. A
causa não era o parser (ele lia a portaria corretamente), e sim o **filtro que
decidia quais portarias valia a pena abrir**:

- O índice diário do DOU entrega só um **trecho de ~403 caracteres** de cada ato.
- O coletor exigia a palavra "nomear" nesse trecho para então baixar a portaria.
- Portarias com **preâmbulo longo** (vários "CONSIDERANDO…") têm o "Art. 1º
  NOMEAR" **fora** desse trecho — então eram descartadas **sem nem serem lidas**.

Agora o coletor **abre todos os atos da Justiça Eleitoral** do dia e deixa o
parser decidir (ele só devolve nomeações de TI). Isso vale para todos os órgãos —
qualquer portaria com preâmbulo longo estava sujeita ao mesmo problema.

**Também corrigido no parser**
- **Especialidade limpa**: em "Área de Apoio Especializado, Especialidade X" vinha
  *"Especialidade X"* (com a palavra colada e cortada); agora vem só *"X"*.
- **Área longa**: textos como "Área de Apoio Especializado em Tecnologia da
  Informação e Comunicação, Especialidade Y" não eram alcançados; agora são.

**Dados**
- +Victor Costa de Alemão Cisneiros (TRE-SE, PORTARIA 512, 28/07) — total **258**
  (97 Analistas + 161 Técnicos). Testes de regressão: 22 casos.

## [1.13.1] — 2026-07-27

**Correção (parser) — portaria do TRE-PA escapava**
As duas nomeações de TI de 24/07 (TRE-PA, PORTARIA 25.019) não entraram porque a
portaria usa **dois padrões novos** ao mesmo tempo:

- **"ESPECIALIDADE EM Programação de Sistemas"** — com a preposição "em", que os
  padrões antigos não aceitavam (esperavam "Especialidade X" ou "Especialidade: X").
- **Lista em algarismos romanos** — "I - FULANO, em vaga…; II - CICLANO, …".

Agora o parser entende os dois. Como a portaria tem **três artigos com cargos
diferentes** (Área Judiciária, Contabilidade e Programação de Sistemas), a regra de
fronteira por cargo continua valendo: só entram os nomes que estão sob o artigo de
TI — os demais são ignorados. Coberto por um novo teste de regressão (19 casos).

**Dados**
- +Marcelo Nascimento Moutinho e +Healley Ardasse Monteiro (TRE-PA, 24/07) e
  sincronização seed=base — total **256** (96 Analistas + 160 Técnicos).

## [1.13.0] — 2026-07-01

**Coletor — fonte de reserva (Escavador) quando o DOU cai**
- O in.gov.br oscilou (a busca dele deu erro e o índice do dia atrasou), e uma
  nomeação (TRE-SP, 01/07) não foi capturada no mesmo dia. Para esses casos, o
  coletor ganhou uma **3ª fase**: quando o in.gov.br não cobre uma data, ele
  consulta o **Escavador** (que espelha o texto oficial do DOU e costuma ter o dia
  antes do próprio in.gov.br). Só dispara para as datas não cobertas, varre a
  Seção 2 **de trás para frente com janela ampla** (a Justiça Eleitoral fica na
  parte final, mas a posição varia com o tamanho da edição — em edições grandes,
  de ~170 páginas, ela pode estar bem antes do fim), com parada antecipada e
  pausas, para ser gentil. O texto passa pelo mesmo parser de sempre.
- **`rebuild_data.py`** agora regenera a base pela **união seed + base** (sem
  duplicar; seed vence), com recuperação pelo seed se o arquivo corromper — assim
  nunca mais perde um registro que o coletor já tinha pego.

**Dados**
- +Felipe Luiz da Silva Brandão (TRE-SP, PORTARIA 221, 01/07) e sincronização
  seed=base — total **239** (90 Analistas + 149 Técnicos).

## [1.12.0] — 2026-06-15

**Polimento visual (sem mudar a estrutura)**
- Tipografia mais nítida: suavização de fonte, *kerning* mais justo nos títulos e
  **números tabulares** nos KPIs, tabela e contadores (os dígitos ficam alinhados).
- Cores com um pouco mais de profundidade: um leve degradê de fundo (nos temas
  claro e escuro), cartões "glass" levemente mais vivos e sombra suave ao passar o
  mouse nos KPIs.
- Acessibilidade/celular: contornos de foco visíveis ao navegar pelo teclado,
  botões do topo com área de toque maior e abas com espaçamento melhor no celular.

**Automação (agendamento)**
- O robô passou a rodar **a cada 30 minutos, das 00:00 às 10:00 de Brasília**
  (inclusive), concentrando as tentativas na janela em que o DOU sai e você acorda
  — compensando os atrasos/skips do agendador do GitHub. Coletor mais enxuto
  (janela menor + busca só nas páginas recentes) para cada execução ser rápida.

## [1.11.0] — 2026-06-09

**Coletor — mapeamento de TODOS os formatos de portaria já vistos**

Cada tribunal publica a nomeação num formato de texto diferente. Antes, o coletor
só entendia alguns; agora ele cobre **todos os formatos dos órgãos que já temos**,
validado portaria por portaria contra os nomes reais (TSE, DF, MG, BA, RJ, PI, RO,
MT, AC, AP, ES, GO, MA, MS, PB, PR, RN, SC, SE, PE, AM, CE, SP…). Famílias de
formato reconhecidas:

- **Inline** "Nomear o candidato/a Sr.(a) Fulano… cargo de Técnico/Analista…
  Especialidade X" — inclusive variações com texto entre "Nomear" e o nome,
  "o(a) candidato(a)" com parênteses de gênero, e cargo escrito como
  "Apoio Especializado - X" (sem a palavra "Especialidade").
- **Nome direto** "Nomear FULANO DE TAL, … Especialidade X" (TRE-SC).
- **Caixa alta** "FULANO Cargo: Técnico Judiciário, Apoio Especializado,
  Programação de Sistemas" — inclusive a portaria multi-área do TRE-AM.
- **Lista/tabela** com "1. FULANO - 1º lugar" / "1º FULANO 1º Lugar" /
  "FULANO Nº lugar" (TRE-GO, TRE-MA, TRE-PE).
- **Lista sem classificação** "FULANO Cargo criado pela Lei…" (TSE).
- Formato "Fulano, Nª colocação" (TRE-SP).

Inclui um **filtro de nome válido** que descarta quem aparece no texto mas **não é
nomeado** — por exemplo o servidor anterior cujo cargo ficou vago, ou alguém que
desistiu/foi exonerado. Quando uma portaria tem **várias seções de cargo**
(ex.: TRE-SP, com uma seção de "Programação de Sistemas" e outra de "Área
Administrativa"), cada cabeçalho de cargo vira uma **fronteira**: os nomes só
entram se a seção em que estão for de TI — assim os de Área Administrativa não
são contados por engano. Pelo mesmo motivo, numa portaria com **vários artigos**
("Art. 9 Nomear o candidato X… Art. 10 Nomear o candidato Y…"), a busca pela
especialidade **não cruza** para o próximo "Nomear" — cada nomeado fica com a
especialidade do **seu** artigo (corrige um caso do TRE-DF em que um candidato de
Engenharia Mecânica entrava como TI). Tudo coberto por testes automáticos
(17 casos) que rodam contra trechos reais de cada formato.

**Coletor — nova fonte de descoberta (resolve o "não atualiza")**

O coletor agora descobre as portarias por **dois caminhos** e junta tudo (sem
duplicar):

1. **Busca** (`/consulta/-/buscar`): mostra as publicações **do próprio dia**,
   então pega nomeações no mesmo dia. (Em alguns ambientes ela pode responder 502;
   nesse caso o passo 2 cobre.)
2. **Edição diária** (`leiturajornal`): um acesso por dia, bem estável, serve de
   rede de segurança. O índice do dia às vezes demora a sair, por isso a busca
   vem antes.

Antes o coletor usava só a busca (que falhava com 502) ou só a edição diária (que
atrasava no mesmo dia); com os dois juntos, a chance de pegar **no mesmo dia**
aumenta bastante.

**Automação — acordar com os dados já atualizados**

Antes os horários cedo (02h/03h) rodavam **antes** do DOU sair e o próximo era só
10h — sobrava um vão justo na hora de acordar. Agora o robô roda **a cada 30 min,
das 00:00 às 10:00 de Brasília** (inclusive). Assim, quando o DOU sai de manhã, em
pouco tempo um run já pega; e, como o GitHub costuma atrasar/pular agendados, a
alta frequência compensa, deixando o painel atualizado antes de você acordar. A
janela de varredura foi reduzida e a busca limitada às páginas recentes para cada
execução ficar rápida e não empilhar.

**Dados**
- Base evoluiu conforme as publicações do DOU: Hibernon (TRE-SP, 08/06),
  Francisco/CE e Yves/SC (09/06), Marcos/DF (12/06) e as 3 de TI do TRE-MG de
  15/06 (Jheffrey, Luciana e Alexandra) — totalizando **237** nomeações
  (89 Analistas + 148 Técnicos) até 15/06/2026.

## [1.10.2] — 2026-06-08

**Correção (coletor) — cobertura de mais formatos**
- Alguns TREs (ex.: TRE-SP) publicam num formato diferente e nem citam o nome do
  concurso, então escapavam. Agora a busca inclui a **especialidade de TI**
  ("Programação de Sistemas", "Análise de Sistemas de Informação"…), que pega
  qualquer órgão, e o parser entende também o formato "Cargo de X… Especialidade Y…
  Fulano, Nª colocação" (validado na portaria do TRE-SP que listava o "Hibernon").

## [1.10.1] — 2026-06-08

**Correção (coletor)**
- O coletor não estava atualizando: as buscas no DOU usavam várias frases entre
  aspas e retornavam 0 resultados. Trocadas pela frase única do concurso
  ("Concurso Público Nacional Unificado da Justiça Eleitoral"), que traz só as
  nomeações da Justiça Eleitoral, ordenadas por data.
- Filtro de órgão antes de baixar o texto, janela dos últimos 60 dias, e
  proteção contra o limite de requisições do in.gov.br (pausas + novas tentativas).

## [1.10.0] — 2026-06-03

**Novidade**
- **Notificações no navegador**: botão 🔔 no cabeçalho. Quem autorizar e deixar a
  aba aberta (mesmo em segundo plano) recebe um aviso do sistema sempre que o
  painel detecta novas nomeações — sem precisar ficar olhando o site.

## [1.9.3] — 2026-06-03

- Logo: o selo "TI" foi substituído pelo **emblema oficial do TSE** (SVG, com o
  texto "Tribunal Superior Eleitoral" removido) no cabeçalho, no card de
  compartilhamento e na og:image. O **favicon da aba foi mantido** como estava.
- Título atualizado para **"Nomeações · Concurso TSE Unificado TI"**.
- Siglas dos estados alinhadas corretamente na imagem de compartilhamento.
- Adicionado arquivo **LICENSE** (direitos autorais / uso restrito).

## [1.9.2] — 2026-06-03

- **Correção da imagem de compartilhamento**: em vez de "fotografar" a seção da
  página (que saía desalinhada por causa do recorte de texto), o botão agora gera
  um card próprio, com layout limpo e alinhado, pronto para compartilhar.

## [1.9.1] — 2026-06-03

- Crédito **"Desenvolvido por Alexander Reis"** no rodapé, com o ícone do LinkedIn
  linkando para o perfil.

## [1.9.0] — 2026-06-03

**Novidades**
- **Tema claro/escuro**: botão no cabeçalho (🌙/☀️); a preferência fica salva no
  navegador e os gráficos se ajustam ao tema.
- **Compartilhamento**: imagem de prévia (og:image) ao compartilhar o link em
  redes/WhatsApp, e botão **"📷 Compartilhar"** que gera uma imagem das
  "Convocações do dia" para enviar (ou baixar).

## [1.8.0] — 2026-06-03

**Layout profissional em abas** (inspirado no painel da Embrapa)
- Abas: **Visão Geral · Por Estado · Por Cargo · Lista Completa**.
- **Por Estado**: grid de cards por órgão, cada um com total e a barra de divisão
  Analista (índigo) / Técnico (violeta); clicar abre a lista daquele órgão.
- **Por Cargo**: comparativo lado a lado Analista x Técnico (total, %, nº de órgãos,
  última data e os órgãos que mais convocaram em cada cargo).
- Mapa e cards levam direto para a Lista já filtrada pelo órgão.

## [1.7.0] — 2026-06-03

**Novidades**
- **Mapa do Brasil (heatmap)**: cada estado colorido pelo volume de nomeações de TI;
  clicar num estado filtra a lista.
- **Tabela com ordenação e paginação**: clique nas colunas (Nome, Órgão, Cargo, Data)
  para ordenar; navegação por páginas (25 por página) nas 230+ nomeações.

## [1.6.0] — 2026-06-03

**Mais visual e profissional**
- Distinção clara por **cargo** em todo o painel: Analista (índigo) x Técnico (violeta)
  — pílulas coloridas na lista, nos cards do dia e no gráfico de rosca.
- Gráfico "por órgão" virou **barra empilhada Analista × Técnico**, dá pra ver de
  relance o peso de cada cargo em cada tribunal.
- **Órgãos coloridos por região** (Norte, Nordeste, Centro-Oeste, Sudeste, Sul + TSE),
  com legenda — facilita identificar e comparar os tribunais.

## [1.5.0] — 2026-06-03

**Automação de verdade (coletor do DOU)**
- O coletor foi religado à fonte real: a busca do DOU entrega os resultados no
  próprio HTML do servidor (validado), então o robô do GitHub Actions consegue
  ler sem precisar de navegador.
- Novo leitor tolerante ao `id` do bloco de resultados (que o DOU renomeou).
- Extração estruturada por candidato — captura **nome, classificação, cargo e
  especialidade**, filtrando só TI mesmo em portarias com várias áreas.
  Validado contra a PORTARIA 148/DF: dos 17 nomeados, extraiu exatamente os 12 de TI.
- A **classificação** ("Nº lugar") agora aparece ao lado do nome na lista.

**Tela**
- **Auto-atualização**: a página verifica novos dados a cada 5 min e se atualiza
  sozinha (sem F5), com um aviso discreto quando há novidade.

## [1.4.0] — 2026-06-03

**Dados (lidos via navegador, direto da fonte renderizada)**
- Base atualizada para **230 nomeações em 25 órgãos** (antes 201/22).
- Novos órgãos: **RN** (1), **SC** (1) e **DF** (12 analistas — PORTARIA 148).
- Correções/atualizações: **PI** 15→23, **MA** 11→15, **RJ** 2→4, **MT** 2→3.
- Faltam convocar (3): Alagoas, Rio Grande do Sul e Tocantins.

## [1.3.0] — 2026-06-03

**Novidades**
- Gráfico de **ritmo mensal** (nomeações por mês) + indicador de "ritmo recente".
- **Busca sem acento**: encontrar "Joao" acha "João".
- **Link direto por estado**: abrir `.../tse-dashboard/#SP` já mostra filtrado por SP
  (o filtro de estado também atualiza o endereço, facilitando compartilhar).

## [1.2.0] — 2026-06-03

**Correções**
- **Adrian Newey Santos** e **Rafael Souza Santos** (PORTARIA 201 e 202) estavam
  listados em Espírito Santo, mas foram nomeados em **Sergipe** — corrigido.

**Novidades**
- Painel **“Cobertura nacional”**: mostra quantos dos **28 órgãos** (27 TREs + TSE)
  já convocaram em TI e lista os que ainda não convocaram.
- Botão **“Baixar CSV”**, que exporta a lista (respeitando os filtros aplicados).

## [1.1.0] — 2026-06-03

**Novidades**
- Adicionada a seção **“Convocações do dia”**, que destaca as nomeações de hoje
  (ou, se não houver nenhuma hoje, a última divulgação publicada).
- **Favicon** próprio do site.
- Versão do painel exibida no rodapé.

**Automação**
- O robô passou a rodar **5 vezes ao dia** (02h, 03h, 10h, 13h e 18h de Brasília).
- O coletor agora **só atualiza o site quando há novidade**: se nada mudou desde a
  última execução, nada é gravado nem publicado.

**Dados**
- Base ampliada para **todos os estados que já convocaram** (TSE + 21 TREs),
  com as nomeações reais de TI.

## [1.0.0] — 2026-06-02

- Versão inicial: dashboard interativo (KPIs, gráficos, filtros e busca por nome),
  coletor automático do Diário Oficial da União e publicação via GitHub Pages +
  GitHub Actions. Base inicial com as nomeações do TSE.
