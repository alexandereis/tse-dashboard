# -*- coding: utf-8 -*-
"""
Testes da identificação de órgão. Alguns nomes são PREFIXO de outros
("…do Pará" x "…do Paraná", "…de Mato Grosso" x "…de Mato Grosso do Sul"),
o que já causou nomeação do TRE-PR ser registrada como TRE-PA.
Rode com:  python3 test_orgaos.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import identificar_orgao

CASOS = [
    ("Poder Judiciário/Tribunal Regional Eleitoral do Paraná", "PR"),
    ("Poder Judiciário/Tribunal Regional Eleitoral do Pará", "PA"),
    ("Tribunal Regional Eleitoral de Mato Grosso do Sul", "MS"),
    # Como o DOU realmente escreve na hierarquia do TRE-MS: "DO Mato Grosso do
    # Sul" (o nome oficial é "DE Mato Grosso do Sul"). Essa troca de preposição
    # fez as nomeações de 20/08/2026 (PORTARIA 196) sumirem do painel.
    ("Poder Judiciário/Tribunal Regional Eleitoral do Mato Grosso do Sul", "MS"),
    ("Poder Judiciário/Tribunal Regional Eleitoral do Mato Grosso", "MT"),
    ("Tribunal Regional Eleitoral de Mato Grosso", "MT"),
    ("Tribunal Regional Eleitoral do Rio Grande do Norte", "RN"),
    ("Tribunal Regional Eleitoral do Rio Grande do Sul", "RS"),
    ("Tribunal Regional Eleitoral do Rio de Janeiro", "RJ"),
    ("Tribunal Regional Eleitoral de São Paulo", "SP"),
    ("Tribunal Superior Eleitoral", "TSE"),
    ("Ministério da Defesa", None),
]


def _todos_os_orgaos():
    """Cada um dos 28 órgãos tem de se identificar como ele mesmo."""
    from config import ORGAOS
    erros = []
    for sigla, info in ORGAOS.items():
        got = identificar_orgao("Poder Judiciário/" + info["nome"])
        if got != sigla:
            erros.append(f"{sigla} -> {got}")
    return erros


def _variantes_de_preposicao():
    """O DOU troca a preposição depois de "Eleitoral" sem aviso (de/do/da).
    Cada órgão tem de continuar se identificando em todas as variantes."""
    import re
    from config import ORGAOS
    erros = []
    for sigla, info in ORGAOS.items():
        if sigla == "TSE":
            continue
        for prep in ("de", "do", "da"):
            variante = re.sub(r"(?i)^(Tribunal Regional Eleitoral)\s+(?:de|do|da)\s+",
                              rf"\1 {prep} ", info["nome"])
            got = identificar_orgao("Poder Judiciário/" + variante)
            if got != sigla:
                erros.append(f"{variante} -> {got} (esperado {sigla})")
    return erros


def main():
    ok = True
    for texto, esperado in CASOS:
        got = identificar_orgao(texto)
        st = "OK  " if got == esperado else "FALHA"
        if got != esperado:
            ok = False
        print(f"[{st}] {texto[:52]:54s} -> {got} (esperado {esperado})")
    erros = _todos_os_orgaos()
    if erros:
        ok = False
        print(f"[FALHA] varredura dos 28 órgãos: {', '.join(erros)}")
    else:
        print("[OK  ] os 28 órgãos se identificam corretamente")
    erros = _variantes_de_preposicao()
    if erros:
        ok = False
        print(f"[FALHA] variantes de preposição: {'; '.join(erros)}")
    else:
        print("[OK  ] os 27 TREs resistem à troca de preposição (de/do/da)")
    print("\n==> ÓRGÃOS OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
