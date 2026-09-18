# -*- coding: utf-8 -*-
"""
CORREÇÕES DO DOU — republicação e retificação — memória permanente e aplicação
na base.

Por que isto existe: quando o Diário erra o nome de um nomeado, ele NÃO publica
uma nomeação nova — ele republica o ato ("Republicada por incorreção no nome do
candidato…") ou publica uma retificação ("Onde se lê… Leia-se…"). Como a chave
de um registro é o nome, o coletor via um nome diferente e criava uma SEGUNDA
pessoa: "Guilherme Ramalho" (TRE-PB, 24/08/2026) e "Guilherme Ramalho
Magalhães" (a republicação, 16/09/2026) eram a mesma pessoa em duas linhas do
painel, em dias diferentes.

Por que um arquivo PRÓPRIO e permanente (data/correcoes.json), como as
anulações: renomear o registro no data/nomeacoes.json não resolve. O seed (base
curada) traz a grafia antiga de volta na execução seguinte, e a republicação já
terá saído da janela de dias que o coletor varre. A correção precisa de memória
própria, reaplicada toda vez que a base é montada.

O QUE a correção faz com a nomeação original (errar aqui inventa ou apaga
gente):
  * a nomeação continua com a DATA e o ATO originais — a convocação aconteceu
    no dia em que saiu a primeira vez; a republicação só conserta o texto;
  * o nome passa a ser o corrigido, e a grafia anterior fica guardada em
    "nome_publicado" (é por ela que alguém acha o nome que leu no DOU antigo);
  * o registro criado pela republicação, com a data da republicação, é
    descartado — é a mesma pessoa.

O que este módulo NÃO faz de propósito: apagar nomeado. Se o ato republicado
não traz mais alguém que o original trazia, isso vira ALERTA para olho humano —
uma nomeação que some em silêncio é o pior defeito possível aqui.
"""

import json
import os
import re
import unicodedata
from datetime import datetime, timezone

# Quanto tempo para trás a correção pode alcançar. Número de portaria se repete
# a cada ano ("Portaria nº 312" existe em 2025 e em 2026); sem esse limite, uma
# republicação poderia casar com o ato homônimo do ano passado.
DIAS_ALCANCE = 365

_CONECTIVOS = {"de", "da", "do", "dos", "das", "e"}


def _sem_acento(texto):
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _numero(rotulo):
    """Só os dígitos do rótulo: 'PORTARIA Nº 312' e 'Portaria 312/2026' -> '312'."""
    m = re.search(r"(\d[\d.]*)", rotulo or "")
    return m.group(1).replace(".", "").lstrip("0") if m else ""


def _chave_nome(reg):
    return (reg.get("cargo", ""), _sem_acento(reg.get("nome", "")))


def chave_correcao(c):
    return (c.get("uf", ""), _numero(c.get("ato", "")),
            _sem_acento(c.get("nome_anterior", "")), _sem_acento(c.get("nome", "")))


def _tokens(nome):
    return {t for t in _sem_acento(nome).split() if t not in _CONECTIVOS}


def _mesma_pessoa(a, b):
    """Os dois nomes são a mesma pessoa escrita de outro jeito?

    Vale quando um contém o outro ("Guilherme Ramalho" ⊂ "Guilherme Ramalho
    Magalhães") ou quando só uma palavra difere — que é como o DOU erra: troca
    uma letra do sobrenome ("BARRETO"/"BARRETTO") ou come um nome do meio.
    """
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    if ta <= tb or tb <= ta:
        return True
    comuns = len(ta & tb)
    return comuns >= 2 and comuns >= min(len(ta), len(tb)) - 1


def _dias(d1, d2):
    fmt = "%Y-%m-%d"
    try:
        return abs((datetime.strptime(d1, fmt) - datetime.strptime(d2, fmt)).days)
    except (ValueError, TypeError):
        return 10 ** 6


def _correcao(uf, ato, antes, depois, marca):
    """Uma linha do arquivo: quem era, quem passou a ser e qual ato corrigiu."""
    return {
        "uf": uf,
        "ato": ato,                                   # o ato corrigido
        "tipo": marca["tipo"],                        # republicacao | retificacao
        "cargo_anterior": antes.get("cargo", ""),
        "nome_anterior": antes.get("nome", ""),
        "cargo": depois.get("cargo", ""),
        "nome": depois.get("nome", ""),
        "especialidade": depois.get("especialidade", ""),
        "classificacao": depois.get("classificacao", 0),
        "data": depois.get("data", ""),               # quando a correção saiu
        "data_br": depois.get("data_br", ""),
        "url": depois.get("url", ""),
    }


def _parear(originais, novos):
    """Casa cada nomeado do ato corrigido com o da versão corrigida.

    Ordem das tentativas, da mais segura para a menos:
      1. mesmo cargo e mesma classificação (quando o ato declara a colocação —
         duas pessoas não disputam a mesma colocação do mesmo cargo);
      2. nomes parecidos (veja `_mesma_pessoa`);
      3. sobrou exatamente um de cada lado, no mesmo cargo — é a correção que
         troca o nome inteiro.
    Devolve (pares, originais_sem_par, novos_sem_par).
    """
    o, n = list(originais), list(novos)
    pares = []

    def casar(condicao):
        for novo in list(n):
            achados = [x for x in o if condicao(x, novo)]
            if len(achados) == 1:
                pares.append((achados[0], novo))
                o.remove(achados[0])
                n.remove(novo)

    casar(lambda x, y: (x.get("cargo") == y.get("cargo")
                        and x.get("classificacao") and y.get("classificacao")
                        and x["classificacao"] == y["classificacao"]))
    casar(lambda x, y: _mesma_pessoa(x.get("nome", ""), y.get("nome", "")))
    if len(o) == 1 and len(n) == 1 and o[0].get("cargo") == n[0].get("cargo"):
        pares.append((o[0], n[0]))
        o, n = [], []
    return pares, o, n


def detectar(novos, registros_base, conhecidas=()):
    """Acha as correções que os atos desta execução declaram.

    `novos` são os registros que o coletor acabou de ler (os que vieram de um
    ato de correção carregam a marca "_correcao"); `registros_base` é o que o
    painel já tem. Devolve (correções, alertas) — alerta é texto para olho
    humano, nunca decisão automática.
    """
    alertas = []
    sabidas = {chave_correcao(c) for c in conhecidas}
    # Grafias que uma correção JÁ conhecida substituiu. O seed continua trazendo
    # a antiga a cada execução; sem isso, enquanto a republicação estivesse na
    # janela do coletor, todo dia sairia um alerta de "não traz mais fulano"
    # para alguém que já foi corrigido.
    substituidas = {(c.get("uf", ""), _numero(c.get("ato", "")),
                     _sem_acento(c.get("nome_anterior", ""))) for c in conhecidas}
    atos = {}
    for reg in novos:
        if reg.get("_correcao"):
            atos.setdefault(reg.get("url", ""), []).append(reg)

    achadas = []
    for url, regs in sorted(atos.items()):
        marca = regs[0]["_correcao"]
        uf = regs[0].get("uf", "")
        data_corr = regs[0].get("data", "")
        numero = _numero(marca.get("ato", ""))
        # Só é correção da PRÓPRIA nomeação quando o ato corrigido é o ato de
        # onde estes nomes saíram: a republicação repete o número da portaria e
        # a retificação avulsa herda o rótulo do ato que ela conserta. Um ato
        # comum que por acaso retifica OUTRA portaria não renomeia ninguém.
        if not numero or any(_numero(r.get("portaria")) != numero for r in regs):
            alertas.append(f"{uf}: {marca['tipo']} de {marca.get('ato')} citada em "
                           f"{regs[0].get('portaria')} — não casa com o ato, nada foi "
                           f"alterado ({url})")
            continue

        originais = [r for r in registros_base
                     if r.get("uf") == uf
                     and _numero(r.get("portaria")) == numero
                     and (r.get("url") or "") != url
                     and (r.get("data") or "") < data_corr
                     and _dias(r.get("data") or "", data_corr) <= DIAS_ALCANCE]
        if marca.get("data_original"):
            exatos = [r for r in originais if r.get("data") == marca["data_original"]]
            if exatos:
                originais = exatos
        if originais:                      # o ato original mais recente é o corrigido
            ultima = max(r.get("data", "") for r in originais)
            originais = [r for r in originais if r.get("data") == ultima]
        if not originais:
            continue                       # nada na base para corrigir: segue como está

        chaves_novas = {_chave_nome(r) for r in regs}
        chaves_orig = {_chave_nome(r) for r in originais}
        pares, sem_par_orig, sem_par_novo = _parear(
            [r for r in originais if _chave_nome(r) not in chaves_novas
             and (uf, numero, _sem_acento(r.get("nome", ""))) not in substituidas],
            [r for r in regs if _chave_nome(r) not in chaves_orig])

        for antes, depois in pares:
            c = _correcao(uf, marca["ato"], antes, depois, marca)
            if chave_correcao(c) not in sabidas:
                sabidas.add(chave_correcao(c))
                achadas.append(c)
        for r in sem_par_orig:
            alertas.append(f"{uf}: {marca['tipo']} de {marca['ato']} não traz mais "
                           f"{r.get('nome')} ({r.get('cargo')}) — confira o ato: {url}")
        for r in sem_par_novo:
            alertas.append(f"{uf}: {marca['tipo']} de {marca['ato']} traz "
                           f"{r.get('nome')} ({r.get('cargo')}), que não estava no ato "
                           f"original — entrou como nomeação nova: {url}")
    return achadas, alertas


def _limpar(registro):
    """Cópia do registro sem as marcas internas do coletor (as que começam com
    "_" não vão para o arquivo publicado)."""
    return {k: v for k, v in registro.items() if not k.startswith("_")}


def aplicar(registros, correcoes):
    """Devolve (registros corrigidos, quantas correções pegaram).

    A nomeação corrigida fica com o nome novo, guarda a grafia publicada em
    "nome_publicado" e carrega o link do ato que corrigiu — e a linha duplicada
    que a correção tinha criado sai da base.
    """
    saida = [_limpar(r) for r in registros]
    aplicadas = 0
    for c in correcoes:
        # A nomeação pode estar na base com a grafia ANTIGA (o caso normal) ou
        # já com a corrigida — é o que acontece com as correções antigas, que
        # foram acertadas à mão no seed antes de este arquivo existir. Nos dois
        # casos o registro fica igual: nome corrigido e a grafia publicada
        # guardada, que é como a varredura reconhece o ato original.
        alvos = {_sem_acento(c.get("nome_anterior", "")), _sem_acento(c.get("nome", ""))}
        cargos = {c.get("cargo_anterior", ""), c.get("cargo", "")}
        numero = _numero(c.get("ato", ""))
        for i, r in enumerate(saida):
            if (r.get("uf") != c.get("uf")
                    or _sem_acento(r.get("nome", "")) not in alvos
                    or r.get("cargo", "") not in cargos
                    or _numero(r.get("portaria")) != numero
                    or (r.get("data") or "") > (c.get("data") or "")):
                continue
            corrigido = dict(r)
            corrigido.update({
                "cargo": c.get("cargo") or r.get("cargo"),
                "nome": c.get("nome") or r.get("nome"),
                "nome_publicado": (r.get("nome_publicado")
                                   or c.get("nome_anterior") or r.get("nome")),
                "corrigido_em": c.get("data", ""),
                "corrigido_em_br": c.get("data_br", ""),
                "corrigido_url": c.get("url", ""),
                "corrigido_tipo": c.get("tipo", ""),
            })
            if c.get("especialidade"):
                corrigido["especialidade"] = c["especialidade"]
            if c.get("classificacao"):
                corrigido["classificacao"] = c["classificacao"]
            saida[i] = corrigido
            aplicadas += 1

    # A republicação virou um registro próprio (com a data da republicação)
    # antes de a correção ser conhecida; agora ele tem a mesma chave da
    # nomeação corrigida. Fica a nomeação ORIGINAL, que é a que tem a data certa.
    unicos = {}
    for r in sorted(saida, key=lambda x: (x.get("data") or "9999", x.get("corrigido_em") or "")):
        unicos.setdefault((r.get("uf", ""), r.get("cargo", ""),
                           _sem_acento(r.get("nome", ""))), r)
    return list(unicos.values()), aplicadas


def carregar(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if isinstance(dados, dict):
        return dados.get("correcoes", []) or []
    return dados or []


def salvar(caminho, correcoes):
    """Grava sem duplicar, em ordem cronológica. Devolve quantas ficaram.

    Não regrava quando nada mudou: o robô roda ~20x por dia e um "atualizado_em"
    novo a cada rodada viraria um commit por execução, sem nada de novo dentro.
    """
    unicas = {}
    for c in correcoes:
        unicas.setdefault(chave_correcao(c), c)
    lista = sorted(unicas.values(),
                   key=lambda c: (c.get("data", ""), c.get("uf", ""), c.get("nome", "")))
    if lista == carregar(caminho):
        return len(lista)
    saida = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(lista),
        "correcoes": lista,
    }
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    return len(lista)
