import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sqlite3
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# --- Page Configuration ---
st.set_page_config(
    page_title="Travel Photo Map",
    page_icon=":material/globe_location_pin:",
    layout="wide",
)

# --- Database Configuration ---
DATABASE_PATH = "data/travel_map.db"

# --- Geocoding Configuration ---
GEO_USER_AGENT = "TravelPhotoMap"
geolocator = Nominatim(user_agent=GEO_USER_AGENT, timeout=10)


# temporary code for testing
def execute_sql_command(sql):
    """Executes a SQL command on the database (for testing only)."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print(f"SQL command executed successfully: {sql}")
    except sqlite3.Error as e:
        print(f"Error executing SQL command: {e}")
    finally:
        conn.close()


def get_data_from_db():
    """Retrieves location and photo data from the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        df_locations = pd.read_sql_query("SELECT * FROM locations", conn)
        df_photos = pd.read_sql_query("SELECT * FROM photos", conn)

        # Merge the dataframes on location_id
        # df = pd.merge(df_locations, df_photos, left_on="id", right_on="location_id", how="left")
        return df_locations, df_photos
    except Exception as e:
        print(f"Error fetching data from database: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()


def is_valid_url(url):
    """Checks if a URL is valid."""
    regex = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return bool(re.match(regex, url))


def geocode_location(location_name):
    """Geocodes a location name to latitude and longitude."""
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
        else:
            st.error(f"Could not geocode location: {location_name}")
            return None, None
    except GeocoderTimedOut as e:
        st.error(f"Geocoding timed out for location: {location_name}")
        return None, None
    except GeocoderServiceError as e:
        st.error(f"Geocoding service error: {e}")
        return None, None
    except Exception as e:
        st.error(f"An unexpected error occurred during geocoding: {e}")
        return None, None


# --- Main Application ---
st.title("Our Travel Photo Map")

# Get data from the database
df_locations, df_photos = get_data_from_db()

# Insert initial data (TEMPORARY - FOR TESTING ONLY)
if df_locations.empty:
    # Example address to geocode
    austin_coords = geocode_location("Austin, Texas")
    if austin_coords:
        execute_sql_command(
            f"""
            INSERT INTO locations (location_name, latitude, longitude)
            VALUES ('Austin', {austin_coords[0]}, {austin_coords[1]})
            """
        )
    else:
        execute_sql_command(
            """
            INSERT INTO locations (location_name, latitude, longitude)
            VALUES ('Austin', 30.2672, -97.7431)
            """
        )
        execute_sql_command(
            """
            INSERT INTO locations (location_name, latitude, longitude)
            VALUES ('Austin', 30.2672, -97.7431),
                ('New York', 40.7128, -74.0060),
                ('San Francisco', 37.7749, -122.4194)
            """
        )
    execute_sql_command(
        """
        INSERT INTO photos (location_id, photo_url)
        VALUES (1, 'https://content.r9cdn.net/rimg/dimg/15/27/c7e81fad-city-22863-177642838c4.jpg?width=1366&height=768&xhint=3008&yhint=1481&crop=true'),
               (2, 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzUqME3_q2Nh5I-PMBL7vMA8paL61l4XS-8Q&s'),
               (3, 'https://media.istockphoto.com/id/1136437406/photo/san-francisco-skyline-with-oakland-bay-bridge-at-sunset-california-usa.jpg?s=612x612&w=0&k=20&c=JVBBZT2uquZbfY0njYHv8vkLfatoM4COJc-lX5QKYpE=')"""
    )
    df_locations, df_photos = get_data_from_db()

# Check if data is available
if df_locations.empty:
    st.warning("No location data found in the database. Please add locations.")
else:
    # Validate data before displaying
    valid_locations = []
    for index, row in df_locations.iterrows():
        if -90 <= row["latitude"] <= 90 and -180 <= row["longitude"] <= 180:
            valid_locations.append(row)
        else:
            st.error(
                f"Invalid coordinates for location: {row['location_name']}. Skipping this location."
            )

    valid_photos = []
    for index, row in df_photos.iterrows():
        if is_valid_url(row["photo_url"]):
            valid_photos.append(row)
        else:
            st.error(f"Invalid URL: {row['photo_url']}. Skipping this photo.")

    df_locations = pd.DataFrame(valid_locations)
    df_photos = pd.DataFrame(valid_photos)

    if not df_locations.empty:
        # Create a folium map centered on the first location
        m = folium.Map(
            location=[
                df_locations["latitude"].iloc[0],
                df_locations["longitude"].iloc[0],
            ],
            zoom_start=4,
        )

        # Add markers for each location
        for index, row in df_locations.iterrows():
            # Find the photo URL
            photo_url = (
                df_photos[df_photos["location_id"] == row["id"]]["photo_url"].iloc[0]
                if not df_photos.empty
                and not df_photos[df_photos["location_id"] == row["id"]].empty
                else ""
            )

            # Create the popup HTML with the location name and photo
            popup_html = f"""
            <h3>{row["location_name"]}</h3>
            <img src={photo_url} alt="{row["location_name"]}" style="width:200px;height:auto;">
            """
            popup = folium.Popup(popup_html, max_width=300)

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=8,
                color="blue",
                fill=True,
                fill_color="blue",
                popup=popup,
                tooltip=row["location_name"],
            ).add_to(m)

        # Display the map in Streamlit
        st_folium(m, width=700, height=500)
    else:
        st.warning(
            "No valid locations found in the database. Please add valid locations."
        )
