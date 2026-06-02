# 📊 Painel de Nomeações — Concurso TSE Unificado (TI)

Dashboard **profissional e automático** que mostra, em um só lugar, todas as
nomeações de **Tecnologia da Informação** (Analista e Técnico Judiciário) do
**Concurso Público Nacional Unificado da Justiça Eleitoral** (o "TSE Unificado"),
para o **TSE** e os **27 TREs**.

Os dados vêm do **Diário Oficial da União** e são atualizados **sozinhos**, todos
os dias, via GitHub Actions — sem você precisar fazer nada.

> Este guia é **do zero**. Mesmo que você nunca tenha usado GitHub, é só seguir
> os passos na ordem. Onde aparecer `SEU-USUARIO`, troque pelo seu nome de
> usuário do GitHub.

---

## Sumário

1. [Como funciona a publicação no Diário Oficial](#1-como-funciona-a-publicação-no-diário-oficial-a-fonte-dos-dados)
2. [Como o projeto funciona (a arquitetura)](#2-como-o-projeto-funciona-a-arquitetura)
3. [Criar uma conta no GitHub](#3-criar-uma-conta-no-github)
4. [Instalar o Git no seu computador](#4-instalar-o-git-no-seu-computador)
5. [Criar o repositório](#5-criar-o-repositório)
6. [Enviar os arquivos para o GitHub](#6-enviar-os-arquivos-para-o-github)
7. [Ativar o GitHub Pages (colocar o site no ar)](#7-ativar-o-github-pages-colocar-o-site-no-ar)
8. [Ligar o GitHub Actions e rodar o coletor](#8-ligar-o-github-actions-e-rodar-o-coletor)
9. [Entender o agendamento automático](#9-entender-o-agendamento-automático)
10. [Manutenção do dia a dia](#10-manutenção-do-dia-a-dia)
11. [Rodar e testar no seu computador](#11-rodar-e-testar-no-seu-computador-opcional)
12. [Solução de problemas](#12-solução-de-problemas)

---

## 1. Como funciona a publicação no Diário Oficial (a fonte dos dados)

Esta é a parte mais importante de entender. Tudo no painel depende dela.

**A Justiça Eleitoral é um órgão federal.** Por isso, quando o TSE ou qualquer
TRE nomeia um aprovado em concurso, o ato (chamado **Portaria de Nomeação**) é
publicado no **Diário Oficial da União (DOU)**, na **Seção 2** — que é a seção
reservada aos "atos de pessoal" (nomeações, exonerações, aposentadorias, etc.).

Isso é ótimo para nós: significa que **uma única fonte** (o DOU) concentra as
nomeações do TSE **e** dos 27 TREs. Não precisamos visitar 28 sites diferentes.

O DOU tem um buscador público em **<https://www.in.gov.br/consulta/>**. Quando
você pesquisa lá, o site internamente chama uma API e devolve os resultados em
um bloco de dados escondido na página (um `<script id="params">` com JSON). O
nosso coletor faz exatamente a mesma pesquisa que você faria à mão, só que
automaticamente, e lê esse bloco de dados.

**Como uma portaria de nomeação se parece** (exemplo real, resumido):

> **PORTARIA Nº 352, DE 5 DE AGOSTO DE 2025** — O Diretor-Geral do Tribunal
> Superior Eleitoral resolve: Art. 1º **Nomear**, em virtude de aprovação no
> Concurso Público Nacional Unificado da Justiça Eleitoral, para o cargo de
> **Analista Judiciário**, Área Apoio Especializado, Especialidade Análise de
> Sistemas de Informação: LUCAS RODRIGUES FONSECA, MATEUS MANUEL ...

O coletor procura portarias com a palavra **"nomear"**, descobre **qual tribunal**
publicou (pelo cabeçalho), confere se o cargo é de **TI**, e extrai os **nomes**
(que no DOU vêm em MAIÚSCULAS).

> ℹ️ **Observação honesta:** o formato das portarias varia um pouco entre os
> tribunais. O coletor acerta a grande maioria, mas pode escapar de algum caso
> raro ou captar um nome a mais. Por isso o projeto tem um arquivo de
> **dados verificados à mão** (`seed/seed.json`) que sempre tem prioridade e
> nunca é sobrescrito — garantindo que o painel esteja sempre correto e cheio.
> Veja a [seção 10](#10-manutenção-do-dia-a-dia).

---

## 2. Como o projeto funciona (a arquitetura)

```
  ┌──────────────────────────┐     roda todo dia
  │   GitHub Actions (cron)   │  ───────────────────┐
  └──────────────────────────┘                      │
                                                     ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  collector/collect.py  →  busca no DOU (in.gov.br, Seção 2)    │
  │  • encontra portarias de nomeação (TSE + TREs)                 │
  │  • filtra só cargos de TI e extrai os nomes                    │
  │  • junta com o seed (dados verificados) sem duplicar           │
  └──────────────────────────────────────────────────────────────┘
                                                     │ gera/atualiza
                                                     ▼
                              ┌─────────────────────────────┐
                              │   data/nomeacoes.json        │  ◄── o "banco de dados"
                              └─────────────────────────────┘
                                                     │ é lido por
                                                     ▼
                              ┌─────────────────────────────┐
                              │   index.html (dashboard BI)  │  ◄── o site que todos veem
                              └─────────────────────────────┘
                                                     │ publicado por
                                                     ▼
                              ┌─────────────────────────────┐
                              │        GitHub Pages          │  ◄── https://SEU-USUARIO.github.io/tse-dashboard
                              └─────────────────────────────┘
```

**Mapa dos arquivos:**

| Arquivo / pasta | Para que serve |
|---|---|
| `index.html` | O dashboard (página única com gráficos, filtros e busca). |
| `data/nomeacoes.json` | O "banco de dados". Gerado automaticamente pelo coletor. |
| `seed/seed.json` | Dados conferidos à mão. Têm prioridade e nunca somem. |
| `collector/collect.py` | O robô que busca no DOU. |
| `collector/parser.py` | As regras que "leem" o texto da portaria. |
| `collector/config.py` | Lista de tribunais, palavras-chave de TI e as buscas. |
| `.github/workflows/update.yml` | O agendamento que roda o coletor sozinho. |

---

## 3. Criar uma conta no GitHub

> Se você já tem conta, pule para a [seção 4](#4-instalar-o-git-no-seu-computador).

1. Acesse <https://github.com/signup>.
2. Informe seu e-mail, crie uma senha e escolha um **nome de usuário** (este nome
   vai aparecer no endereço do seu site, então escolha algo simples).
3. Confirme o e-mail que o GitHub enviar.
4. Pode escolher o plano **gratuito** — ele já permite Pages e Actions.

---

## 4. Instalar o Git no seu computador

O Git é o programa que envia os arquivos para o GitHub.

**Windows:** baixe em <https://git-scm.com/download/win> e instale clicando
"Avançar" em tudo (as opções padrão servem).

**Mac:** abra o aplicativo **Terminal** e digite `git --version`. Se não estiver
instalado, o próprio Mac oferece a instalação.

Para conferir, abra o **Prompt de Comando** (Windows) ou o **Terminal** (Mac) e
digite:

```bash
git --version
```

Se aparecer algo como `git version 2.x.x`, está pronto.

> 💡 **Caminho sem instalar nada:** você também pode enviar os arquivos pelo
> próprio site do GitHub (arrastar e soltar). Mostro esse atalho na
> [seção 6](#6-enviar-os-arquivos-para-o-github).

---

## 5. Criar o repositório

1. Logado no GitHub, clique no **+** no canto superior direito → **New repository**.
2. Em **Repository name**, escreva: `tse-dashboard`
3. Deixe como **Public** (necessário para o GitHub Pages gratuito).
4. **Não** marque nenhuma opção de "Add a README/.gitignore/license" (já temos os
   arquivos prontos).
5. Clique em **Create repository**.

Anote o endereço que aparece, algo como
`https://github.com/SEU-USUARIO/tse-dashboard`.

---

## 6. Enviar os arquivos para o GitHub

Você tem **duas opções**. Escolha uma.

### Opção A — Pelo site (mais fácil, sem instalar nada)

1. Na página do repositório recém-criado, clique em **uploading an existing file**
   (ou **Add file → Upload files**).
2. Abra a pasta do projeto no seu computador, **selecione todos os arquivos e
   pastas** e arraste para a área de upload do GitHub.
   - ⚠️ Importante: a pasta **`.github`** começa com ponto e às vezes fica
     "escondida". Garanta que ela (com o arquivo `update.yml` dentro) também
     suba. No Windows, ative "Itens ocultos" no Explorador de Arquivos.
3. Lá embaixo, em "Commit changes", clique em **Commit changes**.

### Opção B — Pelo Git (linha de comando)

Abra o terminal **dentro da pasta do projeto** e rode, trocando `SEU-USUARIO`:

```bash
git init
git add .
git commit -m "primeira versão do painel"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/tse-dashboard.git
git push -u origin main
```

Se pedir login, use seu usuário e um **token** (o GitHub não aceita mais senha
comum aqui — crie um token em *Settings → Developer settings → Personal access
tokens → Tokens (classic)*, marcando a permissão `repo`).

Ao terminar, atualize a página do repositório: os arquivos devem aparecer.

---

## 7. Ativar o GitHub Pages (colocar o site no ar)

1. No repositório, clique em **Settings** (aba no topo).
2. No menu da esquerda, clique em **Pages**.
3. Em **Source**, escolha **Deploy from a branch**.
4. Em **Branch**, selecione **main** e a pasta **/ (root)**. Clique em **Save**.
5. Aguarde 1–2 minutos e recarregue a página. Vai aparecer o endereço do seu site:

   ```
   https://SEU-USUARIO.github.io/tse-dashboard/
   ```

Pronto — esse é o link que você compartilha com os concurseiros. 🎉
Ele já vai mostrar os dados do **seed** (22 nomeações do TSE) imediatamente.

---

## 8. Ligar o GitHub Actions e rodar o coletor

Por segurança, o GitHub às vezes deixa o Actions só de leitura. Precisamos
liberar a escrita para o robô poder salvar os dados.

1. **Settings → Actions → General**.
2. Role até **Workflow permissions**.
3. Marque **Read and write permissions** e clique em **Save**.

Agora rode o coletor pela primeira vez, manualmente:

4. Vá na aba **Actions** (no topo do repositório).
5. Se aparecer um aviso pedindo para habilitar workflows, clique em
   **I understand my workflows, go ahead and enable them**.
6. Na lista à esquerda, clique em **Atualizar nomeações (coletor do DOU)**.
7. Clique no botão **Run workflow → Run workflow** (deixe a branch `main`).
8. Aguarde ~1 minuto. Quando ficar com o ✅ verde, o robô buscou o DOU e, se
   encontrou nomeações novas, atualizou o `data/nomeacoes.json` sozinho.

Recarregue o site do Pages — ele já refletirá qualquer novidade encontrada.

> Se o robô não encontrar nada novo, está tudo certo também: ele só não tinha o
> que adicionar. Os dados do seed continuam aparecendo.

---

## 9. Entender o agendamento automático

No arquivo `.github/workflows/update.yml`, esta parte define **quando** o robô roda:

```yaml
on:
  schedule:
    - cron: "0 11 * * *"   # 08:00 de Brasília
    - cron: "0 21 * * *"   # 18:00 de Brasília
  workflow_dispatch: {}    # botão de rodar manualmente
```

O `cron` usa o fuso **UTC**. Como o Brasil é **UTC-3**:

- `0 11 * * *` → roda às **08:00** (horário de Brasília).
- `0 21 * * *` → roda às **18:00** (horário de Brasília).

A leitura do cron é: `minuto hora dia-do-mês mês dia-da-semana`.
Exemplos para você ajustar se quiser:

| Quero que rode... | cron |
|---|---|
| Uma vez por dia, meio-dia BRT | `0 15 * * *` |
| A cada 6 horas | `0 */6 * * *` |
| Só em dias úteis, 09:00 BRT | `0 12 * * 1-5` |

> ⏳ O agendamento do GitHub pode atrasar alguns minutos em horários de pico —
> isso é normal e não é problema.

---

## 10. Manutenção do dia a dia

### Adicionar ou corrigir nomeações à mão (recomendado)

O arquivo **`seed/seed.json`** é a sua "fonte da verdade". Tudo que estiver nele
**sempre aparece** e **nunca é apagado** pelo robô. Use-o para garantir os dados
de TREs que o coletor ainda não pegou, ou para corrigir algum nome.

Cada nomeação é um bloco assim (copie um existente e edite):

```json
{
  "uf": "SP",
  "orgao": "São Paulo",
  "cargo": "Analista Judiciário",
  "area": "TI",
  "especialidade": "Tecnologia da Informação",
  "nome": "Fulano de Tal",
  "data_br": "15/09/2025",
  "data": "2025-09-15",
  "portaria": "PORTARIA Nº 200",
  "url": "https://www.in.gov.br/web/dou/-/link-da-portaria",
  "fonte": "seed"
}
```

Regras simples: `uf` deve ser a sigla do estado (ou `TSE`); `data` é a mesma data
de `data_br` mas no formato ano-mês-dia (para ordenar). Depois de editar, faça o
upload do arquivo atualizado (igual à [seção 6](#6-enviar-os-arquivos-para-o-github))
ou rode o Actions de novo — o painel se atualiza.

### Ajustar as buscas e os filtros

Tudo isso está em **`collector/config.py`**, bem comentado:

- `CONSULTAS` — as frases pesquisadas no DOU. Adicione novas para ampliar a captura.
- `PALAVRAS_TI` — termos que marcam um cargo como TI.
- `ORGAOS` — a lista dos 28 tribunais (já completa).

---

## 11. Rodar e testar no seu computador (opcional)

Útil para ver o resultado antes de subir. Precisa do **Python 3** instalado.

```bash
# 1) entrar na pasta do projeto e instalar a dependência
pip install -r collector/requirements.txt

# 2) rodar o coletor (gera/atualiza data/nomeacoes.json)
python collector/collect.py

# 3) abrir o dashboard com um servidor local
python -m http.server 8000
# agora acesse no navegador:  http://localhost:8000
```

> ⚠️ Não abra o `index.html` com duplo-clique (`file://`): o navegador bloqueia a
> leitura do JSON nesse modo. Use o `python -m http.server` acima, ou o GitHub Pages.

---

## 12. Solução de problemas

**O site abre mas não mostra dados / fica vazio.**
Você provavelmente abriu o `index.html` por `file://`. Use o servidor local
(seção 11) ou acesse pelo endereço do GitHub Pages.

**O Actions falhou (❌ vermelho).**
Abra a aba **Actions**, clique na execução que falhou e leia o passo em vermelho.
O motivo mais comum é não ter marcado **Read and write permissions** (seção 8).

**O robô rodou mas não adicionou ninguém novo.**
Normal: ou não há nomeações novas no DOU, ou o formato da portaria fugiu do
padrão. Os dados do seed continuam intactos. Se souber de uma nomeação que
faltou, adicione no `seed/seed.json` (seção 10).

**Quero mudar o título, as cores ou os textos do painel.**
Tudo está no `index.html`. O título fica na tag `<title>` e no cabeçalho; as
cores usam classes do Tailwind (ex.: `indigo`, `violet`).

---

## ⚖️ Aviso

Este é um painel **independente**, sem vínculo oficial com o TSE ou os TREs.
Os dados são coletados automaticamente do Diário Oficial da União e podem conter
imprecisões. **Sempre confirme as informações na portaria oficial** (o link está
em cada linha da tabela). Trate os nomes publicados com responsabilidade — são
dados pessoais, ainda que de publicação oficial.
