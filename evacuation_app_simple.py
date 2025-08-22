import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process
import math

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="Mumbai Flood Evacuation Routing System", layout="wide")
st.title("🌊 Mumbai Flood Evacuation Routing System (Simplified)")

# -------------------------------
# Load data
# -------------------------------
@st.cache_data
def load_flood_data():
    # Load flood-prone regions CSV
    try:
        flood_df = pd.read_csv("mumbai_ward_area_floodrisk.csv")
    except:
        # Create sample data if file not found
        sample_data = {
            'Ward Code': ['Ward A', 'Ward B', 'Ward C', 'A', 'B', 'C'],
            'Areas': ['colaba causeway', 'fort', 'marine lines', 'ballard estate', 'dongri circle', 'cst'],
            'Latitude': [18.9151, 19.0509, 18.9458, 18.9496, 18.9594, 18.9472],
            'Longitude': [72.8141, 72.7615, 72.8238, 72.8414, 72.8376, 72.8272],
            'Flood-risk_level': ['Moderate', 'Low', 'Moderate', 'Moderate', 'Moderate', 'Moderate']
        }
        flood_df = pd.DataFrame(sample_data)
    
    # Normalize area names
    flood_df["Areas"] = flood_df["Areas"].str.strip().str.lower()
    return flood_df

flood_df = load_flood_data()

# -------------------------------
# Simple route calculation
# -------------------------------
def calculate_simple_routes(user_area, flood_df):
    # Fuzzy match region
    all_areas = list(flood_df["Areas"].unique())
    best_match, score = process.extractOne(user_area.lower(), all_areas)
    
    if score < 60:
        return None, None, []  # too poor match

    # Get starting point
    start = flood_df[flood_df["Areas"] == best_match].iloc[0]
    start_lat, start_lon = start["Latitude"], start["Longitude"]

    # Find safe areas (low risk)
    safe_areas = flood_df[flood_df["Flood-risk_level"].str.lower().isin(["low", "minimal", "safe"])]
    
    if safe_areas.empty:
        return best_match, score, []

    # Calculate simple distances and create routes
    routes = []
    for _, safe_area in safe_areas.head(3).iterrows():  # Top 3 safe areas
        # Simple Euclidean distance calculation
        lat_diff = safe_area["Latitude"] - start_lat
        lon_diff = safe_area["Longitude"] - start_lon
        distance_km = math.sqrt(lat_diff**2 + lon_diff**2) * 111  # Rough km conversion
        
        # Estimate travel time (assuming 25 km/h average speed)
        eta_min = (distance_km / 25) * 60
        
        routes.append({
            "destination": safe_area["Areas"].title(),
            "destination_lat": safe_area["Latitude"],
            "destination_lon": safe_area["Longitude"],
            "distance_km": distance_km,
            "eta_min": eta_min,
            "risk_level": safe_area["Flood-risk_level"]
        })
    
    # Sort by distance
    routes = sorted(routes, key=lambda x: x["distance_km"])
    return best_match, score, routes[:2]

# -------------------------------
# Streamlit UI with Session State
# -------------------------------

# Initialize session state
if 'routes_computed' not in st.session_state:
    st.session_state.routes_computed = False
if 'best_match' not in st.session_state:
    st.session_state.best_match = None
if 'match_score' not in st.session_state:
    st.session_state.match_score = None
if 'routes' not in st.session_state:
    st.session_state.routes = None
if 'user_region_input' not in st.session_state:
    st.session_state.user_region_input = ""

# Display available areas
with st.expander("📍 Available Areas in Dataset"):
    areas_list = sorted(flood_df["Areas"].str.title().unique())
    st.write(", ".join(areas_list))

user_region = st.text_input("Enter your region name (area):", value=st.session_state.user_region_input)

if st.button("🔍 Find Evacuation Routes"):
    if not user_region.strip():
        st.error("⚠️ Please enter a region name.")
        st.session_state.routes_computed = False
    else:
        st.session_state.user_region_input = user_region
        with st.spinner("Finding safe evacuation routes..."):
            best_match, score, routes = calculate_simple_routes(user_region, flood_df)
            
            st.session_state.best_match = best_match
            st.session_state.match_score = score
            st.session_state.routes = routes
            st.session_state.routes_computed = True

# Display results
if st.session_state.routes_computed:
    best_match = st.session_state.best_match
    score = st.session_state.match_score
    routes = st.session_state.routes
    
    if best_match is None:
        st.error(f"❌ Region '{st.session_state.user_region_input}' not recognized in the dataset.")
    elif not routes:
        st.error("⚠️ No safe evacuation routes found.")
    else:
        st.success(f"✅ Starting from: **{best_match.title()}** (matched {score}%)")
        
        # Create map
        start = flood_df[flood_df["Areas"] == best_match].iloc[0]
        m = folium.Map(location=[start["Latitude"], start["Longitude"]], zoom_start=13)
        
        # Add starting point
        folium.Marker(
            [start["Latitude"], start["Longitude"]],
            popup=f"Start: {best_match.title()}",
            icon=folium.Icon(color='red', icon='play')
        ).add_to(m)
        
        # Display routes and add to map
        colors = ['blue', 'green']
        for i, route in enumerate(routes):
            # Route details
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"### 🚦 Route {i+1}: To {route['destination']}")
                st.write(f"**Distance:** {route['distance_km']:.2f} km")
                st.write(f"**ETA:** {route['eta_min']:.1f} minutes")
                st.write(f"**Safety Level:** {route['risk_level']}")
            
            # Add destination marker
            folium.Marker(
                [route["destination_lat"], route["destination_lon"]],
                popup=f"Safe Zone {i+1}: {route['destination']}",
                icon=folium.Icon(color=colors[i], icon='stop')
            ).add_to(m)
            
            # Add simple line between start and destination
            folium.PolyLine(
                [[start["Latitude"], start["Longitude"]], 
                 [route["destination_lat"], route["destination_lon"]]],
                color=colors[i],
                weight=4,
                opacity=0.8,
                popup=f"Route {i+1}: {route['distance_km']:.1f}km, {route['eta_min']:.1f}min"
            ).add_to(m)
        
        # Display map
        st.write("### 🗺️ Evacuation Routes Map")
        st_folium(m, width=1000, height=500)
        
        # Clear button
        if st.button("🔄 Clear Results"):
            st.session_state.routes_computed = False
            st.session_state.best_match = None
            st.session_state.match_score = None
            st.session_state.routes = None
            st.session_state.user_region_input = ""
            st.rerun()

# Footer
st.markdown("---")
st.markdown("🌊 **Mumbai Flood Evacuation System** - Find the safest routes during flood emergencies")
