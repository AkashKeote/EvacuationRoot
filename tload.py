#!/usr/bin/env python3
"""
tload.py (lighter map version)

- Map all CSV regions to the GraphML (nearest-region assignment for every graph node)
- Color the road network by region flood risk level (sampled to avoid huge HTML)
- Show region name & risk level on hover for centroids only
- Ask user for location, compute 2 shortest evacuation routes to LOW risk regions
- Save single HTML: mumbai_evacuation_routes.html
"""
import os
import math
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import folium
from folium import GeoJson, PolyLine, CircleMarker

# -------------------------
# fuzzy matching (robust)
# -------------------------
try:
    from rapidfuzz import process as fuzzy_process
except Exception:
    try:
        from fuzzywuzzy import process as fuzzy_process
    except Exception:
        import difflib
        class _DLProcess:
            @staticmethod
            def extractOne(query, choices):
                qry = str(query)
                matches = difflib.get_close_matches(qry, choices, n=1, cutoff=0)
                if matches:
                    score = int(difflib.SequenceMatcher(None, qry, matches[0]).ratio() * 100)
                    return (matches[0], score)
                return (None, 0)
        fuzzy_process = _DLProcess()

# -------------------------
# helpers
# -------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    alias_map = {
        "ward": "areas", "area": "areas", "region": "areas",
        "neighbourhood": "areas", "neighborhood": "areas",
        "flood-risk_level": "flood_risk_level", "flood risk level": "flood_risk_level",
        "risk_level": "flood_risk_level", "risk": "flood_risk_level",
        "lat": "latitude", "y": "latitude", "lon": "longitude", "lng": "longitude", "x": "longitude"
    }
    for old, new in alias_map.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    required = ["areas", "latitude", "longitude", "flood_risk_level"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing} — found: {list(df.columns)}")
    df["areas"] = df["areas"].astype(str).str.strip().str.lower()
    df["flood_risk_level"] = df["flood_risk_level"].astype(str).str.strip().str.lower()
    return df

def extract_best_match(query: str, choices):
    res = fuzzy_process.extractOne(query, choices)
    if res is None:
        return None, 0
    if isinstance(res, (tuple, list)):
        if len(res) >= 2:
            return res[0], int(res[1])
        elif len(res) == 1:
            return res[0], 100
    return res, 100

def haversine_m(lon1, lat1, lon2, lat2):
    R = 6371000.0
    lon1 = np.radians(lon1); lat1 = np.radians(lat1)
    lon2 = np.radians(lon2); lat2 = np.radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def route_length_m(G: nx.MultiDiGraph, route):
    try:
        lengths = ox.utils_graph.get_route_edge_attributes(G, route, "length")
        return float(sum(lengths)) if lengths else 0.0
    except Exception:
        total = 0.0
        for u, v in zip(route[:-1], route[1:]):
            data = G.get_edge_data(u, v)
            if data:
                vals = list(data.values())
                best = min(vals, key=lambda d: d.get("length", float("inf")))
                total += float(best.get("length", 0.0))
        return total

# -------------------------
# load data
# -------------------------
print("🚀 Loading road network...")
try:
    G = ox.load_graphml("roads_all.graphml")
except FileNotFoundError:
    raise SystemExit("❌ 'roads_all.graphml' not found in current directory.")

print(f"✅ Loaded graph: {len(G.nodes)} nodes, {len(G.edges)} edges")

csv_path = "mumbai_ward_area_floodrisk.csv"
if not os.path.exists(csv_path):
    raise SystemExit(f"❌ CSV not found: {csv_path}")
flood_df_raw = pd.read_csv(csv_path)
flood_df = normalize_columns(flood_df_raw)

regions = flood_df["areas"].tolist()
region_lons = flood_df["longitude"].astype(float).to_numpy()
region_lats = flood_df["latitude"].astype(float).to_numpy()
region_risks = flood_df["flood_risk_level"].tolist()
print(f"✅ Loaded {len(regions)} regions from CSV")

# -------------------------
# assign graph nodes to nearest region
# -------------------------
node_ids = np.array(list(G.nodes))
node_lons = np.array([G.nodes[n].get("x", G.nodes[n].get("lon")) for n in node_ids], dtype=float)
node_lats = np.array([G.nodes[n].get("y", G.nodes[n].get("lat")) for n in node_ids], dtype=float)

distances_stack = np.empty((len(region_lons), len(node_ids)), dtype=float)
for i in range(len(region_lons)):
    distances_stack[i] = haversine_m(region_lons[i], region_lats[i], node_lons, node_lats)

nearest_region_idx_per_node = np.argmin(distances_stack, axis=0)
nodeid_to_region_idx = dict(zip(node_ids.tolist(), nearest_region_idx_per_node.tolist()))
nodeid_to_region_name = {nid: regions[idx] for nid, idx in nodeid_to_region_idx.items()}
nodeid_to_region_risk = {nid: region_risks[idx] for nid, idx in nodeid_to_region_idx.items()}

print("✅ Node → region assignment done.")

# -------------------------
# edges GeoDataFrame (lighter)
# -------------------------
edges_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True, fill_edge_geometry=True)
if "u" not in edges_gdf.columns or "v" not in edges_gdf.columns:
    edges_gdf = edges_gdf.reset_index()
edges_gdf["_u"] = edges_gdf["u"].astype(int)
edges_gdf["_v"] = edges_gdf["v"].astype(int)

edges_gdf["region_idx"] = edges_gdf["_u"].map(nodeid_to_region_idx)
edges_gdf["region_name"] = edges_gdf["region_idx"].apply(lambda i: regions[i] if i is not None else "unknown")
edges_gdf["risk_level"] = edges_gdf["region_idx"].apply(lambda i: region_risks[i] if i is not None else "unknown")

# sample edges for lighter visualization
edges_gdf = edges_gdf.iloc[::10]  # keep every 10th edge
print(f"✅ Edge tagging complete. Number of edges used for map: {len(edges_gdf)}")

# -------------------------
# Color mapping
# -------------------------
risk_color_map = {
    "high": "#d73027",
    "moderate": "#fc8d59",
    "low": "#1a9850",
    "unknown": "#aaaaaa"
}

def edge_style(feature):
    risk = feature["properties"].get("risk_level", "unknown")
    color = risk_color_map.get(risk.lower(), risk_color_map["unknown"])
    return {"color": color, "weight": 1.5, "opacity": 0.9}

# -------------------------
# Route finder
# -------------------------
def find_two_safest_routes_for_user(user_input_str):
    best_match, score = extract_best_match(user_input_str.lower().strip(), regions)
    if not best_match or score < 50:
        return None, score, []
    print(f"🔎 Matched '{user_input_str}' → '{best_match}' (score {score}%)")
    idx = regions.index(best_match)
    start_lon, start_lat = region_lons[idx], region_lats[idx]
    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    except Exception:
        start_node = ox.nearest_nodes(G, start_lon, start_lat)

    low_region_idxs = [i for i, r in enumerate(region_risks) if str(r).lower() == "low"]
    if not low_region_idxs:
        return best_match, score, []

    safe_nodes = [nid for nid, ridx in nodeid_to_region_idx.items() if ridx in low_region_idxs]
    if not safe_nodes:
        return best_match, score, []

    lengths = nx.single_source_dijkstra_path_length(G, start_node, weight="length")
    candidates = [(node, lengths[node]) for node in safe_nodes if node in lengths]
    if not candidates:
        return best_match, score, []
    candidates = sorted(candidates, key=lambda x: x[1])

    selected, seen = [], set()
    for node, dist_m in candidates:
        ridx = nodeid_to_region_idx.get(node)
        if ridx not in seen:
            selected.append((node, dist_m, ridx))
            seen.add(ridx)
        if len(selected) >= 2:
            break

    routes = []
    for node, dist_m, ridx in selected:
        path = nx.shortest_path(G, start_node, node, weight="length")
        length_m = route_length_m(G, path)
        eta_min = (length_m / 1000.0) / 25.0 * 60.0
        routes.append({
            "dest_region": regions[ridx],
            "dest_region_idx": ridx,
            "dest_node": node,
            "path": path,
            "distance_km": length_m / 1000.0,
            "eta_min": eta_min
        })
    return best_match, score, routes

# -------------------------
# Map saver (lighter)
# -------------------------
def save_map(start_region, routes, out_file="mumbai_evacuation_routes.html"):
    idx = regions.index(start_region)
    center = [float(region_lats[idx]), float(region_lons[idx])]
    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    GeoJson(
        data=edges_gdf.__geo_interface__,
        style_function=edge_style,
        name="Road network (sampled)"
    ).add_to(m)

    # centroids with tooltips
    for i, nm in enumerate(regions):
        folium.CircleMarker(
            location=[float(region_lats[i]), float(region_lons[i])],
            radius=5,
            fill=True,
            fill_opacity=0.9,
            color=risk_color_map.get(region_risks[i].lower(), "#888888"),
            tooltip=f"{nm.title()} — Risk: {region_risks[i].title()}",
        ).add_to(m)

    route_colors = ["#0066ff", "#00cc44"]
    for i, r in enumerate(routes):
        coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in r["path"]]
        PolyLine(
            coords,
            color=route_colors[i % len(route_colors)],
            weight=6,
            opacity=0.9,
            tooltip=f"Route {i+1}: {r['distance_km']:.2f} km, ETA {r['eta_min']:.0f} min → {r['dest_region'].title()}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    m.save(out_file)
    print(f"\n✅ Map saved to: {out_file}")

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    try:
        user_input = input("🏠 Enter your region name (area): ").strip()
    except EOFError:
        raise SystemExit("❌ No input provided.")

    if not user_input:
        raise SystemExit("❌ Empty input.")

    matched, score, routes = find_two_safest_routes_for_user(user_input)
    if not matched:
        print(f"❌ Could not match '{user_input}'. Try a different name.")
        raise SystemExit()
    if not routes:
        print("⚠️ No safe evacuation routes found.")
        raise SystemExit()

    print(f"\n✅ Using region: {matched.title()} (matched score {score}%)")
    for i, r in enumerate(routes, start=1):
        print(f"--- Route {i} ---")
        print(f"Destination region: {r['dest_region'].title()}")
        print(f"Distance: {r['distance_km']:.2f} km")
        print(f"ETA: {r['eta_min']:.0f} minutes")

    save_map(matched, routes)
