from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Campus:
    """
    Representa um campus da PUC Minas onde as disciplinas de Trabalho
    Interdisciplinar (TI) são lecionadas.

    O campus determina duas coisas no momento da criação de um repositório:
    a organização do GitHub em que ele será criado e a sigla usada como
    prefixo do nome padronizado.

    O repositório-modelo não é atributo do campus: em ADS ele depende também da
    disciplina, e é resolvido em `app/models/template.py`.

    Attributes:
        sigla (str): Sigla usada como prefixo do nome do repositório (ex: pbe, pco).
        nome (str): Nome do campus (ex: Contagem).
        organizacao (str): Nome da organização no GitHub (ex: ICEI-PUC-Minas-PCO-ADS-TI).
        curso (str): Nome do curso associado. Valor padrão: "Análise e Desenvolvimento
                     de Sistemas".
    """
    sigla: str
    nome: str
    organizacao: str
    curso: str = "Análise e Desenvolvimento de Sistemas"

    @property
    def url_organizacao(self) -> str:
        """Retorna a URL da organização do campus no GitHub."""
        return f"https://github.com/{self.organizacao}"

    def __str__(self) -> str:
        return f"{self.nome} ({self.sigla.upper()})"


CAMPI: Dict[str, Campus] = {
    "Betim": Campus(
        sigla="pbe",
        nome="Betim",
        organizacao="ICEI-PUC-Minas-PBE-ADS-TI"
    ),
    "Contagem": Campus(
        sigla="pco",
        nome="Contagem",
        organizacao="ICEI-PUC-Minas-PCO-ADS-TI"
    ),
}
"""Campi disponíveis, indexados pelo nome exibido na interface."""


def listar_nomes_campi() -> List[str]:
    """
    Retorna os nomes dos campi cadastrados, em ordem alfabética.

    Returns:
        List[str]: Nomes dos campi disponíveis para seleção.
    """
    return sorted(CAMPI.keys())


def obter_campus(nome: str) -> Campus:
    """
    Obtém um campus a partir do seu nome.

    Args:
        nome (str): Nome do campus (ex: "Contagem").

    Returns:
        Campus: Instância correspondente ao nome informado.

    Raises:
        KeyError: Se o campus não estiver cadastrado.
    """
    return CAMPI[nome]
