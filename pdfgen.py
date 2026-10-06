# -*- coding: utf-8 -*-
"""Geração dos comprovantes em PDF.

A Resolução CNS nº 510/2016 e o Ofício Circular nº 2/2021 da CONEP pedem que
o participante de pesquisa em ambiente virtual receba uma cópia do termo que
aceitou. Eu gero essa cópia como PDF, na hora, a partir do mesmo texto que é
mostrado na tela (terms.py): uma única fonte de verdade para os dois formatos.

Os PDFs não são gravados em disco nem no banco. Eles são montados quando o
participante clica em "Baixar" e entregues direto ao navegador dele.

Uso a biblioteca fpdf2, que é pequena, escrita em Python puro e não depende de
programas externos (como wkhtmltopdf ou LibreOffice).
"""
import os
import unicodedata

from fpdf import FPDF

import questions
import terms

# As fontes que já vêm dentro da fpdf2 (Helvetica, Times, Courier) não têm
# acentos completos do português e quebram em caracteres como "ç". Por isso
# procuro uma fonte TrueType com Unicode já instalada no sistema operacional,
# em vez de embutir um arquivo de fonte no repositório. No servidor Debian, a
# fonte vem do pacote fonts-dejavu-core (ver INSTALL.md).
_UNICODE_FONT_CANDIDATES = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]


def _find_unicode_font():
    """Devolvo o caminho da primeira fonte da lista que existir no sistema."""
    for path in _UNICODE_FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _strip_accents(text):
    """Removo os acentos (ação -> acao). Só uso isso se não houver fonte Unicode."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _render(text):
    """Transformo um texto corrido em PDF A4, um parágrafo por linha.

    Linhas vazias viram um pequeno espaço vertical. A quebra de página é
    automática.
    """
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_path = _find_unicode_font()
    if font_path:
        pdf.add_font("Body", "", font_path)
        pdf.set_font("Body", size=11)
    else:
        # ponytail: sem fonte Unicode no sistema, prefiro gerar o PDF sem
        # acentos a deixar o participante sem comprovante. Para ter os acentos
        # de volta no Linux: apt install fonts-dejavu-core.
        pdf.set_font("Helvetica", size=11)
        text = _strip_accents(text)

    for paragraph in text.strip("\n").split("\n"):
        if paragraph.strip() == "":
            pdf.ln(4)
        else:
            pdf.multi_cell(0, 6, paragraph.strip(), align="L", new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())


def _answers_block(answers):
    """Seção com as respostas dadas: cada item seguido da resposta marcada.

    answers é uma lista de (código, valor). Itens em branco não aparecem.
    """
    if not answers:
        return "\n\nSUAS RESPOSTAS À PESQUISA\n\nNenhum item foi respondido.\n"
    lines = ["\n\nSUAS RESPOSTAS À PESQUISA\n"]
    for code, value in answers:
        lines.append(f"{questions.question_text(code)}\nResposta: {questions.answer_display(code, value)}\n")
    return "\n".join(lines)


def adult_pdf(consent_at, answers):
    """Comprovante do adulto: RCLE completo + data/hora do aceite + respostas."""
    body = terms.flatten(terms.RCLE_TITLE, terms.RCLE_SUBTITLE, terms.RCLE_SECTIONS)
    footer = (
        "\n\nDADOS DO REGISTRO\n"
        "Decisão: Concordo em participar.\n"
        "Declaração: tenho 18 anos ou mais.\n"
        f"Data/hora do registro: {consent_at}\n"
    )
    return _render(body + footer + _answers_block(answers))


def guardian_pdf(guardian_name, relationship, access_code, access_link, consent_on):
    """Comprovante do responsável: acesso do(a) menor + TCLE completo + quem
    autorizou.

    Coloco o link e o código de acesso NO INÍCIO do documento, porque é a
    informação que o responsável vai procurar quando for repassar o acesso
    ao(à) menor. O texto explica que o acesso é de uso único e deixa de
    funcionar depois que o(a) menor decide.

    O(A) menor é identificado(a) pelo código de acesso, e não pelo nome, que
    o sistema não coleta. O responsável sabe a quem repassou cada código.
    """
    access = (
        "ACESSO DO(A) MENOR À PESQUISA\n"
        "Repasse ao(à) menor o link abaixo (ou o código, que pode ser digitado na página "
        'inicial da pesquisa, em "Sou menor de idade e já tenho um código de acesso").\n'
        f"Link de acesso: {access_link}\n"
        f"Código de acesso: {access_code}\n"
        "O acesso é de uso único: depois que o(a) menor decidir se quer ou não participar, "
        "o link e o código deixam de funcionar. Guarde este documento até lá e não o "
        "compartilhe com outras pessoas.\n\n"
    )
    body = terms.flatten(terms.TCLE_TITLE, terms.TCLE_SUBTITLE, terms.TCLE_SECTIONS)
    footer = (
        "\n\nDADOS DO REGISTRO\n"
        f"Responsável: {guardian_name}\n"
        f"Grau de parentesco / vínculo: {relationship}\n"
        "Decisão: Autorizo a participação do(a) menor.\n"
        f"Código de acesso do(a) menor: {access_code}\n"
        f"Data do registro: {consent_on}\n"
    )
    return _render(access + body + footer)


def minor_pdf(consent_at, answers):
    """Comprovante do(a) menor: TALE completo + data/hora do aceite + respostas."""
    body = terms.flatten(terms.TALE_TITLE, terms.TALE_SUBTITLE, terms.TALE_SECTIONS)
    footer = (
        "\n\nDADOS DO REGISTRO\n"
        "Decisão: SIM, quero participar!\n"
        f"Data/hora do registro: {consent_at}\n"
    )
    return _render(body + footer + _answers_block(answers))
