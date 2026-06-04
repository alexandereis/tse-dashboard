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
