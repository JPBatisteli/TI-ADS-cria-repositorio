import re
import unicodedata

from app.models.disciplina import Disciplina

# Limite de caracteres imposto pelo GitHub para o nome de um repositório
TAMANHO_MAXIMO_NOME_REPOSITORIO = 100

# Os pares período/sigla aceitos vêm da própria enumeração, para que acrescentar ou
# renomear uma disciplina não exija manter esta expressão em dia. Casar o par inteiro,
# e não cada parte em separado, recusa combinações inexistentes como 'p3-tiaw'.
_PERIODO_E_SIGLA = "|".join(
    f"{disciplina.rotulo_periodo}-{disciplina.sigla}" for disciplina in Disciplina
)

# Expressão regular para nome de repositório no formato padronizado
NOME_REPO_REGEX = re.compile(
    rf"^(?P<ano>\d{{4}})-(?P<semestre>[12])-"
    rf"(?P<turma>{_PERIODO_E_SIGLA})-(?P<projeto>.+)$"
)
"""Regex que valida nomes de repositórios institucionais.

O grupo `turma` casa o par período/sigla inteiro; `parse_nome_repositorio` o separa
nos campos `periodo` e `disciplina`.
"""

# Expressão regular para o código da disciplina (apenas dígitos, ex: 2401100)
CODIGO_DISCIPLINA_REGEX = re.compile(r"^\d+$")


def gerar_slug(texto: str) -> str:
    """
    Converte um texto livre no formato usado pelo GitHub em nomes de repositório.

    A conversão remove acentuação, aplica letras minúsculas e substitui qualquer
    sequência de caracteres não alfanuméricos por um único hífen.

    Args:
        texto (str): Texto informado pelo professor (ex: "Brechó Re-Use").

    Returns:
        str: Texto convertido em slug (ex: "brecho-re-use").
    """
    texto_sem_acento = unicodedata.normalize("NFKD", texto)
    texto_sem_acento = texto_sem_acento.encode("ascii", "ignore").decode("ascii")
    texto_sem_acento = texto_sem_acento.lower()
    texto_sem_acento = re.sub(r"[^a-z0-9]+", "-", texto_sem_acento)
    return texto_sem_acento.strip("-")


def parse_nome_repositorio(nome_repositorio: str) -> dict | None:
    """
    Faz o parse do nome de um repositório conforme padrão institucional.

    Args:
        nome_repositorio (str): Nome do repositório (ex: 2026-1-p3-tidai-adota-pet).

    Returns:
        dict | None: Um dicionário com os grupos extraídos (ano, semestre, periodo,
                     disciplina, projeto), ou None se o nome não corresponder ao
                     padrão esperado.
    """
    correspondencia = NOME_REPO_REGEX.match(nome_repositorio)

    if not correspondencia:
        return None

    dados = correspondencia.groupdict()
    dados["periodo"], dados["disciplina"] = dados.pop("turma").split("-")
    return dados


def validar_nome_repositorio(nome_repositorio: str) -> bool:
    """
    Verifica se um nome de repositório está de acordo com o padrão institucional.

    Args:
        nome_repositorio (str): Nome do repositório a ser validado.

    Returns:
        bool: True se o nome seguir o padrão, False caso contrário.
    """
    return parse_nome_repositorio(nome_repositorio) is not None


def validar_codigo_disciplina(codigo: str) -> bool:
    """
    Verifica se o código da disciplina contém apenas dígitos.

    Args:
        codigo (str): Código informado pelo professor (ex: 2401100).

    Returns:
        bool: True se o código for composto apenas por dígitos, False caso contrário.
    """
    return bool(CODIGO_DISCIPLINA_REGEX.match(codigo.strip()))
