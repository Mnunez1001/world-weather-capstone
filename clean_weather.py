from pathlib import Path

import pandas as pd


# File locations
BASE_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = BASE_DIRECTORY / "data"
RAW_CSV_PATH = DATA_DIRECTORY / "raw_weather_data.csv"
CLEANED_CSV_PATH = DATA_DIRECTORY / "cleaned_weather_data.csv"


# Confirming that the scraper created the raw CSV
if not RAW_CSV_PATH.exists():
    raise FileNotFoundError(
        "The raw weather CSV was not found. "
        "Run scrape_weather.py before cleaning the data."
    )


# Loading the raw weather data
weather_df = pd.read_csv(RAW_CSV_PATH)


print("Raw weather data loaded successfully.")

print("\n--- BEFORE CLEANING ---")

print(f"Rows: {weather_df.shape[0]}")
print(f"Columns: {weather_df.shape[1]}")

print("\nColumn names:")
print(weather_df.columns.tolist())

print("\nData types:")
print(weather_df.dtypes)

print("\nMissing values:")
print(weather_df.isna().sum())

print("\nExact duplicate rows:")
print(weather_df.duplicated().sum())

print("\nDuplicate cities:")
print(weather_df.duplicated(subset=["city"]).sum())

print("\nFirst five raw records:")
print(weather_df.head().to_string(index=False))

# Making a separate copy so the raw DataFrame remains unchanged
cleaned_weather_df = weather_df.copy()


# Removing extra whitespace from text columns
text_columns = [
    "city",
    "local_datetime_raw",
    "weather_condition",
    "temperature_raw",
    "scraped_at_utc",
    "city_url",
]

for column in text_columns:
    cleaned_weather_df[column] = (
        cleaned_weather_df[column]
        .astype("string")
        .str.strip()
    )


# Removing duplicates if future scraping sessions produce any
cleaned_weather_df = cleaned_weather_df.drop_duplicates()

cleaned_weather_df = cleaned_weather_df.drop_duplicates(
    subset=["city"],
    keep="first"
)


# Spliting the local day and local time
local_datetime_parts = cleaned_weather_df[
    "local_datetime_raw"
].str.extract(
    r"^(?P<local_day>[A-Za-z]{3})\s+(?P<local_time>.+)$"
)

cleaned_weather_df["local_day"] = (
    local_datetime_parts["local_day"]
    .str.title()
)

parsed_local_time = pd.to_datetime(
    local_datetime_parts["local_time"],
    format="%I:%M %p",
    errors="coerce"
)

cleaned_weather_df["local_time"] = (
    parsed_local_time.dt.strftime("%H:%M:%S")
)

cleaned_weather_df["local_hour"] = parsed_local_time.dt.hour


# Extracting the numeric temperature
cleaned_weather_df["temperature_value"] = pd.to_numeric(
    cleaned_weather_df["temperature_raw"].str.extract(
        r"(-?\d+(?:\.\d+)?)",
        expand=False
    ),
    errors="coerce"
)


# Extracting F or C in case the website changes its unit
cleaned_weather_df["temperature_unit"] = (
    cleaned_weather_df["temperature_raw"]
    .str.extract(r"°\s*([FC])", expand=False)
    .str.upper()
)


# Keeping Fahrenheit values and converting Celsius values if necessary
celsius_rows = (
    cleaned_weather_df["temperature_unit"] == "C"
)

cleaned_weather_df["temperature_f"] = (
    cleaned_weather_df["temperature_value"]
)

cleaned_weather_df.loc[
    celsius_rows,
    "temperature_f"
] = (
    cleaned_weather_df.loc[
        celsius_rows,
        "temperature_value"
    ] * 9 / 5
) + 32

cleaned_weather_df["temperature_f"] = (
    cleaned_weather_df["temperature_f"].round(1)
)


# Cleaning extra punctuation and whitespace from weather descriptions
cleaned_weather_df["weather_condition"] = (
    cleaned_weather_df["weather_condition"]
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    .str.rstrip(".")
)


# Extracting a simpler category for later charts
cleaned_weather_df["primary_condition"] = (
    cleaned_weather_df["weather_condition"]
    .str.split(".")
    .str[0]
    .str.strip()
)


# Extracting the country from each city URL
cleaned_weather_df["country"] = (
    cleaned_weather_df["city_url"]
    .str.extract(
        r"/weather/([^/]+)/",
        expand=False
    )
    .str.replace("-", " ", regex=False)
    .str.title()
)

# Correcting common country abbreviations
cleaned_weather_df["country"] = (
    cleaned_weather_df["country"].replace(
        {
            "Usa": "USA",
            "Uk": "UK",
            "Uae": "UAE",
        }
    )
)


# Converting the collection timestamp into a datetime value
cleaned_weather_df["scraped_at_utc"] = pd.to_datetime(
    cleaned_weather_df["scraped_at_utc"],
    errors="coerce",
    utc=True
)


# Using Unknown for a missing weather description
cleaned_weather_df["weather_condition"] = (
    cleaned_weather_df["weather_condition"]
    .fillna("Unknown")
)

cleaned_weather_df["primary_condition"] = (
    cleaned_weather_df["primary_condition"]
    .fillna("Unknown")
)


# Removing malformed records missing essential information
rows_before_removing_malformed = len(cleaned_weather_df)

cleaned_weather_df = cleaned_weather_df.dropna(
    subset=[
        "city",
        "country",
        "local_time",
        "temperature_f",
        "scraped_at_utc",
    ]
)

malformed_rows_removed = (
    rows_before_removing_malformed
    - len(cleaned_weather_df)
)


# Selecting and arranging the final cleaned columns
cleaned_weather_df = cleaned_weather_df[
    [
        "city",
        "country",
        "local_day",
        "local_time",
        "local_hour",
        "weather_condition",
        "primary_condition",
        "temperature_f",
        "daylight_saving",
        "scraped_at_utc",
        "city_url",
    ]
]


print("\n--- CLEANING RESULTS ---")
print(f"Malformed rows removed: {malformed_rows_removed}")
print(f"Cleaned rows: {len(cleaned_weather_df)}")
print(f"Cleaned columns: {len(cleaned_weather_df.columns)}")

print("\nCleaned data types:")
print(cleaned_weather_df.dtypes)

print("\nMissing values after cleaning:")
print(cleaned_weather_df.isna().sum())

print("\nFirst five cleaned records:")
print(cleaned_weather_df.head().to_string(index=False))

# Checking if the cleaned dataset is empty
if cleaned_weather_df.empty:
    raise RuntimeError(
        "The cleaned dataset is empty. "
        "The cleaned CSV was not created."
    )


# Saving the cleaned dataset
cleaned_weather_df.to_csv(
    CLEANED_CSV_PATH,
    index=False,
    encoding="utf-8",
    date_format="%Y-%m-%dT%H:%M:%SZ"
)


# Reading the file again to verify that it was saved successfully
verification_df = pd.read_csv(CLEANED_CSV_PATH)

print(f"\nCleaned weather data saved to: {CLEANED_CSV_PATH}")
print(f"Saved CSV rows: {verification_df.shape[0]}")
print(f"Saved CSV columns: {verification_df.shape[1]}")