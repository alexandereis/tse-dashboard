# -*- coding: utf-8 -*-
"""
Funções que "leem" o texto de uma portaria do DOU e extraem informação
estruturada: órgão (UF), cargo, especialidade e a lista de nomeados.

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
    o nome oficial de cada órgão com os textos fornecidos (cabeçalho, título,
    hierarquia, corpo). Retorna a sigla (ex.: 'SP', 'TSE') ou None.
    """
    alvo = sem_acento(" ".join(t for t in textos if t))
    # Primeiro tenta casar com os TREs (nome mais específico).
    for sigla, info in ORGAOS.items():
        if sigla == "TSE":
            continue
        if sem_acento(info["nome"]) in alvo:
            return sigla
    # Por último o TSE (nome mais genérico, evita falso positivo).
    if sem_acento(ORGAOS["TSE"]["nome"]) in alvo:
        return "TSE"
    return None


def extrair_cargo(texto: str):
    """Retorna 'Analista Judiciário', 'Técnico Judiciário' ou None."""
    t = sem_acento(texto)
    tem_analista = "analista judiciario" in t
    tem_tecnico = "tecnico judiciario" in t
    if tem_analista and not tem_tecnico:
        return "Analista Judiciário"
    if tem_tecnico and not tem_analista:
        return "Técnico Judiciário"
    # Se os dois aparecem, deixamos a classificação por nome (mais granular)
    # a cargo de quem chama; aqui devolvemos None para tratar caso a caso.
    return None


def extrair_especialidade(texto: str):
    """
    Tenta capturar a especialidade declarada na portaria
    (ex.: 'Análise de Sistemas de Informação').
    """
    m = re.search(r"[Ee]specialidade[:\s]+([A-ZÀ-Ú][^.,;:\n]{3,60})", texto)
    if m:
        return m.group(1).strip()
    return ""


def eh_ti(*textos: str) -> bool:
    """
    True se o contexto indicar cargo de Tecnologia da Informação.
    Usa PALAVRAS_TI e descarta PALAVRAS_NAO_TI.
    """
    alvo = sem_acento(" ".join(t for t in textos if t))
    if any(p in alvo for p in PALAVRAS_NAO_TI):
        # Só descarta se NÃO houver também um termo claro de TI no mesmo trecho.
        if not any(p in alvo for p in PALAVRAS_TI):
            return False
    return any(p in alvo for p in PALAVRAS_TI)


# Palavras em MAIÚSCULAS que aparecem no DOU mas NÃO são nomes de pessoas.
_RUIDO_NOMES = {
    "PORTARIA", "ANEXO", "DOU", "DIARIO", "OFICIAL", "UNIAO", "SECAO",
    "ANALISTA", "TECNICO", "JUDICIARIO", "AREA", "APOIO", "ESPECIALIZADO",
    "ESPECIALIDADE", "ADMINISTRATIVA", "JUDICIARIA", "TECNOLOGIA",
    "INFORMACAO", "ANALISE", "SISTEMAS", "DESENVOLVIMENTO", "SUPORTE",
    "PROGRAMACAO", "CONCURSO", "PUBLICO", "NACIONAL", "UNIFICADO",
    "JUSTICA", "ELEITORAL", "TRIBUNAL", "REGIONAL", "SUPERIOR", "CARGO",
    "EFETIVO", "CLASSE", "PADRAO", "NOMEAR", "RESOLVE", "ART", "VIRTUDE",
    "APROVACAO", "RESULTADO", "FINAL", "HOMOLOGADO", "EDITAL", "VAGA",
    "VAGAS", "QUADRO", "PESSOAL", "SERVIDORES", "BRASIL", "REPUBLICA",
    "GOVERNO", "FEDERAL", "MINISTERIO", "GABINETE", "PRESIDENCIA",
    "RELACAO", "LISTA", "SEGUINTE", "SEGUINTES", "ABAIXO", "RELACIONADOS",
    "CANDIDATO", "CANDIDATOS", "CANDIDATA", "CANDIDATAS", "POSSE",
}


def extrair_nomes(texto: str):
    """
    Extrai prováveis nomes de pessoas (escritos em MAIÚSCULAS no DOU).

    Estratégia: procurar sequências de 2 a 6 palavras totalmente em
    maiúsculas (aceitando acentos e conectivos 'DE/DA/DO/DOS/DAS/E'),
    e descartar trechos que sejam claramente cabeçalho/ruído.
    """
    if not texto:
        return []

    # Sequência de palavras maiúsculas (com acento) e conectivos minúsculos.
    padrao = re.compile(
        r"\b([A-ZÀ-Ú][A-ZÀ-Ú']+(?:\s+(?:DE|DA|DO|DOS|DAS|E|da|de|do|dos|das|e)\s+|\s+)"
        r"(?:[A-ZÀ-Ú][A-ZÀ-Ú']+)(?:\s+(?:DE|DA|DO|DOS|DAS|E|da|de|do|dos|das|e|"
        r"[A-ZÀ-Ú][A-ZÀ-Ú']+)){0,4})\b"
    )

    nomes = []
    vistos = set()
    for m in padrao.finditer(texto):
        bruto = re.sub(r"\s+", " ", m.group(1)).strip()
        palavras = bruto.split()
        if len(palavras) < 2 or len(palavras) > 7:
            continue
        # Descarta se alguma palavra "forte" (>=4 letras) for ruído conhecido.
        tokens = [sem_acento(p).upper() for p in palavras]
        if any(t in _RUIDO_NOMES for t in tokens if len(t) >= 3):
            continue
        # Precisa ter ao menos 2 palavras "de verdade" (não só conectivos).
        reais = [p for p in palavras if sem_acento(p) not in
                 {"de", "da", "do", "dos", "das", "e"}]
        if len(reais) < 2:
            continue
        chave = sem_acento(bruto)
        if chave in vistos:
            continue
        vistos.add(chave)
        nomes.append(formatar_nome(bruto))  # "FULANO DE TAL" -> "Fulano de Tal"
    return nomes


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


# ---------------------------------------------------------------------------
# Extração ESTRUTURADA (formato padrão do DOU)
# Ex.: "Art. 26 Nomear o candidato Fábio Freire Jacinto, classificado em 1º
#       lugar ... cargo efetivo de Analista Judiciário, Área: Apoio
#       Especializado, Especialidade: Tecnologia da Informação, Classe ..."
# Captura nome + classificação + cargo + especialidade de cada nomeado, e
# já filtra só os de TI pela especialidade.
# ---------------------------------------------------------------------------
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
    Lê o texto de uma portaria e devolve uma lista de nomeados de TI, cada um
    como: {nome, classificacao, cargo, especialidade}.

    Usa o padrão estruturado do DOU (acima). Funciona para o TSE e para os TREs
    que seguem esse formato formal — que é a maioria. Formatos muito fora do
    padrão podem escapar; nesse caso o seed (dados conferidos) garante o painel.
    """
    out = []
    vistos = set()
    for m in _RE_NOMEADO.finditer(texto):
        nome = formatar_nome(re.sub(r"\s+", " ", m.group(1)).strip())
        cls = int(m.group(2))
        cargo = ("Analista Judiciário" if "analista" in sem_acento(m.group(3))
                 else "Técnico Judiciário")
        esp = re.sub(r"\s+", " ", m.group(4)).strip()
        if not eh_ti(esp):                 # só TI (pela especialidade)
            continue
        chave = sem_acento(nome)
        if chave in vistos:
            continue
        vistos.add(chave)
        out.append({"nome": nome, "classificacao": cls,
                    "cargo": cargo, "especialidade": esp})
    return out
