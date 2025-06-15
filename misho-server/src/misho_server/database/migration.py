from misho_server.database import SqliteDatabase
from alembic.config import Config
from alembic import command
import os


def insert_hour_slot() -> str:
    return """
    INSERT INTO hour_slots (from_hour, to_hour) VALUES
        (7, 8),
        (8, 9),
        (9, 10),
        (10, 11),
        (11, 12),
        (12, 13),
        (13, 14),
        (14, 15),
        (15, 16),
        (16, 17),
        (17, 19),
        (19, 21),
        (21, 23)
    ON CONFLICT DO NOTHING;
    """


def insert_courts_table_query() -> str:
    return """
    INSERT INTO courts (id, name) VALUES
        (4, 'Court 4'),
        (5, 'Court 5'),
        (6, 'Court 6'),
        (7, 'Court 7'),
        (8, 'Court 8')
    ON CONFLICT DO NOTHING;
    """


def run_migrations():
    # Adjust path to the root-level alembic.ini
    alembic_cfg = Config(os.path.join(
        os.path.dirname(__file__), "../../../alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def migrate():
    run_migrations()
    print("Database migration completed successfully.")

    with SqliteDatabase().connect() as context:
        context.cursor.execute(insert_hour_slot())
        context.cursor.execute(insert_courts_table_query())
        context.connection.commit()
        print("Inserted initial data")


if __name__ == "__main__":
    migrate()
