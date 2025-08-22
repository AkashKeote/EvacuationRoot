import os
import math
import pandas as pd
import networkx as nx
import folium
import osmnx as ox
from folium.plugins import MiniMap

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
FLOOD_CSV   = "mumbai_ward_area_floodrisk.csv"  
GRAPH_FILE  = "roads_all.graphml"                
OUTPUT_HTML = "mumbai_evacuation_map.html"
CITY_CENTER = (19.0760, 72.8777)
CITY_ZOOM   = 11
EVAC_SPEED_KMPH = 30  

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def safe_lower(x: str) -> str:
    try:
        return x.strip().lower()
    except Exception:
        return ""

def nearest_node(G, lat, lon):
    # osmnx >= 1.2: nearest_nodes(G, X, Y) where X=lon, Y=lat
    return ox.distance.nearest_nodes(G, lon, lat)

def route_length_m_multidigraph(G: nx.MultiDiGraph, route) -> float:
    """
    Robustly compute the total 'length' (meters) of a route for MultiDiGraphs, choosing
    the shortest parallel edge between consecutive nodes where multiple edges exist.
    """
    total = 0.0
    for u, v in zip(route[:-1], route[1:]):
        data = G.get_edge_data(u, v)
        if not data:
            # Try reverse (in case of directed graph and route was reversed)
            data = G.get_edge_data(v, u)
        if not data:
            # No edge data—treat as break
            return math.inf
        # pick the smallest length among parallel edges
        best = math.inf
        for k, attrs in data.items():
            length = attrs.get("length", math.inf)
            if length < best:
                best = length
        total += best
    return total

def compute_route_info(G, orig_node, dest_node, speed_kmph=EVAC_SPEED_KMPH):
    """
    Compute shortest route between two nodes; return (route, distance_km, eta_minutes).
    Uses 'length' edge weight in meters.
    """
    try:
        route = nx.shortest_path(G, orig_node, dest_node, weight="length")
    except nx.NetworkXNoPath:
        return None, float("inf"), float("inf")
    except nx.NodeNotFound:
        return None, float("inf"), float("inf")

    # Sum edge lengths robustly for MultiDiGraph
    dist_m = route_length_m_multidigraph(G, route)
    if not math.isfinite(dist_m):
        return None, float("inf"), float("inf")

    dist_km = dist_m / 1000.0
    eta_min = (dist_km / max(speed_kmph, 1e-6)) * 60.0
    return route, dist_km, eta_min

def style_for_risk(level_lower: str):
    if level_lower == "low":
        return dict(color="green", fill=True, fill_opacity=0.7)
    if level_lower == "moderate":
        return dict(color="orange", fill=True, fill_opacity=0.7)
    if level_lower == "high":
        return dict(color="red", fill=True, fill_opacity=0.7)
    return dict(color="gray", fill=True, fill_opacity=0.7)

# -------------------------------------------------
# MAIN
# -------------------------------------------------
print("Loading flood CSV...")
flood_df = pd.read_csv(FLOOD_CSV)


rename_map = {}
for col in flood_df.columns:
    cl = col.strip().lower()
    if cl in ("ward code", "ward_code"):
        rename_map[col] = "Ward Code"
    elif cl in ("areas", "area", "location"):
        rename_map[col] = "Areas"
    elif cl in ("latitude", "lat"):
        rename_map[col] = "Latitude"
    elif cl in ("longitude", "lon", "lng"):
        rename_map[col] = "Longitude"
    elif cl in ("flood-risk_level", "flood_risk_level", "risk", "flood risk level"):
        rename_map[col] = "Flood-risk_level"
if rename_map:
    flood_df = flood_df.rename(columns=rename_map)

required_cols = ["Ward Code", "Areas", "Latitude", "Longitude", "Flood-risk_level"]
missing = [c for c in required_cols if c not in flood_df.columns]
if missing:
    raise ValueError(f"CSV is missing required columns: {missing}")

print("Loading road graph:", GRAPH_FILE)
G: nx.MultiDiGraph = ox.load_graphml(GRAPH_FILE)


if not nx.get_edge_attributes(G, "length"):
    print("WARNING: Graph edges missing 'length'—attempting to add via great-circle estimate.")

    G = ox.add_edge_lengths(G)

print("Mapping regions to nearest nodes...")
flood_df["nearest_node"] = flood_df.apply(
    lambda row: nearest_node(G, float(row["Latitude"]), float(row["Longitude"])),
    axis=1
)

flood_df["risk_l"] = flood_df["Flood-risk_level"].apply(safe_lower)
safe_df   = flood_df[flood_df["risk_l"] == "low"].copy()
unsafe_df = flood_df[flood_df["risk_l"] != "low"].copy()


print("Building evacuation map...")
m = folium.Map(location=CITY_CENTER, zoom_start=CITY_ZOOM, tiles="cartodbpositron", control_scale=True)

# Base layers / feature groups
fg_roads   = folium.FeatureGroup(name="Road Network", show=True)
fg_safe    = folium.FeatureGroup(name="Safe Regions (Low Risk)", show=True)
fg_unsafe  = folium.FeatureGroup(name="Unsafe/Moderate/High Regions", show=True)
fg_routes  = folium.FeatureGroup(name="Evacuation Routes", show=True)

# Add road network lightly (edges only)
try:
    _, edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True, fill_edge_geometry=True)
    folium.GeoJson(
        edges_gdf.to_json(),
        name="Roads",
        style_function=lambda _feat: {"weight": 1, "opacity": 0.3, "color": "#666"},
        highlight_function=lambda _feat: {"weight": 2, "opacity": 0.6},
        tooltip=None,
        overlay=True,
        control=False,
    ).add_to(fg_roads)
except Exception as e:
    print("Note: could not render road network layer:", e)

# Add all regions as hoverable circles
for _, row in flood_df.iterrows():
    st = style_for_risk(row["risk_l"])
    tooltip = f"{row['Areas']} ({row['Flood-risk_level']})"
    popup_html = (
        f"<b>{row['Areas']}</b><br>"
        f"Ward: {row['Ward Code']}<br>"
        f"Risk: <b>{row['Flood-risk_level']}</b><br>"
        f"Lat/Lon: {row['Latitude']:.5f}, {row['Longitude']:.5f}"
    )
    marker = folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=6,
        color=st["color"],
        fill=st["fill"],
        fill_opacity=st["fill_opacity"],
        tooltip=tooltip,
        popup=folium.Popup(popup_html, max_width=300),
    )
    if row["risk_l"] == "low":
        marker.add_to(fg_safe)
    else:
        marker.add_to(fg_unsafe)

# Compute and draw 2 safest (nearest) evacuation routes for each unsafe region
print("Computing evacuation routes...")
if safe_df.empty:
    print("WARNING: No low-risk (safe) regions found. No routes will be drawn.")
else:
    # Pre-collect safe nodes to speed up lookups
    safe_nodes = safe_df["nearest_node"].tolist()

    # Two contrasting colors for the two nearest destinations from each origin
    route_colors = ["#1f77b4", "#9467bd"]  # blue, purple

    for _, urow in unsafe_df.iterrows():
        orig_node = urow["nearest_node"]

        # Compute shortest-path distance (meters) from this origin to each safe node
        dists = []
        for sn in safe_nodes:
            if nx.has_path(G, orig_node, sn):
                try:
                    d = nx.shortest_path_length(G, orig_node, sn, weight="length")
                except Exception:
                    d = math.inf
            else:
                d = math.inf
            dists.append(d)

        # pick indices of the 2 nearest safe regions
        nearest_pairs = sorted(
            [(i, d) for i, d in enumerate(dists) if math.isfinite(d)],
            key=lambda x: x[1]
        )[:2]

        for idx, (safe_idx, _dist_m) in enumerate(nearest_pairs):
            srow = safe_df.iloc[safe_idx]
            dest_node = srow["nearest_node"]

            route, dist_km, eta_min = compute_route_info(G, orig_node, dest_node)
            if route is None or not math.isfinite(dist_km):
                continue

            # Convert route nodes to lat/lon for plotting
            route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]

            folium.PolyLine(
                locations=route_coords,
                color=route_colors[idx % len(route_colors)],
                weight=5 if idx == 0 else 4,
                opacity=0.8 if idx == 0 else 0.6,
                tooltip=(
                    f"Evacuation route: <b>{urow['Areas']}</b> → <b>{srow['Areas']}</b> "
                    f"({dist_km:.2f} km, {eta_min:.1f} min)"
                ),
                popup=folium.Popup(
                    f"<b>From:</b> {urow['Areas']}<br>"
                    f"<b>To:</b> {srow['Areas']} (Low Risk)<br>"
                    f"<b>Distance:</b> {dist_km:.2f} km<br>"
                    f"<b>ETA:</b> {eta_min:.1f} minutes",
                    max_width=320,
                ),
            ).add_to(fg_routes)

# Add extras: minimap, legend, layers
MiniMap(zoom_level_offset=-2, toggle_display=True).add_to(m)

legend_html = """
<div style="
    position: fixed; bottom: 20px; left: 20px; z-index: 9999;
    background: white; padding: 10px 12px; border: 1px solid #ccc;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15); border-radius: 8px; font-size: 13px;">
  <div style="font-weight:600; margin-bottom:6px;">Legend</div>
  <div><span style="display:inline-block;width:10px;height:10px;background:#2ca02c;border-radius:50%;margin-right:6px;"></span>Safe (Low)</div>
  <div><span style="display:inline-block;width:10px;height:10px;background:#ff7f0e;border-radius:50%;margin-right:6px;"></span>Moderate</div>
  <div><span style="display:inline-block;width:10px;height:10px;background:#d62728;border-radius:50%;margin-right:6px;"></span>High</div>
  <div style="margin-top:6px;">
    <span style="display:inline-block;width:18px;height:3px;background:#1f77b4;margin-right:6px;"></span>Nearest route
  </div>
  <div>
    <span style="display:inline-block;width:18px;height:3px;background:#9467bd;margin-right:6px;"></span>2nd nearest route
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

fg_roads.add_to(m)
fg_safe.add_to(m)
fg_unsafe.add_to(m)
fg_routes.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# Save HTML
m.save(OUTPUT_HTML)
print(f"Evacuation map saved to {OUTPUT_HTML}")
