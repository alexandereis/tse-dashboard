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
    print("\n==> ÓRGÃOS OK" if ok else "\n==> HA FALHAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
