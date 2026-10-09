# Air Pollution Dashboard — Streamlit Walkthrough

An interactive air quality dashboard built with **Streamlit, Python, PyDeck, and the Open-Meteo APIs**. This project demonstrates how to integrate live API data, geocoding, interactive maps, metric cards, and time-series visualizations into a single dashboard.

It is designed as a hands-on project for the Streamlit introduction session, covering API integration, data processing, caching, session state, and interactive UI components.

## What's Included

- `app.py` — Main Streamlit dashboard application.
- `requirements.txt` — Python libraries and dependencies required to run the application.

## Data Sources

This dashboard uses two free APIs from Open-Meteo. **No API key is required.**

### 1. Air Quality API

Documentation: https://open-meteo.com/en/docs/air-quality-api

The Air Quality API provides current and hourly pollutant-specific US AQI sub-indices, along with historical and forecast data.

Pollutants included:

- **PM2.5** — Fine particulate matter.
- **PM10** — Particulate matter with a diameter of 10 micrometres or less.
- **NO2** — Nitrogen dioxide.
- **O3** — Ozone.

The dashboard uses these values to display current AQI metrics, AQI categories, approximate 24-hour changes, and hourly trends.

### 2. Geocoding API

Documentation: https://open-meteo.com/en/docs/geocoding-api

The Geocoding API converts a city or place name into geographic coordinates and returns matching location details.

The dashboard uses this API to:

- Search for locations by name.
- Display multiple matching results.
- Distinguish locations using state, country, and district information when available.
- Retrieve latitude and longitude for the selected location.
- Add new locations to the dashboard.

**Important:** The locations represent geographic coordinates queried against Open-Meteo's air quality model. They are not necessarily physical air quality monitoring stations, and the returned values should not be interpreted as measurements from a specific ground-based monitoring station.

## Features

### 1. Dynamic Location Search

- Search for a city using the sidebar.
- Retrieve multiple matching locations through the Geocoding API.
- Select the correct location from the results.
- View its latitude and longitude.
- Add the selected location to the dashboard.
- Prevent duplicate locations based on geographic coordinates.

Delhi and Mumbai are included as default locations.

### 2. Interactive Location Map

- Displays the locations added to the dashboard.
- Uses PyDeck's `ScatterplotLayer` to render map markers.
- Highlights the selected location in red.
- Displays other added locations in blue.
- Automatically centers the map on the selected location.
- Provides location names through marker tooltips.

The marker colors represent selection status, not AQI severity.

### 3. Current Pollutant AQI Cards

Displays four pollutant-specific metric cards for the selected location:

- PM2.5 AQI
- PM10 AQI
- NO2 AQI
- O3 AQI

Each card includes the current AQI value, its category, and the approximate percentage change compared with the hourly AQI value from about 24 hours earlier.

AQI categories are displayed using color-coded labels:

| US AQI range | Category |

| 0–50 | Good |
| 51–100 | Moderate |
| 101–150 | Unhealthy for Sensitive Groups |
| 151–200 | Unhealthy |
| 201–300 | Very Unhealthy |
| Above 300 | Hazardous |

Unavailable values are displayed as `N/A`.

### 4. AQI Change Calculation

The dashboard calculates both the absolute and percentage change in the AQI sub-index.

**Absolute change:**

`Current AQI - Previous AQI`

**Percentage change:**

`((Current AQI - Previous AQI) / Previous AQI) × 100`

The previous value is taken from the latest available hourly record at or before approximately 24 hours before the API's current timestamp.

- A positive change indicates that the AQI sub-index increased, which generally indicates worsening air quality.
- A negative change indicates that the AQI sub-index decreased, which generally indicates improvement.
- A zero previous value, missing data, or an unavailable comparison prevents the percentage calculation.

**Note:** This percentage represents the change in the AQI sub-index, not the percentage change in pollutant concentration. AQI changes are also not a direct measure of the percentage change in health risk.

### 5. Hourly Pollutant Trend Charts

The dashboard provides separate tabs for PM2.5, PM10, NO2, and O3.

Each tab displays an hourly US AQI trend chart containing:

- Five days of historical hourly data.
- Two days of forecast data.
- Date and time on the X-axis.
- Pollutant-specific US AQI on the Y-axis.

Selecting a different pollutant tab changes the trend chart without hiding the four current pollutant cards.

The historical and forecast series are returned by the Open-Meteo Air Quality API. Forecast values are estimates and may change as new forecasts become available.

### 6. API Caching

The dashboard uses Streamlit's `@st.cache_data` decorator to reduce repeated API requests.

- **Geocoding data:** Cached for 24 hours (`ttl=86400`).
- **Current AQI data:** Cached for 30 minutes (`ttl=1800`).
- **Hourly trend data:** Cached for 30 minutes (`ttl=1800`).

Caching improves responsiveness and reduces unnecessary API calls. Consequently, displayed data may not refresh on every interaction.

## Prerequisites

- Python 3.9 or later.
- pip, Python's package installer.
- An active internet connection to access the Open-Meteo APIs.

## Setup and Run

### 1. Create a project folder

Create a folder named `air-pollution-dashboard` and place both files inside it:

```text
air-pollution-dashboard/
├── app.py
└── requirements.txt
```

### 2. Create a virtual environment

Open a terminal or VS Code terminal in the project folder.

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

Once activated, the terminal should indicate that the virtual environment is active.

### 4. Install the dependencies

Install all libraries listed in `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

This installs the project's declared dependencies, including the libraries needed for Streamlit, data processing, HTTP requests, and interactive mapping.

There is no need to install the libraries individually if they are already declared in `requirements.txt`.

### 5. Run the dashboard

Execute:

```bash
streamlit run app.py
```

Streamlit will start a local web server and normally open the dashboard in your browser.

If it does not open automatically, navigate to:

http://localhost:8501

### 6. Use the dashboard

1. Open the sidebar and enter a city name, such as `Kanpur`.
2. Click **Search locations**.
3. Choose the correct matching location.
4. Review its coordinates and click **Add selected location**.
5. Use the **Location** dropdown to select any added location.
6. Explore the selected location on the map.
7. Review the four current pollutant AQI cards and their 24-hour changes.
8. Select the PM2.5, PM10, NO2, or O3 tab to explore its hourly historical and forecast trend.

The map, pollutant cards, and trend charts respond to the selected location.

### 7. Make changes to the code

Open `app.py` in your code editor and modify the required function or UI component.

Save the file. Streamlit will usually detect the change and offer to rerun the application. Accept the rerun to see the updated dashboard.

### 8. Stop the application

Return to the terminal where Streamlit is running and press:

```text
Ctrl + C
```

## Code Structure

The application is organized into functions with specific responsibilities.

| Function or variable | Purpose |
|---|---|
| `geocode_city()` | Searches for matching locations using the Open-Meteo Geocoding API. |
| `load_pollution_data()` | Retrieves current AQI sub-indices for all added locations and converts the results into a Pandas DataFrame. |
| `get_aqi_category()` | Maps a numeric AQI value to a category label and color. |
| `filter_data()` | Filters a DataFrame by city and, optionally, pollutant. |
| `render_map()` | Displays the selected location and other locations using PyDeck. |
| `calculate_aqi_change()` | Calculates absolute and percentage changes using current and approximately 24-hour-old AQI values. |
| `render_pollutant_cards()` | Displays the four pollutant-specific AQI cards and their change indicators. |
| `fetch_trend_data()` | Retrieves hourly historical and forecast AQI data for a selected coordinate and pollutant. |
| `render_trend_chart()` | Displays the hourly AQI line chart for a pollutant. |
| `main()` | Coordinates location search, session state, data loading, the map, metric cards, and pollutant tabs. |

### Important variables

- `AIR_QUALITY_URL` — Endpoint for the Air Quality API.
- `GEOCODING_URL` — Endpoint for the Geocoding API.
- `DEFAULT_STATIONS` — Initial locations supplied with the application.
- `POLLUTANT_FIELDS` — Maps readable pollutant names to the corresponding API field names.
- `AQI_CATEGORY_HEX` — Stores hexadecimal color codes for AQI category labels.
- `st.session_state.stations` — Maintains the list of added locations across Streamlit reruns.
- `st.session_state.geocode_candidates` — Stores the location search results for selection.

### Key Streamlit and Python concepts demonstrated

- `st.cache_data` — Caches API responses and processed data.
- `st.session_state` — Preserves application state between reruns.
- `st.rerun()` — Reruns the application after a location is added.
- `st.columns()` — Arranges the four pollutant metric cards horizontally.
- `st.metric()` — Displays AQI values and change indicators.
- `st.tabs()` — Separates the four pollutant trend charts.
- `st.sidebar` — Groups location search and selection controls.
- `requests.get()` — Sends HTTP requests to the APIs.
- `response.raise_for_status()` — Raises an exception when an HTTP request fails.
- `pd.DataFrame()` — Structures API results into tabular data.
- `pd.to_datetime()` — Converts API timestamps into datetime values.
- `pdk.Layer()` and `pdk.Deck()` — Configure and display the interactive map.

## Troubleshooting

**`streamlit: command not found`**

Make sure the virtual environment is activated. Alternatively, run:

```bash
python -m streamlit run app.py
```

**Missing Python library**

If an error reports `ModuleNotFoundError`, verify that the virtual environment is active and install the declared dependencies again:

```bash
python -m pip install -r requirements.txt
```

**Port already in use**

Start the application on another port:

```bash
streamlit run app.py --server.port 8502
```

**No locations found**

Check the spelling of the city name and your internet connection. Try a more specific or alternate place name.

**Air-quality API request failed**

Check your internet connection and retry. The dashboard requires outbound HTTPS access to Open-Meteo. API errors and timeouts can prevent data from loading.

**Some AQI values show `N/A`**

The API may not return a value for a particular pollutant or location. The dashboard only creates records for available values.

**Map is empty or the selected location is not displayed**

Check whether the API returned AQI data and whether the selected location is present in the current dataset.

**Data looks stale**

The application caches current AQI and hourly trend data for 30 minutes and geocoding results for 24 hours. Cached results may be reused until their cache entries expire.

**AQI change is unavailable**

The application needs a valid current AQI value and an hourly value from approximately 24 hours earlier. Missing data or a previous AQI value of zero can prevent the percentage change from being calculated.

## Next Steps and Extensions

- Add more default locations or let users manage and remove locations.
- Add AQI thresholds to highlight locations with elevated AQI values.
- Use richer map tooltips to display current pollutant values.
- Add downloadable CSV reports for the selected location.
- Add a comparison view to compare AQI trends across multiple locations.
- Introduce additional pollutants supported by the Open-Meteo API.
- Add error handling and user-facing messages for individual API failures.

## Learning Outcomes

By completing this project, learners will understand how to:

- Integrate external APIs into a Streamlit application.
- Convert place names into geographic coordinates using geocoding.
- Process JSON API responses with Python and Pandas.
- Display geographic information using PyDeck.
- Build metric cards, tabs, and interactive sidebar controls.
- Calculate absolute and percentage changes from time-series data.
- Cache API results and manage state across Streamlit reruns.
- Combine maps, numerical indicators, and line charts into a complete dashboard.

## License and Data Attribution

This project uses Open-Meteo's public APIs. Review the applicable terms, attribution requirements, and data licensing information before redistributing the application or using it commercially.

- Air Quality API: https://open-meteo.com/en/docs/air-quality-api
- Geocoding API: https://open-meteo.com/en/docs/geocoding-api
- Open-Meteo: https://open-meteo.com/
