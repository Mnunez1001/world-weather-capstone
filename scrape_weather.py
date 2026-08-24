#Selenium: Retrieves and renders the dynamic webpage.
#WebDriver Manager: Downloads or locates a compatible ChromeDriver.
#Beautiful Soup: Parses the copied HTML locally.
#Pandas: Organizes the extracted records and saves them as CSV.

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By

#These create an explicit wait. Instead of guessing how long the page needs with time.sleep(), 
# Selenium waits until the table actually exists. This makes the scraper more reliable.
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from webdriver_manager.chrome import ChromeDriverManager

from datetime import datetime, timezone
import pandas as pd

#This allows us to parse the HTML and extract the data we want.
from bs4 import BeautifulSoup
from urllib.parse import urljoin

#This allows us to create a path to the CSV file in a way that works on any operating system.
from pathlib import Path

# Website containing the weather table
WEATHER_URL = "https://www.timeanddate.com/weather/"

# The following constants define the paths to the data directory and the raw CSV file.
BASE_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = BASE_DIRECTORY / "data"
RAW_CSV_PATH = DATA_DIRECTORY / "raw_weather_data.csv"

# Configuring Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# Starting the browser
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
    options=options
)


weather_records = []
table_html = None

try:
    # Selenium retrieves the dynamic webpage
    driver.get(WEATHER_URL)

    weather_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.zebra.fw.tb-theme")
        )
    )

    print("Weather page loaded successfully.")
    print("Weather table found successfully.")

    # Copy the complete table HTML with one Selenium request
    table_html = weather_table.get_attribute("outerHTML")

finally:
    # Selenium is no longer needed after copying the table
    driver.quit()


if not table_html:
    raise RuntimeError("The weather table HTML could not be retrieved.")


# Parsing the captured table locally
soup = BeautifulSoup(table_html, "html.parser")
rows = soup.select("tbody tr")

scraped_at_utc = datetime.now(timezone.utc).isoformat(
    timespec="seconds"
)

for row in rows:
    # Only select cells that belong directly to this row
    cells = row.find_all("td", recursive=False)

    # Each city uses four consecutive cells in total, so we can iterate over the cells in steps of four
    for index in range(0, len(cells), 4):
        if index + 3 >= len(cells):
            continue

        city_cell = cells[index]
        time_cell = cells[index + 1]
        condition_cell = cells[index + 2]
        temperature_cell = cells[index + 3]

        city_link = city_cell.find("a")

        # A valid record must contain a city link 
        if city_link is None:
            continue

        city = city_link.get_text(strip=True)

        relative_city_url = city_link.get("href", "")
        city_url = urljoin(WEATHER_URL, relative_city_url)

        dst_marker = city_cell.select_one("span.wds")

        daylight_saving = (
            dst_marker is not None
            and "*" in dst_marker.get_text(strip=True)
        )

        local_datetime_raw = (
            time_cell.get_text(" ", strip=True) or None
        )

        weather_image = condition_cell.find("img")

        if weather_image is not None:
            weather_condition = (
                weather_image.get("alt", "").strip() or None
            )
        else:
            weather_condition = None

        temperature_raw = (
            temperature_cell.get_text(" ", strip=True) or None
        )

        weather_records.append(
            {
                "city": city,
                "local_datetime_raw": local_datetime_raw,
                "weather_condition": weather_condition,
                "temperature_raw": temperature_raw,
                "daylight_saving": daylight_saving,
                "scraped_at_utc": scraped_at_utc,
                "city_url": city_url,
            }
        )


raw_weather_df = pd.DataFrame(weather_records)

print("\nScraping completed.")
print(f"Total cities collected: {len(raw_weather_df)}")

print("\nFirst five records:")
print(raw_weather_df.head().to_string(index=False))

if raw_weather_df.empty:
    raise RuntimeError(
        "No weather records were collected. CSV file was not created."
    )


# Creating the data directory if it does not already exist
DATA_DIRECTORY.mkdir(exist_ok=True)

# Saving the unmodified scraped records
raw_weather_df.to_csv(
    RAW_CSV_PATH,
    index=False,
    encoding="utf-8"
)

print(f"\nRaw weather data saved to: {RAW_CSV_PATH}")
print(f"CSV rows: {len(raw_weather_df)}")
print(f"CSV columns: {len(raw_weather_df.columns)}")