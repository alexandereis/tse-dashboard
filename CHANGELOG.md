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
