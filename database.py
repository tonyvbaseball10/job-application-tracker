"""MySQL connection and query helpers for the Job Application Tracker."""

import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Return a new MySQL connection using environment configuration."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "job_tracker"),
        autocommit=False,
    )


@contextmanager
def db_cursor(dictionary=True):
    """Yield a cursor and commit, or roll back if an operation fails."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def fetch_all(query, params=()):
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_one(query, params=()):
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def execute(query, params=()):
    with db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.lastrowid

