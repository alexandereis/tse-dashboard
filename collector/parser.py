# -*- coding: utf-8 -*-
"""
Lê o texto de uma portaria do DOU e extrai os nomeados de TI
(nome, classificação, cargo, especialidade).

Cobre DOIS formatos comuns:
  A) "Nomear o candidato Fulano, classificado em 1º lugar ... cargo de
      Técnico Judiciário ... Especialidade: Tecnologia da Informação" (TSE, RJ, DF…)
  B) "NOMEAR, por concurso ... Cargo de Técnico Judiciário ... Especialidade
      Programação de Sistemas ... Fulano de Tal, 10ª colocação ..." (TRE-SP…)
"""

import re
import unicodedata

from config import ORGAOS, PALAVRAS_TI, PALAVRAS_NAO_TI


def sem_acento(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def limpar_html(html: str) -> str:
    if not html:
        return ""
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = texto.replace("&nbsp;", " ").replace("&amp;", "&")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def identificar_orgao(*textos: str):
    alvo = sem_acento(" ".join(t for t in textos if t))
    for sigla, info in ORGAOS.items():
        if sigla == "TSE":
            continue
        if sem_acento(info["nome"]) in alvo:
            return sigla
    if sem_acento(ORGAOS["TSE"]["nome"]) in alvo:
        return "TSE"
    return None


def eh_ti(*textos: str) -> bool:
    alvo = sem_acento(" ".join(t for t in textos if t))
    if any(p in alvo for p in PALAVRAS_NAO_TI):
        if not any(p in alvo for p in PALAVRAS_TI):
            return False
    return any(p in alvo for p in PALAVRAS_TI)


_CONECTIVOS = {"de", "da", "do", "dos", "das", "e"}


def formatar_nome(bruto: str) -> str:
    partes = []
    for i, palavra in enumerate(bruto.split()):
        baixa = palavra.lower()
        if i > 0 and baixa in _CONECTIVOS:
            partes.append(baixa)
        else:
            partes.append(palavra.capitalize())
    return " ".join(partes)


def _cargo_norm(txt):
    return "Analista Judiciário" if "analista" in sem_acento(txt) else "Técnico Judiciário"


# --- Formato A: "Nomear o candidato X, classificado em Nº lugar ... Especialidade: Y"
_RE_A = re.compile(
    r"nomear\s+(?:o|a)\s+candidat[oa]\s+([A-ZÀ-Ú][^,]{3,70}?),\s+"
    r"classificad[oa]\s+em\s+(\d+)\s*[ºo]?\s*lugar"
    r"[\s\S]{0,600}?cargo\s+(?:efetivo\s+)?de\s+"
    r"(Analista\s+Judici[áa]rio|T[ée]cnico\s+Judici[áa]rio)"
    r"[\s\S]{0,300}?especialidade:?\s*([^,.;\n]{3,70})",
    re.IGNORECASE,
)


def _extrair_a(texto):
    out = []
    for m in _RE_A.finditer(texto):
        esp = re.sub(r"\s+", " ", m.group(4)).strip()
        if not eh_ti(esp):
            continue
        out.append({"nome": formatar_nome(re.sub(r"\s+", " ", m.group(1)).strip()),
                    "classificacao": int(m.group(2)),
                    "cargo": _cargo_norm(m.group(3)), "especialidade": esp})
    return out


# --- Formato B: blocos "Cargo de X ... Especialidade Y" + nomes "Fulano, Nª colocação"
_RE_B_BLOCO = re.compile(
    r"cargo\s+de\s+(analista|t[ée]cnico)\s+judici[áa]rio"
    r"[\s\S]{0,200}?especialidade[:\s]+([^,.;\n]{3,55})",
    re.IGNORECASE,
)
_RE_B_NOME = re.compile(
    r"([A-ZÀ-Ú][A-Za-zÀ-úÇ'.\-]+(?:\s+[A-ZÀ-Úa-zà-ú][A-Za-zÀ-úÇ'.\-]+){1,5}),\s*"
    r"(\d+)\s*[ªaº]?\s*coloca[çc]"
)


def _extrair_b(texto):
    blocos = []
    for m in _RE_B_BLOCO.finditer(texto):
        blocos.append((m.start(), _cargo_norm(m.group(1)),
                       re.sub(r"\s+", " ", m.group(2)).strip()))
    if not blocos:
        return []
    out = []
    for m in _RE_B_NOME.finditer(texto):
        pos = m.start()
        cargo = esp = None
        for (bp, bc, be) in blocos:        # bloco mais próximo ANTES do nome
            if bp < pos:
                cargo, esp = bc, be
            else:
                break
        if not esp or not eh_ti(esp):
            continue
        out.append({"nome": formatar_nome(re.sub(r"\s+", " ", m.group(1)).strip()),
                    "classificacao": int(m.group(2)),
                    "cargo": cargo, "especialidade": esp})
    return out


def extrair_nomeados(texto):
    """Junta os dois formatos, sem duplicar (por nome sem acento)."""
    out = []
    vistos = set()
    for r in _extrair_a(texto) + _extrair_b(texto):
        ch = sem_acento(r["nome"])
        if ch in vistos:
            continue
        vistos.add(ch)
        out.append(r)
    return out
