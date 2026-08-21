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


def _com_download(resposta):
    """Troca o download da portaria por uma resposta fixa (sem internet)."""
    original = collect.baixar_texto_portaria
    collect.baixar_texto_portaria = lambda ut, tentativas=3: resposta
    return original


def caso_resumo_sem_nome_do_tribunal():
    """A busca não traz o nome do tribunal no resumo — o texto completo traz."""
    original = _com_download((TEXTO_COMPLETO, "https://www.in.gov.br/x"))
    try:
        regs, avaliado = collect.processar_portaria(ITEM)
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
        regs, avaliado = collect.processar_portaria(ITEM)
    finally:
        collect.baixar_texto_portaria = original
    problemas = []
    if avaliado:
        problemas.append("marcou como avaliado mesmo sem conseguir o texto")
    if regs:
        problemas.append(f"extraiu {[r['nome'] for r in regs]} de um resumo cortado")
    return problemas


CASOS = {
    "busca: resumo sem o nome do tribunal (TRE-MS 196)": caso_resumo_sem_nome_do_tribunal,
    "download falhou: ato não conta como avaliado": caso_download_falhou_nao_marca_como_visto,
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
