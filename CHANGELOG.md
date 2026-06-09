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
desistiu/foi exonerado. Tudo coberto por testes automáticos (15 casos) que rodam
contra trechos reais de cada formato.

**Coletor — nova fonte de descoberta (resolve o "não atualiza")**

A automação não atualizava porque a **busca** do DOU (`/consulta/-/buscar`)
respondia **502 (Bad Gateway)** para o robô do GitHub Actions. O coletor passou a
usar a **edição diária** do DOU (endpoint `leiturajornal`): um único acesso por
dia que traz todos os atos da Seção 2, dos quais ele separa as nomeações da
Justiça Eleitoral e extrai os de TI. Mais simples e estável.

**Dados**
- Adicionada a nomeação do **Hibernon Olegário da Silva Júnior** (TRE-SP,
  PORTARIA Nº 184, 08/06/2026) — base agora com **231** nomeações, batendo com a
  referência pública até 08/06/2026.

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
