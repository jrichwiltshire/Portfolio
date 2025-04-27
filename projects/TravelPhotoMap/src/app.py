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
data = {
    "location_name": ["Austin, TX", "New York, NY", "San Francisco, CA"],
    "latitude": [30.2672, 40.7128, 37.7749],
    "longitude": [-97.7431, -74.0059, -122.4194],
    "photo_url": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Austin_Downtown_Skyline_at_Night.jpg/1280px-Austin_Downtown_Skyline_at_Night.jpg",  # Replace with your actual photo URLs
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b9/Manhattan_from_Jersey_City_-_cropped.jpg/1280px-Manhattan_from_Jersey_City_-_cropped.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/SanFranciscoBayBridgeNewSkyline.jpg/1280px-SanFranciscoBayBridgeNewSkyline.jpg",
    ],
}
df = pd.DataFrame(data)

# --- Main Application ---
st.title("Our Travel Photo Map")

# Create a folium map centered on the first location
m = folium.Map(location=[df["latitude"][0], df["longitude"][0]], zoom_start=10)

# Add markers for each location
for index, row in df.iterrows():
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=row["location_name"],  # Location name displays on hover
        tooltip=row["location_name"],
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)
