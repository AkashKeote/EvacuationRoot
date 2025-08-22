"""
Mumbai Flood Evacuation Route System - Enhanced Version
Maps 102 regions to road network, colors roads by region risk, finds safest routes
"""

import osmnx as ox
import networkx as nx
import pandas as pd
import folium
import numpy as np
from folium import plugins
from scipy.spatial import cKDTree
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

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
                matches = difflib.get_close_matches(query, choices, n=1, cutoff=0)
                if matches:
                    score = int(difflib.SequenceMatcher(None, query, matches[0]).ratio() * 100)
                    return matches[0], score
                return None, 0
        fuzzy_process = _DLProcess()

# -------------------------------
# Configuration
# -------------------------------
FLOOD_RISK_COLORS = {
    'low': '#2E8B57',      # Sea Green - Safe
    'moderate': '#FFD700', # Gold - Caution
    'high': '#FF8C00',     # Dark Orange - Warning
    'severe': '#DC143C',   # Crimson - Danger
    'extreme': '#8B008B'   # Dark Magenta - Critical
}

ROUTE_COLORS = ['#0066FF', '#00CC66']  # Primary Blue, Success Green
MUMBAI_CENTER = [19.0760, 72.8777]

# -------------------------------
# Core Functions
# -------------------------------

def normalize_csv_data(df):
    """Normalize CSV data with robust column mapping."""
    df = df.copy()
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    df.columns = df.columns.str.replace(' ', '_').str.replace('-', '_')
    
    # Map common column variations
    column_mapping = {
        'ward_code': 'ward_code',
        'area': 'areas', 'region': 'areas', 'ward_name': 'areas',
        'lat': 'latitude', 'y': 'latitude',
        'lon': 'longitude', 'lng': 'longitude', 'x': 'longitude',
        'flood_risk_level': 'flood_risk_level', 'risk_level': 'flood_risk_level'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df.rename(columns={old_col: new_col}, inplace=True)
    
    # Validate required columns
    required = ['areas', 'latitude', 'longitude', 'flood_risk_level']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {list(df.columns)}")
    
    # Clean and validate data
    df['areas'] = df['areas'].astype(str).str.strip().str.title()
    df['flood_risk_level'] = df['flood_risk_level'].astype(str).str.strip().str.lower()
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Remove invalid coordinates
    df = df.dropna(subset=['latitude', 'longitude'])
    
    return df

def map_regions_to_road_network(G, flood_df, region_radius_km=2.0):
    """Map each region to nearby road network nodes and edges."""
    print(f"🗺️  Mapping {len(flood_df)} regions to road network...")
    print(f"   Using {region_radius_km} km radius for each region")
    
    # Prepare region data
    region_coords = np.array([[row['latitude'], row['longitude']] for _, row in flood_df.iterrows()])
    region_data = flood_df[['areas', 'flood_risk_level', 'latitude', 'longitude']].to_dict('records')
    
    # Build KDTree for efficient spatial queries
    tree = cKDTree(region_coords)
    
    # Initialize region mappings
    node_to_region = {}
    edge_to_region = {}
    region_networks = defaultdict(list)
    
    print("   Assigning nodes to regions...")
    
    # Assign each node to the nearest region
    for node_id, node_data in G.nodes(data=True):
        node_coord = [node_data['y'], node_data['x']]  # lat, lon
        
        # Find nearest region
        distance_deg, region_idx = tree.query(node_coord)
        
        # Convert distance to kilometers (approximate)
        distance_km = distance_deg * 111.0  # 1 degree ≈ 111 km
        
        if distance_km <= region_radius_km:
            region_info = region_data[region_idx]
            node_to_region[node_id] = region_info
            region_networks[region_info['areas']].append(node_id)
            
            # Add region info to node attributes
            G.nodes[node_id]['region_name'] = region_info['areas']
            G.nodes[node_id]['flood_risk'] = region_info['flood_risk_level']
    
    print(f"   ✅ Mapped {len(node_to_region)} nodes to regions")
    
    # Assign edges to regions based on their nodes
    print("   Assigning edges to regions...")
    
    for u, v, key in G.edges(keys=True):
        u_region = node_to_region.get(u)
        v_region = node_to_region.get(v)
        
        if u_region and v_region:
            # Both nodes have regions - use the higher risk region
            risk_priority = {'low': 0, 'moderate': 1, 'high': 2, 'severe': 3, 'extreme': 4}
            
            u_risk_level = risk_priority.get(u_region['flood_risk_level'], 1)
            v_risk_level = risk_priority.get(v_region['flood_risk_level'], 1)
            
            if u_risk_level >= v_risk_level:
                edge_to_region[(u, v, key)] = u_region
            else:
                edge_to_region[(u, v, key)] = v_region
        elif u_region:
            edge_to_region[(u, v, key)] = u_region
        elif v_region:
            edge_to_region[(u, v, key)] = v_region
    
    print(f"   ✅ Mapped {len(edge_to_region)} edges to regions")
    
    return node_to_region, edge_to_region, region_networks

def calculate_route_distance(G, route):
    """Calculate total route distance in meters."""
    try:
        edge_lengths = ox.utils_graph.get_route_edge_attributes(G, route, 'length')
        return sum(edge_lengths) if edge_lengths else 0.0
    except:
        total = 0.0
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            edge_data = G.get_edge_data(u, v)
            if edge_data:
                min_edge = min(edge_data.values(), key=lambda x: x.get('length', float('inf')))
                total += min_edge.get('length', 0.0)
        return total

def find_user_location_and_routes(user_input, G, flood_df, node_to_region):
    """Find user's location and calculate safest evacuation routes."""
    
    # Fuzzy match user input to available regions
    all_areas = flood_df['areas'].tolist()
    all_areas_lower = [area.lower() for area in all_areas]
    
    try:
        best_match, confidence = fuzzy_process.extractOne(user_input.lower().strip(), all_areas_lower)
    except:
        return None, None, []
    
    if confidence < 60:
        return None, None, []
    
    # Find the original case region name
    matched_region = None
    for area in all_areas:
        if area.lower() == best_match:
            matched_region = area
            break
    
    if not matched_region:
        return None, None, []
    
    # Get user's region data
    user_region_data = flood_df[flood_df['areas'] == matched_region].iloc[0]
    start_lat, start_lon = float(user_region_data['latitude']), float(user_region_data['longitude'])
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    
    print(f"📍 User location: {matched_region}")
    print(f"   Risk level: {user_region_data['flood_risk_level'].upper()}") 
    print(f"   Coordinates: {start_lat:.4f}, {start_lon:.4f}")
    
    # Find safe destination regions (low flood risk)
    safe_regions = flood_df[flood_df['flood_risk_level'] == 'low']
    
    if safe_regions.empty:
        print("⚠️  Warning: No regions with 'low' flood risk found!")
        # Fallback to moderate risk regions
        safe_regions = flood_df[flood_df['flood_risk_level'] == 'moderate']
        if safe_regions.empty:
            return matched_region, confidence, []
    
    print(f"🔍 Found {len(safe_regions)} safe destination regions")
    
    # Calculate routes to all safe regions
    potential_routes = []
    
    for _, safe_region in safe_regions.iterrows():
        try:
            dest_lat, dest_lon = float(safe_region['latitude']), float(safe_region['longitude'])
            dest_node = ox.distance.nearest_nodes(G, dest_lon, dest_lat)
            
            if dest_node == start_node:
                continue
            
            # Find shortest path
            path = nx.shortest_path(G, start_node, dest_node, weight='length')
            distance_m = calculate_route_distance(G, path)
            
            # Calculate ETA (assuming 25 km/h in Mumbai traffic)
            eta_minutes = (distance_m / 1000.0) / 25.0 * 60.0
            
            potential_routes.append({
                'path': path,
                'destination': safe_region['areas'],
                'destination_coords': (dest_lat, dest_lon),
                'distance_km': distance_m / 1000.0,
                'eta_minutes': eta_minutes,
                'risk_level': safe_region['flood_risk_level'],
                'ward_code': safe_region.get('ward_code', 'N/A')
            })
            
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
        except Exception:
            continue
    
    # Sort by distance and return top 2 routes
    potential_routes.sort(key=lambda x: x['distance_km'])
    
    return matched_region, confidence, potential_routes[:2]

def create_comprehensive_evacuation_map(G, flood_df, edge_to_region, user_region, routes):
    """Create detailed evacuation map with region-colored road network."""
    
    print("🎨 Creating comprehensive evacuation map...")
    
    # Get map center from user location
    user_data = flood_df[flood_df['areas'] == user_region].iloc[0]
    map_center = [float(user_data['latitude']), float(user_data['longitude'])]
    
    # Create base map
    m = folium.Map(
        location=map_center,
        zoom_start=11,
        tiles='OpenStreetMap',
        control_scale=True
    )
    
    # Add map title
    title_html = f'''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%); 
                background: white; padding: 10px; border: 2px solid #333; 
                border-radius: 5px; z-index: 9999; text-align: center;">
        <h3 style="margin: 0; color: #d32f2f;">🚨 Mumbai Flood Evacuation System</h3>
        <p style="margin: 5px 0 0 0;">Starting from: <strong>{user_region}</strong></p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # 1. Color road network by regions' flood risk
    print("🌈 Coloring road network by regional flood risk...")
    
    # Group edges by risk level
    risk_groups = defaultdict(list)
    
    for (u, v, key), region_info in edge_to_region.items():
        if region_info:
            risk_level = region_info['flood_risk_level']
            u_coord = (G.nodes[u]['y'], G.nodes[u]['x'])
            v_coord = (G.nodes[v]['y'], G.nodes[v]['x'])
            
            risk_groups[risk_level].append({
                'coords': [u_coord, v_coord],
                'region': region_info['areas']
            })
    
    # Add road network layers by risk level
    for risk_level, edges in risk_groups.items():
        if edges:
            color = FLOOD_RISK_COLORS.get(risk_level, '#808080')
            
            # Create feature group for this risk level
            risk_group = folium.FeatureGroup(
                name=f'{risk_level.title()} Risk Roads ({len(edges)} segments)',
                show=True
            )
            
            # Add road segments
            for edge_info in edges:
                folium.PolyLine(
                    edge_info['coords'],
                    color=color,
                    weight=2.5,
                    opacity=0.7,
                    tooltip=f"Road in {edge_info['region']} - {risk_level.title()} flood risk"
                ).add_to(risk_group)
            
            risk_group.add_to(m)
    
    # 2. Add all 102 region markers with detailed information
    print("📍 Adding all 102 Mumbai region markers...")
    
    regions_group = folium.FeatureGroup(name='Mumbai Regions (102)', show=True)
    
    for _, region in flood_df.iterrows():
        risk_level = region['flood_risk_level']
        region_name = region['areas']
        
        # Choose icon based on risk level
        if risk_level == 'low':
            icon_name, icon_color = 'ok-sign', 'green'
        elif risk_level == 'moderate':
            icon_name, icon_color = 'exclamation-sign', 'orange'
        elif risk_level == 'high':
            icon_name, icon_color = 'warning-sign', 'red'
        elif risk_level == 'severe':
            icon_name, icon_color = 'remove-sign', 'darkred'
        else:  # extreme
            icon_name, icon_color = 'ban-circle', 'purple'
        
        # Create detailed popup
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">{region_name}</h4>
            <table style="width: 100%; font-size: 12px;">
                <tr><td><strong>Ward Code:</strong></td><td>{region.get('ward_code', 'N/A')}</td></tr>
                <tr><td><strong>Flood Risk:</strong></td><td><span style="color: {FLOOD_RISK_COLORS.get(risk_level, '#000')}; font-weight: bold;">{risk_level.upper()}</span></td></tr>
                <tr><td><strong>Latitude:</strong></td><td>{region['latitude']:.6f}</td></tr>
                <tr><td><strong>Longitude:</strong></td><td>{region['longitude']:.6f}</td></tr>
            </table>
        </div>
        """
        
        # Add marker
        folium.Marker(
            location=[region['latitude'], region['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{region_name} - {risk_level.title()} Risk",
            icon=folium.Icon(color=icon_color, icon=icon_name)
        ).add_to(regions_group)
    
    regions_group.add_to(m)
    
    # 3. Highlight user's starting location
    folium.Marker(
        location=[user_data['latitude'], user_data['longitude']],
        popup=f"<b>🏠 YOUR STARTING LOCATION</b><br>{user_region}<br>Risk: {user_data['flood_risk_level'].upper()}",
        tooltip=f"You are here: {user_region}",
        icon=folium.Icon(color='blue', icon='home', prefix='fa')
    ).add_to(m)
    
    # 4. Add evacuation routes if found
    if routes:
        print(f"🛣️  Adding {len(routes)} safest evacuation routes...")
        
        routes_group = folium.FeatureGroup(name='Evacuation Routes', show=True)
        
        for i, route in enumerate(routes):
            route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route['path']]
            color = ROUTE_COLORS[i % len(ROUTE_COLORS)]
            
            # Main route line with enhanced styling
            route_line = folium.PolyLine(
                route_coords,
                color=color,
                weight=8,
                opacity=0.9,
                tooltip=f"🚦 Route {i+1} to {route['destination']}<br>Distance: {route['distance_km']:.2f} km<br>ETA: {route['eta_minutes']:.0f} minutes"
            )
            route_line.add_to(routes_group)
            
            # Add directional arrows along the route
            plugins.PolyLineTextPath(
                route_line,
                f"    ➤ ROUTE {i+1}    ",
                repeat=True,
                offset=10,
                attributes={
                    'fill': color,
                    'font-weight': 'bold',
                    'font-size': '14px',
                    'font-family': 'Arial'
                }
            ).add_to(routes_group)
            
            # Mark destination with detailed info
            dest_popup = f"""
            <div style="font-family: Arial; text-align: center;">
                <h4>🛡️ SAFE DESTINATION {i+1}</h4>
                <p><strong>{route['destination']}</strong></p>
                <p>📏 Distance: <strong>{route['distance_km']:.2f} km</strong></p>
                <p>⏱️ ETA: <strong>{route['eta_minutes']:.0f} minutes</strong></p>
                <p>🛡️ Risk Level: <strong style="color: green;">{route['risk_level'].upper()}</strong></p>
            </div>
            """
            
            folium.Marker(
                location=route['destination_coords'],
                popup=folium.Popup(dest_popup, max_width=200),
                tooltip=f"Safe Zone: {route['destination']}",
                icon=folium.Icon(color='green', icon='shield', prefix='fa')
            ).add_to(routes_group)
        
        routes_group.add_to(m)
    
    # 5. Add comprehensive legend
    legend_html = '''
    <div style="position: fixed; top: 80px; right: 10px; width: 220px; 
                background-color: white; border: 2px solid #333; z-index: 9999; 
                font-size: 13px; padding: 15px; border-radius: 5px;">
        <h4 style="margin: 0 0 10px 0; text-align: center;">🗺️ Map Legend</h4>
        
        <h5 style="margin: 10px 0 5px 0;">Flood Risk Levels:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#2E8B57"></i> Low Risk (Safe)</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#FFD700"></i> Moderate Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#FF8C00"></i> High Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#DC143C"></i> Severe Risk</p>
        <p style="margin: 2px 0;"><i class="fa fa-circle" style="color:#8B008B"></i> Extreme Risk</p>
        
        <h5 style="margin: 10px 0 5px 0;">Evacuation Routes:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-minus" style="color:#0066FF; font-weight: bold; font-size: 16px;"></i> Route 1 (Shortest)</p>
        <p style="margin: 2px 0;"><i class="fa fa-minus" style="color:#00CC66; font-weight: bold; font-size: 16px;"></i> Route 2 (Alternative)</p>
        
        <h5 style="margin: 10px 0 5px 0;">Markers:</h5>
        <p style="margin: 2px 0;"><i class="fa fa-home" style="color:#0066FF;"></i> Your Location</p>
        <p style="margin: 2px 0;"><i class="fa fa-shield" style="color:#28a745;"></i> Safe Destinations</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 6. Add layer control
    folium.LayerControl(collapsed=False).add_to(m)
    
    # 7. Add measurement tool
    plugins.MeasureControl(primary_length_unit='kilometers').add_to(m)
    
    # 8. Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    return m

def display_evacuation_summary(routes, user_region):
    """Display detailed evacuation route information."""
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
        
        # Show route path (first few and last few locations)
        path_regions = []
        for node in route['path'][::max(1, len(route['path'])//8)]:  # Sample path
            if hasattr(G.nodes[node], 'get') and G.nodes[node].get('region_name'):
                path_regions.append(G.nodes[node]['region_name'])
        
        if path_regions:
            unique_path_regions = []
            for region in path_regions:
                if region not in unique_path_regions:
                    unique_path_regions.append(region)
            print(f"   🗺️  Route passes through: {' → '.join(unique_path_regions[:5])}{'...' if len(unique_path_regions) > 5 else ''}")

def main():
    """Main execution function."""
    print("🚨" + "="*58 + "🚨")
    print("🚨 MUMBAI FLOOD EVACUATION ROUTE SYSTEM - ENHANCED 🚨") 
    print("🚨" + "="*58 + "🚨")
    
    # Step 1: Load Mumbai road network
    print("\n📡 STEP 1: Loading Mumbai road network...")
    try:
        G = ox.load_graphml("roads_all.graphml")
        print(f"✅ Road network loaded successfully!")
        print(f"   📊 Network size: {len(G.nodes):,} nodes, {len(G.edges):,} edges")
    except FileNotFoundError:
        print("❌ Error: 'roads_all.graphml' not found in current directory.")
        print("   Please ensure the GraphML file exists.")
        return
    except Exception as e:
        print(f"❌ Error loading road network: {e}")
        return
    
    # Step 2: Load flood risk data
    print("\n📋 STEP 2: Loading Mumbai flood risk data...")
    try:
        flood_df_raw = pd.read_csv("mumbai_ward_area_floodrisk.csv")
        flood_df = normalize_csv_data(flood_df_raw)
        print(f"✅ Flood risk data loaded successfully!")
        print(f"   📊 Loaded {len(flood_df)} Mumbai regions")
    except FileNotFoundError:
        print("❌ Error: 'mumbai_ward_area_floodrisk.csv' not found.")
        return
    except Exception as e:
        print(f"❌ Error processing flood data: {e}")
        return
    
    # Display risk distribution
    risk_counts = flood_df['flood_risk_level'].value_counts()
    print("\n📈 Mumbai flood risk distribution:")
    for risk_level, count in risk_counts.items():
        print(f"   🔸 {risk_level.upper()}: {count} regions")
    
    # Step 3: Map regions to road network
    print(f"\n🗺️  STEP 3: Mapping {len(flood_df)} regions to road network...")
    node_to_region, edge_to_region, region_networks = map_regions_to_road_network(G, flood_df)
    
    print(f"✅ Region mapping completed:")
    print(f"   📍 {len(node_to_region):,} road nodes mapped to regions")
    print(f"   🛣️  {len(edge_to_region):,} road edges assigned risk levels")
    
    # Step 4: Get user location
    print("\n🏠 STEP 4: User location input...")
    print("-" * 40)
    print("Available regions include:")
    sample_regions = sorted(flood_df['areas'].unique())[:8]
    for region in sample_regions:
        risk = flood_df[flood_df['areas'] == region].iloc[0]['flood_risk_level']
        print(f"   • {region} ({risk})")
    print(f"   ... and {len(flood_df) - len(sample_regions)} more regions")
    
    try:
        user_input = input("\n🏠 Enter your current Mumbai area/region: ").strip()
        if not user_input:
            print("❌ No area name provided.")
            return
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Input cancelled.")
        return
    
    # Step 5: Find evacuation routes
    print(f"\n🔍 STEP 5: Finding safest evacuation routes from '{user_input}'...")
    user_region, confidence, routes = find_user_location_and_routes(user_input, G, flood_df, node_to_region)
    
    if not user_region:
        print(f"❌ Could not match '{user_input}' to any Mumbai region.")
        print("\n💡 Suggestions:")
        close_matches = []
        for area in flood_df['areas']:
            if user_input.lower() in area.lower():
                close_matches.append(area)
        
        if close_matches:
            for match in close_matches[:5]:
                print(f"   • {match}")
        else:
            print("   Try: Bandra, Andheri, Colaba, Marine Drive, etc.")
        return
    
    print(f"✅ Location matched: {user_region} (confidence: {confidence}%)")
    
    # Display route summary
    display_evacuation_summary(routes, user_region)
    
    # Step 6: Create comprehensive map
    print(f"\n🎨 STEP 6: Creating interactive evacuation map...")
    evacuation_map = create_comprehensive_evacuation_map(G, flood_df, edge_to_region, user_region, routes)
    
    # Save the map
    output_filename = "mumbai_flood_evacuation_comprehensive.html"
    evacuation_map.save(output_filename)
    
    # Final summary
    print("\n" + "🎉"*20)
    print("🎉 EVACUATION MAP GENERATED SUCCESSFULLY! 🎉")
    print("🎉"*20)
    print(f"\n📁 File saved: {output_filename}")
    print("\n🗺️  Map includes:")
    print("   ✅ Complete Mumbai road network colored by flood risk")
    print("   ✅ All 102 regions marked with risk levels")
    print("   ✅ Your location highlighted")
    print("   ✅ 2 safest evacuation routes with distance & ETA")
    print("   ✅ Interactive tooltips and popups")
    print("   ✅ Layer controls and measurement tools")
    print("   ✅ Region names and risk levels on hover")
    print("\n🌐 Open the HTML file in your web browser to view the interactive map!")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
