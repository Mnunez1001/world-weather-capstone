# World Weather Dashboard

The World Weather Dashboard is a Python web-scraping and data visualization project created for the Code the Dream Python Essentials capstone project.

The project collects weather observations for major cities around the world, cleans and transforms the scraped information, stores the raw and cleaned datasets in a SQLite database, and presents the results through an interactive Streamlit dashboard.

## Project Purpose

The purpose of this project is to demonstrate a complete data pipeline:

1. Retrieve data from a website.
2. Extract and organize the raw information.
3. Clean and transform the dataset with Pandas.
4. Store the raw and cleaned data in SQLite.
5. Query the database from a Streamlit application.
6. Present interactive visualizations and filters.
7. Deploy the completed dashboard online.

## Data Source

Weather information is collected from the [Time and Date – Weather Around the World](https://www.timeanddate.com/weather/) page.

The scraped dataset is a snapshot of the weather observations available when the scraper was executed. It does not update continuously or represent live weather after that collection time.

## Technologies Used

- Python
- Selenium
- WebDriver Manager
- Beautiful Soup
- Pandas
- SQLite
- Streamlit
- Plotly
- Git and GitHub

## Project Workflow

### 1. Web Scraping

`selenium` loads the Weather Around the World webpage in a headless Chrome browser.

After Selenium locates the weather table, the program copies its rendered HTML. Beautiful Soup then parses the captured HTML locally and extracts:

- City
- Local day and time
- Weather condition
- Temperature
- Daylight-saving status
- Collection timestamp
- City source URL

The unmodified observations are saved in `raw_weather_data.csv`.

### 2. Data Cleaning and Transformation

Pandas loads the raw CSV into a DataFrame and performs several cleaning and transformation operations:

- Removes extra whitespace
- Checks for missing values
- Checks for exact duplicates and repeated cities
- Splits the local day and time
- Converts local time to 24-hour format
- Extracts the local hour
- Extracts numeric temperature values
- Standardizes temperatures in Fahrenheit
- Cleans weather descriptions
- Creates a simplified primary weather condition
- Extracts country names from city URLs
- Converts collection timestamps into UTC datetimes
- Removes malformed records missing essential values

The transformed records are saved in `cleaned_weather_data.csv`.

### 3. SQLite Database

The database loader creates `weather.db` and stores each CSV in a separate table:

| CSV file | SQLite table |
|---|---|
| `raw_weather_data.csv` | `raw_weather` |
| `cleaned_weather_data.csv` | `cleaned_weather` |

The database program explicitly creates both tables, inserts the records, verifies the row totals, commits successful changes, rolls back unsuccessful transactions, and closes the connection.

### 4. Streamlit Dashboard

The Streamlit application queries the `cleaned_weather` table from the SQLite database.

The dashboard includes dynamic summary metrics for:

- Cities displayed
- Countries displayed
- Average temperature
- Selected temperature range

Users can filter the data by:

- Country
- Primary weather condition
- Fahrenheit temperature range
- Daylight-saving status

All dashboard metrics, visualizations, insights, and records respond to the selected filters.

## Interactive Visualizations

### Temperature Distribution

An interactive Plotly histogram displays the distribution of Fahrenheit temperatures. A reference line identifies the average temperature within the current selection.

### City Temperature Ranking

A horizontal bar chart ranks the warmest or coldest cities. Users can choose the ranking direction and the number of cities displayed.

### Weather Condition Summary

A horizontal bar chart compares the number of cities associated with each primary weather condition. Bar colors represent the average temperature for each condition.

The dashboard also generates a dynamic statement identifying the most common weather condition in the filtered dataset.

## Additional Dashboard Features

- Responsive sidebar filters
- Interactive Plotly hover information
- Dynamic metrics and descriptions
- Expandable dataset documentation
- Collection timestamp
- Clickable source links
- Formatted database records
- Downloadable filtered CSV data
- Graceful handling of filters that return no records


## Installation

Clone the repository:

```bash
git clone <repository-url>
cd <repository-directory>
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Running the Complete Pipeline

Run the web scraper:

```bash
python scrape_weather.py
```

Clean and transform the scraped data:

```bash
python clean_weather.py
```

Create and populate the SQLite database:

```bash
python db_loader.py
```

Start the Streamlit dashboard:

```bash
python -m streamlit run streamlit_app.py
```

The local application should be available at:

```text
http://localhost:8501
```

## Deployed Application

The public Streamlit dashboard is available here:

[Open the World Weather Dashboard](<streamlit-application-url>)

## Limitations

- The dataset represents one collection period rather than historical weather trends.
- The dashboard does not update automatically in real time.
- The webpage reported 143 locations, while 140 complete city records were collected.
- Incomplete table groups or records without valid city links are intentionally skipped.
- Country names are derived from the structure of each city URL.
- Website structure changes could require updates to the scraper.
- Weather conditions reflect the source website’s descriptions at the time of collection.

## Future Improvements

Possible future additions include:

- Scheduling the scraper to collect weather observations regularly
- Preserving multiple collection periods in the database
- Creating historical temperature trends
- Adding geographic coordinates and an interactive world map
- Comparing temperature patterns by region
- Adding unit selection between Fahrenheit and Celsius

## Author

Alex Núñez Palomares

Created for the Code the Dream Python Essentials capstone project.
