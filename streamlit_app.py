from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st
import plotly.express as px


# Streamlit page configuration
st.set_page_config(
    page_title="World Weather Dashboard",
    page_icon="🌎",
    layout="wide"
)


# File locations
BASE_DIRECTORY = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIRECTORY / "data" / "weather.db"

#allows Streamlit to reuse the loaded DataFrame until the underlying function or input changes. 
# This makes the dashboard more responsive.
@st.cache_data
def load_weather_data(database_path):
    """
    Loading the cleaned weather records from the SQLite database.

    Streamlit caches the returned DataFrame so the database does not
    need to be queried every time the user interacts with the dashboard.
    """
    connection = None

    try:
        connection = sqlite3.connect(database_path)

        query = """
            SELECT
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
            FROM cleaned_weather
            ORDER BY city
        """

        weather_df = pd.read_sql_query(
            query,
            connection
        )

        return weather_df

    except sqlite3.Error as error:
        st.error(f"Could not load the weather database: {error}")
        return pd.DataFrame()

    finally:
        if connection is not None:
            connection.close()


# Stopping the application if the database cannot be found
if not DATABASE_PATH.exists():
    st.error(
        "The weather database could not be found. "
        "Run db_loader.py before starting the dashboard."
    )
    st.stop()


# Loading the database records
weather_df = load_weather_data(DATABASE_PATH)


# Stopping if the query returned no records
if weather_df.empty:
    st.warning("No cleaned weather records are available.")
    st.stop()


# Preparing database values for the dashboard
weather_df["scraped_at_utc"] = pd.to_datetime(
    weather_df["scraped_at_utc"],
    errors="coerce",
    utc=True
)

weather_df["daylight_saving"] = (
    weather_df["daylight_saving"].astype(bool)
)
##################################################################################################################################

# Sidebar filters
st.sidebar.header("Dashboard Filters")

st.sidebar.write(
    "Use the options below to explore weather conditions "
    "for different locations."
)


# Country filter
country_options = sorted(
    weather_df["country"].dropna().unique()
)

selected_countries = st.sidebar.multiselect(
    label="Select countries",
    options=country_options,
    default=[],
    placeholder="All countries"
)


# Weather-condition filter
condition_options = sorted(
    weather_df["primary_condition"].dropna().unique()
)

selected_conditions = st.sidebar.multiselect(
    label="Select weather conditions",
    options=condition_options,
    default=[],
    placeholder="All weather conditions"
)


# Temperature-range filter
minimum_temperature = int(
    weather_df["temperature_f"].min()
)

maximum_temperature = int(
    weather_df["temperature_f"].max()
)

selected_temperature_range = st.sidebar.slider(
    label="Temperature range (°F)",
    min_value=minimum_temperature,
    max_value=maximum_temperature,
    value=(
        minimum_temperature,
        maximum_temperature
    )
)


# Daylight-saving filter
daylight_saving_filter = st.sidebar.radio(
    label="Daylight-saving status",
    options=[
        "All cities",
        "Observing daylight saving",
        "Not observing daylight saving",
    ]
)

# Creating a copy that will contain the filtered records
filtered_weather_df = weather_df.copy()


# Applying the country filter
if selected_countries:
    filtered_weather_df = filtered_weather_df[
        filtered_weather_df["country"].isin(
            selected_countries
        )
    ]


# Applying the weather-condition filter
if selected_conditions:
    filtered_weather_df = filtered_weather_df[
        filtered_weather_df["primary_condition"].isin(
            selected_conditions
        )
    ]


# Applying the temperature-range filter
filtered_weather_df = filtered_weather_df[
    filtered_weather_df["temperature_f"].between(
        selected_temperature_range[0],
        selected_temperature_range[1]
    )
]


# Applying the daylight-saving filter
if daylight_saving_filter == "Observing daylight saving":
    filtered_weather_df = filtered_weather_df[
        filtered_weather_df["daylight_saving"]
    ]

elif daylight_saving_filter == "Not observing daylight saving":
    filtered_weather_df = filtered_weather_df[
        ~filtered_weather_df["daylight_saving"]
    ]


# Dashboard heading################################################################################################################
st.title("🌎 World Weather Dashboard")

st.write(
    "Explore a scraped snapshot of temperatures and weather "
    "conditions for major cities around the world."
)


# Displaying when the observations were collected
latest_scrape_time = weather_df["scraped_at_utc"].max()

if pd.notna(latest_scrape_time):
    formatted_scrape_time = latest_scrape_time.strftime(
        "%B %d, %Y at %H:%M UTC"
    )

    st.caption(
        f"Weather observations collected on "
        f"{formatted_scrape_time}. "
        "This dashboard displays a saved snapshot and does not "
        "update in real time."
    )

# The expander provides useful context without taking up too much dashboard space.
with st.expander("About this dataset"):
    st.write(
        f"This dataset contains weather observations for "
        f"{weather_df['city'].nunique()} cities across "
        f"{weather_df['country'].nunique()} countries."
    )

    st.write(
        "The data was collected from the Weather Around the World "
        "table using Selenium and Beautiful Soup. Pandas was used "
        "to clean and transform the records before they were saved "
        "in a SQLite database."
    )

    st.write(
        "Temperatures are standardized in Fahrenheit. Weather "
        "descriptions, local times, countries, daylight-saving "
        "status, and source links are also included."
    )

    st.markdown(
        "Data source: "
        "[Time and Date - Weather Around the World]"
        "(https://www.timeanddate.com/weather/)"
    )


# Stopping before creating metrics or charts if no records match
if filtered_weather_df.empty:
    st.warning(
        "No weather records match the selected filters. "
        "Try expanding the temperature range or changing a selection."
    )
    st.stop()


# Dynamic summary metrics
metric_column1, metric_column2, metric_column3, metric_column4 = (
    st.columns(4)
)

with metric_column1:
    st.metric(
        label="Cities Displayed",
        value=filtered_weather_df["city"].nunique()
    )

with metric_column2:
    st.metric(
        label="Countries Displayed",
        value=filtered_weather_df["country"].nunique()
    )

with metric_column3:
    st.metric(
        label="Average Temperature",
        value=(
            f"{filtered_weather_df['temperature_f'].mean():.1f} °F"
        )
    )

with metric_column4:
    lowest_temperature = (
        filtered_weather_df["temperature_f"].min()
    )

    highest_temperature = (
        filtered_weather_df["temperature_f"].max()
    )

    st.metric(
        label="Temperature Range",
        value=(
            f"{lowest_temperature:.0f}–"
            f"{highest_temperature:.0f} °F"
        )
    )

#################################################################################################################
# Visualization 1: Temperature distribution

st.subheader("Temperature Distribution")

st.write(
    "This histogram shows how frequently different Fahrenheit "
    "temperature ranges appear among the selected cities. "
    "Use the sidebar filters to update the visualization."
)


average_temperature = (
    filtered_weather_df["temperature_f"].mean()
)


temperature_histogram = px.histogram(
    filtered_weather_df,
    x="temperature_f",
    nbins=15,
    title="Distribution of City Temperatures",
    labels={
        "temperature_f": "Temperature (°F)",
        "count": "Number of Cities",
    },
    color_discrete_sequence=["#FF4B4B"],
    hover_data={
        "temperature_f": True,
        "city": True,
        "country": True,
    }
)


# Add a line marking the current filtered average
temperature_histogram.add_vline(
    x=average_temperature,
    line_width=2,
    line_dash="dash",
    line_color="#00CC96",
    annotation_text=(
        f"Average: {average_temperature:.1f} °F"
    ),
    annotation_position="top right"
)


temperature_histogram.update_layout(
    xaxis_title="Temperature (°F)",
    yaxis_title="Number of Cities",
    bargap=0.08,
    hovermode="x unified"
)


st.plotly_chart(
    temperature_histogram,
    use_container_width=True,
    theme="streamlit"
)

# Visualization 2: Warmest and coldest cities

st.subheader("City Temperature Ranking")

st.write(
    "Compare the warmest or coldest cities within the current "
    "sidebar selections."
)


ranking_control1, ranking_control2 = st.columns(2)


with ranking_control1:
    ranking_type = st.radio(
        label="Choose a ranking",
        options=[
            "Warmest cities",
            "Coldest cities",
        ],
        horizontal=True
    )


with ranking_control2:
    requested_city_count = st.select_slider(
        label="Number of cities to display",
        options=[5, 10, 15, 20],
        value=10
    )


# Preventing the requested number from exceeding the available records
city_count = min(
    requested_city_count,
    len(filtered_weather_df)
)


if ranking_type == "Warmest cities":
    ranked_cities_df = (
        filtered_weather_df
        .nlargest(city_count, "temperature_f")
        .sort_values(
            "temperature_f",
            ascending=True
        )
    )

    ranking_title = (
        f"Top {city_count} Warmest Cities"
    )

else:
    ranked_cities_df = (
        filtered_weather_df
        .nsmallest(city_count, "temperature_f")
        .sort_values(
            "temperature_f",
            ascending=False
        )
    )

    ranking_title = (
        f"Top {city_count} Coldest Cities"
    )


city_ranking_chart = px.bar(
    ranked_cities_df,
    x="temperature_f",
    y="city",
    orientation="h",
    color="temperature_f",
    color_continuous_scale="RdYlBu_r",
    title=ranking_title,
    text="temperature_f",
    labels={
        "temperature_f": "Temperature (°F)",
        "city": "City",
    },
    hover_data={
        "country": True,
        "primary_condition": True,
        "weather_condition": True,
        "temperature_f": ":.1f",
    }
)


city_ranking_chart.update_traces(
    texttemplate="%{text:.0f} °F",
    textposition="outside"
)


city_ranking_chart.update_layout(
    xaxis_title="Temperature (°F)",
    yaxis_title="City",
    coloraxis_colorbar_title="°F",
    margin={
        "l": 20,
        "r": 40,
        "t": 60,
        "b": 20,
    }
)


st.plotly_chart(
    city_ranking_chart,
    use_container_width=True,
    theme="streamlit"
)

# Visualization 3: Weather-condition frequency

st.subheader("Weather Condition Summary")

st.write(
    "This visualization compares the frequency of primary weather "
    "conditions. Longer bars represent more cities, while the color "
    "shows the average temperature for each condition."
)


# Grouping the filtered records by primary weather condition
condition_summary_df = (
    filtered_weather_df
    .groupby(
        "primary_condition",
        as_index=False
    )
    .agg(
        city_count=("city", "nunique"),
        average_temperature=("temperature_f", "mean")
    )
    .sort_values(
        "city_count",
        ascending=True
    )
)


# Rounding the average for cleaner labels and hover information
condition_summary_df["average_temperature"] = (
    condition_summary_df["average_temperature"].round(1)
)


condition_chart = px.bar(
    condition_summary_df,
    x="city_count",
    y="primary_condition",
    orientation="h",
    color="average_temperature",
    color_continuous_scale="RdYlBu_r",
    title="Frequency of Primary Weather Conditions",
    text="city_count",
    labels={
        "city_count": "Number of Cities",
        "primary_condition": "Primary Weather Condition",
        "average_temperature": "Average Temperature (°F)",
    },
    hover_data={
        "city_count": True,
        "average_temperature": ":.1f",
    }
)


condition_chart.update_traces(
    texttemplate="%{text} cities",
    textposition="outside"
)


condition_chart.update_layout(
    xaxis_title="Number of Cities",
    yaxis_title="Primary Weather Condition",
    coloraxis_colorbar_title="Average °F",
    height=max(
        450,
        len(condition_summary_df) * 32
    ),
    margin={
        "l": 20,
        "r": 60,
        "t": 60,
        "b": 20,
    }
)


st.plotly_chart(
    condition_chart,
    use_container_width=True,
    theme="streamlit"
)

# Identifying the most common condition in the filtered data
most_common_condition = (
    condition_summary_df
    .sort_values(
        "city_count",
        ascending=False
    )
    .iloc[0]
)


st.info(
    f"The most common condition in the current selection is "
    f"{most_common_condition['primary_condition']}, appearing in "
    f"{int(most_common_condition['city_count'])} cities with an "
    f"average temperature of "
    f"{most_common_condition['average_temperature']:.1f} °F."
)

# ############################################################################################################
# Filtered records and CSV download

st.subheader("Filtered Weather Records")

st.write(
    f"The current filters contain "
    f"{len(filtered_weather_df)} weather records."
)


# Convert the filtered DataFrame into downloadable CSV data
filtered_csv = filtered_weather_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Filtered Weather Data",
    data=filtered_csv,
    file_name="filtered_world_weather_data.csv",
    mime="text/csv"
)


st.dataframe(
    filtered_weather_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "city": st.column_config.TextColumn(
            "City"
        ),
        "country": st.column_config.TextColumn(
            "Country"
        ),
        "temperature_f": st.column_config.NumberColumn(
            "Temperature (°F)",
            format="%.1f °F"
        ),
        "daylight_saving": st.column_config.CheckboxColumn(
            "Daylight Saving"
        ),
        "scraped_at_utc": st.column_config.DatetimeColumn(
            "Collected at (UTC)",
            format="YYYY-MM-DD HH:mm"
        ),
        "city_url": st.column_config.LinkColumn(
            "Source Page",
            display_text="Open weather page"
        ),
    }
)

# Dashboard footer
st.divider()

st.caption(
    "World Weather Dashboard | Created by Alex Núñez Palomares "
    "for the Code the Dream Python Essentials capstone project."
)