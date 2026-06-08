# -*- coding: utf-8 -*-
"""
Configuração central do coletor.

Aqui ficam todas as "regras" que o robô usa para buscar e classificar as
nomeações. Você pode ajustar livremente sem mexer no resto do código.
"""

# ---------------------------------------------------------------------------
# 1) ÓRGÃOS DA JUSTIÇA ELEITORAL (TSE + 27 TREs)
#    O nome aqui é exatamente como aparece no DOU (campo "hierarchyStr"/cabeçalho).
#    A sigla/UF é usada para agrupar no dashboard.
# ---------------------------------------------------------------------------
ORGAOS = {
    "TSE": {"nome": "Tribunal Superior Eleitoral", "uf": "TSE", "rotulo": "TSE - Sede"},
    "AC":  {"nome": "Tribunal Regional Eleitoral do Acre", "uf": "AC", "rotulo": "Acre"},
    "AL":  {"nome": "Tribunal Regional Eleitoral de Alagoas", "uf": "AL", "rotulo": "Alagoas"},
    "AP":  {"nome": "Tribunal Regional Eleitoral do Amapá", "uf": "AP", "rotulo": "Amapá"},
    "AM":  {"nome": "Tribunal Regional Eleitoral do Amazonas", "uf": "AM", "rotulo": "Amazonas"},
    "BA":  {"nome": "Tribunal Regional Eleitoral da Bahia", "uf": "BA", "rotulo": "Bahia"},
    "CE":  {"nome": "Tribunal Regional Eleitoral do Ceará", "uf": "CE", "rotulo": "Ceará"},
    "DF":  {"nome": "Tribunal Regional Eleitoral do Distrito Federal", "uf": "DF", "rotulo": "Distrito Federal"},
    "ES":  {"nome": "Tribunal Regional Eleitoral do Espírito Santo", "uf": "ES", "rotulo": "Espírito Santo"},
    "GO":  {"nome": "Tribunal Regional Eleitoral de Goiás", "uf": "GO", "rotulo": "Goiás"},
    "MA":  {"nome": "Tribunal Regional Eleitoral do Maranhão", "uf": "MA", "rotulo": "Maranhão"},
    "MT":  {"nome": "Tribunal Regional Eleitoral de Mato Grosso", "uf": "MT", "rotulo": "Mato Grosso"},
    "MS":  {"nome": "Tribunal Regional Eleitoral de Mato Grosso do Sul", "uf": "MS", "rotulo": "Mato Grosso do Sul"},
    "MG":  {"nome": "Tribunal Regional Eleitoral de Minas Gerais", "uf": "MG", "rotulo": "Minas Gerais"},
    "PA":  {"nome": "Tribunal Regional Eleitoral do Pará", "uf": "PA", "rotulo": "Pará"},
    "PB":  {"nome": "Tribunal Regional Eleitoral da Paraíba", "uf": "PB", "rotulo": "Paraíba"},
    "PR":  {"nome": "Tribunal Regional Eleitoral do Paraná", "uf": "PR", "rotulo": "Paraná"},
    "PE":  {"nome": "Tribunal Regional Eleitoral de Pernambuco", "uf": "PE", "rotulo": "Pernambuco"},
    "PI":  {"nome": "Tribunal Regional Eleitoral do Piauí", "uf": "PI", "rotulo": "Piauí"},
    "RJ":  {"nome": "Tribunal Regional Eleitoral do Rio de Janeiro", "uf": "RJ", "rotulo": "Rio de Janeiro"},
    "RN":  {"nome": "Tribunal Regional Eleitoral do Rio Grande do Norte", "uf": "RN", "rotulo": "Rio Grande do Norte"},
    "RS":  {"nome": "Tribunal Regional Eleitoral do Rio Grande do Sul", "uf": "RS", "rotulo": "Rio Grande do Sul"},
    "RO":  {"nome": "Tribunal Regional Eleitoral de Rondônia", "uf": "RO", "rotulo": "Rondônia"},
    "RR":  {"nome": "Tribunal Regional Eleitoral de Roraima", "uf": "RR", "rotulo": "Roraima"},
    "SC":  {"nome": "Tribunal Regional Eleitoral de Santa Catarina", "uf": "SC", "rotulo": "Santa Catarina"},
    "SP":  {"nome": "Tribunal Regional Eleitoral de São Paulo", "uf": "SP", "rotulo": "São Paulo"},
    "SE":  {"nome": "Tribunal Regional Eleitoral de Sergipe", "uf": "SE", "rotulo": "Sergipe"},
    "TO":  {"nome": "Tribunal Regional Eleitoral do Tocantins", "uf": "TO", "rotulo": "Tocantins"},
}

# ---------------------------------------------------------------------------
# 2) PALAVRAS-CHAVE QUE IDENTIFICAM CARGOS DE TI
#    Se o texto do cargo/especialidade contiver qualquer um destes termos,
#    a nomeação é classificada como TI. (Comparação sem acento e em minúsculas.)
# ---------------------------------------------------------------------------
PALAVRAS_TI = [
    "tecnologia da informacao",
    "analise de sistemas",
    "desenvolvimento de sistemas",
    "programacao de sistemas",
    "suporte",
    "infraestrutura",
    "operacao de computador",
    "operador de computador",
    "seguranca da informacao",
    "banco de dados",
    "redes",
]

# Termos que, mesmo sendo "Apoio Especializado", NÃO são de TI e devem ser
# ignorados (evita falso positivo quando o cargo aparece junto na mesma portaria).
PALAVRAS_NAO_TI = [
    "medicina", "enfermagem", "odontologia", "psicologia", "engenharia civil",
    "arquitetura", "contabilidade", "biblioteconomia", "estatistica",
    "comunicacao social", "serico social", "servico social", "nutricao",
    "farmacia", "taquigrafia", "fisioterapia", "assistente social",
]

# ---------------------------------------------------------------------------
# 3) CONSULTAS ENVIADAS AO BUSCADOR DO DOU
#    O coletor roda CADA consulta abaixo na Seção 2 e junta os resultados.
#    Várias consultas aumentam a cobertura (formatos de portaria variam).
# ---------------------------------------------------------------------------
CONSULTAS = [
    '"Concurso Público Nacional Unificado da Justiça Eleitoral"',
    '"Concurso Público Nacional Unificado"',
]

# Seção do DOU onde saem atos de pessoal (nomeações). do2 = Seção 2.
SECAO_DOU = "do2"

# Quantidade de resultados por página na busca.
RESULTADOS_POR_PAGINA = 20

# Máximo de páginas a percorrer por consulta (trava de segurança).
MAX_PAGINAS = 8

# Só processa portarias dos últimos N dias (o seed cobre o histórico).
DIAS_RETROATIVOS = 60

# User-Agent "de navegador" — o in.gov.br responde melhor assim.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)