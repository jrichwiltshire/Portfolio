import sqlite3

DATABASE_PATH = "data/travel_map.db"

def create_connection():
    """Creates a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        print(f"Successfully connected to the database at {DATABASE_PATH}")
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_tables():
    """Creates the necessary tables in the database."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # Create locations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL
                )
            """)

            # Create photos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    photo_url TEXT NOT NULL,
                    date_taken TEXT,
                    description TEXT,
                    FOREIGN KEY (location_id) REFERENCES locations (id)
                )
            """)

            conn.commit()
            print("Tables created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
        finally:
            conn.close()
    else:
        print("Could not create database connection.")

if __name__ == "__main__":
    create_tables()
    print("Database setup complete.")