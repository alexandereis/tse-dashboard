# -*- coding: utf-8 -*-
"""
COLETOR DE NOMEAÇÕES — Concurso TSE Unificado (área de TI)
==========================================================

Passos:
  1. Lê o que já temos (seed/seed.json + data/nomeacoes.json).
  2. Busca no Diário Oficial da União (in.gov.br, Seção 2) pela frase do concurso
     ("Concurso Público Nacional Unificado da Justiça Eleitoral"), que traz só as
     nomeações da Justiça Eleitoral, ordenadas por data.
  3. Para cada portaria recente, confirma o órgão, baixa o texto, extrai os
     nomeados e mantém só os de TI (com classificação, cargo e especialidade).
  4. Junta com o que já existia (sem duplicar) e grava data/nomeacoes.json.

REGRA DE OURO: se a internet falhar/limitar, NÃO apaga os dados antigos.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, date, timedelta

import requests

from config import (
    CONSULTAS, SECAO_DOU, RESULTADOS_POR_PAGINA, MAX_PAGINAS,
    DIAS_RETROATIVOS, USER_AGENT, ORGAOS,
)
from parser import (
    limpar_html, sem_acento, identificar_orgao, extrair_nomeados,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")

BASE_BUSCA = "https://www.in.gov.br/consulta/-/buscar/dou"
BASE_ARTIGO = "https://www.in.gov.br/web/dou/-/"

SESSAO = requests.Session()
SESSAO.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
})


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def chave_registro(reg):
    return (reg.get("uf", ""), reg.get("cargo", ""), sem_acento(reg.get("nome", "")))


def data_iso(data_br):
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", data_br or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def extrair_params_json(html):
    """Pega o <script type="application/json"> com os resultados (jsonArray)."""
    for m in re.finditer(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
    ):
        bloco = m.group(1).strip()
        if "jsonArray" not in bloco:
            continue
        try:
            return json.loads(bloco)
        except json.JSONDecodeError:
            continue
    return None


# ---------------------------------------------------------------------------
# Acesso ao DOU (com retry e detecção de "throttling")
# ---------------------------------------------------------------------------
def aquecer():
    """Visita a busca uma vez para obter cookies de sessão antes de coletar."""
    try:
        SESSAO.get(BASE_BUSCA, params={"q": "nomear", "s": SECAO_DOU}, timeout=40)
        time.sleep(2)
    except requests.RequestException:
        pass


def buscar_pagina(consulta, pagina, tentativas=3):
    """
    Devolve a lista de resultados (jsonArray) da página, ou None se falhar.
    Detecta a página-stub que o in.gov.br devolve quando limita as requisições
    (resposta pequena, sem jsonArray) e tenta de novo com espera crescente.
    """
    params = {
        "q": consulta, "s": SECAO_DOU, "exibirCabecalho": "true",
        "delta": RESULTADOS_POR_PAGINA, "page": pagina,
        "newPage": pagina, "currentPage": pagina, "score": "0", "sortType": "0",
    }
    for t in range(tentativas):
        try:
            r = SESSAO.get(BASE_BUSCA, params=params, timeout=45)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"   ! erro de rede (pág {pagina}, tentativa {t+1}): {e}")
            time.sleep(5 * (t + 1))
            continue
        if len(r.text) < 50000:   # página-stub de limite de requisições
            print(f"   ~ resposta curta ({len(r.text)} bytes) — limite do site; aguardando…")
            time.sleep(10 * (t + 1))
            continue
        dados = extrair_params_json(r.text)
        if dados is None:
            time.sleep(6 * (t + 1))
            continue
        return dados.get("jsonArray", []) or []
    return None


def baixar_texto_portaria(url_title):
    """Baixa o texto completo de uma portaria a partir do 'urlTitle'."""
    url = BASE_ARTIGO + url_title
    try:
        r = SESSAO.get(url, timeout=45)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"   ! erro ao baixar portaria: {e}")
        return "", url
    time.sleep(1)  # gentileza entre artigos

    dados = extrair_params_json(r.text)
    if dados:
        for chave in ("conteudo", "content", "texto"):
            if isinstance(dados.get(chave), str) and len(dados[chave]) > 50:
                return limpar_html(dados[chave]), url
        arr = dados.get("jsonArray") or []
        if arr and isinstance(arr[0], dict) and arr[0].get("content"):
            return limpar_html(arr[0]["content"]), url

    m = re.search(r'<div[^>]*class="[^"]*texto-dou[^"]*"[^>]*>(.*?)</div>\s*</div>',
                  r.text, re.DOTALL)
    if m:
        return limpar_html(m.group(1)), url
    return limpar_html(r.text), url


# ---------------------------------------------------------------------------
# Transformar uma portaria em registros de nomeados
# ---------------------------------------------------------------------------
def processar_portaria(item):
    titulo = item.get("title", "") or ""
    pub_date = item.get("pubDate", "") or item.get("date", "") or ""
    hierarquia = item.get("hierarchyStr", "") or item.get("hierarchy", "") or ""
    url_title = item.get("urlTitle", "") or ""
    snippet = limpar_html(item.get("content", "") or "")

    if "nomear" not in sem_acento(titulo + " " + snippet):
        return []

    # 1) Filtra por ÓRGÃO usando o cabeçalho da busca, ANTES de baixar o artigo
    #    (a busca traz portarias de vários órgãos; só seguimos com os da Justiça
    #    Eleitoral, economizando requisições).
    sigla = identificar_orgao(hierarquia, titulo, snippet)
    if not sigla:
        return []

    # 2) Agora sim baixa o texto completo e extrai os nomeados de TI.
    texto, url = baixar_texto_portaria(url_title) if url_title else (snippet, "")
    if not texto:
        texto = snippet
    if not sigla:
        sigla = identificar_orgao(hierarquia, titulo, texto)
        if not sigla:
            return []

    nomeados = extrair_nomeados(texto)
    if not nomeados:
        return []

    mport = re.search(r"(PORTARIA|ATO)[^\d]*(\d[\d.]*)", titulo, re.IGNORECASE)
    rotulo_portaria = (f"{mport.group(1).upper()} Nº {mport.group(2)}"
                       if mport else (titulo[:45] or "Portaria"))
    info = ORGAOS[sigla]
    mdata = re.search(r"\d{2}/\d{2}/\d{4}", pub_date)
    data_br = mdata.group(0) if mdata else pub_date

    registros = []
    for nd in nomeados:
        registros.append({
            "uf": sigla, "orgao": info["rotulo"], "cargo": nd["cargo"], "area": "TI",
            "especialidade": nd["especialidade"] or "Tecnologia da Informação",
            "nome": nd["nome"], "classificacao": nd["classificacao"],
            "data": data_iso(data_br), "data_br": data_br,
            "portaria": rotulo_portaria, "url": url, "fonte": "dou",
        })
    return registros


def _data_item(item):
    m = re.search(r"\d{2}/\d{2}/\d{4}", item.get("pubDate", "") or "")
    return data_iso(m.group(0)) if m else ""


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
def coletar_do_dou():
    """Roda as consultas e devolve os registros encontrados (lista)."""
    corte = (date.today() - timedelta(days=DIAS_RETROATIVOS)).isoformat()
    encontrados = {}
    vistas = set()

    for consulta in CONSULTAS:
        print(f"\n> Consulta: {consulta}")
        for pagina in range(1, MAX_PAGINAS + 1):
            resultados = buscar_pagina(consulta, pagina)
            if not resultados:   # None (falha/limite) ou [] (sem mais) → encerra
                break
            recentes = 0
            for item in resultados:
                di = _data_item(item)
                if di and di < corte:        # fora da janela de datas
                    continue
                recentes += 1
                ut = item.get("urlTitle", "")
                if ut in vistas:
                    continue
                vistas.add(ut)
                for reg in processar_portaria(item):
                    encontrados[chave_registro(reg)] = reg
            print(f"   página {pagina}: {len(resultados)} result., {recentes} na janela, "
                  f"{len(encontrados)} de TI até agora")
            if recentes == 0:    # resultados já passaram da janela (ordenado por data)
                break
            time.sleep(2)
            if len(resultados) < RESULTADOS_POR_PAGINA:
                break
        time.sleep(3)            # pausa entre consultas
    return list(encontrados.values())


def main():
    print("=" * 60)
    print("COLETOR DE NOMEAÇÕES — Concurso TSE Unificado (TI)")
    print("=" * 60)

    seed = carregar_json(ARQ_SEED, [])
    anterior = carregar_json(ARQ_DADOS, {"registros": []}).get("registros", [])

    base = {}
    for reg in seed:
        reg = dict(reg)
        reg["fonte"] = "seed"
        reg.setdefault("data", data_iso(reg.get("data_br", "")))
        base[chave_registro(reg)] = reg
    for reg in anterior:
        if chave_registro(reg) not in base:
            base[chave_registro(reg)] = reg
    print(f"\nRegistros de base (seed + histórico): {len(base)}")

    try:
        aquecer()
        novos = coletar_do_dou()
    except Exception as e:
        print(f"\n! Falha inesperada na coleta: {e}")
        novos = []

    add = 0
    for reg in novos:
        ch = chave_registro(reg)
        if ch not in base:
            base[ch] = reg
            add += 1
    print(f"\nNovos registros adicionados pelo DOU: {add}")

    registros = sorted(base.values(),
                       key=lambda r: (r.get("data", ""), r.get("nome", "")),
                       reverse=True)

    def assinatura(lista):
        campos = ("uf", "cargo", "nome", "data", "data_br", "portaria", "url")
        return sorted("|".join(str(r.get(c, "")) for c in campos) for r in lista)

    if assinatura(registros) == assinatura(anterior):
        print("\nNenhuma novidade no DOU desde a última execução. Arquivo NÃO alterado.")
        return 0

    saida = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(registros), "registros": registros,
    }
    os.makedirs(os.path.dirname(ARQ_DADOS), exist_ok=True)
    with open(ARQ_DADOS, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    print(f"\nOK! Houve novidade. {len(registros)} registros gravados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
