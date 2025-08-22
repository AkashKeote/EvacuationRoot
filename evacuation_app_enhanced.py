#!/usr/bin/env python3

"""
Enhanced Mumbai Flood Evacuation Route System
- Robust region mapping and fuzzy matching
- Rich, interactive map: colored roads, region markers, popups, legend, measurement/fullscreen tools
- Clear user prompts and route summaries
"""
import os
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import folium
from folium import plugins, GeoJson, PolyLine, CircleMarker
from scipy.spatial import cKDTree
from collections import defaultdict

# Fuzzy matching with fallbacks
try:
    from rapidfuzz import process as fuzzy_process
except ImportError:
    try:
        from fuzzywuzzy import process as fuzzy_process
    except ImportError:
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

# Color mapping for risk levels
FLOOD_RISK_COLORS = {
    'low': '#1a9850',      # Green
    'moderate': '#fc8d59', # Orange
    'high': '#d73027',     # Red
    'severe': '#DC143C',   # Crimson
    'extreme': '#8B008B',  # Magenta
    'unknown': '#aaaaaa'   # Grey
}
ROUTE_COLORS = ['#0066FF', '#00CC66']

# Normalize CSV columns
def normalize_csv_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')
    column_mapping = {
        'ward': 'areas', 'area': 'areas', 'region': 'areas', 'ward_name': 'areas',
        'lat': 'latitude', 'y': 'latitude', 'lon': 'longitude', 'lng': 'longitude', 'x': 'longitude',
        'flood_risk_level': 'flood_risk_level', 'risk_level': 'flood_risk_level', 'risk': 'flood_risk_level'
    }
    for old, new in column_mapping.items():
        if old in df.columns and new not in df.columns:
            df.rename(columns={old: new}, inplace=True)
    required = ['areas', 'latitude', 'longitude', 'flood_risk_level']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {list(df.columns)}")
    df['areas'] = df['areas'].astype(str).str.strip().str.title()
    df['flood_risk_level'] = df['flood_risk_level'].astype(str).str.strip().str.lower()
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

# Map regions to road network using KDTree
def map_regions_to_road_network(G, flood_df, region_radius_km=2.0):
    region_coords = np.array([[row['latitude'], row['longitude']] for _, row in flood_df.iterrows()])
    region_data = flood_df[['areas', 'flood_risk_level', 'latitude', 'longitude']].to_dict('records')
    tree = cKDTree(region_coords)
    node_to_region = {}
    edge_to_region = {}
    for node_id, node_data in G.nodes(data=True):
        node_coord = [node_data.get('y', node_data.get('lat')), node_data.get('x', node_data.get('lon'))]
        distance_deg, region_idx = tree.query(node_coord)
        distance_km = distance_deg * 111.0
        if distance_km <= region_radius_km:
            region_info = region_data[region_idx]
            node_to_region[node_id] = region_info
            G.nodes[node_id]['region_name'] = region_info['areas']
            G.nodes[node_id]['flood_risk'] = region_info['flood_risk_level']
    for u, v, key in G.edges(keys=True):
        u_region = node_to_region.get(u)
        v_region = node_to_region.get(v)
        if u_region and v_region:
            # Use higher risk region
            risk_priority = {'low': 0, 'moderate': 1, 'high': 2, 'severe': 3, 'extreme': 4}
            u_risk = risk_priority.get(u_region['flood_risk_level'], 5)
            v_risk = risk_priority.get(v_region['flood_risk_level'], 5)
            edge_to_region[(u, v, key)] = u_region if u_risk >= v_risk else v_region
        elif u_region:
            edge_to_region[(u, v, key)] = u_region
        elif v_region:
            edge_to_region[(u, v, key)] = v_region
    return node_to_region, edge_to_region

# Route length calculation
def calculate_route_distance(G, route):
    try:
        edge_lengths = ox.utils_graph.get_route_edge_attributes(G, route, 'length')
        return sum(edge_lengths) if edge_lengths else 0.0
    except Exception:
        total = 0.0
        for i in range(len(route) - 1):
            data = G.get_edge_data(route[i], route[i+1])
            if data:
                vals = list(data.values())
                best = min(vals, key=lambda d: d.get('length', float('inf')))
                total += float(best.get('length', 0.0))
        return total

# Fuzzy match user input to region
def fuzzy_match_region(user_input, flood_df):
    all_areas = flood_df['areas'].tolist()
    all_areas_lower = [area.lower() for area in all_areas]
    res = fuzzy_process.extractOne(user_input.lower().strip(), all_areas_lower)
    if res is None:
        return None, 0
    if isinstance(res, (tuple, list)):
        if len(res) >= 2:
            best_match, confidence = res[0], int(res[1])
        elif len(res) == 1:
            best_match, confidence = res[0], 100
        else:
            best_match, confidence = res, 100
    else:
        best_match, confidence = res, 100
    if confidence < 60:
        return None, confidence
    for area in all_areas:
        if area.lower() == best_match:
            return area, confidence
    return None, confidence

# Find safest routes
def find_safest_routes(user_region, G, flood_df):
    user_row = flood_df[flood_df['areas'] == user_region].iloc[0]
    start_lat, start_lon = float(user_row['latitude']), float(user_row['longitude'])
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    safe_regions = flood_df[flood_df['flood_risk_level'] == 'low']
    if safe_regions.empty:
        safe_regions = flood_df[flood_df['flood_risk_level'] == 'moderate']
    routes = []
    for _, safe_row in safe_regions.iterrows():
        dest_lat, dest_lon = float(safe_row['latitude']), float(safe_row['longitude'])
        dest_node = ox.distance.nearest_nodes(G, dest_lon, dest_lat)
        try:
            path = nx.shortest_path(G, start_node, dest_node, weight='length')
            length_m = calculate_route_distance(G, path)
            eta_min = (length_m / 1000.0) / 25.0 * 60.0
            routes.append({
                'destination': safe_row['areas'],
                'risk_level': safe_row['flood_risk_level'],
                'ward_code': safe_row.get('ward_code', 'N/A'),
                'distance_km': length_m / 1000.0,
                'eta_minutes': eta_min,
                'path': path
            })
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
    routes.sort(key=lambda x: x['distance_km'])
    return routes[:2]

# Create interactive map
def create_evacuation_map(G, flood_df, edge_to_region, user_region, routes):
    user_data = flood_df[flood_df['areas'] == user_region].iloc[0]
    map_center = [float(user_data['latitude']), float(user_data['longitude'])]
    m = folium.Map(location=map_center, zoom_start=12, tiles='cartodbpositron', control_scale=True)
    # 1. Color road network by risk
    risk_groups = defaultdict(list)
    for (u, v, key), region_info in edge_to_region.items():
        if region_info:
            risk_groups[region_info['flood_risk_level']].append((u, v, key))
    for risk_level, edges in risk_groups.items():
        color = FLOOD_RISK_COLORS.get(risk_level, '#888888')
        group = folium.FeatureGroup(name=f"Roads: {risk_level.title()}", show=(risk_level=='low'))
        for u, v, key in edges[::10]:  # sample for performance
            try:
                data = G.get_edge_data(u, v, key)
                geom = data.get('geometry')
                if geom:
                    coords = [(lat, lon) for lon, lat in geom.coords]
                    PolyLine(coords, color=color, weight=2, opacity=0.7).add_to(group)
            except Exception:
                continue
        group.add_to(m)
    # 2. Add region markers
    regions_group = folium.FeatureGroup(name='Mumbai Regions', show=True)
    for _, region in flood_df.iterrows():
        risk_level = region['flood_risk_level']
        region_name = region['areas']
        popup_html = f"""
        <div style='font-family: Arial; width: 220px;'>
            <h4 style='margin:0;color:#333;'>{region_name}</h4>
            <table style='width:100%;font-size:12px;'>
                <tr><td><b>Ward Code:</b></td><td>{region.get('ward_code', 'N/A')}</td></tr>
                <tr><td><b>Flood Risk:</b></td><td><span style='color:{FLOOD_RISK_COLORS.get(risk_level, '#000')};font-weight:bold;'>{risk_level.upper()}</span></td></tr>
                <tr><td><b>Latitude:</b></td><td>{region['latitude']:.6f}</td></tr>
                <tr><td><b>Longitude:</b></td><td>{region['longitude']:.6f}</td></tr>
            </table>
        </div>
        """
        folium.CircleMarker(
            location=[region['latitude'], region['longitude']],
            radius=5,
            fill=True,
            fill_opacity=0.9,
            color=FLOOD_RISK_COLORS.get(risk_level, '#888888'),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{region_name} - {risk_level.title()} Risk"
        ).add_to(regions_group)
    regions_group.add_to(m)
    # 3. Highlight user's location
    folium.Marker(
        location=[user_data['latitude'], user_data['longitude']],
        popup=f"<b>🏠 YOUR STARTING LOCATION</b><br>{user_region}<br>Risk: {user_data['flood_risk_level'].upper()}",
        tooltip=f"You are here: {user_region}",
        icon=folium.Icon(color='blue', icon='home', prefix='fa')
    ).add_to(m)
    # 4. Add evacuation routes
    if routes:
        routes_group = folium.FeatureGroup(name='Evacuation Routes', show=True)
        for i, route in enumerate(routes):
            coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route['path']]
            PolyLine(
                coords,
                color=ROUTE_COLORS[i % len(ROUTE_COLORS)],
                weight=6,
                opacity=0.9,
                tooltip=f"Route {i+1}: {route['distance_km']:.2f} km, ETA {route['eta_minutes']:.0f} min → {route['destination']}"
            ).add_to(routes_group)
        routes_group.add_to(m)
    # 5. Add legend
    legend_html = '''
    <div style="position: fixed; top: 80px; right: 10px; width: 220px; background-color: white; border: 2px solid #333; z-index: 9999; font-size: 13px; padding: 15px; border-radius: 5px;">
        <h4 style="margin: 0 0 10px 0; text-align: center;">🗺️ Map Legend</h4>
        <h5 style="margin: 10px 0 5px 0;">Flood Risk Levels:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#1a9850"></i> Low Risk (Safe)</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#fc8d59"></i> Moderate Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#d73027"></i> High Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#DC143C"></i> Severe Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#8B008B"></i> Extreme Risk</p>
        <h5 style="margin: 10px 0 5px 0;">Evacuation Routes:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-minus" style="color:#0066FF; font-weight: bold; font-size: 16px;"></i> Route 1 (Shortest)</p>
        <p style="margin: 2px 0;"><i class="fa fa-minus" style="color:#00CC66; font-weight: bold; font-size: 16px;"></i> Route 2 (Alternative)</p>
        <h5 style="margin: 10px 0 5px 0;">Markers:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-home" style="color:#0066FF;"></i> Your Location</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    # 6. Add controls
    folium.LayerControl(collapsed=False).add_to(m)
    plugins.MeasureControl(primary_length_unit='kilometers').add_to(m)
    plugins.Fullscreen().add_to(m)
    return m

# Display route summary
def display_evacuation_summary(routes, user_region):
    print("\n" + "="*60)
    print("🚨 EVACUATION ROUTE SUMMARY")
    print("="*60)
    if not routes:
        print("❌ No safe evacuation routes found from your location.")
        return
    print(f"📍 Starting Location: {user_region}")
    print(f"🛣️  Number of Safe Routes Found: {len(routes)}")
    print("\n" + "-"*40)
    for i, route in enumerate(routes, 1):
        print(f"\n🚦 EVACUATION ROUTE {i}:")
        print(f"   🎯 Destination: {route['destination']}")
        print(f"   📏 Distance: {route['distance_km']:.2f} km")
        print(f"   ⏱️  Estimated Time: {route['eta_minutes']:.0f} minutes")
        print(f"   🛡️  Safety Level: {route['risk_level'].upper()}")
        print(f"   🏛️  Ward: {route['ward_code']}")

# Main execution
if __name__ == "__main__":
    print("\n🚨 MUMBAI FLOOD EVACUATION ROUTE SYSTEM - ENHANCED 🚨\n")
    # Load road network
    try:
        G = ox.load_graphml("roads_all.graphml")
        print(f"✅ Road network loaded: {len(G.nodes):,} nodes, {len(G.edges):,} edges")
    except FileNotFoundError:
        print("❌ Error: 'roads_all.graphml' not found.")
        exit(1)
    # Load flood risk data
    try:
        flood_df_raw = pd.read_csv("mumbai_ward_area_floodrisk.csv")
        flood_df = normalize_csv_data(flood_df_raw)
        print(f"✅ Flood risk data loaded: {len(flood_df)} regions")
    except FileNotFoundError:
        print("❌ Error: 'mumbai_ward_area_floodrisk.csv' not found.")
        exit(1)
    except Exception as e:
        print(f"❌ Error processing flood data: {e}")
        exit(1)
    # Map regions to road network
    node_to_region, edge_to_region = map_regions_to_road_network(G, flood_df)
    # User input
    print("\n🏠 Enter your current Mumbai area/region:")
    user_input = input("Area name: ").strip()
    if not user_input:
        print("❌ No input provided.")
        exit(1)
    user_region, confidence = fuzzy_match_region(user_input, flood_df)
    if not user_region:
        print(f"❌ Could not match '{user_input}' to any Mumbai region. Try again.")
        exit(1)
    print(f"✅ Location matched: {user_region} (confidence: {confidence}%)")
    # Find routes
    routes = find_safest_routes(user_region, G, flood_df)
    display_evacuation_summary(routes, user_region)
    # Create map
    print("\n🎨 Generating interactive evacuation map...")
    evacuation_map = create_evacuation_map(G, flood_df, edge_to_region, user_region, routes)
    output_filename = "mumbai_evacuation_routes_enhanced.html"
    evacuation_map.save(output_filename)
    print(f"\n✅ Map saved: {output_filename}\nOpen the HTML file in your browser to view the interactive map!")
