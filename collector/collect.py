# -*- coding: utf-8 -*-
"""
COLETOR DE NOMEAÇÕES — Concurso TSE Unificado (área de TI)
==========================================================

Descobre as portarias por DOIS caminhos (e junta tudo, sem duplicar):

  FASE 1 — BUSCA (`/consulta/-/buscar`): mostra publicações do DIA, então pega
           nomeações no mesmo dia. Pode falhar (502) em alguns ambientes; se
           falhar, seguimos para a fase 2.
  FASE 2 — EDIÇÃO DIÁRIA (`leiturajornal`): um GET por dia, bem estável; serve de
           rede de segurança. O índice do dia às vezes demora a sair, por isso a
           fase 1 vem antes.

Para cada portaria encontrada: confirma o órgão, baixa o texto, extrai os
nomeados e mantém só os de TI (nome, classificação, cargo, especialidade).

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
    SECAO_DOU, DIAS_RETROATIVOS, USER_AGENT, ORGAOS,
    CONSULTAS, RESULTADOS_POR_PAGINA, MAX_PAGINAS,
)
from parser import (
    limpar_html, sem_acento, identificar_orgao, extrair_nomeados,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")

BASE_EDICAO = "https://www.in.gov.br/leiturajornal"
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


def _data_item(item):
    m = re.search(r"\d{2}/\d{2}/\d{4}", item.get("pubDate", "") or item.get("date", "") or "")
    return data_iso(m.group(0)) if m else ""


def extrair_params_json(html):
    """Pega o <script type="application/json"> com 'jsonArray' — escolhe o de
    maior jsonArray (a página tem vários scripts; o certo é o maior)."""
    melhor = None
    melhor_n = -1
    for m in re.finditer(
        r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL
    ):
        bloco = m.group(1).strip()
        if "jsonArray" not in bloco:
            continue
        try:
            dados = json.loads(bloco)
        except json.JSONDecodeError:
            continue
        n = len(dados.get("jsonArray") or [])
        if n > melhor_n:
            melhor, melhor_n = dados, n
    return melhor


# ---------------------------------------------------------------------------
# Acesso ao DOU (com retry e detecção de resposta curta/limite)
# ---------------------------------------------------------------------------
def aquecer():
    try:
        SESSAO.get(BASE_EDICAO,
                   params={"data": date.today().strftime("%d-%m-%Y"), "secao": SECAO_DOU},
                   timeout=60)
        time.sleep(2)
    except requests.RequestException:
        pass


def buscar_consulta(consulta, paginas=MAX_PAGINAS, tentativas=2):
    """FASE 1 — resultados da busca (jsonArray) para uma consulta, ordenados por
    data (mais recente primeiro). Retorna lista de itens (pode ser vazia)."""
    itens = []
    for pagina in range(1, paginas + 1):
        params = {
            "q": consulta, "s": SECAO_DOU, "exibirCabecalho": "true",
            "delta": RESULTADOS_POR_PAGINA, "page": pagina,
            "newPage": pagina, "currentPage": pagina, "score": "0", "sortType": "0",
        }
        dados = None
        for t in range(tentativas):
            try:
                r = SESSAO.get(BASE_BUSCA, params=params, timeout=45)
                r.raise_for_status()
            except requests.RequestException as e:
                print(f"   ! busca: erro de rede (pág {pagina}, tent {t+1}): {e}")
                time.sleep(5 * (t + 1))
                continue
            if len(r.text) < 5000:
                print(f"   ~ busca: resposta curta ({len(r.text)} bytes); aguardando…")
                time.sleep(8 * (t + 1))
                continue
            dados = extrair_params_json(r.text)
            if dados is None:
                time.sleep(6 * (t + 1))
                continue
            break
        if not dados:
            break
        arr = dados.get("jsonArray", []) or []
        if not arr:
            break
        itens += arr
        time.sleep(2)
        if len(arr) < RESULTADOS_POR_PAGINA:
            break
    return itens


def baixar_edicao(data_ddmmaaaa, tentativas=4):
    """FASE 2 — lista de atos (jsonArray) da Seção 2 naquele dia, ou None."""
    params = {"data": data_ddmmaaaa, "secao": SECAO_DOU}
    for t in range(tentativas):
        try:
            r = SESSAO.get(BASE_EDICAO, params=params, timeout=60)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"   ! erro de rede ({data_ddmmaaaa}, tentativa {t+1}): {e}")
            time.sleep(5 * (t + 1))
            continue
        if len(r.text) < 5000:
            print(f"   ~ resposta curta ({len(r.text)} bytes) em {data_ddmmaaaa}; aguardando…")
            time.sleep(8 * (t + 1))
            continue
        dados = extrair_params_json(r.text)
        if dados is None:
            time.sleep(6 * (t + 1))
            continue
        return dados.get("jsonArray", []) or []
    return None


def baixar_texto_portaria(url_title, tentativas=3):
    """Baixa o texto completo de uma portaria a partir do 'urlTitle' (com retry,
    pois o artigo às vezes volta como página-stub quando há limite)."""
    url = BASE_ARTIGO + url_title
    for t in range(tentativas):
        try:
            r = SESSAO.get(url, timeout=45)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"   ! erro ao baixar portaria (tent {t+1}): {e}")
            time.sleep(4 * (t + 1))
            continue

        dados = extrair_params_json(r.text)
        if dados:
            for chave in ("conteudo", "content", "texto"):
                if isinstance(dados.get(chave), str) and len(dados[chave]) > 50:
                    time.sleep(1)
                    return limpar_html(dados[chave]), url
            arr = dados.get("jsonArray") or []
            if arr and isinstance(arr[0], dict) and arr[0].get("content"):
                texto = limpar_html(arr[0]["content"])
                if len(texto) > 200:
                    time.sleep(1)
                    return texto, url
        m = re.search(r'<div[^>]*class="[^"]*texto-dou[^"]*"[^>]*>(.*?)</div>\s*</div>',
                      r.text, re.DOTALL)
        if m:
            time.sleep(1)
            return limpar_html(m.group(1)), url
        # resposta sem conteúdo útil (stub) — espera e tenta de novo
        time.sleep(5 * (t + 1))
    return "", url


# ---------------------------------------------------------------------------
# Filtro e transformação
# ---------------------------------------------------------------------------
def eh_nomeacao_je(item):
    hier = item.get("hierarchyStr", "") or ""
    title = item.get("title", "") or ""
    if "eleitoral" not in sem_acento(hier + " " + title):
        return False
    blob = sem_acento(title + " " + limpar_html(item.get("content", "") or ""))
    return "nome" in blob   # "nomear", "nomeia", "nomeação"…


def processar_portaria(item, dia=None):
    titulo = item.get("title", "") or ""
    hierarquia = item.get("hierarchyStr", "") or ""
    url_title = item.get("urlTitle", "") or ""
    snippet = limpar_html(item.get("content", "") or "")

    sigla = identificar_orgao(hierarquia, titulo, snippet)
    if not sigla:
        return []

    texto, url = baixar_texto_portaria(url_title) if url_title else (snippet, "")
    if not texto:
        texto = snippet

    nomeados = extrair_nomeados(texto)
    if not nomeados:
        return []

    mport = re.search(r"(PORTARIA|ATO)[^\d]*(\d[\d.]*)", titulo, re.IGNORECASE)
    rotulo_portaria = (f"{mport.group(1).upper()} Nº {mport.group(2)}"
                       if mport else (titulo[:45] or "Portaria"))
    info = ORGAOS[sigla]

    # data: prioriza a pubDate do item; senão o dia da edição
    di = _data_item(item)
    if di:
        data = di
        data_br = f"{di[8:10]}/{di[5:7]}/{di[0:4]}"
    elif dia:
        data = dia.isoformat()
        data_br = dia.strftime("%d/%m/%Y")
    else:
        data = data_br = ""

    registros = []
    for nd in nomeados:
        registros.append({
            "uf": sigla, "orgao": info["rotulo"], "cargo": nd["cargo"], "area": "TI",
            "especialidade": nd["especialidade"] or "Tecnologia da Informação",
            "nome": nd["nome"], "classificacao": nd["classificacao"],
            "data": data, "data_br": data_br,
            "portaria": rotulo_portaria, "url": url, "fonte": "dou",
        })
    return registros


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
def coletar_do_dou():
    corte = (date.today() - timedelta(days=DIAS_RETROATIVOS)).isoformat()
    encontrados = {}
    vistas = set()

    # ---- FASE 1: BUSCA (pega o mesmo dia) --------------------------------
    for consulta in CONSULTAS:
        print(f"\n> Busca: {consulta}")
        try:
            # 3 páginas (60 resultados) bastam: a busca vem ordenada por data,
            # então os recentes estão no topo — mantém a execução rápida.
            itens = buscar_consulta(consulta, paginas=3)
        except Exception as e:
            print(f"   ! busca falhou: {e}")
            itens = []
        recentes = 0
        for item in itens:
            di = _data_item(item)
            if di and di < corte:
                continue
            recentes += 1
            ut = item.get("urlTitle", "")
            if not ut or ut in vistas:
                continue
            vistas.add(ut)
            for reg in processar_portaria(item):
                encontrados[chave_registro(reg)] = reg
        print(f"   busca: {len(itens)} itens, {recentes} na janela, "
              f"{len(encontrados)} de TI até agora")
        time.sleep(3)

    # ---- FASE 2: EDIÇÃO DIÁRIA (rede de segurança) ----------------------
    dia = date.today()
    while dia.isoformat() >= corte:
        ed = baixar_edicao(dia.strftime("%d-%m-%Y"))
        if ed is None:
            print(f"   {dia.isoformat()}: edição indisponível (pulando)")
            dia -= timedelta(days=1)
            continue
        je = [a for a in ed if eh_nomeacao_je(a)]
        for item in je:
            ut = item.get("urlTitle", "")
            if not ut or ut in vistas:
                continue
            vistas.add(ut)
            for reg in processar_portaria(item, dia):
                encontrados[chave_registro(reg)] = reg
        print(f"   {dia.isoformat()}: {len(ed)} atos, {len(je)} nomeações JE, "
              f"{len(encontrados)} de TI até agora")
        time.sleep(2)
        dia -= timedelta(days=1)

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
        reg["fonte"] = reg.get("fonte", "seed")
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
