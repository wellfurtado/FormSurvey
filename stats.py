# -*- coding: utf-8 -*-
"""Números agregados para o painel administrativo (/admin).

Aqui eu só calculo contagens e médias, nunca listo participantes. Os gráficos
do painel são barras feitas em CSS puro (largura proporcional ao valor), sem
biblioteca de gráficos: menos dependências e nada carregado de sites externos.

O painel serve para acompanhar a coleta em andamento: quantas pessoas
entraram, como está a distribuição entre as condições e se a verificação da
manipulação (itens HUM e PER) está indo na direção esperada.
"""
from collections import defaultdict

import config
import db
import questions


def _consent_counts():
    """Quantos concordaram e quantos recusaram, em cada termo."""
    def count(sql):
        return db.query_one(sql)["n"]

    return {
        "adult": {
            "agreed": count("SELECT COUNT(*) n FROM adults WHERE agreed = 1"),
            "declined": count("SELECT COUNT(*) n FROM adults WHERE agreed = 0"),
        },
        "guardian": {
            "agreed": count("SELECT COUNT(*) n FROM guardians WHERE agreed = 1"),
            "declined": count("SELECT COUNT(*) n FROM guardians WHERE agreed = 0"),
        },
        # O assentimento do(a) menor fica na própria tabela de códigos.
        "minor": {
            "agreed": count("SELECT COUNT(*) n FROM access_codes WHERE minor_agreed = 1"),
            "declined": count("SELECT COUNT(*) n FROM access_codes WHERE minor_agreed = 0"),
            "pending": count("SELECT COUNT(*) n FROM access_codes WHERE used = 0"),
        },
    }


def _condition_counts():
    """Por condição: quantos foram sorteados, quantos abriram o chatbot e
    quantos concluíram. É aqui que eu acompanho se os grupos estão
    equilibrados e onde está a desistência."""
    rows = {
        r["condition"]: r
        for r in db.query_all(
            "SELECT condition, COUNT(*) AS assigned, "
            "COUNT(chatbot_opened_at) AS opened, COUNT(completed_at) AS completed "
            "FROM participants GROUP BY condition"
        )
    }
    result = []
    for name, cond in config.CONDITIONS.items():
        r = rows.get(name)
        result.append({
            "name": name,
            "factors": {f: cond[f] for f in config.FACTORS},
            "assigned": r["assigned"] if r else 0,
            "opened": r["opened"] if r else 0,
            "completed": r["completed"] if r else 0,
        })
    return result


def _construct_averages():
    """Média de cada construto, no geral e separada por condição.

    O construto de um item é o prefixo do código (HUM1 -> HUM). Só considero
    participantes que concluíram. Devolvo uma lista com, para cada construto,
    a média geral e um dicionário {condição: média}.
    """
    rows = db.query_all(
        "SELECT p.condition, r.question_code, r.value FROM responses r "
        "JOIN participants p ON p.id = r.participant_id WHERE p.completed_at IS NOT NULL"
    )
    likert = questions.all_likert_codes()
    sums, counts = defaultdict(float), defaultdict(int)
    for r in rows:
        if r["question_code"] not in likert:
            continue
        prefix = r["question_code"].rstrip("0123456789")
        value = float(r["value"])
        for key in ((prefix, None), (prefix, r["condition"])):
            sums[key] += value
            counts[key] += 1

    constructs = []
    for prefix in questions.CONSTRUCT_LABELS:
        if not counts[(prefix, None)]:
            continue
        avg = sums[(prefix, None)] / counts[(prefix, None)]
        by_condition = {
            name: round(sums[(prefix, name)] / counts[(prefix, name)], 2) if counts[(prefix, name)] else None
            for name in config.CONDITIONS
        }
        constructs.append({
            "code": prefix,
            "label": questions.CONSTRUCT_LABELS[prefix],
            "avg": round(avg, 2),
            "n": counts[(prefix, None)],
            "pct": round(avg / 5 * 100, 1),
            "by_condition": by_condition,
        })
    return constructs


def _profile_breakdown():
    """Distribuição das respostas do Bloco IV (perfil), em quantidade e %."""
    profile = []
    for code, text, _options in questions.PROFILE_BLOCK[1]:
        rows = db.query_all(
            "SELECT value, COUNT(*) c FROM responses WHERE question_code = ? GROUP BY value ORDER BY c DESC",
            (code,),
        )
        total = sum(r["c"] for r in rows)
        options = [
            {"label": r["value"], "count": r["c"], "pct": round(r["c"] / total * 100, 1) if total else 0}
            for r in rows
        ]
        profile.append({"code": code, "text": text, "total": total, "options": options})
    return profile


def compute():
    """Tudo o que o painel mostra, calculado a cada abertura da página."""
    return {
        "consent": _consent_counts(),
        "conditions": _condition_counts(),
        "factors": config.FACTORS,
        "constructs": _construct_averages(),
        "profile": _profile_breakdown(),
    }
