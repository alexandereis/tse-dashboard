# -*- coding: utf-8 -*-
"""
Testes das CORREÇÕES do DOU (republicação e retificação).

O DOU não publica nomeação nova quando erra o nome: ele republica o ato ou
publica uma retificação. Ler isso como convocação cria uma segunda pessoa no
painel — foi o caso real de "Guilherme Ramalho" (TRE-PB, 24/08/2026) e
"Guilherme Ramalho Magalhães" (a republicação, 16/09/2026).

O que estes testes travam:
  * reconhecer o ato de correção pelo que ele declara — e só por isso;
  * casar a versão corrigida com a nomeação ORIGINAL (data e ato originais);
  * nunca apagar nomeado em silêncio: o que não casa vira alerta;
  * não renomear ninguém quando o ato corrige OUTRA portaria;
  * reaplicar a correção a cada execução (o seed traz a grafia antiga de volta).

Rode com:  python3 test_correcoes.py
"""
import sys, os, json, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import correcoes as corr
from parser import ato_de_correcao

# --- textos reais (resumidos) ---------------------------------------------
NOTA_PB = (
    "PORTARIA Nº 312 TRE-PB/PTRE/ASPRE, DE 14 DE SETEMBRO DE 2026* O PRESIDENTE DO TRIBUNAL "
    "REGIONAL ELEITORAL DA PARAIBA resolve: Art. 3º NOMEAR o candidato GUILHERME RAMALHO "
    "MAGALHAES, classificado em 1º lugar, para exercer o cargo de Analista Judiciario - Apoio "
    "Especializado, Especialidade: Tecnologia da Informacao, Classe A, Padrao 1. Art. 8º Esta "
    "portaria entra em vigor na data de sua publicacao. Republicada por incorrecao no nome do "
    "candidato informado na Portaria nº 312/2026 TRE-PB/PTRE/ASPRE, publicada em 24/08/2026, "
    "Edicao 159, Secao 2, Pagina 80."
)
TITULO_PB = "PORTARIA Nº 312 TRE-PB/PTRE/ASPRE, DE 14 DE SETEMBRO DE 2026*"

TEXTO_BA = (
    "RETIFICACAO Na PORTARIA Nº 488, DE 25 DE JULHO DE 2025, publicada no DOU de 05/08/2025, que "
    "trata do ato de nomeacao de EVERTON SIMOES BARRETTO. Onde se le: \"EVERTON SIMOES BARRETO\". "
    "Leia-se: \"EVERTON SIMOES BARRETTO\"."
)

TEXTO_COMUM = (
    "PORTARIA Nº 312, DE 21 DE AGOSTO DE 2026 O PRESIDENTE resolve: Art. 1º NOMEAR o candidato "
    "GUILHERME RAMALHO, classificado em 1º lugar, para exercer o cargo de Analista Judiciario - "
    "Apoio Especializado, Especialidade: Tecnologia da Informacao."
)


def reg(uf, nome, data, portaria, url, cargo="Analista Judiciário", classif=0, correcao=None):
    r = {"uf": uf, "orgao": uf, "cargo": cargo, "area": "TI",
         "especialidade": "Tecnologia da Informação", "nome": nome,
         "classificacao": classif, "data": data,
         "data_br": f"{data[8:10]}/{data[5:7]}/{data[0:4]}",
         "portaria": portaria, "url": url, "fonte": "dou"}
    if correcao:
        r["_correcao"] = correcao
    return r


MARCA_PB = {"tipo": "republicacao", "ato": "PORTARIA Nº 312", "data_original": "2026-08-24"}
URL_ORIG = "https://www.in.gov.br/web/dou/-/portaria-n-312-tre-pb-de-21-de-agosto-de-2026-727252277"
URL_REPUB = "https://www.in.gov.br/web/dou/-/portaria-n-312-tre-pb-de-14-de-setembro-de-2026*-732091796"


def base_pb():
    """O painel antes da republicação: a portaria 312 com quatro nomeados de TI."""
    return [
        reg("PB", "Guilherme Ramalho", "2026-08-24", "PORTARIA Nº 312", URL_ORIG, classif=1),
        reg("PB", "Lucas Pereira Castanheira Nascimento", "2026-08-24", "PORTARIA Nº 312",
            URL_ORIG, cargo="Técnico Judiciário", classif=2),
    ]


def novos_republicacao():
    return [
        reg("PB", "Guilherme Ramalho Magalhães", "2026-09-16", "PORTARIA Nº 312", URL_REPUB,
            classif=1, correcao=MARCA_PB),
        reg("PB", "Lucas Pereira Castanheira Nascimento", "2026-09-16", "PORTARIA Nº 312",
            URL_REPUB, cargo="Técnico Judiciário", classif=2, correcao=MARCA_PB),
    ]


# --- casos -----------------------------------------------------------------
def caso_le_a_republicacao_real():
    got = ato_de_correcao(TITULO_PB, NOTA_PB, "PORTARIA Nº 312")
    esperado = MARCA_PB
    return [] if got == esperado else [f"esperado {esperado}, veio {got}"]


def caso_le_a_retificacao_real():
    got = ato_de_correcao("RETIFICAÇÃO", TEXTO_BA)
    esperado = {"tipo": "retificacao", "ato": "PORTARIA Nº 488",
                "data_original": "2025-08-05"}
    return [] if got == esperado else [f"esperado {esperado}, veio {got}"]


def caso_ato_comum_nao_e_correcao():
    got = ato_de_correcao("PORTARIA Nº 312, DE 21 DE AGOSTO DE 2026", TEXTO_COMUM,
                          "PORTARIA Nº 312")
    return [] if got is None else [f"ato comum virou correção: {got}"]


def caso_republicacao_vira_uma_correcao():
    achadas, alertas = corr.detectar(novos_republicacao(), base_pb())
    problemas = []
    if len(achadas) != 1:
        return [f"esperava 1 correção, vieram {len(achadas)}: {achadas}"]
    c = achadas[0]
    if (c["nome_anterior"], c["nome"]) != ("Guilherme Ramalho", "Guilherme Ramalho Magalhães"):
        problemas.append(f"casou errado: {c['nome_anterior']} -> {c['nome']}")
    if c["ato"] != "PORTARIA Nº 312" or c["tipo"] != "republicacao":
        problemas.append(f"ato/tipo errados: {c['ato']} / {c['tipo']}")
    if alertas:
        problemas.append(f"alertas inesperados: {alertas}")
    return problemas


def caso_a_nomeacao_fica_com_a_data_original():
    achadas, _ = corr.detectar(novos_republicacao(), base_pb())
    # a base depois que o coletor somou o registro da republicação (a duplicata)
    registros = base_pb() + [r for r in novos_republicacao()
                             if r["nome"] == "Guilherme Ramalho Magalhães"]
    saida, aplicadas = corr.aplicar(registros, achadas)
    problemas = []
    nomes = sorted(r["nome"] for r in saida)
    if nomes != ["Guilherme Ramalho Magalhães", "Lucas Pereira Castanheira Nascimento"]:
        problemas.append(f"a duplicata não saiu: {nomes}")
    g = [r for r in saida if r["nome"] == "Guilherme Ramalho Magalhães"]
    if not g:
        return problemas + ["o nome corrigido sumiu da base"]
    g = g[0]
    if g["data"] != "2026-08-24":
        problemas.append(f"data deveria ser a do ato original, veio {g['data']}")
    if g["portaria"] != "PORTARIA Nº 312" or g["url"] != URL_ORIG:
        problemas.append("o ato original não foi preservado")
    if g.get("nome_publicado") != "Guilherme Ramalho":
        problemas.append(f"grafia anterior não guardada: {g.get('nome_publicado')}")
    if g.get("corrigido_url") != URL_REPUB or g.get("corrigido_em") != "2026-09-16":
        problemas.append("o link da republicação não ficou no registro")
    if "_correcao" in g:
        problemas.append("marca interna vazou para o arquivo publicado")
    # a correção pega nos dois registros (a grafia antiga e a linha que a
    # republicação criou); o que importa é que sobre um só, com a data certa
    if not aplicadas:
        problemas.append("a correção não pegou em nenhum registro")
    return problemas


def caso_reaplicar_e_idempotente():
    """O seed traz a grafia antiga a cada execução: aplicar de novo tem de dar
    exatamente o mesmo resultado."""
    achadas, _ = corr.detectar(novos_republicacao(), base_pb())
    uma, _ = corr.aplicar(base_pb(), achadas)
    duas, _ = corr.aplicar(uma + base_pb(), achadas)
    a = sorted((r["nome"], r["data"]) for r in uma)
    b = sorted((r["nome"], r["data"]) for r in duas)
    return [] if a == b else [f"não é idempotente: {a} != {b}"]


def caso_base_ja_corrigida_a_mao_ganha_a_procedencia():
    """Correções antigas foram acertadas à mão no seed, antes deste arquivo
    existir. Aplicá-las a uma base que já tem o nome certo não muda o nome —
    só carimba de onde ele veio, que é como a varredura para de acusar o ato
    original como 'nomeado fora da base'."""
    achadas, _ = corr.detectar(novos_republicacao(), base_pb())
    ja_certa = [reg("PB", "Guilherme Ramalho Magalhães", "2026-08-24", "PORTARIA Nº 312",
                    URL_ORIG, classif=1)]
    saida, aplicadas = corr.aplicar(ja_certa, achadas)
    problemas = []
    if len(saida) != 1 or saida[0]["nome"] != "Guilherme Ramalho Magalhães":
        problemas.append(f"mexeu no nome: {[r['nome'] for r in saida]}")
    if saida and saida[0].get("nome_publicado") != "Guilherme Ramalho":
        problemas.append(f"procedência errada: {saida[0].get('nome_publicado')}")
    if saida and saida[0].get("data") != "2026-08-24":
        problemas.append("mexeu na data")
    if aplicadas != 1:
        problemas.append(f"aplicadas={aplicadas}")
    return problemas


def caso_correcao_ja_conhecida_nao_repete_nem_alerta():
    """Enquanto a republicação está na janela do coletor, ela é lida todo dia —
    e o seed segue trazendo a grafia antiga. Nada de correção repetida nem de
    alerta dizendo que sumiu alguém que já foi corrigido."""
    achadas, _ = corr.detectar(novos_republicacao(), base_pb())
    ja_corrigida, _ = corr.aplicar(base_pb(), achadas)
    # a base da execução seguinte: o seed (grafia antiga) + a base corrigida
    base = base_pb() + ja_corrigida
    de_novo, alertas = corr.detectar(novos_republicacao(), base, conhecidas=achadas)
    problemas = []
    if de_novo:
        problemas.append(f"gravaria a mesma correção de novo: {de_novo}")
    if alertas:
        problemas.append(f"alertas repetidos: {alertas}")
    return problemas


def caso_correcao_de_outra_portaria_nao_renomeia():
    """Ato comum que, de passagem, retifica OUTRA portaria: ninguém é renomeado."""
    marca = {"tipo": "retificacao", "ato": "PORTARIA Nº 100", "data_original": ""}
    novos = [reg("PB", "Fulano de Tal Souza", "2026-09-16", "PORTARIA Nº 400",
                 "https://exemplo/400", classif=1, correcao=marca)]
    achadas, alertas = corr.detectar(novos, base_pb())
    problemas = []
    if achadas:
        problemas.append(f"renomeou sem ser a mesma portaria: {achadas}")
    if not alertas:
        problemas.append("o caso passou em silêncio, sem alerta")
    return problemas


def caso_nomeado_que_some_da_republicacao_vira_alerta():
    """A republicação não traz mais um nomeado: ninguém é apagado em silêncio."""
    novos = [reg("PB", "Guilherme Ramalho Magalhães", "2026-09-16", "PORTARIA Nº 312",
                 URL_REPUB, classif=1, correcao=MARCA_PB)]
    base = base_pb() + [reg("PB", "Outro Nome Qualquer", "2026-08-24", "PORTARIA Nº 312",
                            URL_ORIG, cargo="Técnico Judiciário", classif=9)]
    achadas, alertas = corr.detectar(novos, base)
    saida, _ = corr.aplicar(base, achadas)
    problemas = []
    if not any("Outro Nome Qualquer" in a for a in alertas):
        problemas.append(f"faltou alerta sobre quem sumiu: {alertas}")
    if not any(r["nome"] == "Outro Nome Qualquer" for r in saida):
        problemas.append("o nomeado sem par foi apagado — nunca apagar em silêncio")
    return problemas


def caso_ato_do_ano_passado_nao_e_alcancado():
    """Número de portaria se repete a cada ano: a correção não alcança 2025."""
    base = [reg("PB", "Homonimo Antigo Silva", "2025-08-24", "PORTARIA Nº 312",
                "https://exemplo/2025", classif=1)]
    achadas, _ = corr.detectar(novos_republicacao(), base)
    return [] if not achadas else [f"alcançou o ato do ano passado: {achadas}"]


def caso_arquivo_nao_duplica_nem_regrava_a_toa():
    achadas, _ = corr.detectar(novos_republicacao(), base_pb())
    problemas = []
    with tempfile.TemporaryDirectory() as pasta:
        arq = os.path.join(pasta, "correcoes.json")
        corr.salvar(arq, achadas)
        antes = os.path.getmtime(arq)
        total = corr.salvar(arq, achadas + achadas)
        if total != 1:
            problemas.append(f"duplicou: total={total}")
        if os.path.getmtime(arq) != antes:
            problemas.append("regravou o arquivo sem novidade")
        if corr.carregar(arq) != achadas:
            problemas.append("o que voltou do arquivo não é o que entrou")
    return problemas


def main():
    ok = True
    casos = (
        ("lê a republicação real do TRE-PB", caso_le_a_republicacao_real),
        ("lê a retificação real do TRE-BA", caso_le_a_retificacao_real),
        ("ato comum não é tratado como correção", caso_ato_comum_nao_e_correcao),
        ("republicação vira UMA correção (não uma pessoa nova)",
         caso_republicacao_vira_uma_correcao),
        ("a nomeação fica com a data e o ato originais",
         caso_a_nomeacao_fica_com_a_data_original),
        ("reaplicar a correção é idempotente", caso_reaplicar_e_idempotente),
        ("base já corrigida à mão ganha a procedência, sem mudar de nome",
         caso_base_ja_corrigida_a_mao_ganha_a_procedencia),
        ("correção já conhecida não repete nem vira alerta",
         caso_correcao_ja_conhecida_nao_repete_nem_alerta),
        ("correção de OUTRA portaria não renomeia ninguém",
         caso_correcao_de_outra_portaria_nao_renomeia),
        ("nomeado que some da republicação vira alerta, não sumiço",
         caso_nomeado_que_some_da_republicacao_vira_alerta),
        ("portaria homônima do ano passado não é alcançada",
         caso_ato_do_ano_passado_nao_e_alcancado),
        ("arquivo não duplica nem regrava à toa", caso_arquivo_nao_duplica_nem_regrava_a_toa),
    )
    for tag, funcao in casos:
        problemas = funcao()
        if problemas:
            ok = False
            print(f"[FALHA] {tag}")
            for p in problemas:
                print(f"        {p}")
        else:
            print(f"[OK  ] {tag}")
    print("\n==> CORRECOES OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
