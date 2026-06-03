# -*- coding: utf-8 -*-
"""
COLETOR DE NOMEAÇÕES — Concurso TSE Unificado (área de TI)
==========================================================

O que este programa faz, em passos:

  1. Lê os dados que já temos (seed/seed.json + data/nomeacoes.json).
  2. Pergunta ao buscador do Diário Oficial da União (in.gov.br), na Seção 2,
     por portarias de nomeação da Justiça Eleitoral (TSE + TREs).
  3. Para cada portaria encontrada, baixa o texto completo, descobre o órgão
     (UF), o cargo e os nomes; e mantém só os de TI.
  4. Junta tudo com o que já existia (sem duplicar) e grava data/nomeacoes.json.

REGRA DE OURO: se a internet falhar ou o site mudar, o programa NÃO apaga os
dados antigos. Ele apenas mantém o que já havia. Assim o dashboard nunca quebra.

Rode com:  python collect.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

from config import (
    CONSULTAS, SECAO_DOU, RESULTADOS_POR_PAGINA, MAX_PAGINAS,
    USER_AGENT, ORGAOS,
)
from parser import (
    limpar_html, sem_acento, identificar_orgao, extrair_cargo,
    extrair_especialidade, eh_ti, extrair_nomes,
)

# Caminhos (relativos à raiz do projeto).
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")

BASE_BUSCA = "https://www.in.gov.br/consulta/-/buscar/dou"
BASE_ARTIGO = "https://www.in.gov.br/web/dou/-/"

SESSAO = requests.Session()
SESSAO.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})


# ---------------------------------------------------------------------------
# Utilidades de arquivo
# ---------------------------------------------------------------------------
def carregar_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return padrao


def chave_registro(reg):
    """Identidade única de um nomeado: UF + cargo + nome (sem acento)."""
    return (reg.get("uf", ""), reg.get("cargo", ""), sem_acento(reg.get("nome", "")))


def data_iso(data_br):
    """'07/08/2025' -> '2025-08-07' (para ordenar). Devolve '' se não der."""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", data_br or "")
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""


# ---------------------------------------------------------------------------
# Acesso ao buscador do DOU
# ---------------------------------------------------------------------------
def extrair_params_json(html):
    """
    As páginas do in.gov.br trazem um bloco escondido:
        <script id="params" type="application/json">{...}</script>
    que contém os resultados em JSON. Esta função devolve esse dicionário.
    """
    m = re.search(
        r'<script[^>]*id="params"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def buscar_pagina(consulta, pagina):
    """Faz uma busca e devolve a lista de resultados (jsonArray) daquela página."""
    params = {
        "q": consulta,
        "s": SECAO_DOU,
        "exibirCabecalho": "true",
        "delta": RESULTADOS_POR_PAGINA,
        "page": pagina,
        "newPage": pagina,
        "currentPage": pagina,
        "score": "0",
        "sortType": "0",
    }
    try:
        r = SESSAO.get(BASE_BUSCA, params=params, timeout=40)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"   ! erro de rede na busca (pág {pagina}): {e}")
        return None
    dados = extrair_params_json(r.text)
    if not dados:
        return []
    return dados.get("jsonArray", []) or []


def baixar_texto_portaria(url_title):
    """Baixa o texto completo de uma portaria a partir do seu 'urlTitle'."""
    url = BASE_ARTIGO + url_title
    try:
        r = SESSAO.get(url, timeout=40)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"   ! erro ao baixar portaria: {e}")
        return "", url

    # 1ª tentativa: bloco JSON com o conteúdo do artigo.
    dados = extrair_params_json(r.text)
    if dados:
        for chave in ("conteudo", "content", "texto"):
            if isinstance(dados.get(chave), str) and len(dados[chave]) > 50:
                return limpar_html(dados[chave]), url
        arr = dados.get("jsonArray") or []
        if arr and isinstance(arr[0], dict) and arr[0].get("content"):
            return limpar_html(arr[0]["content"]), url

    # 2ª tentativa: div com a classe do corpo da matéria.
    m = re.search(r'<div[^>]*class="[^"]*texto-dou[^"]*"[^>]*>(.*?)</div>\s*</div>',
                  r.text, re.DOTALL)
    if m:
        return limpar_html(m.group(1)), url

    # 3ª tentativa (fallback): limpa a página inteira.
    return limpar_html(r.text), url


# ---------------------------------------------------------------------------
# Transformar uma portaria em registros de nomeados
# ---------------------------------------------------------------------------
def processar_portaria(item):
    """
    Recebe um resultado da busca (item do jsonArray) e devolve uma lista de
    registros de nomeados de TI encontrados naquela portaria.
    """
    titulo = item.get("title", "") or ""
    pub_date = item.get("pubDate", "") or item.get("date", "") or ""
    hierarquia = item.get("hierarchyStr", "") or item.get("hierarchy", "") or ""
    url_title = item.get("urlTitle", "") or ""
    snippet = limpar_html(item.get("content", "") or "")

    # Precisa ser uma portaria de NOMEAÇÃO.
    if "nomear" not in sem_acento(titulo + " " + snippet):
        return []

    texto, url = baixar_texto_portaria(url_title) if url_title else (snippet, "")
    if not texto:
        texto = snippet

    # Identifica o órgão (TSE ou TRE) e, com ele, a UF.
    sigla = identificar_orgao(hierarquia, titulo, texto)
    if not sigla:
        return []

    # Só interessa se a portaria fala de cargo de TI.
    if not eh_ti(titulo, texto):
        return []

    cargo = extrair_cargo(titulo) or extrair_cargo(texto) or ""
    especialidade = extrair_especialidade(texto)

    # Número da portaria (rótulo curto para o link).
    mport = re.search(r"PORTARIA[^\d]*(\d+)", titulo, re.IGNORECASE)
    rotulo_portaria = f"PORTARIA Nº {mport.group(1)}" if mport else (titulo[:40] or "Portaria")

    nomes = extrair_nomes(texto)
    if not nomes:
        return []

    info = ORGAOS[sigla]
    data_br = re.search(r"\d{2}/\d{2}/\d{4}", pub_date)
    data_br = data_br.group(0) if data_br else pub_date

    registros = []
    for nome in nomes:
        registros.append({
            "uf": sigla,
            "orgao": info["rotulo"],
            "cargo": cargo or "Não identificado",
            "area": "TI",
            "especialidade": especialidade,
            "nome": nome,
            "data": data_iso(data_br),
            "data_br": data_br,
            "portaria": rotulo_portaria,
            "url": url,
            "fonte": "dou",
        })
    return registros


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
def coletar_do_dou():
    """Roda todas as consultas e devolve os registros encontrados (lista)."""
    encontrados = {}
    portarias_vistas = set()

    for consulta in CONSULTAS:
        print(f"\n> Consulta: {consulta}")
        for pagina in range(1, MAX_PAGINAS + 1):
            resultados = buscar_pagina(consulta, pagina)
            if resultados is None:      # erro de rede → encerra esta consulta
                break
            if not resultados:          # sem mais resultados
                break
            print(f"   página {pagina}: {len(resultados)} resultado(s)")
            for item in resultados:
                ut = item.get("urlTitle", "")
                if ut in portarias_vistas:
                    continue
                portarias_vistas.add(ut)
                for reg in processar_portaria(item):
                    encontrados[chave_registro(reg)] = reg
            time.sleep(1)  # gentileza com o servidor
            if len(resultados) < RESULTADOS_POR_PAGINA:
                break
    return list(encontrados.values())


def main():
    print("=" * 60)
    print("COLETOR DE NOMEAÇÕES — Concurso TSE Unificado (TI)")
    print("=" * 60)

    # 1) Base: seed (dados verificados à mão) + dados já coletados antes.
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

    # 2) Coleta nova no DOU.
    try:
        novos = coletar_do_dou()
    except Exception as e:                 # nunca deixa o erro derrubar tudo
        print(f"\n! Falha inesperada na coleta: {e}")
        novos = []

    add = 0
    for reg in novos:
        ch = chave_registro(reg)
        if ch not in base:                 # seed/histórico sempre têm prioridade
            base[ch] = reg
            add += 1
    print(f"\nNovos registros adicionados pelo DOU: {add}")

    # 3) Ordena (mais recentes primeiro).
    registros = sorted(
        base.values(),
        key=lambda r: (r.get("data", ""), r.get("nome", "")),
        reverse=True,
    )

    # 4) Só grava se houve mudança real em relação à execução anterior.
    #    (Comparamos o CONTEÚDO dos registros, ignorando o horário de atualização.)
    def assinatura(lista):
        campos = ("uf", "cargo", "nome", "data", "data_br", "portaria", "url")
        return sorted("|".join(str(r.get(c, "")) for c in campos) for r in lista)

    if assinatura(registros) == assinatura(anterior):
        print("\nNenhuma novidade no DOU desde a última execução. "
              "Arquivo NÃO foi alterado (o site continua igual).")
        return 0

    saida = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(registros),
        "registros": registros,
    }
    os.makedirs(os.path.dirname(ARQ_DADOS), exist_ok=True)
    with open(ARQ_DADOS, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"\nOK! Houve novidade. {len(registros)} registros gravados em data/nomeacoes.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
