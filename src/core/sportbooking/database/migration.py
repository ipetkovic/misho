

from core.sportbooking.database import SqliteDatabase


# user - id, name, username, password
# user_token -> user_id, token, created_at, updated_at
# reserve_job -> user_id, config, created_at, cron
#   config -> Reserve(date, time_range, court_ids_by_priority)
#   config -> Login(user_id, cron)

def create_hour_slot() -> str:
    return """
    CREATE TABLE IF NOT EXISTS hour_slot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_hour INT NOT NULL,
        end_hour INT NOT NULL
    );

    """


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


def create_time_slot() -> str:
    return """
    CREATE TABLE IF NOT EXISTS time_slot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        hour_slot_id INTEGER NOT NULL,
        FOREIGN KEY (hour_slot_id) REFERENCES hour_slot(id)
    );
    """


def create_courts_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS courts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );
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


def create_reservation_slots_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS reservation_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time_slot_id INTEGER NOT NULL,
        court_id INTEGER NOT NULL,
        FOREIGN KEY (time_slot_id) REFERENCES time_slot(id),
        FOREIGN KEY (court_id) REFERENCES courts(id)
    );
    """


def create_jobs_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        time_slot_id INTEGER NOT NULL,
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
        FOREIGN KEY (time_slot_id) REFERENCES time_slot(id)
    );
    """


def create_job_courts_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS job_courts (
        job_id INTEGER NOT NULL,
        court_id INTEGER NOT NULL,
        priority INTEGER NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (court_id) REFERENCES courts(id)
    );
    """


def create_reserve_job_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS reserve_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    """


def create_monitoring_job_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS monitoring_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    """


def create_calendar_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS calendar (
        date DATE NOT NULL,
        time_slot_id INTEGER NOT NULL,
        court_id INTEGER NOT NULL,
        FOREIGN KEY (time_slot_id) REFERENCES time_slot(id),
        FOREIGN KEY (court_id) REFERENCES courts(id)
    );
    """


def create_monitoring_changes_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS monitoring_job_reservation_slot_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        reservation_slot_id INTEGER NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (reservation_slot_id) REFERENCES reservation_slots(id)
    );
    """


def time_slot_unique_constraint() -> str:
    return """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_time_slot_unique ON time_slot (date, hour_slot_id);
    """


def jobs_unique_constraint() -> str:
    return """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_unique ON jobs (user_id, time_slot_id);
    """


def create_users_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        name TEXT NOT NULL UNIQUE
    );
    """


def create_user_tokens_table_query() -> str:
    return """
    CREATE TABLE IF NOT EXISTS user_tokens (
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """


def insert_user() -> str:
    return """
    INSERT INTO users (username, password, name) VALUES
        ('Ivo Petkovic', 'i2802989', 'Petković_Ivo')
    ON CONFLICT DO NOTHING;
    """


# def create_schedule_job_table_query() -> str:
#     return """
#     CREATE TABLE IF NOT EXISTS schedule_jobs (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         user_id INTEGER NOT NULL,
#         config JSON NOT NULL,
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#         FOREIGN KEY (user_id) REFERENCES users(id)
#     );
#     """


# def alter_job_table_add_status_column_query() -> str:
#     return """
#     ALTER TABLE schedule_jobs
#     ADD COLUMN status TEXT DEFAULT 'pending';
#     """


# def create_reservation_calendar_table_query() -> str:
#     return """
#     CREATE TABLE IF NOT EXISTS reservation_calendar (
#         id INTEGER PRIMARY KEY,
#         calendar TEXT NOT NULL,
#         updated_at TIMESTAMP NOT NULL
#     );
#     """

def migrate():
    with SqliteDatabase().connect() as context:
        context.cursor.execute(insert_hour_slot())
        context.cursor.execute(insert_courts_table_query())
        context.cursor.execute(insert_user())

        context.connection.commit()
        print("Database migration completed successfully.")


if __name__ == "__main__":
    migrate()
