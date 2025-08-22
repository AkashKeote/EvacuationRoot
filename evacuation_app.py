import os
import networkx as nx
import osmnx as ox
import pandas as pd
import geopandas as gpd
import folium
from fuzzywuzzy import process
import streamlit as st
from streamlit_folium import st_folium

# Set cache directory to a writable location
ox.settings.cache_folder = os.path.expanduser("~/osmnx_cache")

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="Mumbai Flood Evacuation Routing System", layout="wide")
st.title("🌊 Mumbai Flood Evacuation Routing System")

# -------------------------------
# Load data
# -------------------------------
@st.cache_resource
def load_data():
    # Load Mumbai road network
    G = ox.graph_from_place("Mumbai, India", network_type="drive")
    G = ox.project_graph(G)

    # Keep only the largest strongly connected component
    try:
        G = ox.truncate.largest_component(G, strongly=True)
    except:
        # Fallback to simpler approach if the above doesn't work
        largest_cc = max(nx.strongly_connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()

    # Load flood-prone regions CSV (replace with your CSV file path)
    flood_csv = r"c:\Users\AkashK\Documents\New_folder[1]\New folder\mumbai_ward_area_floodrisk.csv"
    flood_df = pd.read_csv(flood_csv)

    # Normalize area names
    flood_df["Areas"] = flood_df["Areas"].str.strip().str.lower()

    return G, flood_df

G, flood_df = load_data()

# -------------------------------
# Risk assignment
# -------------------------------
def assign_risk_to_edges(G, flood_df):
    # Default: no risk
    for u, v, k, data in G.edges(keys=True, data=True):
        data["risk"] = 0
    return G

G = assign_risk_to_edges(G, flood_df)

# -------------------------------
# Get two safest routes
# -------------------------------
def get_two_safest_routes(user_area, G, flood_df):
    # Fuzzy match region
    all_areas = list(flood_df["Areas"].unique())
    best_match, score = process.extractOne(user_area.lower(), all_areas)
    if score < 60:
        return None, None, None  # too poor match

    # Pick centroid of best match as start point
    start = flood_df[flood_df["Areas"] == best_match].iloc[0]
    start_lat, start_lon = start["Latitude"], start["Longitude"]

    orig_node = ox.distance.nearest_nodes(G, start_lon, start_lat)

    # Define "safe" as low flood-risk areas
    safe_df = flood_df[flood_df["Flood-risk_level"].str.lower().isin(["low", "minimal", "safe"])]
    safe_nodes = [
        ox.distance.nearest_nodes(G, row["Longitude"], row["Latitude"])
        for _, row in safe_df.iterrows()
    ]
    if not safe_nodes:
        return best_match, score, []

    # Compute shortest path by distance + risk
    routes = []
    for dest_node in safe_nodes[:5]:  # limit to first 5 candidates
        try:
            path = nx.shortest_path(G, orig_node, dest_node, weight="length")
            length = sum([G[u][v][0].get("length", 0) for u, v in zip(path[:-1], path[1:])])
            risk = sum([G[u][v][0].get("risk", 0) for u, v in zip(path[:-1], path[1:])])
            eta = (length / 1000) / 30 * 60  # ETA assuming 30 km/h
            road_names = [
                d.get("name", "Unnamed Road")
                for u, v, k, d in G.edges(keys=True, data=True)
                if u in path and v in path
            ]
            routes.append({
                "path": path,
                "distance_km": length / 1000,
                "eta_min": eta,
                "risk": risk,
                "roads": list(set(road_names)),
            })
        except Exception:
            continue

    # Sort by risk first, then by distance
    routes = sorted(routes, key=lambda x: (x["risk"], x["distance_km"]))

    return best_match, score, routes[:2]

# -------------------------------
# Streamlit UI
# -------------------------------

# Initialize session state for storing results
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

user_region = st.text_input("Enter your region name (area):", value=st.session_state.user_region_input)

if st.button("Compute Evacuation Routes"):
    if not user_region.strip():
        st.error("⚠️ Please enter a region name.")
        st.session_state.routes_computed = False
    else:
        # Store the input and compute routes
        st.session_state.user_region_input = user_region
        with st.spinner("Computing evacuation routes... This may take a few moments."):
            best_match, score, routes = get_two_safest_routes(user_region, G, flood_df)
            
            # Store results in session state
            st.session_state.best_match = best_match
            st.session_state.match_score = score
            st.session_state.routes = routes
            st.session_state.routes_computed = True

# Display results if they exist in session state
if st.session_state.routes_computed:
    best_match = st.session_state.best_match
    score = st.session_state.match_score
    routes = st.session_state.routes
    
    if best_match is None:
        st.error(f"❌ Region '{st.session_state.user_region_input}' not recognized in the dataset.")
    elif not routes:
        st.error("⚠️ No safe evacuation routes found.")
    else:
        st.success(f"✅ Using region: **{best_match.title()}** (matched {score}%)")

        # Show route details
        for i, r in enumerate(routes, 1):
            st.write(f"### 🚦 Route {i}")
            st.write(f"**Distance:** {r['distance_km']:.2f} km")
            st.write(f"**ETA:** {r['eta_min']:.1f} minutes")
            st.write(f"**Roads:** {', '.join(r['roads'][:10])} ...")

        # Plot routes on folium map
        m = folium.Map(location=[19.076, 72.877], zoom_start=12)
        colors = ["blue", "green"]
        for i, r in enumerate(routes):
            nodes = r["path"]
            coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in nodes]
            folium.PolyLine(coords, color=colors[i], weight=5, opacity=0.8,
                            tooltip=f"Route {i+1}: {r['distance_km']:.2f} km, {r['eta_min']:.1f} min").add_to(m)

        st_folium(m, width=1000, height=600)
        
        # Add a clear button to reset results
        if st.button("🔄 Clear Results"):
            st.session_state.routes_computed = False
            st.session_state.best_match = None
            st.session_state.match_score = None
            st.session_state.routes = None
            st.session_state.user_region_input = ""
            st.rerun()
