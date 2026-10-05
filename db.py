# -*- coding: utf-8 -*-
"""Acesso ao banco SQLite.

Eu uso o módulo sqlite3 da biblioteca padrão do Python, sem ORM. O sistema
tem cinco tabelas e consultas simples; um ORM seria uma camada a mais para
aprender e manter sem ganho real. Todas as consultas usam parâmetros (?), e
nunca concatenação de texto, o que impede injeção de SQL.
"""
import os
import sqlite3

from flask import g

import config


def get_db():
    """Devolvo a conexão da requisição atual, abrindo-a se for a primeira vez.

    O Flask guarda objetos por requisição em "g". Abro uma conexão por
    requisição e fecho no fim (close_db), o que é o padrão recomendado para
    SQLite com vários processos do Gunicorn.
    """
    if "db" not in g:
        os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
        g.db = sqlite3.connect(config.DATABASE_PATH)
        # Row permite acessar colunas pelo nome: row["token"] em vez de row[1].
        g.db.row_factory = sqlite3.Row
        # O SQLite só respeita as chaves estrangeiras (REFERENCES) se eu pedir.
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exc=None):
    """Fecho a conexão ao final de cada requisição (registrado em app.py)."""
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    """Crio as tabelas a partir do schema.sql (comando: flask --app app init-db)."""
    conn = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def execute(query, params=()):
    """Executo um INSERT/UPDATE e já confirmo (commit).

    Confirmo a cada comando porque cada passo do participante precisa ficar
    gravado na hora: se a conexão cair logo depois, a decisão dele não se perde.
    """
    conn = get_db()
    cur = conn.execute(query, params)
    conn.commit()
    return cur


def query_one(query, params=()):
    """Devolvo a primeira linha do resultado (ou None)."""
    return get_db().execute(query, params).fetchone()


def query_all(query, params=()):
    """Devolvo todas as linhas do resultado."""
    return get_db().execute(query, params).fetchall()
