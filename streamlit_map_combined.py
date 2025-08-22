import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MiniMap
import pandas as pd
import networkx as nx
import osmnx as ox

st.set_page_config(page_title="Mumbai Evacuation Map", layout="wide")
st.title("🚨 Unified Mumbai Flood Evacuation Map")

# Load data
G = ox.load_graphml("roads_all.graphml")
flood_df = pd.read_csv("mumbai_ward_area_floodrisk.csv")

risk_colors = {"low": "green", "moderate": "orange", "high": "red"}
route_colors = ["blue", "purple"]
center = [flood_df["Latitude"].mean(), flood_df["Longitude"].mean()]
m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

# MiniMap
minimap = MiniMap(tile_layer="OpenStreetMap", position="bottomright", width=150, height=150, zoom_level_offset=-5)
minimap.add_to(m)

road_group = folium.FeatureGroup(name="Road Network", show=True)
safe_group = folium.FeatureGroup(name="Safe Regions (Low Risk)", show=True)
unsafe_group = folium.FeatureGroup(name="Unsafe/Moderate/High Regions", show=True)
evac_group = folium.FeatureGroup(name="Evacuation Routes", show=True)

edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True, fill_edge_geometry=True)
for _, row in edges_gdf.iloc[::10].iterrows():
    color = risk_colors.get(str(row.get("risk_level", "moderate")).lower(), "gray")
    geom = row["geometry"]
    folium.PolyLine(
        [(lat, lon) for lon, lat in geom.coords],
        color=color,
        weight=2,
        opacity=0.7
    ).add_to(road_group)

for _, region in flood_df.iterrows():
    color = risk_colors.get(str(region["Flood-risk_level"]).lower(), "gray")
    marker = folium.CircleMarker(
        location=[region["Latitude"], region["Longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        tooltip=f"{region['Areas'].title()} — Risk: {region['Flood-risk_level'].title()}"
    )
    if region["Flood-risk_level"].lower() == "low":
        marker.add_to(safe_group)
    else:
        marker.add_to(unsafe_group)

# Dummy evacuation routes (replace with your route logic)
evac_routes = [
    [(19.0760, 72.8777), (19.1, 72.85)],
    [(19.0760, 72.8777), (19.12, 72.88)]
]
for i, route in enumerate(evac_routes):
    folium.PolyLine(
        route,
        color=route_colors[i % len(route_colors)],
        weight=5,
        opacity=0.9,
        tooltip=f"{'Nearest' if i==0 else '2nd nearest'} route"
    ).add_to(evac_group)

road_group.add_to(m)
safe_group.add_to(m)
unsafe_group.add_to(m)
evac_group.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

legend_html = '''
 <div style="position: fixed; bottom: 40px; left: 40px; z-index:9999; background: white; padding: 10px; border-radius: 8px; border: 2px solid #333; font-size: 14px;">
 <b>Legend</b><br>
 <span style="color:green; font-weight:bold;">●</span> Safe (Low)<br>
 <span style="color:orange; font-weight:bold;">●</span> Moderate<br>
 <span style="color:red; font-weight:bold;">●</span> High<br>
 <span style="color:blue; font-weight:bold;">━</span> Nearest route<br>
 <span style="color:purple; font-weight:bold;">━</span> 2nd nearest route<br>
 </div>
 '''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1100, height=700)
