from pathlib import Path
import sqlite3

import pandas as pd


# File locations
BASE_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = BASE_DIRECTORY / "data"

RAW_CSV_PATH = DATA_DIRECTORY / "raw_weather_data.csv"
CLEANED_CSV_PATH = DATA_DIRECTORY / "cleaned_weather_data.csv"
DATABASE_PATH = DATA_DIRECTORY / "weather.db"


# Confirming that both CSV files exist
required_files = [
    RAW_CSV_PATH,
    CLEANED_CSV_PATH,
]

for file_path in required_files:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required file was not found: {file_path}\n"
            "Run the scraping and cleaning programs first."
        )


# Loading each CSV into a separate DataFrame
raw_weather_df = pd.read_csv(RAW_CSV_PATH)

cleaned_weather_df = pd.read_csv(
    CLEANED_CSV_PATH,
    parse_dates=["scraped_at_utc"]
)


# Confirming that the datasets contain records
if raw_weather_df.empty:
    raise RuntimeError(
        "The raw weather dataset is empty."
    )

if cleaned_weather_df.empty:
    raise RuntimeError(
        "The cleaned weather dataset is empty."
    )


print("CSV files loaded successfully.")

print("\nRaw weather dataset:")
print(f"Rows: {raw_weather_df.shape[0]}")
print(f"Columns: {raw_weather_df.shape[1]}")

print("\nCleaned weather dataset:")
print(f"Rows: {cleaned_weather_df.shape[0]}")
print(f"Columns: {cleaned_weather_df.shape[1]}")

# Converting the DataFrames into records for SQLite
raw_weather_records = [
    (
        row.city,
        row.local_datetime_raw,
        row.weather_condition,
        row.temperature_raw,
        int(row.daylight_saving),
        row.scraped_at_utc,
        row.city_url,
    )
    for row in raw_weather_df.itertuples(index=False)
]


cleaned_weather_records = [
    (
        row.city,
        row.country,
        row.local_day,
        row.local_time,
        int(row.local_hour),
        row.weather_condition,
        row.primary_condition,
        float(row.temperature_f),
        int(row.daylight_saving),
        row.scraped_at_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        row.city_url,
    )
    for row in cleaned_weather_df.itertuples(index=False)
]

#Creating and populating the database

connection = None

try:
    # Creating or connecting to the SQLite database
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    print(f"\nConnected to SQLite database: {DATABASE_PATH}")

    # Removing old versions of the tables so the pipeline can run again
    cursor.execute("DROP TABLE IF EXISTS raw_weather")
    cursor.execute("DROP TABLE IF EXISTS cleaned_weather")

    # Creating the table for the raw CSV data
    cursor.execute(
        """
        CREATE TABLE raw_weather (
            raw_weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            local_datetime_raw TEXT,
            weather_condition TEXT,
            temperature_raw TEXT,
            daylight_saving INTEGER NOT NULL,
            scraped_at_utc TEXT NOT NULL,
            city_url TEXT NOT NULL
        )
        """
    )

    # Creating the table for the cleaned CSV data
    cursor.execute(
        """
        CREATE TABLE cleaned_weather (
            cleaned_weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            local_day TEXT NOT NULL,
            local_time TEXT NOT NULL,
            local_hour INTEGER NOT NULL,
            weather_condition TEXT NOT NULL,
            primary_condition TEXT NOT NULL,
            temperature_f REAL NOT NULL,
            daylight_saving INTEGER NOT NULL,
            scraped_at_utc TEXT NOT NULL,
            city_url TEXT NOT NULL
        )
        """
    )

    print("Database tables created successfully.")

    # Inserting all raw weather records
    cursor.executemany(
        """
        INSERT INTO raw_weather (
            city,
            local_datetime_raw,
            weather_condition,
            temperature_raw,
            daylight_saving,
            scraped_at_utc,
            city_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        raw_weather_records
    )

    # Inserting all cleaned weather records
    cursor.executemany(
        """
        INSERT INTO cleaned_weather (
            city,
            country,
            local_day,
            local_time,
            local_hour,
            weather_condition,
            primary_condition,
            temperature_f,
            daylight_saving,
            scraped_at_utc,
            city_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cleaned_weather_records
    )

    # Permanently saving the database changes
    connection.commit()

    print("Weather records inserted successfully.")

    # Verifying the number of records in both tables
    cursor.execute("SELECT COUNT(*) FROM raw_weather")
    raw_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cleaned_weather")
    cleaned_count = cursor.fetchone()[0]

    print("\nDatabase verification:")
    print(f"raw_weather rows: {raw_count}")
    print(f"cleaned_weather rows: {cleaned_count}")

    # Previewing records from the cleaned table
    cleaned_preview_df = pd.read_sql_query(
        """
        SELECT *
        FROM cleaned_weather
        LIMIT 5
        """,
        connection
    )

    print("\nFirst five cleaned database records:")
    print(cleaned_preview_df.to_string(index=False))

except sqlite3.Error as error:
    # Undoing unfinished database changes
    if connection is not None:
        connection.rollback()

    print(f"\nSQLite database error: {error}")

except Exception as error:
    # Catching errors that do not come directly from SQLite
    if connection is not None:
        connection.rollback()

    print(f"\nUnexpected error: {error}")

finally:
    # Closing the connection whether the program succeeds or fails
    if connection is not None:
        connection.close()
        print("\nSQLite database connection closed.")