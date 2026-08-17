from typing import Dict, List, Tuple

from app.models.disciplina import Disciplina

# Disciplinas ofertadas em cada campus e, quando houver, os códigos das suas turmas.
#
# O curso é ofertado apenas à noite, de modo que não há distinção de turno: os códigos
# de uma disciplina ficariam listados diretamente, sem nível intermediário.
#
# Hoje o que este catálogo determina é quais disciplinas cada campus oferece — é daqui
# que sai a lista da interface. O código da turma é digitado livremente pelo professor e
# não compõe o nome do repositório; o seu uso definitivo ainda será decidido, e é por
# isso que a estrutura para cadastrá-los permanece aqui, ainda vazia.
#
# Betim não consta: enquanto não houver acesso de owner à organização de lá, o trabalho
# concentra-se em Contagem. A interface avisa quando o campus não tem disciplinas.
CODIGOS_POR_TURMA: Dict[str, Dict[Disciplina, Tuple[str, ...]]] = {
    # Contagem
    "pco": {
        Disciplina.TIAW: (),
        Disciplina.TIAM: (),
        Disciplina.TIDAI: (),
        Disciplina.TIAPN: (),
        Disciplina.TIAI: (),
    },
}


def listar_disciplinas(sigla_campus: str) -> List[Disciplina]:
    """
    Lista as disciplinas ofertadas no campus, na ordem de oferta do curso.

    Args:
        sigla_campus (str): Sigla do campus (ex: 'pco').

    Returns:
        List[Disciplina]: Disciplinas com turmas cadastradas.
    """
    ofertadas = CODIGOS_POR_TURMA.get(sigla_campus, {})
    return [disciplina for disciplina in Disciplina if disciplina in ofertadas]


def listar_codigos(sigla_campus: str, disciplina: Disciplina) -> List[str]:
    """
    Lista os códigos das turmas de uma disciplina no campus.

    Args:
        sigla_campus (str): Sigla do campus.
        disciplina (Disciplina): Disciplina selecionada.

    Returns:
        List[str]: Códigos das turmas ofertadas.
    """
    return list(CODIGOS_POR_TURMA.get(sigla_campus, {}).get(disciplina, ()))


def codigo_valido(sigla_campus: str, codigo: str) -> bool:
    """
    Verifica se um código pertence a alguma turma cadastrada do campus.

    Args:
        sigla_campus (str): Sigla do campus.
        codigo (str): Código a ser verificado.

    Returns:
        bool: True se o código constar no catálogo do campus.
    """
    disciplinas = CODIGOS_POR_TURMA.get(sigla_campus, {})
    return any(codigo in codigos for codigos in disciplinas.values())
