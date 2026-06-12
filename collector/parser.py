# -*- coding: utf-8 -*-
"""
Lê o texto de uma portaria do DOU e extrai os nomeados de TI
(nome, classificação, cargo, especialidade).

Cobre os formatos publicados pelos órgãos da Justiça Eleitoral:
  A)  "Nomear o candidato Fulano, classificado em 1º lugar ... cargo de
      Técnico Judiciário ... Especialidade: Tecnologia da Informação" (TSE, RJ, DF…)
  1/2) Variantes inline: há texto entre "Nomear" e o nome (TRE-AP), ou
      "Nomear ... o Sr. Fulano, para o cargo de ... Especialidade X" (TRE-ES).
  3)  Nome em CAIXA ALTA seguido de "Técnico/Analista Judiciário - Área ...
      Especialidade X" (TRE-AC).
  4)  Lista/tabela: cabeçalho com cargo+especialidade e, abaixo,
      "1. FULANO DE TAL - 1º lugar" / "1º FULANO 1º Lugar" (TRE-GO, TRE-MA).
  B)  "Cargo de X ... Especialidade Y ... Fulano, Nª colocação" (TRE-SP).

Em todos, um filtro de "nome válido" descarta trechos que não são nome de
pessoa (ex.: o servidor anterior cujo cargo ficou vago).
"""

import re
import unicodedata

from config import ORGAOS, PALAVRAS_TI, PALAVRAS_NAO_TI


def sem_acento(texto):
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def limpar_html(html):
    if not html:
        return ""
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = texto.replace("&nbsp;", " ").replace("&amp;", "&")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def identificar_orgao(*textos):
    alvo = sem_acento(" ".join(t for t in textos if t))
    for sigla, info in ORGAOS.items():
        if sigla == "TSE":
            continue
        if sem_acento(info["nome"]) in alvo:
            return sigla
    if sem_acento(ORGAOS["TSE"]["nome"]) in alvo:
        return "TSE"
    return None


def eh_ti(*textos):
    alvo = sem_acento(" ".join(t for t in textos if t))
    if any(p in alvo for p in PALAVRAS_NAO_TI):
        if not any(p in alvo for p in PALAVRAS_TI):
            return False
    return any(p in alvo for p in PALAVRAS_TI)


_CONECTIVOS = {"de", "da", "do", "dos", "das", "e"}


def formatar_nome(bruto):
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


# Palavras que NÃO podem aparecer num nome de pessoa: se aparecerem, o regex
# capturou um trecho de texto (não um nome) e o candidato é descartado.
_BAD = set((
    "cargo cargos lugar listagem ocupante candidatos candidato negros servidor "
    "servidora para quadro classe padrao area judiciario judiciaria tribunal "
    "especialidade efetivo razao virtude habilitacao concurso publico nacional "
    "unificado justica eleitoral provimento vagas vaga deste neste exercer "
    "exercerem caracter ordem classificacao lei art artigo inciso superior "
    "regional portaria ato fundamento atividade origem convocacao"
).split())


def _nome_valido(s):
    tokens = _trim_nome(s).split()
    if len(tokens) < 2 or len(tokens) > 6:
        return False
    for t in tokens:
        if sem_acento(t) in _BAD:
            return False
    cap = sum(1 for t in tokens if len(t) >= 2 and t[:1].isalpha() and t[:1].isupper())
    return cap >= 2


def _trim_nome(bruto):
    """Remove palavras "coladas" no começo/fim que não fazem parte do nome
    (ex.: 'respectivamente JONATHAN…' ou 'e FELIPE…')."""
    tokens = re.sub(r"\s+", " ", bruto).strip().split()
    def descartavel(t):
        return (t.islower() or sem_acento(t) in _CONECTIVOS
                or sem_acento(t) in _BAD)
    while tokens and descartavel(tokens[0]):
        tokens.pop(0)
    while tokens and descartavel(tokens[-1]):
        tokens.pop()
    return " ".join(tokens)


def _limpar_esp(esp):
    esp = re.sub(r"\s+", " ", esp).strip()
    # corta sufixos que às vezes "colam" no fim da especialidade
    esp = re.sub(r"\s+(classe|padr[ãa]o|n[isí]|do quadro|para integrar|ordem|nome|origem).*$", "",
                 esp, flags=re.IGNORECASE).strip(" ,-–")
    return esp


def _registro(nome, classif, cargo, esp):
    return {
        "nome": formatar_nome(_trim_nome(nome)),
        "classificacao": int(classif) if classif else 0,
        "cargo": _cargo_norm(cargo),
        "especialidade": _limpar_esp(esp),
    }


# Fragmento compartilhado: "(Analista|Técnico) Judiciário ... Especialidade X"
# Aceita tanto "Especialidade X" quanto "Apoio Especializado - X" (sem a palavra).
_CARGOESP = (
    r"(analista|t[ée]cnico)\s+judici[áa]rio"
    r"[\s\S]{0,60}?(?:especialidade[:\s\-–]+|apoio\s+especializado\s*[-–,]\s*)"
    r"([^,.;\n]{3,45})"
)


# --- Formato A: "Nomear o candidato X, classificado em Nº lugar ... Especialidade: Y"
_RE_A = re.compile(
    r"nomear\s+(?:o|a)(?:\(a\))?\s+candidat[oa](?:\(a\))?\s+([A-ZÀ-Ú][^,]{3,70}?),\s*"
    r"classificad[oa]\s+em\s+(\d+)\s*[ºn°o]?\s*lugar"
    r"(?:(?!\bnomear\b)[\s\S]){0,600}?cargo\s+(?:efetivo\s+)?de\s+"
    r"(Analista\s+Judici[áa]rio|T[ée]cnico\s+Judici[áa]rio)"
    r"(?:(?!\bnomear\b)[\s\S]){0,300}?especialidade:?\s*([^,.;\n]{3,70})",
    re.IGNORECASE,
)


def _extrair_a(texto):
    out = []
    for m in _RE_A.finditer(texto):
        if not eh_ti(m.group(4)) or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), m.group(2), m.group(3), m.group(4)))
    return out


# --- Famílias 1/2: inline com texto entre "Nomear" e o nome (AP, ES, MS, PB…)
_RE_INLINE = re.compile(
    r"nomear(?:(?!\bnomear\b)[\s\S]){0,240}?\b(?:o|a)(?:\(a\))?\s+"
    r"(?:sr\.?\s+|sra\.?\s+|candidat[oa](?:\(a\))?\s+)"
    r"([A-ZÀ-Ú][^,]{3,70}?)\s*,(?:(?!\bnomear\b)[\s\S]){0,280}?" + _CARGOESP,
    re.IGNORECASE,
)


def _classif_perto(texto, pos):
    trecho = texto[pos:pos + 160]
    m = re.search(r"classificad[oa]\s+em\s+(\d+)|(\d+)\s*[ºn°oªa]?\s*lugar",
                  trecho, re.IGNORECASE)
    if m:
        return m.group(1) or m.group(2)
    return 0


def _extrair_inline(texto):
    out = []
    for m in _RE_INLINE.finditer(texto):
        if not eh_ti(m.group(3)) or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), _classif_perto(texto, m.start(1)),
                              m.group(2), m.group(3)))
    return out


# --- Família "direta": "Nomear FULANO DE TAL, ... cargo ... especialidade X" (SC)
_RE_DIRETO = re.compile(
    r"(?i:nomear)\s+([A-ZÀ-Ú][A-ZÀ-Ú'’.\- ]{5,55}?)\s*,(?:(?!(?i:nomear))[\s\S]){0,280}?(?i:" + _CARGOESP + r")"
)


def _extrair_direto(texto):
    out = []
    for m in _RE_DIRETO.finditer(texto):
        if not eh_ti(m.group(3)) or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), _classif_perto(texto, m.start(1)),
                              m.group(2), m.group(3)))
    return out


# --- Família 3: nome em CAIXA ALTA + cargo + especialidade (AC, MG…)
# Nome em CAIXA ALTA é case-sensitive (não pode "vazar" para palavras minúsculas
# coladas, ex.: "...SOUZA. os cargos de Técnico"); só as palavras-chave do cargo
# são case-insensitive, via flag de escopo (?i:...).
_RE_CAPS = re.compile(
    r"\b([A-ZÀ-Ú][A-ZÀ-Ú'’.\- ]{6,55}?)\s+(?i:(?:cargo[\s:]+)?" + _CARGOESP + r")"
)


def _extrair_caps(texto):
    out = []
    for m in _RE_CAPS.finditer(texto):
        if not eh_ti(m.group(3)) or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), _classif_perto(texto, m.start(1)),
                              m.group(2), m.group(3)))
    return out


# --- Detector de blocos de cargo (GERAL) -----------------------------------
# Captura TODA declaração "Cargo de (Analista|Técnico) Judiciário ...", inclusive
# as NÃO-TI (ex.: "- Área Administrativa"). Cada bloco vira uma fronteira: um nome
# listado depois herda o cargo/especialidade do bloco imediatamente anterior, e só
# é aceito se esse bloco for de TI. Assim, nomes de uma seção Administrativa não
# "vazam" para a especialidade de TI da seção anterior.
_RE_CARGO_HEAD = re.compile(
    r"cargo[s]?\s+de\s+(analista|t[ée]cnico)\s+judici[áa]rio([\s\S]{0,100})",
    re.IGNORECASE,
)


def _esp_do_desc(desc):
    m = re.search(r"especialidade[:\s\-–]+([^,.;\n]{3,45})", desc, re.IGNORECASE)
    if not m:
        m = re.search(r"apoio\s+especializado\s*[-–,]\s*([^,.;\n]{3,45})", desc, re.IGNORECASE)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def _blocos_cargo(texto):
    """Lista de (posição, cargo, especialidade, eh_ti) para cada cabeçalho de cargo."""
    out = []
    for m in _RE_CARGO_HEAD.finditer(texto):
        desc = m.group(2)
        out.append((m.start(), _cargo_norm(m.group(1)), _esp_do_desc(desc), eh_ti(desc)))
    return out


def _bloco_antes(blocos, pos):
    """Bloco imediatamente anterior à posição (cargo, esp, ti) ou None."""
    achado = None
    for (bp, bc, be, bt) in blocos:
        if bp < pos:
            achado = (bc, be, bt)
        else:
            break
    return achado


# --- Família 4: lista/tabela (cabeçalho cargo+especialidade + "N NOME Nº lugar")
_RE_BLOCO = re.compile(r"cargo[s]?\b[\s\S]{0,30}?" + _CARGOESP, re.IGNORECASE)
_RE_ITEM = re.compile(
    r"([A-ZÀ-Ú][A-ZÀ-Ú'’.\- ]{5,55}?)\s*[-–]?\s*"
    r"(\d{1,3})\s*[º°ªo]?\s*[Ll]ugar"
)


def _extrair_lista(texto):
    blocos = _blocos_cargo(texto)
    if not blocos:
        return []
    out = []
    for m in _RE_ITEM.finditer(texto):
        b = _bloco_antes(blocos, m.start())
        if not b or not b[2] or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), m.group(2), b[0], b[1] or "Tecnologia da Informação"))
    return out


# --- Família 5: lista sem classificação — "NOME Cargo criado pela Lei …" (TSE)
_RE_NOMECARGO = re.compile(
    r"([A-ZÀ-Ú][A-Za-zÀ-úÇ.'’\- ]{6,60}?)\s+cargo\s+criado\s+pela\s+lei",
    re.IGNORECASE,
)


def _extrair_nomecargo(texto):
    blocos = _blocos_cargo(texto)
    if not blocos:
        return []
    out = []
    for m in _RE_NOMECARGO.finditer(texto):
        b = _bloco_antes(blocos, m.start())
        if not b or not b[2] or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), _classif_perto(texto, m.start(1)),
                              b[0], b[1] or "Tecnologia da Informação"))
    return out


# --- Formato B: blocos "Cargo de X ... Especialidade Y" + "Fulano, Nª colocação" (SP)
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
    blocos = _blocos_cargo(texto)
    if not blocos:
        return []
    out = []
    for m in _RE_B_NOME.finditer(texto):
        b = _bloco_antes(blocos, m.start())
        if not b or not b[2] or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), m.group(2), b[0], b[1] or "Tecnologia da Informação"))
    return out


def extrair_nomeados(texto):
    """Junta todos os formatos, sem duplicar (por nome sem acento)."""
    out = []
    vistos = set()
    candidatos = (_extrair_a(texto) + _extrair_inline(texto) +
                  _extrair_direto(texto) + _extrair_caps(texto) +
                  _extrair_lista(texto) + _extrair_nomecargo(texto) +
                  _extrair_b(texto))
    for r in candidatos:
        ch = sem_acento(r["nome"])
        if not ch or ch in vistos:
            continue
        vistos.add(ch)
        out.append(r)
    return out
