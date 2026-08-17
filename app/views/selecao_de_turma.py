from typing import Optional, Tuple

import streamlit as st

from app.models.campus import Campus
from app.models.disciplina import Disciplina
from app.models.turma import listar_disciplinas


def selecionar_turma(campus: Campus, sufixo_de_chave: str = "") -> Tuple[Optional[Disciplina], str]:
    """
    Monta a seleção da disciplina e o campo do código da turma.

    A disciplina define o período e o repositório-modelo, por isso vem de uma lista
    fechada. O código da turma é digitado livremente: ele não compõe o nome do
    repositório, servindo apenas para identificar a turma nos relatórios, e o seu uso
    definitivo ainda será decidido.

    Não há seleção de turno: o curso é ofertado apenas à noite.

    Args:
        campus (Campus): Campus selecionado, que determina as disciplinas ofertadas.
        sufixo_de_chave (str): Sufixo das chaves dos widgets, para que a mesma seleção
                               possa ser usada em mais de uma aba.

    Returns:
        Tuple[Optional[Disciplina], str]: Disciplina selecionada e código informado. A
                                          disciplina é None se o campus não tiver
                                          nenhuma cadastrada.
    """
    disciplinas = listar_disciplinas(campus.sigla)

    if not disciplinas:
        st.warning(
            f"Nenhuma disciplina cadastrada para o campus {campus.nome}. "
            "Atualize o catálogo em `app/models/turma.py`."
        )
        return None, ""

    coluna_disciplina, coluna_codigo = st.columns([2, 3])

    with coluna_disciplina:
        rotulo = st.selectbox(
            "Disciplina",
            [disciplina.rotulo for disciplina in disciplinas],
            key=f"disciplina{sufixo_de_chave}",
            help="A disciplina define o período e o repositório-modelo usado."
        )
        disciplina = Disciplina[rotulo]

    with coluna_codigo:
        codigo = st.text_input(
            "Código da turma (opcional)",
            key=f"codigo{sufixo_de_chave}",
            placeholder="Ex: 2401100",
            help="Apenas dígitos. Não entra no nome do repositório."
        )

    return disciplina, codigo.strip()
