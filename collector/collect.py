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
  FASE 3 — ESCAVADOR (fallback grátis): só para as datas que o in.gov.br NÃO
           cobriu. O Escavador espelha o texto oficial do DOU e costuma ter o dia
           antes do próprio in.gov.br indexar — útil quando o DOU está fora/atrasado.

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
    extrair_anulacoes,
)
import anulacoes as anul

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ_DADOS = os.path.join(RAIZ, "data", "nomeacoes.json")
ARQ_SEED = os.path.join(RAIZ, "seed", "seed.json")
ARQ_ANULACOES = os.path.join(RAIZ, "data", "anulacoes.json")

BASE_EDICAO = "https://www.in.gov.br/leiturajornal"
BASE_BUSCA = "https://www.in.gov.br/consulta/-/buscar/dou"
BASE_ARTIGO = "https://www.in.gov.br/web/dou/-/"
BASE_ESCAVADOR = "https://www.escavador.com"

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
def eh_ato_je(item):
    """O ato é da Justiça Eleitoral?

    ATENÇÃO: não dá para decidir aqui se é uma NOMEAÇÃO. O índice do dia entrega
    apenas um trecho curto (~403 caracteres) de cada ato, e portarias com
    preâmbulo longo (vários "CONSIDERANDO…") têm o "Art. 1º NOMEAR" fora desse
    trecho. Filtrar por "nomear" no trecho fazia o coletor descartar nomeações
    reais sem nem abrir a portaria. Por isso baixamos todos os atos da Justiça
    Eleitoral e deixamos o parser decidir — ele só devolve nomeações de TI.
    """
    hier = item.get("hierarchyStr", "") or ""
    title = item.get("title", "") or ""
    return "eleitoral" in sem_acento(hier + " " + title)


def processar_portaria(item, dia=None):
    """Devolve (registros, anulacoes, avaliado).

    'avaliado' diz se o ato foi REALMENTE analisado — ou seja, se a portaria
    abriu e deu para ler o texto inteiro. Só um ato avaliado pode ser marcado
    como "já visto"; se o download falhou, ele precisa continuar disponível para
    as fases seguintes e para a próxima execução (senão a nomeação some).

    'anulacoes' são as nomeações que ESTE ato tornou sem efeito — o mesmo ato
    costuma anular umas e nomear outras (o TRE-MG publica os dois em artigos
    alternados na mesma portaria), por isso as duas listas saem juntas.
    """
    titulo = item.get("title", "") or ""
    hierarquia = item.get("hierarchyStr", "") or ""
    url_title = item.get("urlTitle", "") or ""
    snippet = limpar_html(item.get("content", "") or "")

    sigla = identificar_orgao(hierarquia, titulo, snippet)

    texto, url = baixar_texto_portaria(url_title) if url_title else ("", "")
    avaliado = bool(texto)          # conseguimos o texto integral da portaria?
    if not texto:
        texto = snippet

    if not sigla:
        # O resumo que a BUSCA devolve é recortado em volta do termo procurado e
        # muitas vezes não traz o nome do tribunal; o texto completo sempre traz
        # (fica no preâmbulo, "…PRESIDENTE DO TRIBUNAL REGIONAL ELEITORAL DE …").
        sigla = identificar_orgao(texto)
    if not sigla:
        return [], [], avaliado

    nomeados = extrair_nomeados(texto)
    desfeitas = extrair_anulacoes(texto) if avaliado else []
    if not nomeados and not desfeitas:
        return [], [], avaliado

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

    anuladas = []
    for an in desfeitas:
        anuladas.append({
            "uf": sigla, "nome": an["nome"],
            "portaria_desfeita": an["portaria"],
            "data": data, "data_br": data_br,
            "ato": rotulo_portaria, "url": url,
        })
    return registros, anuladas, avaliado


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# FASE 3 — ESCAVADOR (fallback grátis quando o in.gov.br está fora/atrasado)
#   O Escavador espelha o texto oficial do DOU e costuma ter o dia antes do
#   próprio in.gov.br indexar. Só é usado para as datas que o in.gov.br NÃO
#   cobriu (evita peso desnecessário). A Justiça Eleitoral fica na parte final
#   da Seção 2, então varremos as páginas de trás para frente, com pausas.
# ---------------------------------------------------------------------------
def escavador_indice():
    """{data_iso: id} das edições recentes da Seção 2 do DOU no Escavador."""
    try:
        r = SESSAO.get(f"{BASE_ESCAVADOR}/diarios/DOU", timeout=45)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"   ! Escavador índice falhou: {e}")
        return {}
    idx = {}
    for m in re.finditer(r"/diarios/(\d+)/DOU/secao-2/(\d{4}-\d{2}-\d{2})", r.text):
        idx.setdefault(m.group(2), m.group(1))
    return idx


def _escav_total_paginas(html):
    nums = [int(n) for n in re.findall(r"[?&]page=(\d+)", html)]
    return max(nums) if nums else 1


def _registros_pagina_escavador(texto, dia_iso, url):
    """Divide o texto da página por órgão (nome do ORGAOS) e extrai os de TI.

    Devolve (registros, anulacoes) — a página do Escavador traz a seção inteira,
    então tanto as nomeações quanto os atos que desfazem nomeação passam por aqui.
    """
    alvo = sem_acento(texto)
    marcas = []
    for sigla, info in ORGAOS.items():
        nome = sem_acento(info["nome"])
        i = alvo.find(nome)
        while i >= 0:
            marcas.append((i, sigla))
            i = alvo.find(nome, i + len(nome))
    if not marcas:
        return [], []
    marcas.sort()
    data_br = f"{dia_iso[8:10]}/{dia_iso[5:7]}/{dia_iso[0:4]}"
    out = []
    anuladas = []
    for k, (pos, sigla) in enumerate(marcas):
        fim = marcas[k + 1][0] if k + 1 < len(marcas) else len(texto)
        trecho = texto[pos:fim]
        mport = re.search(r"(PORTARIA|ATO)[^\n\d]{0,20}?(\d[\d.]*)", trecho, re.IGNORECASE)
        rot = f"{mport.group(1).upper()} Nº {mport.group(2)}" if mport else "Portaria"
        info = ORGAOS[sigla]
        for nd in extrair_nomeados(trecho):
            out.append({
                "uf": sigla, "orgao": info["rotulo"], "cargo": nd["cargo"], "area": "TI",
                "especialidade": nd["especialidade"] or "Tecnologia da Informação",
                "nome": nd["nome"], "classificacao": nd["classificacao"],
                "data": dia_iso, "data_br": data_br,
                "portaria": rot, "url": url, "fonte": "escavador",
            })
        for an in extrair_anulacoes(trecho):
            anuladas.append({
                "uf": sigla, "nome": an["nome"],
                "portaria_desfeita": an["portaria"],
                "data": dia_iso, "data_br": data_br,
                "ato": rot, "url": url,
            })
    return out, anuladas


def escavador_dia(diario_id, dia_iso, limite_paginas=130):
    """Varre a Seção 2 daquele dia no Escavador (de trás para frente) e extrai
    os nomeados de TI. A Justiça Eleitoral costuma ficar na parte final da seção
    (mas a posição varia com o tamanho da edição), por isso a janela é ampla e há
    parada antecipada assim que o bloco da JE termina. Gentil: pausa entre páginas."""
    base = f"{BASE_ESCAVADOR}/diarios/{diario_id}/DOU/secao-2/{dia_iso}"
    try:
        r = SESSAO.get(base, timeout=45)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"   ! Escavador {dia_iso} falhou: {e}")
        return []
    total = _escav_total_paginas(r.text)
    encontrados = {}
    desfeitas = []
    achou_je = False
    apos = 0
    lidas = 0
    p = total
    while p >= 1 and lidas < limite_paginas:
        url = base + (f"?page={p}" if p > 1 else "")
        try:
            rp = SESSAO.get(url, timeout=45)
            rp.raise_for_status()
            texto = limpar_html(rp.text)
        except requests.RequestException:
            texto = ""
        lidas += 1
        alvo = sem_acento(texto)
        if "eleitoral" in alvo and "nome" in alvo:
            achou_je = True
            apos = 0
            regs, anuladas = _registros_pagina_escavador(texto, dia_iso, url)
            for reg in regs:
                encontrados[chave_registro(reg)] = reg
            desfeitas += anuladas
        elif achou_je:
            apos += 1
            if apos >= 3:
                break
        time.sleep(1.2)
        p -= 1
    return list(encontrados.values()), desfeitas


def coletar_do_dou():
    corte = (date.today() - timedelta(days=DIAS_RETROATIVOS)).isoformat()
    encontrados = {}
    desfeitas = []         # nomeações que os atos do período tornaram sem efeito
    vistas = set()
    dias_com_dou = set()   # datas que o in.gov.br cobriu (não precisam do Escavador)

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
            regs, anuladas, avaliado = processar_portaria(item)
            for reg in regs:
                encontrados[chave_registro(reg)] = reg
            desfeitas += anuladas
            # Só marca como visto o que foi realmente avaliado: se a portaria não
            # abriu, a fase 2 (edição diária) ainda tem uma chance de pegá-la.
            if avaliado or regs:
                vistas.add(ut)
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
        je = [a for a in ed if eh_ato_je(a)]
        if ed:
            dias_com_dou.add(dia.isoformat())
        for item in je:
            ut = item.get("urlTitle", "")
            if not ut or ut in vistas:
                continue
            regs, anuladas, avaliado = processar_portaria(item, dia)
            for reg in regs:
                encontrados[chave_registro(reg)] = reg
            desfeitas += anuladas
            if avaliado or regs:
                vistas.add(ut)
        print(f"   {dia.isoformat()}: {len(ed)} atos, {len(je)} da Justiça Eleitoral, "
              f"{len(encontrados)} de TI até agora")
        time.sleep(2)
        dia -= timedelta(days=1)

    # ---- FASE 3: ESCAVADOR (só para datas que o in.gov.br não cobriu) -----
    try:
        indice = escavador_indice()
    except Exception as e:
        print(f"   ! Escavador índice falhou: {e}")
        indice = {}
    escav_feitas = 0
    for dia_iso in sorted(indice, reverse=True):
        if dia_iso < corte or dia_iso in dias_com_dou:
            continue
        if escav_feitas >= 3:      # no máximo 3 datas por execução (gentileza)
            break
        escav_feitas += 1
        print(f"\n> Escavador (fallback) para {dia_iso}…")
        try:
            regs, anuladas = escavador_dia(indice[dia_iso], dia_iso)
        except Exception as e:
            print(f"   ! Escavador {dia_iso} falhou: {e}")
            regs, anuladas = [], []
        for reg in regs:
            encontrados[chave_registro(reg)] = reg
        desfeitas += anuladas
        print(f"   Escavador {dia_iso}: {len(regs)} de TI | total {len(encontrados)}")
        time.sleep(2)

    return list(encontrados.values()), desfeitas


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
        novos, desfeitas = coletar_do_dou()
    except Exception as e:
        print(f"\n! Falha inesperada na coleta: {e}")
        novos, desfeitas = [], []

    add = 0
    for reg in novos:
        ch = chave_registro(reg)
        if ch not in base:
            base[ch] = reg
            add += 1
    print(f"\nNovos registros adicionados pelo DOU: {add}")

    # Nomeações tornadas sem efeito: guardadas em arquivo próprio e permanente.
    # Sem essa memória o registro voltaria na execução seguinte — o seed o traz
    # de volta, e a portaria que o anulou já saiu da janela dos últimos dias.
    conhecidas = anul.carregar(ARQ_ANULACOES)
    antes = {anul.chave_anulacao(a) for a in conhecidas}
    novas = [a for a in desfeitas if anul.chave_anulacao(a) not in antes]
    if novas:
        for a in novas:
            print(f"   nomeação tornada sem efeito: {a['uf']} — {a['nome']} "
                  f"(desfaz {a.get('portaria_desfeita') or '?'}, {a['ato']})")
    total_anul = anul.salvar(ARQ_ANULACOES, conhecidas + desfeitas)
    print(f"Anulações conhecidas: {total_anul} ({len(novas)} nova(s) nesta execução)")

    registros = sorted(base.values(),
                       key=lambda r: (r.get("data", ""), r.get("nome", "")),
                       reverse=True)
    registros, removidos = anul.aplicar_anulacoes(registros, anul.carregar(ARQ_ANULACOES))
    for r in removidos:
        print(f"   fora do painel (nomeação sem efeito): {r['uf']} — {r['nome']}")

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
