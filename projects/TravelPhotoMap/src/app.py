import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- Page Configuration ---
st.set_page_config(
    page_title="Travel Photo Map",
    page_icon=":material/globe_location_pin:",
    layout="wide",
)

# --- Load Data ---
DATA_URL = "data/locations.csv"
df = pd.read_csv(DATA_URL)

# --- Main Application ---
st.title("Our Travel Photo Map")

# Create a folium map centered on the first location
m = folium.Map(location=[df["latitude"][0], df["longitude"][0]], zoom_start=4)

# Add markers for each location
for index, row in df.iterrows():
    # Create the popup HTML with the location name and photo
    popup_html = f"""
    <h3>{row["location_name"]}</h3>
    <img src={row["photo_url"]} alt="{row["location_name"]}" style="width:200px;height:auto;">
    """
    popup = folium.Popup(popup_html, max_width=300)

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=popup,  # Location name displays on hover
        tooltip=row["location_name"],
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)
