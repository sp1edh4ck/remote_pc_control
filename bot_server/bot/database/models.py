TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        client_id TEXT UNIQUE NOT NULL,
        name TEXT UNIQUE
    );
    """
]