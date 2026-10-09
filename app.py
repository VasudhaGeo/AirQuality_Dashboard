"""Air Pollution Dashboard — Streamlit walkthrough
Run with: streamlit run app.py
"""

import json
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

st.set_page_config(page_title="Air Pollution Dashboard", layout="wide")

# API endpoints
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Starting locations are predefined coordinates, not physical monitoring stations.
DEFAULT_STATIONS = [
    {
        "station": "Delhi, Delhi, India",
        "city": "Delhi, Delhi, India",
        "lat": 28.6139,
        "lon": 77.2090,
        "state": "Delhi",
        "country": "India",
        "district": None,
    },
    {
        "station": "Mumbai, Maharashtra, India",
        "city": "Mumbai, Maharashtra, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "state": "Maharashtra",
        "country": "India",
        "district": None,
    },
]

POLLUTANT_FIELDS = {
    "PM2.5": "us_aqi_pm2_5",
    "PM10": "us_aqi_pm10",
    "NO2": "us_aqi_nitrogen_dioxide",
    "O3": "us_aqi_ozone",
}


# ---------------------------------------------------------------------------
# 0. GEOCODING — return multiple matches for the user to choose from
# ---------------------------------------------------------------------------
@st.cache_data(ttl=86400)

def geocode_city(city_name):
    params = {
        "name": city_name,
        "count": 10,
        "language": "en",
        "format": "json",
    }

    response = requests.get(GEOCODING_URL, params=params, timeout=10)
    
    response.raise_for_status()

    data = response.json()
    results = data.get("results", [])

    locations = []
    for place in results:
        name = place.get("name", "Unknown")
        state = place.get("admin1")
        country = place.get("country")
        district = place.get("admin2")

        # Requested display combination: place name, state/region, country.
        label_parts = [name]
        if state:
            label_parts.append(state)
        if country:
            label_parts.append(country)
        label = ", ".join(label_parts)

        # Add district when available to help distinguish similar place names.
        if district:
            label += f" ({district})"

        locations.append(
            {
                "station": label,
                "city": label,
                "lat": float(place["latitude"]),
                "lon": float(place["longitude"]),
                "geocoding_id": place.get("id"),
                "state": state,
                "country": country,
                "district": district,
            }
        )

    # If two results still have the same label, append coordinates so the
    # dropdown options remain distinguishable.
    label_counts = {}
    for location in locations:
        label_counts[location["station"]] = label_counts.get(location["station"], 0) + 1

    for location in locations:
        if label_counts[location["station"]] > 1:
            location["station"] += f" — {location['lat']:.4f}, {location['lon']:.4f}"
            location["city"] = location["station"]

    return locations


# ---------------------------------------------------------------------------
# 1. DATA LOADING — current pollutant-specific AQI for each selected location
# ---------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def load_pollution_data(stations):
    if not stations:
        return pd.DataFrame(columns=["station", "city", "lat", "lon", "pollutant", "aqi"])

    params = {
        "latitude": ",".join(str(s["lat"]) for s in stations),
        "longitude": ",".join(str(s["lon"]) for s in stations),
        "current": ",".join(POLLUTANT_FIELDS.values()),
        "timezone": "auto",
    }

    response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    print("\n--- AIR QUALITY API REQUEST ---")
    print("Request URL:", response.url)
    print("Status Code:", response.status_code)
    response.raise_for_status()
    results = response.json()
    print("\n--- RAW AIR QUALITY API RESPONSE ---")
    print(json.dumps(results, indent=2))

    # A single coordinate can return an object; multiple coordinates return a list.
    if isinstance(results, dict):
        results = [results]

    rows = []
    for station, result in zip(stations, results):
        current = result.get("current", {})
        for pollutant, field in POLLUTANT_FIELDS.items():
            value = current.get(field)
            if value is not None:
                rows.append(
                    {
                        "station": station["station"],
                        "city": station["city"],
                        "lat": station["lat"],
                        "lon": station["lon"],
                        "pollutant": pollutant,
                        "aqi": round(value),
                    }
                )

    return pd.DataFrame(rows, columns=["station", "city", "lat", "lon", "pollutant", "aqi"])


# ---------------------------------------------------------------------------
# 2. AQI CATEGORY HELPER
# ---------------------------------------------------------------------------
def get_aqi_category(aqi_value):
    if pd.isna(aqi_value):
        return "Unavailable", "gray"
    if aqi_value <= 50:
        return "Good", "green"
    elif aqi_value <= 100:
        return "Moderate", "yellow"
    elif aqi_value <= 150:
        return "Unhealthy for Sensitive Groups", "orange"
    elif aqi_value <= 200:
        return "Unhealthy", "red"
    elif aqi_value <= 300:
        return "Very Unhealthy", "purple"
    return "Hazardous", "maroon"


# ---------------------------------------------------------------------------
# 3. FILTERING
# ---------------------------------------------------------------------------
def filter_data(df, city, pollutant):
    filtered = df[df["city"] == city]
    if pollutant != "All":
        filtered = filtered[filtered["pollutant"] == pollutant]
    return filtered


# ---------------------------------------------------------------------------
# 4. MAP RENDERING
# ---------------------------------------------------------------------------
def render_map(df, selected_station):
    if df.empty:
        st.info("No AQI values are available for the current selection.")
        return

    map_df = df.drop_duplicates(subset=["station"]).copy()
    map_df["is_selected"] = map_df["station"] == selected_station
    map_df["color"] = map_df["is_selected"].apply(
        lambda selected: [220, 30, 30, 220] if selected else [30, 120, 220, 140]
    )
    map_df["radius"] = map_df["is_selected"].apply(
        lambda selected: 9000 if selected else 4000
    )

    selected_rows = map_df.loc[map_df["is_selected"]]
    if selected_rows.empty:
        st.info("Select a location to display it on the map.")
        return
    selected_row = selected_rows.iloc[0]

    view_state = pdk.ViewState(
        latitude=selected_row["lat"],
        longitude=selected_row["lon"],
        zoom=10,
        pitch=0,
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=2,
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{station}"},
        )
    )


# ---------------------------------------------------------------------------
# 5. CURRENT POLLUTANT CARDS — current value + 24-hour change
# ---------------------------------------------------------------------------
AQI_CATEGORY_HEX = {
    "Good": "#16803c",
    "Moderate": "#a16207",
    "Unhealthy for Sensitive Groups": "#c2410c",
    "Unhealthy": "#dc2626",
    "Very Unhealthy": "#7e22ce",
    "Hazardous": "#7f1d1d",
    "Unavailable": "#6b7280",
}


def calculate_aqi_change(trend, current_aqi):
    """Compare the current API AQI value with the hourly value about 24h earlier.

    Returns (absolute_change, percentage_change). The percentage describes change
    in the AQI sub-index, not change in pollutant concentration.
    """
    if trend.empty or "aqi" not in trend.columns:
        return None, None

    current_time_text = trend.attrs.get("current_time")
    if not current_time_text:
        return None, None

    current_time = pd.to_datetime(current_time_text, errors="coerce")
    if pd.isna(current_time):
        return None, None

    series = trend["aqi"].dropna().sort_index()
    if series.empty:
        return None, None

    # API hourly timestamps and current.time use the same requested local timezone.
    before_day_ago = series.loc[
        series.index <= (current_time - pd.Timedelta(hours=24))
    ]

    if before_day_ago.empty or pd.isna(current_aqi):
        return None, None

    latest_value = float(current_aqi)
    previous_value = float(before_day_ago.iloc[-1])
    absolute_change = latest_value - previous_value

    if previous_value == 0:
        percentage_change = None
    else:
        percentage_change = (absolute_change / previous_value) * 100

    return absolute_change, percentage_change


def render_pollutant_cards(df, station, station_info):
    station_df = df[df["station"] == station].copy()

    st.subheader("Current pollutant-specific US AQI")
    st.caption(
        "Delta compares the latest hourly AQI sub-index with the value about "
        "24 hours earlier. A positive change means the AQI index increased "
        "(worsened); a negative change means it decreased (improved). "
        "This is not a percentage change in pollutant concentration."
    )

    values = {
        row["pollutant"]: row["aqi"]
        for _, row in station_df.iterrows()
    }

    pollutant_order = list(POLLUTANT_FIELDS.keys())
    cols = st.columns(len(pollutant_order))

    for col, pollutant in zip(cols, pollutant_order):
        with col:
            value = values.get(pollutant)
            category, _ = get_aqi_category(value) if value is not None else ("Unavailable", "gray")
            hex_color = AQI_CATEGORY_HEX.get(category, "#6b7280")

            if value is None or pd.isna(value):
                st.metric(f"{pollutant} AQI", "N/A")
                st.markdown(
                    f"<span style='color:{hex_color};font-weight:600'>"
                    f"Category: {category}</span>",
                    unsafe_allow_html=True,
                )
                continue

            # This function is cached and shared with the trend chart, so the
            # same hourly API response can supply both the chart and delta.
            trend = fetch_trend_data(
                station_info["lat"],
                station_info["lon"],
                pollutant,
            )
            absolute_change, percentage_change = calculate_aqi_change(trend, value)

            if percentage_change is None:
                delta_text = "24h change unavailable"
                delta_color = "off"
            else:
                delta_text = f"{percentage_change:+.1f}% vs 24h ago"
                # AQI rising is undesirable: positive = red, negative = green.
                delta_color = "inverse"

            st.metric(
                label=f"{pollutant} AQI",
                value=int(value),
                delta=delta_text,
                delta_color=delta_color,
                help=(
                    f"Approximate 24-hour change in this pollutant's AQI sub-index. "
                    f"Absolute change: {absolute_change:+.0f} AQI points."
                    if absolute_change is not None
                    else "A 24-hour comparison could not be calculated from available hourly data."
                ),
            )
            st.markdown(
                f"<span style='color:{hex_color};font-weight:600'>"
                f"Category: {category}</span>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# 6. TREND CHART
# ---------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_trend_data(lat, lon, pollutant):
    field = POLLUTANT_FIELDS.get(pollutant, "us_aqi_pm2_5")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": field,
        "hourly": field,
        "past_days": 5,
        "forecast_days": 2,
        "timezone": "auto",
    }

    response = requests.get(AIR_QUALITY_URL, params=params, timeout=10)
    response.raise_for_status()
    payload = response.json()
    hourly = payload.get("hourly", {})

    trend = pd.DataFrame(
        {
            "date": pd.to_datetime(hourly.get("time", [])),
            "aqi": hourly.get(field, []),
        }
    ).set_index("date")

    # Keep the API's current timestamp so 24-hour comparisons are based on
    # the location's requested timezone, not the machine running Streamlit.
    trend.attrs["current_time"] = payload.get("current", {}).get("time")
    return trend


def render_trend_chart(lat, lon, pollutant):
    trend = fetch_trend_data(lat, lon, pollutant)

    st.subheader(f"Hourly US AQI Trend — {pollutant}")
    st.caption(
        "Y-axis: pollutant-specific US AQI sub-index. "
        "X-axis: date and time in the location's time zone. "
        "The series includes historical data and forecast values."
    )

    if trend.empty or "aqi" not in trend.columns or trend["aqi"].dropna().empty:
        st.info(f"No trend data is available for {pollutant}.")
        return

    chart_data = trend.rename(columns={"aqi": f"{pollutant} AQI"})
    st.line_chart(
        chart_data,
        x_label="Date and time",
        y_label="US AQI",
        height=350,
    )


# ---------------------------------------------------------------------------
# 7. MAIN — search, select, add, and then use the chosen location in filters
# ---------------------------------------------------------------------------
def main():
    if "stations" not in st.session_state:
        st.session_state.stations = [station.copy() for station in DEFAULT_STATIONS]
    if "geocode_candidates" not in st.session_state:
        st.session_state.geocode_candidates = []
    if "geocode_search_version" not in st.session_state:
        st.session_state.geocode_search_version = 0

    st.sidebar.header("Add a city")
    new_city = st.sidebar.text_input(
        "Search city name",
        placeholder="e.g. Kanpur",
        key="city_search_input",
    )

    if st.sidebar.button("Search locations"):
        if new_city.strip():
            try:
                candidates = geocode_city(new_city.strip())
                st.session_state.geocode_candidates = candidates
                st.session_state.geocode_search_version += 1
                if not candidates:
                    st.sidebar.warning(f"No matching locations found for '{new_city}'.")
            except requests.RequestException as exc:
                st.session_state.geocode_candidates = []
                st.sidebar.error(f"Geocoding request failed: {exc}")
        else:
            st.sidebar.warning("Please enter a city name.")

    candidates = st.session_state.geocode_candidates
    if candidates:
        selected_index = st.sidebar.selectbox(
            "Choose the correct location",
            options=list(range(len(candidates))),
            format_func=lambda i: candidates[i]["station"],
            key=f"selected_geocode_index_{st.session_state.geocode_search_version}",
        )
        selected_location = candidates[selected_index]
        st.sidebar.caption(
            f"Coordinates: {selected_location['lat']:.5f}, "
            f"{selected_location['lon']:.5f}"
        )

        if st.sidebar.button("Add selected location"):
            already_exists = any(
                abs(float(existing["lat"]) - selected_location["lat"]) < 1e-5
                and abs(float(existing["lon"]) - selected_location["lon"]) < 1e-5
                for existing in st.session_state.stations
            )
            if already_exists:
                st.sidebar.warning("This location has already been added.")
            else:
                st.session_state.stations.append(selected_location.copy())
                st.session_state.geocode_candidates = []
                st.rerun()

    try:
        df = load_pollution_data(st.session_state.stations)
    except requests.RequestException as exc:
        st.error(f"Air-quality API request failed: {exc}")
        st.stop()

    st.title("Air Pollution Dashboard")
    st.caption(
        "Locations are geographic coordinates queried against Open-Meteo's "
        "air-quality model; they are not necessarily physical monitoring stations."
    )

    if df.empty:
        st.warning("No AQI data was returned for the locations currently added.")
        st.stop()

    # One location selector replaces the redundant City and Station selectors.
    location_options = [item["station"] for item in st.session_state.stations]
    station = st.sidebar.selectbox("Location", location_options)
    station_info = next(
        item for item in st.session_state.stations
        if item["station"] == station
    )

    st.subheader("Location map")
    st.caption(
        "Red marks the selected location; blue marks other added locations. "
        "Marker colors do not represent AQI severity."
    )
    render_map(df, station)

    # All current pollutant values remain visible regardless of the selected trend tab.
    render_pollutant_cards(df, station, station_info)

    # Tabs replace the pollutant dropdown and control only the trend chart.
    st.subheader("Pollutant trend")
    chart_tabs = st.tabs(list(POLLUTANT_FIELDS.keys()))
    for tab, pollutant in zip(chart_tabs, POLLUTANT_FIELDS.keys()):
        with tab:
            render_trend_chart(
                station_info["lat"],
                station_info["lon"],
                pollutant,
            )


if __name__ == "__main__":
    main()
