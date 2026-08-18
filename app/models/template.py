from dataclasses import dataclass
from typing import Dict, Optional

from app.models.disciplina import Disciplina


@dataclass(frozen=True)
class Template:
    """
    Representa o repositório-modelo usado como base para os repositórios das equipes.

    O repositório de origem precisa estar marcado como template no GitHub
    (`is_template: true`), caso contrário a API recusa a geração.

    Attributes:
        owner (str): Organização ou usuário dono do repositório-modelo.
        repositorio (str): Nome do repositório-modelo.
    """
    owner: str
    repositorio: str

    @property
    def nome_completo(self) -> str:
        """Retorna o identificador no formato 'owner/repositorio'."""
        return f"{self.owner}/{self.repositorio}"

    @property
    def url(self) -> str:
        """Retorna a URL do repositório-modelo no GitHub."""
        return f"https://github.com/{self.nome_completo}"

    def __str__(self) -> str:
        return self.nome_completo


# Modelos usados nos dois campi. Betim e Contagem mantêm, cada um na sua organização,
# repositórios-modelo com os mesmos nomes — daí um único cadastro compartilhado. Se um
# dos campi passar a usar nomes próprios, basta escrever o seu dicionário em separado.
#
# TIAW e TIAWFE são a mesma disciplina: a sigla do modelo é a forma extensa, a da
# disciplina é a abreviada.
MODELOS_PADRAO: Dict[Disciplina, str] = {
    Disciplina.TIAW: "Template-TIAWFE",
    Disciplina.TIAPN: "Template-TIAPN",
    Disciplina.TIDAI: "Template-TIDAI",
    Disciplina.TIAM: "Template-TIAM",
    Disciplina.TIAI: "Template-TIAI",
}

# Repositórios-modelo, por campus e disciplina.
#
# Em ADS cada disciplina tem o seu modelo, ao contrário da Engenharia de Software, em
# que havia um modelo genérico por campus. Os modelos ficam na própria organização do
# campus, por isso apenas o nome do repositório é registado aqui.
MODELOS_POR_CAMPUS: Dict[str, Dict[Disciplina, str]] = {
    "pbe": MODELOS_PADRAO,  # Betim
    "pco": MODELOS_PADRAO,  # Contagem
}


def obter_template(
        sigla_campus: str,
        organizacao: str,
        disciplina: Disciplina
) -> Optional[Template]:
    """
    Obtém o repositório-modelo de uma disciplina no campus informado.

    Args:
        sigla_campus (str): Sigla do campus (ex: 'pco').
        organizacao (str): Organização do campus no GitHub, onde o modelo reside.
        disciplina (Disciplina): Disciplina selecionada.

    Returns:
        Optional[Template]: Modelo correspondente, ou None quando a disciplina não
                            tiver modelo cadastrado nesse campus. Sem modelo, o
                            repositório é criado vazio.
    """
    repositorio = MODELOS_POR_CAMPUS.get(sigla_campus, {}).get(disciplina)

    if repositorio is None:
        return None

    return Template(owner=organizacao, repositorio=repositorio)
