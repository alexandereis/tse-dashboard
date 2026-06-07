# -*- coding: utf-8 -*-
"""
Funções que "leem" o texto de uma portaria do DOU e extraem informação
estruturada: órgão (UF) e a lista de nomeados de TI (com nome, classificação,
cargo e especialidade).

O formato das portarias varia, então usamos heurísticas (regras aproximadas).
Tudo é comentado para você poder ajustar quando aparecer um formato novo.
"""

import re
import unicodedata

from config import ORGAOS, PALAVRAS_TI, PALAVRAS_NAO_TI


def sem_acento(texto: str) -> str:
    """Remove acentos e baixa para minúsculas — facilita comparações."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def limpar_html(html: str) -> str:
    """Tira tags HTML e normaliza espaços, devolvendo texto puro."""
    if not html:
        return ""
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = texto.replace("&nbsp;", " ").replace("&amp;", "&")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def identificar_orgao(*textos: str):
    """
    Descobre a qual órgão (TSE ou um TRE) a portaria pertence, comparando
    o nome oficial de cada órgão com os textos fornecidos. Retorna a sigla
    (ex.: 'SP', 'TSE') ou None.
    """
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
    """True se o contexto indicar cargo de Tecnologia da Informação."""
    alvo = sem_acento(" ".join(t for t in textos if t))
    if any(p in alvo for p in PALAVRAS_NAO_TI):
        if not any(p in alvo for p in PALAVRAS_TI):
            return False
    return any(p in alvo for p in PALAVRAS_TI)


_CONECTIVOS = {"de", "da", "do", "dos", "das", "e"}


def formatar_nome(bruto: str) -> str:
    """'JOÃO DE TAL' -> 'João de Tal' (conectivos ficam em minúsculo)."""
    partes = []
    for i, palavra in enumerate(bruto.split()):
        baixa = palavra.lower()
        if i > 0 and baixa in _CONECTIVOS:
            partes.append(baixa)
        else:
            partes.append(palavra.capitalize())
    return " ".join(partes)


# Formato padrão do DOU:
# "Nomear o candidato Fulano de Tal, classificado em 1º lugar ... cargo
#  efetivo de Analista Judiciário, ... Especialidade: Tecnologia da Informação"
_RE_NOMEADO = re.compile(
    r"nomear\s+(?:o|a)\s+candidat[oa]\s+([A-ZÀ-Ú][^,]{3,70}?),\s+"
    r"classificad[oa]\s+em\s+(\d+)\s*[ºo]?\s*lugar"
    r"[\s\S]{0,600}?cargo\s+(?:efetivo\s+)?de\s+"
    r"(Analista\s+Judici[áa]rio|T[ée]cnico\s+Judici[áa]rio)"
    r"[\s\S]{0,300}?especialidade:?\s*([^,.;\n]{3,70})",
    re.IGNORECASE,
)


def extrair_nomeados(texto):
    """
    Devolve a lista de nomeados de TI: {nome, classificacao, cargo, especialidade}.
    Filtra só TI pela especialidade. Formatos fora do padrão podem escapar — o
    seed (dados conferidos) garante o painel nesses casos.
    """
    out = []
    vistos = set()
    for m in _RE_NOMEADO.finditer(texto):
        nome = formatar_nome(re.sub(r"\s+", " ", m.group(1)).strip())
        cls = int(m.group(2))
        cargo = ("Analista Judiciário" if "analista" in sem_acento(m.group(3))
                 else "Técnico Judiciário")
        esp = re.sub(r"\s+", " ", m.group(4)).strip()
        if not eh_ti(esp):
            continue
        chave = sem_acento(nome)
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append({"nome": nome, "classificacao": cls,
                    "cargo": cargo, "especialidade": esp})
    return out
