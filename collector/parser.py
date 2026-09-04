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


# Preposições que o DOU troca à vontade: a hierarquia publicada pelo próprio
# Diário diz "Tribunal Regional Eleitoral DO Mato Grosso do Sul", enquanto o nome
# oficial (e o do config) é "…DE Mato Grosso do Sul". Comparar ignorando essas
# palavrinhas deixa a identificação imune à variação, em qualquer um dos 28 órgãos.
_PREPOSICOES = {"de", "do", "da", "dos", "das"}


def _canon(texto):
    """Forma canônica para comparar nome de órgão: sem acento, sem pontuação,
    sem preposições e com um espaço em cada ponta.

    Os espaços das pontas fazem a comparação valer por PALAVRA INTEIRA — sem
    isso, "…Eleitoral do Pará" casava dentro de "…Eleitoral do Paraíba".
    """
    limpo = re.sub(r"[^a-z0-9]+", " ", sem_acento(texto))
    return " " + " ".join(t for t in limpo.split() if t not in _PREPOSICOES) + " "


def identificar_orgao(*textos):
    """Descobre de qual órgão é o texto.

    Escolhe sempre o nome MAIS LONGO que aparecer, porque alguns nomes são
    prefixo de outros e a comparação simples pegava o errado:
      "…Eleitoral do Pará"  x  "…Eleitoral do Paraná"        (PA x PR)
      "…de Mato Grosso"     x  "…de Mato Grosso do Sul"      (MT x MS)

    A comparação usa a forma canônica (veja `_canon`): vale por palavra inteira
    e não se importa com a preposição que o DOU resolveu usar no dia.
    """
    alvo = _canon(" ".join(t for t in textos if t))
    achado, tamanho = None, -1
    for sigla, info in ORGAOS.items():
        if sigla == "TSE":
            continue
        nome = _canon(info["nome"])
        if nome in alvo and len(nome) > tamanho:
            achado, tamanho = sigla, len(nome)
    if achado:
        return achado
    if _canon(ORGAOS["TSE"]["nome"]) in alvo:
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


# Quantas palavras um nome de pessoa pode ter. O limite existe para descartar
# um trecho de texto capturado por engano, mas 6 era baixo demais: nome
# brasileiro com sobrenome composto e conectivos passa disso com facilidade
# ("Indi Li da Silva Alves Moreira Tenorio", TRE-RN, 04/09/2026, tem 7 — e a
# nomeação foi descartada em silêncio). Os regexes já limitam o nome a ~70
# caracteres e a lista _BAD barra palavras que não são de nome, então 10 é
# folga para gente de verdade sem abrir a porta para frases inteiras.
_MAX_PALAVRAS_NOME = 10


def _nome_valido(s):
    tokens = _trim_nome(s).split()
    if len(tokens) < 2 or len(tokens) > _MAX_PALAVRAS_NOME:
        return False
    for t in tokens:
        if sem_acento(t) in _BAD:
            return False
    cap = sum(1 for t in tokens if len(t) >= 2 and t[:1].isalpha() and t[:1].isupper())
    return cap >= 2


# Marcador de item de lista colado no nome: "I - DIEGO AQUINO…" (TRE-AM),
# "1. FULANO", "a) FULANO". Só conta como marcador quando vem com o separador —
# um "I" solto não é descartado, para não mutilar nome de gente de verdade.
_RE_MARCADOR_ITEM = re.compile(r"^\s*(?:[IVXL]{1,5}|\d{1,3}[ºo°ª]?|[A-Za-z])\s*[-–.)]\s+")


def _trim_nome(bruto):
    """Remove palavras "coladas" no começo/fim que não fazem parte do nome
    (ex.: 'respectivamente JONATHAN…', 'e FELIPE…' ou o 'I -' de um item)."""
    bruto = _RE_MARCADOR_ITEM.sub("", bruto or "")
    tokens = re.sub(r"\s+", " ", bruto).strip().split()
    def descartavel(t):
        return (t.islower() or sem_acento(t) in _CONECTIVOS
                or sem_acento(t) in _BAD)
    while tokens and descartavel(tokens[0]):
        tokens.pop(0)
    while tokens and descartavel(tokens[-1]):
        tokens.pop()
    # O marcador pode estar escondido atrás do que acabou de sair: em
    # "candidatos: I - Marcio…" ele só aparece depois que "candidatos:" cai.
    return _RE_MARCADOR_ITEM.sub("", " ".join(tokens))


def _limpar_esp(esp):
    esp = re.sub(r"\s+", " ", esp).strip()
    esp = re.sub(r"^em\s+", "", esp, flags=re.IGNORECASE)   # "Especialidade EM X" -> "X"
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
    r"[\s\S]{0,120}?(?:especialidade\s*(?:em\s+)?[:\s\-–]+|apoio\s+especializado\s*[-–,]\s*(?!\s*especialidade))"
    r"([^,.;\n]{3,45})"
)


# --- Formato A: "Nomear o candidato X, classificado em Nº lugar ... Especialidade: Y"
_RE_A = re.compile(
    r"nomear\s+(?:o|a)(?:\(a\))?\s+candida[dt][oa](?:\(a\))?\s+([A-ZÀ-Ú][^,]{3,70}?),\s*"
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
    r"(?:sr\.?\s+|sra\.?\s+|candida[dt][oa](?:\(a\))?\s+)"
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
    r"cargo[s]?\s+de\s+(analista|t[ée]cnico)\s+judici[áa]rio([\s\S]{0,160})",
    re.IGNORECASE,
)


def _esp_do_desc(desc):
    m = re.search(r"especialidade\s*(?:em\s+)?[:\s\-–]+([^,.;\n]{3,45})", desc, re.IGNORECASE)
    if not m:
        m = re.search(r"apoio\s+especializado\s*[-–,]\s*(?!\s*especialidade)([^,.;\n]{3,45})", desc, re.IGNORECASE)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


# O TRE-SP não escreve "cargo de …": abre a lista com o cargo em cabeçalho
# terminado em dois-pontos — "Analista Judiciário - Área Administrativa, Classe A,
# Padrão 1:" — e embaixo os nomes com a colocação. Sem reconhecer esse cabeçalho,
# os nomes de uma seção Administrativa herdavam o bloco de TI citado antes (num
# artigo que só tornava sem efeito outra nomeação) e entravam no painel.
# O "Classe/Padrão" obrigatório é o que distingue o cabeçalho de uma menção
# corrida como "Técnico Judiciário - Área: Apoio Especializado…".
_RE_CARGO_HEAD_LISTA = re.compile(
    r"(analista|t[ée]cnico)\s+judici[áa]rio\s*[-–,]\s*"
    r"([^:\n]{0,150}?(?:classe|padr[ãa]o)[^:\n]{0,25}?):",
    re.IGNORECASE,
)


def _blocos_cargo(texto):
    """Lista de (posição, cargo, especialidade, eh_ti) para cada cabeçalho de cargo."""
    out = []
    for regex in (_RE_CARGO_HEAD, _RE_CARGO_HEAD_LISTA):
        for m in regex.finditer(texto):
            desc = m.group(2)
            out.append((m.start(), _cargo_norm(m.group(1)), _esp_do_desc(desc), eh_ti(desc)))
    out.sort()
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


# --- Família 7: lista em alíneas — "a) o candidato FULANO, … b) a candidata …" (TRE-PR)
#     Um único "NOMEAR" no caput e vários itens; cada item traz o próprio cargo e
#     especialidade. A janela do item não pode invadir a alínea seguinte.
_RE_ALINEA = re.compile(
    r"\b[a-z]\)\s*(?:o|a)(?:\(a\))?\s+"
    r"(?:candida[dt][oa](?:\(a\))?|sr\.?|sra\.?)\s+"
    r"([A-ZÀ-Ú][^,]{3,70}?)\s*,"
    r"(?:(?!\b[a-z]\))[\s\S]){0,500}?" + _CARGOESP,
    re.IGNORECASE,
)


def _extrair_alinea(texto):
    out = []
    for m in _RE_ALINEA.finditer(texto):
        if not eh_ti(m.group(3)) or not _nome_valido(m.group(1)):
            continue
        out.append(_registro(m.group(1), _classif_perto(texto, m.start(1)),
                              m.group(2), m.group(3)))
    return out


# --- Família 6: lista com algarismos romanos — "I - FULANO, em vaga …" (TRE-PA)
#     Usada em portarias com vários artigos, cada um com um cargo/especialidade.
_RE_ROMANO = re.compile(
    r"\b([IVXL]{1,5})\s*[-–]\s*([A-ZÀ-Ú][A-ZÀ-Ú'’.\- ]{5,60}?)\s*(?=,|\s+em\s+vaga)"
)


def _extrair_romano(texto):
    blocos = _blocos_cargo(texto)
    if not blocos:
        return []
    out = []
    for m in _RE_ROMANO.finditer(texto):
        b = _bloco_antes(blocos, m.start())
        if not b or not b[2] or not _nome_valido(m.group(2)):
            continue
        out.append(_registro(m.group(2), 0, b[0], b[1] or "Tecnologia da Informação"))
    return out


# --- Formato B: blocos "Cargo de X ... Especialidade Y" + "Fulano, Nª colocação" (SP)
# O nome aceita até _MAX_PALAVRAS_NOME palavras. Com o teto antigo de 6, um nome
# de 7 palavras não sumia: o regex encaixava as 6 últimas e o painel mostrava o
# nome sem a primeira palavra.
_RE_B_NOME = re.compile(
    r"([A-ZÀ-Ú][A-Za-zÀ-úÇ'.\-]+(?:\s+[A-ZÀ-Úa-zà-ú][A-Za-zÀ-úÇ'.\-]+){1,%d}),\s*"
    r"(\d+)\s*[ªaº]?\s*coloca[çc]" % (_MAX_PALAVRAS_NOME - 1)
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


# ---------------------------------------------------------------------------
# ANULAÇÕES — atos que TORNAM SEM EFEITO uma nomeação já publicada
# ---------------------------------------------------------------------------
# O tribunal às vezes desfaz uma nomeação (o candidato não tomou posse no prazo,
# desistiu, ou a portaria saiu com erro). Isso vem num ato próprio, dias ou meses
# depois: "Tornar sem efeito a Portaria nº 504 … referente à nomeação do candidato
# FULANO". Sem ler esses atos, o painel segue mostrando como convocado alguém
# cuja nomeação não existe mais.
#
# ATENÇÃO: exoneração NÃO é anulação. Quem foi exonerado tomou posse e depois
# saiu — a convocação aconteceu de verdade e continua valendo como histórico.
_RE_ART = re.compile(r"\bart(?:igo)?\.?\s*\d+\s*[ºo°]?", re.IGNORECASE)

_RE_ANUL_GATILHO = re.compile(
    r"\b(?:tornar|tornad[oa]|declarar|declarad[oa]|considerar)\s+"
    r"(?:sem\s+efeito|insubsistente|nul[ao])\b"
    r"|\brevogar\b|\brevogad[oa]\b|\banular\b|\banulad[oa]\b",
    re.IGNORECASE,
)

# O nome de quem teve a nomeação desfeita, nas formas em que os tribunais
# escrevem: "…referente à nomeação do candidato X", "…que nomeou o(a) X",
# "…tornar sem efeito a nomeação de X".
_RE_ANUL_NOME = re.compile(
    r"(?:nomea[çc][ãa]o\s+d[oea]s?\s*|nomeou\s+(?:[oa](?:\(a\))?\s+)?)"
    r"(?:candida[dt][oa]s?(?:\(a\))?\s*:?\s+|sr\.?\s+|sra\.?\s+|servidor(?:a)?\s+)?"
    r"([A-ZÀ-Ú][^,.;\n]{3,70}?)"
    r"\s*(?=,|\.|;|\s+para\b|\s+no\s+cargo\b|\s+do\s+cargo\b|\s+classificad|\s+constante\b)",
    re.IGNORECASE,
)

# Separa "Fulana e de Ciclano" / "Fulano e da Ciclana" em duas pessoas.
_RE_E_DE = re.compile(r"\s+e\s+d[eao]s?\s+", re.IGNORECASE)

# Lista dentro de um único "tornar sem efeito … a nomeação dos candidatos:
# I - Fulano, constante da Portaria nº 100…; II - Ciclano, …" (TSE, Portaria
# 146 de 15/04/2026). O regex acima só alcança o primeiro nome, porque só há
# um "nomeação"; cada item precisa ser lido por conta própria — e cada um cita
# a sua portaria, que pode ser diferente da do vizinho.
_RE_ANUL_ITEM = re.compile(
    r"(?:^|[:;.]\s*)(?:[IVXL]{1,5}|\d{1,3})\s*[-–.)]\s*"
    r"([A-ZÀ-Ú][^,.;\n]{3,70}?)"
    r"\s*(?=,|\.|;|\s+para\b|\s+no\s+cargo\b|\s+do\s+cargo\b|\s+classificad|\s+constante\b)"
)

# Número da portaria desfeita ("Tornar sem efeito a Portaria … nº 504, de …").
# Palavra inteira: "candidato" e "ato" não são a mesma coisa — sem o \b, o
# "candidato FULANO, classificado em 3º lugar" rendia portaria "3".
_RE_ANUL_PORTARIA = re.compile(r"\b(?:portaria|ato)\b[^\d\n]{0,40}?(\d[\d.]*)", re.IGNORECASE)


def _portaria_desfeita(trecho, gatilho):
    """Número da portaria que o ato desfez.

    Procura DEPOIS do gatilho ("Tornar sem efeito a Portaria nº 504…") e, se não
    houver, a citação mais próxima ANTES dele ("A Portaria nº 88 … fica
    revogada"). Nunca a primeira do trecho: num ato sem "Art." (TRE-ES, Ato 289
    de 19/08/2026) o trecho começa pelo cabeçalho, e o primeiro número seria o
    do próprio ato — e esse número é o que decide qual nomeação sai de quem foi
    nomeado duas vezes (veja anulacoes.py).
    """
    m = _RE_ANUL_PORTARIA.search(trecho, gatilho.end())
    if m:
        return m.group(1)
    antes = list(_RE_ANUL_PORTARIA.finditer(trecho, 0, gatilho.start()))
    return antes[-1].group(1) if antes else ""

# POR QUE a nomeação foi desfeita. O ato quase sempre diz, e é o que mais
# interessa a quem acompanha a fila: "desistiu" conta uma história bem diferente
# de "a portaria saiu com erro". Quando o ato não declara, fica vazio — não vale
# a pena chutar. A ordem importa: o primeiro que casar é o que vale.
_MOTIVOS_ANULACAO = (
    ("Desistência", r"desist[êe]ncia|desistiu|declin(?:ou|a[çc][ãa]o)|ren[úu]ncia"),
    ("Não tomou posse no prazo",
     r"n[ãa]o\s+(?:ter\s+|haver\s+)?tom(?:ado|ou)\s+posse|prazo\s+(?:legal\s+)?para\s+(?:a\s+)?posse"
     r"|decurso\s+d[eo]\s+prazo|n[ãa]o\s+entrou\s+em\s+exerc[íi]cio"
     # Fórmula legal: o art. 13, § 6º, da Lei 8.112/90 diz que "será tornado
     # sem efeito o ato de provimento se a posse não ocorrer no prazo". Citar o
     # dispositivo É declarar o motivo (TRE-RJ, Ato 216 de 08/07/2026).
     r"|art(?:igo)?\.?\s*13\s*,?\s*(?:§|par[áa]grafo)\s*6"),
    ("Perícia médica", r"per[íi]cia\s+m[ée]dica|inspe[çc][ãa]o\s+m[ée]dica|considerad[oa]\s+inapt"),
    ("Erro na portaria", r"erro\s+(?:material|de\s+digita[çc][ãa]o)|equ[íi]voco|incorre[çc][ãa]o"),
    ("A pedido", r"\ba\s+pedido\b"),
)


def _motivo_anulacao(trecho):
    for rotulo, padrao in _MOTIVOS_ANULACAO:
        if re.search(padrao, trecho, re.IGNORECASE):
            return rotulo
    return ""


def _eh_artigo_da_portaria(texto, pos):
    """O "Art. Nº" em `pos` é artigo da PRÓPRIA portaria, e não uma referência
    a artigo de lei?

    Artigo da portaria vem depois do "resolve:" do preâmbulo ou do ponto final
    do artigo anterior. Referência a lei vem depois de uma palavra: "nos termos
    do art. 13", "pelo artigo 20", "com base no art. 9º". Conferido em todos os
    atos da Justiça Eleitoral do DOU de 04/09/2026 (66 ocorrências, sem exceção).

    Tratar a referência como fronteira partia o artigo no meio: "Tornar sem
    efeito, nos termos do art. 13 da Lei…, a nomeação de FULANO" ficava com o
    gatilho num pedaço e o nome no outro — e a anulação se perdia.
    """
    antes = texto[:pos].rstrip()
    if not antes:
        return True
    if antes[-1] in ".:;)]\"”’":
        return True
    return bool(re.search(r"resolvem?$", antes, re.IGNORECASE))


def _trechos_por_artigo(texto):
    """Divide a portaria em trechos "Art. 1º…", "Art. 2º…".

    Sem isso, um ato que no Art. 1º torna sem efeito uma nomeação e no Art. 2º
    nomeia outra pessoa misturaria os dois — e o coletor apagaria o nome errado.
    Só conta como fronteira o artigo da própria portaria (veja
    `_eh_artigo_da_portaria`).
    """
    pos = [m.start() for m in _RE_ART.finditer(texto)
           if _eh_artigo_da_portaria(texto, m.start())]
    if not pos:
        return [texto]
    trechos = [texto[:pos[0]]] if pos[0] > 0 else []
    for i, p in enumerate(pos):
        fim = pos[i + 1] if i + 1 < len(pos) else len(texto)
        trechos.append(texto[p:fim])
    return trechos


def extrair_anulacoes(texto):
    """Nomes cuja NOMEAÇÃO foi tornada sem efeito por este ato.

    Devolve [{"nome", "portaria", "motivo"}] — 'portaria' é a que foi desfeita e
    'motivo' o que o ato declarou (vazio quando ele não diz). Só valem trechos que
    falem de NOMEAÇÃO: "tornar sem efeito" também é usado para designação, cessão
    e outros atos que não interessam aqui.
    """
    out = []
    vistos = set()
    for trecho in _trechos_por_artigo(texto):
        gatilho = _RE_ANUL_GATILHO.search(trecho)
        if not gatilho:
            continue
        portaria = _portaria_desfeita(trecho, gatilho)
        motivo = _motivo_anulacao(trecho)

        def registrar(bruto, portaria_item=None):
            # "a nomeação de Fulana e de Ciclano" (TRE-SP, Portaria 207 de
            # 28/08/2025) são duas pessoas. Nenhum nome tem "e de/da/do" no
            # meio, então a divisão é segura — e sem ela o parser criava uma
            # pessoa de 10 palavras que não existe.
            for parte in _RE_E_DE.split(bruto):
                if not _nome_valido(parte):
                    continue
                nome = formatar_nome(_trim_nome(parte))
                ch = sem_acento(nome)
                if not ch or ch in vistos:
                    continue
                vistos.add(ch)
                out.append({"nome": nome, "portaria": portaria_item or portaria,
                            "motivo": motivo})

        for m in _RE_ANUL_NOME.finditer(trecho):
            registrar(m.group(1))
        # Itens de lista: a portaria de cada um é a primeira citada entre o
        # nome e o item seguinte; sem citação própria, vale a do trecho.
        itens = list(_RE_ANUL_ITEM.finditer(trecho, gatilho.end()))
        for k, m in enumerate(itens):
            fim = itens[k + 1].start() if k + 1 < len(itens) else len(trecho)
            mp = _RE_ANUL_PORTARIA.search(trecho, m.end(), fim)
            registrar(m.group(1), mp.group(1) if mp else None)
    return out


# Um servidor que JÁ é do quadro também é "nomeado" — para uma Função
# Comissionada (FC-03) ou Cargo em Comissão (CJ-2). O DOU escreve isso igualzinho
# a uma convocação ("Nomear FULANO, Analista Judiciário, Apoio Especializado -
# Análise de Sistemas…"), e o TRE-MG publica esses atos toda semana. Não é
# convocação do concurso: quem entra no painel é só quem foi chamado para tomar
# posse num cargo efetivo.
_RE_COMISSAO = re.compile(
    r"fun[çc][ãa]o\s+comissionada|cargo\s+em\s+comiss[ãa]o|\bFC-?\s*\d|\bCJ-?\s*\d",
    re.IGNORECASE,
)


def _trechos_de_provimento(texto):
    """Os trechos do ato que podem conter convocação — os de função/cargo em
    comissão ficam de fora. A divisão é por artigo, porque o mesmo ato mistura
    os dois assuntos (Art. 1º dispensa da FC-03, Art. 3º nomeia para o CJ-2)."""
    return [t for t in _trechos_por_artigo(texto) if not _RE_COMISSAO.search(t)]


def extrair_nomeados(texto):
    """Junta todos os formatos, sem duplicar (por nome sem acento).

    Fora do painel: quem aparece como nomeação DESFEITA no mesmo ato (há
    portarias que tornam sem efeito uma nomeação e citam o cargo/especialidade
    logo em seguida) e quem está sendo nomeado para função ou cargo em comissão,
    que não é convocação do concurso.
    """
    out = []
    vistos = set()
    anulados = {sem_acento(a["nome"]) for a in extrair_anulacoes(texto)}
    # Junta com quebra de linha, não com espaço: assim um artigo descartado não
    # gruda o fim de um no começo do outro e cria um casamento que não existe.
    texto = "\n".join(_trechos_de_provimento(texto))
    candidatos = (_extrair_a(texto) + _extrair_inline(texto) +
                  _extrair_direto(texto) + _extrair_caps(texto) +
                  _extrair_lista(texto) + _extrair_nomecargo(texto) +
                  _extrair_romano(texto) + _extrair_alinea(texto) +
                  _extrair_b(texto))
    for r in candidatos:
        ch = sem_acento(r["nome"])
        if not ch or ch in vistos or ch in anulados:
            continue
        vistos.add(ch)
        out.append(r)
    return out
