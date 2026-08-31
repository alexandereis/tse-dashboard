# -*- coding: utf-8 -*-
"""
NOMEAÇÕES TORNADAS SEM EFEITO — memória permanente e aplicação na base.

Por que isto existe: o coletor só sabia SOMAR. Quando um tribunal desfazia uma
nomeação ("Tornar sem efeito a Portaria nº 504 … referente à nomeação de FULANO"),
o painel seguia mostrando a pessoa como convocada — foi o que aconteceu com o
TRE-SE em 31/08/2026, e o mesmo já tinha acontecido em outros 28 casos desde
junho/2025 sem ninguém notar.

Por que um arquivo PRÓPRIO e permanente (data/anulacoes.json): apagar o registro
do data/nomeacoes.json não resolve. O seed (base curada) e o histórico o trariam
de volta na execução seguinte, e o coletor só varre os últimos dias — a portaria
que anulou já teria saído da janela. A anulação precisa de memória própria, que
é reaplicada toda vez que a base é montada.

QUAL registro sai (errar aqui apaga alguém que foi mesmo nomeado):
  * mesmo tribunal e mesmo nome (comparado sem acento/caixa);
  * nomeação ANTERIOR ao ato — quem foi nomeado de novo depois continua no painel;
  * se o ato cita a portaria desfeita, só a nomeação daquela portaria sai.
"""

import json
import os
import re
import unicodedata
from datetime import datetime, timezone


def _sem_acento(texto):
    nfkd = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _numero(portaria):
    """Só os dígitos do rótulo: 'PORTARIA Nº 504' e 'Portaria 504/2026' -> '504'."""
    m = re.search(r"(\d[\d.]*)", portaria or "")
    return m.group(1).replace(".", "").lstrip("0") if m else ""


def chave_anulacao(a):
    return (a.get("uf", ""), _sem_acento(a.get("nome", "")),
            _numero(a.get("portaria_desfeita", "")), a.get("data", ""))


def aplicar_anulacoes(registros, anulacoes):
    """Devolve (registros_que_ficam, registros_removidos)."""
    fora = set()          # índices removidos
    for a in anulacoes:
        uf = a.get("uf", "")
        nome = _sem_acento(a.get("nome", ""))
        data = a.get("data", "")
        alvo = _numero(a.get("portaria_desfeita", ""))
        if not uf or not nome:
            continue
        candidatos = [
            i for i, r in enumerate(registros)
            if i not in fora
            and r.get("uf") == uf
            and _sem_acento(r.get("nome", "")) == nome
            and (not data or (r.get("data") or "") <= data)
        ]
        if alvo:
            exatos = [i for i in candidatos if _numero(registros[i].get("portaria")) == alvo]
            if exatos:
                candidatos = exatos
        fora.update(candidatos)
    ficam = [r for i, r in enumerate(registros) if i not in fora]
    removidos = [r for i, r in enumerate(registros) if i in fora]
    return ficam, removidos


def carregar(caminho):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if isinstance(dados, dict):
        return dados.get("anulacoes", []) or []
    return dados or []


def salvar(caminho, anulacoes):
    """Grava sem duplicar, em ordem cronológica. Devolve quantas ficaram.

    Se a lista for igual à que já está no arquivo, NÃO regrava — o robô roda
    ~20x por dia e um 'atualizado_em' novo a cada rodada viraria um commit por
    execução, sem nada de novo dentro.
    """
    unicas = {}
    for a in anulacoes:
        unicas.setdefault(chave_anulacao(a), a)
    lista = sorted(unicas.values(),
                   key=lambda a: (a.get("data", ""), a.get("uf", ""), a.get("nome", "")))
    if lista == carregar(caminho):
        return len(lista)
    saida = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "total": len(lista),
        "anulacoes": lista,
    }
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)
    return len(lista)
