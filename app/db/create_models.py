"""
Creating tables in the database.

This script checks for the existence of tables in the database and, if they do not exist, creates them.
It also initializes the `uuid_generate_v4()` function in PostgreSQL to use unique identifiers.

Options:
    - engine: SQLAlchemy engine used to interact with the database.

Actions:
    - The script uses SQL queries to create the users, fsm_context and user_tasks tables.
    - When creating the user_tasks table, foreign keys and a cascade delete are specified, linking it with the users table.
    - If the table in the database has already been created, this action in this file is skipped
"""

from sqlalchemy import text
from sqlalchemy.ext.automap import automap_base

from app.db.db_config import engine

Base = automap_base()
Base.prepare(engine, reflect=True)

# Get the table names
table_names: list[str] = [x for x in Base.metadata.tables.keys()]

with engine.connect() as con:
    con.execute(
        text(
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
        )
    )
    if "users" not in table_names:
        con.execute(
            text(
                'CREATE TABLE users (\
                user_uuid UUID DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY, \
                owner_telegram_id BIGINT UNIQUE NOT NULL, \
                login_name VARCHAR UNIQUE NOT NULL, \
                username VARCHAR NOT NULL, \
                password VARCHAR NOT NULL, \
                is_login bool NOT NULL DEFAULT false, \
                registration_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);'
            )
        )

    if "fsm_context" not in table_names:
        con.execute(
            text(
                'CREATE TABLE fsm_context (\
                telegram_id BIGINT NOT NULL PRIMARY KEY, \
                state VARCHAR DEFAULT NULL, \
                data JSON DEFAULT \'{}\');'
            )
        )

    if "user_tasks" not in table_names:
        con.execute(
            text(
                'CREATE TABLE user_tasks (\
                task_uuid UUID DEFAULT uuid_generate_v4() NOT NULL PRIMARY KEY, \
                id_task serial UNIQUE NOT NULL, \
                owner_telegram_id bigint NOT NULL, \
                task_name VARCHAR NOT NULL, \
                description VARCHAR NOT NULL, \
                start_time TIMESTAMPTZ NOT NULL, \
                end_time TIMESTAMPTZ NOT NULL, \
                completion_time TIMESTAMPTZ DEFAULT NULL, \
                status BOOLEAN NOT NULL DEFAULT FALSE, \
                FOREIGN KEY (owner_telegram_id) REFERENCES users (owner_telegram_id) ON DELETE CASCADE);'
            )
        )

    con.commit()
