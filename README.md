# 📊 Painel de Nomeações — Concurso TSE Unificado (TI)

Painel online, simples e **atualizado automaticamente**, para acompanhar as
**nomeações de Tecnologia da Informação** do **Concurso Público Nacional Unificado
da Justiça Eleitoral** (o "TSE Unificado") — do **TSE** e dos **TREs de todos os
estados**.

## 🔗 Acesse o painel

### 👉 [**Abrir o painel TSE Unificado (TI)**](https://alexandereis.github.io/tse-dashboard/)

> Link direto: https://alexandereis.github.io/tse-dashboard/

---

## Para que serve

Quem fez o concurso na área de TI precisa acompanhar quem já foi chamado, em qual
tribunal e quando. Essa informação existe, mas fica espalhada e é trabalhosa de
procurar. Este painel reúne tudo em um só lugar, de forma visual e fácil de
entender — e se atualiza sozinho conforme saem as portarias no Diário Oficial.

## O que dá pra ver

O painel é organizado em **abas**:

- **Visão Geral** — números principais (total, analistas, técnicos, órgãos),
  as **convocações do dia**, o **mapa do Brasil** colorido por volume de
  nomeações e a evolução ao longo do tempo.
- **Movimentações** — as nomeações que os tribunais **tornaram sem efeito**:
  quem saiu, quando, por quê e o link das portarias.
- **Por Estado** — um card para cada tribunal, com o total e a divisão entre
  Analista e Técnico; clicar num estado abre a lista daquele órgão.
- **Por Cargo** — comparativo lado a lado entre **Analista** e **Técnico**.
- **Lista Completa** — todos os nomeados, com busca por nome, filtros por estado
  e cargo, ordenação e link para a portaria oficial de cada um.

## Recursos

- 🗺️ Mapa do Brasil (mais forte a cor, mais nomeações no estado)
- 🌙 Tema claro/escuro
- 🔎 Busca por nome (ignora acentos) e filtros por estado e cargo
- ⬇️ Exportar a lista em CSV
- 📷 Compartilhar as convocações do dia como imagem
- 🔄 Atualização automática da tela (sem precisar dar F5)

## De onde vêm os dados

As nomeações são publicadas oficialmente no **Diário Oficial da União**. O painel
busca essas publicações e as organiza automaticamente, várias vezes ao dia. Quando
sai uma nomeação nova, o painel se atualiza sozinho.

Quando um tribunal **torna sem efeito** uma nomeação (o candidato não tomou posse,
desistiu, ou a portaria saiu com erro), o painel acompanha: a pessoa sai da conta
de *nomeações em vigor*, mas continua visível na aba **Movimentações** e, se você
quiser, na Lista Completa — com o nome riscado e o motivo. Já uma **exoneração**
não tira ninguém: quem foi exonerado tomou posse e depois saiu, então a convocação
aconteceu de verdade.

Por isso o painel mostra **dois números**: quantas nomeações estão em vigor hoje e
quantas convocações já foram publicadas no total. Comparando com outras fontes,
a diferença costuma ser exatamente essa.

O painel **não diz quem entrou no lugar de quem** — o Diário Oficial não publica
esse vínculo, e apontar um nome ali seria chute, não informação oficial.

## 🔧 Manutenção (para quem cuida do painel)

O robô só sabe o que o parser devolve; um formato de portaria novo faz a
nomeação sumir em silêncio. Três comandos servem de rede de segurança:

```bash
python collector/auditar_dia.py 04-09-2026     # tudo que a Justiça Eleitoral publicou no dia,
                                               # o que o parser leu e o que ficou "suspeito"
python collector/conferir_anulacoes.py         # reabre os atos de data/anulacoes.json com o
                                               # parser atual; rode antes de publicar mudança no parser
python collector/varredura.py --dias 45        # reabre as edições do período e compara com o painel
```

Os três saem com código 1 quando há algo para olhar. A varredura também roda
sozinha **uma vez por mês** (workflow "Varredura mensal do DOU"): incorpora as
anulações que faltavam e, se sobrar nomeado fora da base ou ato suspeito, o job
falha e o GitHub avisa por e-mail. Testes: `python collector/test_*.py`.

## ⚖️ Aviso

Painel **independente**, feito por concurseiro para concurseiro, **sem vínculo
oficial** com o TSE ou os TREs. As informações são coletadas de forma automática e
podem conter algum erro ou atraso — **para qualquer decisão, confirme sempre na
portaria oficial** (o link está em cada linha da lista).

## 👤 Autor

Desenvolvido por **Alexander Reis** — [LinkedIn](https://www.linkedin.com/in/alexandereis/)

© 2026 Alexander Reis. Veja o arquivo [LICENSE](LICENSE) para os termos de uso.
