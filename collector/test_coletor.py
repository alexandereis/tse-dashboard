# -*- coding: utf-8 -*-
"""
Testes do COLETOR (sem internet): o que ele faz com um ato do DOU antes de
entregá-lo ao parser.

Cobre duas regressões reais, ambas vistas na PORTARIA 196 do TRE-MS (20/08/2026):

 1) O resumo que a BUSCA do DOU devolve é recortado em volta do termo procurado,
    então nem sempre traz o nome do tribunal. O coletor desistia ali mesmo, sem
    abrir a portaria. Agora, se o órgão não sai do resumo, ele abre o texto
    completo (que sempre traz o nome no preâmbulo) e tenta de novo.

 2) O ato só pode ser marcado como "já visto" quando foi REALMENTE avaliado.
    Antes, um ato marcado como visto numa fase que falhou nunca mais era
    reprocessado pelas fases seguintes — a nomeação sumia até alguém notar.

Rode com:  python3 test_coletor.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import collect

# Texto integral da PORTARIA TRE/PRE/GABPRE N.º 196, de 19/08/2026 (resumido).
TEXTO_COMPLETO = (
    "PORTARIA TRE/PRE/GABPRE Nº 196, DE 19 DE AGOSTO DE 2026 O DESEMBARGADOR "
    "CARLOS EDUARDO CONTAR, PRESIDENTE DO EGRÉGIO TRIBUNAL REGIONAL ELEITORAL DE "
    "MATO GROSSO DO SUL, no uso das prerrogativas que lhe são conferidas, resolve: "
    "Art. 1º NOMEAR, nos termos do art. 9º, I, da Lei n.º 8.112, de 11.12.1990, a "
    "candidata LARISSA RIBEIRO LOPES, classificada em 6º lugar no Concurso Público "
    "Unificado realizado pelo Tribunal Superior Eleitoral, para exercer em caráter "
    "efetivo o cargo da carreira judiciária de Técnico Judiciário - Área: Apoio "
    "Especializado Especialidade: Programação de Sistemas, Classe A, Padrão 1. "
    "Art. 2º NOMEAR, nos termos do art. 9º, I, da Lei n.º 8.112, de 11.12.1990, a "
    "candidata RAISSA RINALDI YOSHIOKA, classificada em 7º lugar no Concurso Público "
    "Unificado realizado pelo Tribunal Superior Eleitoral, para exercer em caráter "
    "efetivo o cargo da carreira judiciária de Técnico Judiciário Área: Apoio "
    "Especializado Especialidade: Programação de Sistemas, Classe A, Padrão 1."
)

# Resumo exatamente como a BUSCA do DOU o devolve: recortado em volta do termo
# procurado ("Especialidade Programação de Sistemas") — sem o nome do tribunal.
RESUMO_DA_BUSCA = (
    "em caráter efetivo o cargo da carreira judiciária de Técnico Judiciário - "
    "Área: Apoio Especializado Especialidade ... : Programação de Sistemas , "
    "Classe A, Padrão 1, do Quadro Permanente de Pessoal deste Tribunal, criado ..."
)

ITEM = {
    # A hierarquia do DOU escreve "DO Mato Grosso do Sul" (o nome oficial é "DE").
    "hierarchyStr": "Poder Judiciário/Tribunal Regional Eleitoral do Mato Grosso do Sul",
    "title": "PORTARIA TRE/PRE/GABPRE Nº 196, DE 19 DE AGOSTO DE 2026",
    "urlTitle": "portaria-tre/pre/gabpre-n-196-de-19-de-agosto-de-2026-726666042",
    "content": RESUMO_DA_BUSCA,
    "pubDate": "20/08/2026",
}

ESPERADOS = ["Larissa Ribeiro Lopes", "Raissa Rinaldi Yoshioka"]

# PORTARIA 587 do TRE-SE (DOU de 31/08/2026): desfez a nomeação publicada em
# 28/07/2026. O coletor precisa devolver isso como ANULAÇÃO — sem ela, o nomeado
# fica no painel para sempre, porque o seed o traz de volta a cada execução.
TEXTO_ANULACAO = (
    "PORTARIA Nº 587, DE 28 DE AGOSTO DE 2026 A PRESIDENTE DO TRIBUNAL REGIONAL "
    "ELEITORAL DE SERGIPE, no uso das atribuições que lhe são conferidas pelo artigo "
    "28, inciso XXXIV, do Regimento Interno, resolve: Art. 1º Tornar sem efeito a "
    "Portaria de Pessoal nº 504, de 23 de Julho de 2026, publicada no Diário Oficial "
    "da União nº 140, Seção 2, de 28 de Julho de 2026, referente à nomeação do "
    "candidato YTALLO AUGUSTO SANTOS LIMA, para o cargo de Técnico Judiciário, Área "
    "de Apoio Especializado, Especialidade Programação de Sistemas."
)

ITEM_ANULACAO = {
    "hierarchyStr": "Poder Judiciário/Tribunal Regional Eleitoral de Sergipe",
    "title": "PORTARIA Nº 587, DE 28 DE AGOSTO DE 2026",
    "urlTitle": "portaria-n-587-de-28-de-agosto-de-2026-729057471",
    "content": "",
    "pubDate": "31/08/2026",
}


def _com_download(resposta):
    """Troca o download da portaria por uma resposta fixa (sem internet)."""
    original = collect.baixar_texto_portaria
    collect.baixar_texto_portaria = lambda ut, tentativas=3: resposta
    return original


def caso_resumo_sem_nome_do_tribunal():
    """A busca não traz o nome do tribunal no resumo — o texto completo traz."""
    original = _com_download((TEXTO_COMPLETO, "https://www.in.gov.br/x"))
    try:
        regs, anuls, avaliado = collect.processar_portaria(ITEM)
    finally:
        collect.baixar_texto_portaria = original
    nomes = [r["nome"] for r in regs]
    ufs = {r["uf"] for r in regs}
    problemas = []
    if nomes != ESPERADOS:
        problemas.append(f"nomes {nomes} (esperado {ESPERADOS})")
    if ufs != {"MS"}:
        problemas.append(f"uf {ufs} (esperado {{'MS'}})")
    if not avaliado:
        problemas.append("marcou como NÃO avaliado, mas o texto veio inteiro")
    return problemas


def caso_download_falhou_nao_marca_como_visto():
    """Se a portaria não abriu, o ato NÃO pode ser dado por avaliado — senão as
    fases seguintes (e as próximas execuções) o pulam para sempre."""
    original = _com_download(("", "https://www.in.gov.br/x"))
    try:
        regs, anuls, avaliado = collect.processar_portaria(ITEM)
    finally:
        collect.baixar_texto_portaria = original
    problemas = []
    if avaliado:
        problemas.append("marcou como avaliado mesmo sem conseguir o texto")
    if regs:
        problemas.append(f"extraiu {[r['nome'] for r in regs]} de um resumo cortado")
    return problemas


def caso_ato_de_anulacao_vira_anulacao():
    """Ato que torna sem efeito uma nomeacao: sai como ANULACAO, nunca como
    nomeacao nova (o texto cita cargo e especialidade de TI logo em seguida)."""
    original = _com_download((TEXTO_ANULACAO, "https://www.in.gov.br/x"))
    try:
        regs, anuls, avaliado = collect.processar_portaria(ITEM_ANULACAO)
    finally:
        collect.baixar_texto_portaria = original
    problemas = []
    nomes = [a["nome"] for a in anuls]
    if nomes != ["Ytallo Augusto Santos Lima"]:
        problemas.append(f"anulacoes {nomes} (esperado ['Ytallo Augusto Santos Lima'])")
    if anuls and anuls[0].get("uf") != "SE":
        problemas.append(f"uf {anuls[0].get('uf')} (esperado SE)")
    if anuls and anuls[0].get("portaria_desfeita") != "504":
        problemas.append(f"portaria desfeita {anuls[0].get('portaria_desfeita')} (esperado 504)")
    if anuls and anuls[0].get("data") != "2026-08-31":
        problemas.append(f"data {anuls[0].get('data')} (esperado 2026-08-31)")
    if regs:
        problemas.append(f"virou nomeacao: {[r['nome'] for r in regs]}")
    return problemas


ITEM_ANULACAO_RS = {
    "hierarchyStr": "Poder Judiciário/Tribunal Regional Eleitoral do Rio Grande do Sul",
    "title": "PORTARIA TRE-RS P Nº 2.779, DE 28 DE AGOSTO DE 2026",
    "urlTitle": "portaria-tre-rs-p-n-2.779-de-28-de-agosto-de-2026-730202857",
    "content": "",
    "pubDate": "04/09/2026",
}

# Texto real (DOU de 04/09/2026). O ato diz o motivo com todas as letras.
TEXTO_ANULACAO_RS = (
    "PORTARIA TRE-RS P Nº 2.779, DE 28 DE AGOSTO DE 2026 A PRESIDENTE DO TRIBUNAL REGIONAL "
    "ELEITORAL, no exercício de suas atribuições legais e regimentais, resolve: Art. 1º TORNAR SEM "
    "EFEITO, tendo em vista Termo de Desistência Definitiva firmado pelo candidato, a Portaria "
    "TRE-RS P n. 2.751, de 5 de agosto de 2026, publicada na edição do Diário Oficial da União de "
    "10 de agosto de 2026, que nomeou MATEUS ARSAND, classificado em 16º lugar na classificação da "
    "lista geral de candidatos em Concurso Público de Provas, destinado ao provimento das vagas "
    "deste Tribunal, para ocupar o cargo de Técnico Judiciário, Área Administrativa, Classe A, "
    "Padrão 1, do Quadro de Pessoal deste Tribunal, criado pela Lei nº 15.374, de 02.04.2026. "
    "Art. 2º Esta Portaria entra em vigor na data de sua publicação."
)


def caso_anulacao_leva_o_motivo():
    """A anulação sai com o MOTIVO que o ato declara. Sem isso a aba Movimentações
    dizia "motivo não declarado" para tudo que o robô pegava, mesmo quando o ato
    dizia "desistência" com todas as letras."""
    original = _com_download((TEXTO_ANULACAO_RS, "https://www.in.gov.br/x"))
    try:
        regs, anuls, avaliado = collect.processar_portaria(ITEM_ANULACAO_RS)
    finally:
        collect.baixar_texto_portaria = original
    problemas = []
    if [a["nome"] for a in anuls] != ["Mateus Arsand"]:
        problemas.append(f"anulacoes {[a['nome'] for a in anuls]} (esperado ['Mateus Arsand'])")
    if anuls and anuls[0].get("motivo") != "Desistência":
        problemas.append(f"motivo {anuls[0].get('motivo')!r} (esperado 'Desistência')")
    if anuls and anuls[0].get("portaria_desfeita") != "2.751":
        problemas.append(f"portaria desfeita {anuls[0].get('portaria_desfeita')!r} (esperado '2.751')")
    if regs:
        problemas.append(f"virou nomeacao: {[r['nome'] for r in regs]}")
    return problemas


CASOS = {
    "busca: resumo sem o nome do tribunal (TRE-MS 196)": caso_resumo_sem_nome_do_tribunal,
    "download falhou: ato não conta como avaliado": caso_download_falhou_nao_marca_como_visto,
    "ato que torna sem efeito vira anulação (TRE-SE 587)": caso_ato_de_anulacao_vira_anulacao,
    "anulação leva o motivo e a portaria desfeita (TRE-RS 2.779)": caso_anulacao_leva_o_motivo,
}


def main():
    ok = True
    for tag, funcao in CASOS.items():
        problemas = funcao()
        if problemas:
            ok = False
            print(f"[FALHA] {tag}")
            for p in problemas:
                print(f"        {p}")
        else:
            print(f"[OK  ] {tag}")
    print("\n==> COLETOR OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
