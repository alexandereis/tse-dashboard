# -*- coding: utf-8 -*-
"""
AUDITORIA — a biblioteca por trás de auditar_dia.py, conferir_anulacoes.py e
varredura.py.

Por que existe: o coletor só sabe o que o parser devolve. Quando o parser não
entende um formato novo, a nomeação some em silêncio — foi assim com o TRE-RN
em 04/09/2026 (nome de 7 palavras), e com quatro anulações (TRE-RJ, TRE-AM)
que ficaram meses invisíveis. A auditoria olha para o que o parser NÃO devolveu:

  * `cheira_a_nomeacao_perdida`: ato com "nomear" + termo de TI e zero nomeados
    é suspeito e merece um par de olhos;
  * `Base`: diz se um nomeado ou uma anulação já são conhecidos, sem se enganar
    com acento ou caixa — e sem esconder grafia diferente, que precisa de revisão
    humana (o DOU retifica nomes: "BARRETO" -> "BARRETTO");
  * `avaliar_ato`: abre um ato, roda o parser e devolve tudo num só lugar;
  * `incorporar_anulacoes`: grava no data/anulacoes.json as anulações que a
    varredura achou, sempre reprocessadas com o parser ATUAL.

Tudo aqui só lê o DOU; quem grava é quem chama, de propósito.
"""

import json
import os
import re

import collect
import anulacoes as anul
from config import PALAVRAS_TI
from parser import extrair_anulacoes, sem_acento, _RE_COMISSAO

ARQ_DADOS = collect.ARQ_DADOS
ARQ_SEED = collect.ARQ_SEED
ARQ_ANULACOES = collect.ARQ_ANULACOES

_RE_NOMEAR = re.compile(r"\bnomear\b")
# Toda nomeação para cargo efetivo diz de onde vem o nomeado: "habilitação em
# concurso", "caráter efetivo", "classificado em Nº lugar". Um "nomear FULANA
# para responder pela Seção de Suporte" não diz — e não é convocação.
_RE_PROVIMENTO = re.compile(r"concurso|efetivo|habilita|classificad")


def cheira_a_nomeacao_perdida(texto, nomeados):
    """O ato fala em NOMEAR para cargo efetivo, cita um termo de TI e o parser
    não devolveu ninguém.

    Não é prova de erro — pode ser um cargo em comissão, que o parser descarta de
    propósito. É um cheiro: vale abrir o ato e olhar. Foi exatamente esse filtro
    que apontou a Portaria 277 do TRE-RN em 04/09/2026.
    """
    if nomeados:
        return False
    alvo = sem_acento(texto)
    if not _RE_NOMEAR.search(alvo):
        return False
    if not any(p in alvo for p in PALAVRAS_TI):
        return False
    if not _RE_PROVIMENTO.search(alvo):
        return False
    if _RE_COMISSAO.search(texto):
        return False
    return True


def atos_je_do_dia(dia):
    """Atos da Justiça Eleitoral na edição da Seção 2 daquele dia (date).

    Devolve None se a edição não veio (rede/limite) — diferente de uma lista
    vazia, que significa "edição lida, nenhum ato da JE".
    """
    ed = collect.baixar_edicao(dia.strftime("%d-%m-%Y"))
    if ed is None:
        return None
    return [a for a in ed if collect.eh_ato_je(a)]


def avaliar_ato(item, dia=None):
    """Abre o ato e roda o parser. Devolve um dicionário com:

      sigla, titulo, url, avaliado (texto veio inteiro?), texto,
      nomeados e anulacoes (no formato do coletor, prontos para comparar com a
      base) e suspeito (veja `cheira_a_nomeacao_perdida`).
    """
    url_title = item.get("urlTitle", "") or ""
    texto, url = collect.baixar_texto_portaria(url_title) if url_title else ("", "")
    regs, anuls, avaliado = collect.processar_portaria(item, dia, texto=texto or None)
    sigla = regs[0]["uf"] if regs else (anuls[0]["uf"] if anuls else None)
    if sigla is None:
        sigla = collect.identificar_orgao(item.get("hierarchyStr", "") or "",
                                          item.get("title", "") or "", texto)
    return {
        "sigla": sigla,
        "titulo": item.get("title", "") or "",
        "url": url,
        "avaliado": avaliado,
        "texto": texto,
        "nomeados": regs,
        "anulacoes": anuls,
        "suspeito": bool(texto) and cheira_a_nomeacao_perdida(texto, regs),
    }


class Base:
    """O que o painel já conhece: nomeados (base + seed) e anulações.

    Nomeado é conhecido por (tribunal, nome sem acento/caixa). Grafia diferente
    NÃO é reconhecida de propósito: pode ser retificação do DOU ou outra pessoa,
    e isso é decisão humana.

    Anulação é conhecida se for a mesma chave (tribunal, nome, portaria
    desfeita, data) OU se for a mesma pessoa no MESMO ato (url) — um número de
    portaria lido diferente não cria uma anulação nova; já a mesma pessoa em
    OUTRO ato é outra anulação (gente nomeada duas vezes existe).
    """

    def __init__(self, registros, seed, anulacoes):
        self._nomes = {(r.get("uf", ""), sem_acento(r.get("nome", "")))
                       for r in list(registros) + list(seed)}
        self._anul_chaves = {anul.chave_anulacao(a) for a in anulacoes}
        self._anul_no_ato = {(a.get("uf", ""), sem_acento(a.get("nome", "")), a.get("url", ""))
                             for a in anulacoes}

    @classmethod
    def dos_arquivos(cls):
        registros = collect.carregar_json(ARQ_DADOS, {"registros": []}).get("registros", [])
        seed = collect.carregar_json(ARQ_SEED, [])
        return cls(registros, seed, anul.carregar(ARQ_ANULACOES))

    def nomeado_conhecido(self, reg):
        return (reg.get("uf", ""), sem_acento(reg.get("nome", ""))) in self._nomes

    def anulacao_conhecida(self, a):
        if anul.chave_anulacao(a) in self._anul_chaves:
            return True
        return (a.get("uf", ""), sem_acento(a.get("nome", "")), a.get("url", "")) in self._anul_no_ato

    def registrar_anulacao(self, a):
        self._anul_chaves.add(anul.chave_anulacao(a))
        self._anul_no_ato.add((a.get("uf", ""), sem_acento(a.get("nome", "")), a.get("url", "")))


def incorporar_anulacoes(achadas, base=None, arquivo=ARQ_ANULACOES, pausa=0.8):
    """Grava em data/anulacoes.json as anulações achadas fora do arquivo.

    Reabre cada ATO sinalizado e reprocessa com o parser ATUAL — o que vale é o
    que o parser de hoje lê, não o que quem sinalizou leu — e acrescenta todos
    os nomes que a base ainda não conhece. Devolve a lista do que entrou.
    """
    import time
    base = base or Base.dos_arquivos()
    conhecidas = anul.carregar(arquivo)
    atos = {}
    for a in achadas:
        atos.setdefault(a.get("url", ""), a)
    novas = []
    for url, modelo in sorted(atos.items()):
        if not url:
            continue
        texto, _ = collect.baixar_texto_portaria(url.replace(collect.BASE_ARTIGO, ""))
        if not texto:
            print(f"   ! download falhou, ato pulado: {url}")
            continue
        for x in extrair_anulacoes(texto):
            n = dict(modelo, nome=x["nome"], portaria_desfeita=x["portaria"], motivo=x["motivo"])
            if base.anulacao_conhecida(n):
                continue
            base.registrar_anulacao(n)
            novas.append(n)
        time.sleep(pausa)
    if novas:
        anul.salvar(arquivo, conhecidas + novas)
    return novas


def rotulo(reg):
    """Uma linha legível para um nomeado ou uma anulação, para relatórios."""
    if "cargo" in reg:
        return (f"{reg['uf']} {reg['nome']} [{reg['cargo']} / {reg.get('especialidade', '')}] "
                f"{reg.get('data_br', '')} {reg.get('portaria', '')} {reg.get('url', '')}")
    return (f"{reg['uf']} {reg['nome']} (desfaz {reg.get('portaria_desfeita') or '?'}"
            f"{', ' + reg['motivo'] if reg.get('motivo') else ''}) {reg.get('data_br', '')} "
            f"{reg.get('ato', '')} {reg.get('url', '')}")
