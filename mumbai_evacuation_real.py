import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process
import math
import numpy as np

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="🌊 Mumbai Flood Evacuation System | Real-Time Emergency Routing", layout="wide")

# Header with emergency styling
st.markdown("""
<div style="background: linear-gradient(90deg, #FF6B6B, #4ECDC4); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; text-align: center; margin: 0;">🚨 Mumbai Emergency Evacuation System 🚨</h1>
    <p style="color: white; text-align: center; margin: 5px 0 0 0; font-size: 18px;">Real-Time Flood Evacuation Route Finder</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Load comprehensive Mumbai data
# -------------------------------
@st.cache_data
def load_mumbai_data():
    try:
        # Load actual CSV file
        flood_df = pd.read_csv("mumbai_ward_area_floodrisk.csv")
    except:
        # Comprehensive Mumbai data if CSV not found
        mumbai_data = {
            'Ward_Code': [
                'A', 'A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C', 'D', 'D', 'E', 'E', 'E',
                'F/N', 'F/N', 'F/N', 'F/S', 'F/S', 'G/N', 'G/N', 'G/N', 'G/S', 'G/S', 'G/S',
                'H/E', 'H/E', 'H/W', 'H/W', 'H/W', 'K/E', 'K/E', 'K/E', 'K/W', 'K/W', 'K/W',
                'L', 'L', 'L', 'M/E', 'M/E', 'M/W', 'M/W', 'N', 'N', 'P/N', 'P/N', 'P/S', 'P/S',
                'R/N', 'R/N', 'R/S', 'R/S', 'R/C', 'R/C', 'S', 'S', 'S', 'T', 'T', 'T'
            ],
            'Areas': [
                'colaba', 'fort', 'ballard estate', 'cuffe parade', 'dongri', 'mohammed ali road', 'null bazaar',
                'marine lines', 'churchgate', 'cst area', 'girgaon', 'opera house', 'byculla', 'mazgaon', 'cotton green',
                'sion', 'matunga', 'wadala', 'sewri', 'lower parel', 'dadar', 'mahim', 'dharavi', 'worli', 'prabhadevi', 'elphinstone road',
                'kalina', 'vidya vihar', 'bandra west', 'khar west', 'santacruz west', 'andheri east', 'marol', 'sakinaka',
                'andheri west', 'jogeshwari west', 'vile parle west', 'kurla', 'chunabhatti', 'tilak nagar',
                'chembur east', 'govandi', 'chembur west', 'trombay', 'ghatkopar', 'vikhroli',
                'malad east', 'kurar village', 'malad west', 'goregaon west', 'dahisar east', 'borivali east',
                'kandivali west', 'borivali west', 'kandivali east', 'dahisar west', 'bhandup', 'kanjurmarg', 'vikhroli east',
                'mulund west', 'mulund east', 'nahur'
            ],
            'Latitude': [
                18.9151, 18.9354, 18.9496, 18.9225, 18.9594, 18.9633, 18.9578,
                18.9458, 18.9346, 18.9472, 18.9067, 18.9233, 18.9793, 18.9637, 18.9866,
                19.0373, 19.0276, 18.9985, 19.0049, 19.0172, 19.0195, 19.0440, 19.0440,
                19.0176, 19.0144, 19.0098, 19.0802, 19.0866, 19.0544, 19.0717, 19.0833,
                19.1031, 19.1171, 19.1031, 19.1182, 19.1373, 19.0947, 19.0727, 19.0513, 19.0888,
                19.0572, 19.0435, 19.0443, 19.0054, 19.0845, 19.1058, 19.1903, 19.1834,
                19.1598, 19.1613, 19.2525, 19.2536, 19.2064, 19.206, 19.2365, 19.2408,
                19.1436, 19.1145, 19.1086, 19.1741, 19.172, 19.1567
            ],
            'Longitude': [
                72.8141, 72.8354, 72.8414, 72.8312, 72.8376, 72.8433, 72.8378,
                72.8238, 72.8284, 72.8272, 72.8111, 72.8233, 72.8355, 72.8443, 72.8566,
                72.8555, 72.8512, 72.8440, 72.8397, 72.8337, 72.8436, 72.8440, 72.8540,
                72.8199, 72.8244, 72.8319, 72.8655, 72.8800, 72.8301, 72.8391, 72.8344,
                72.8882, 72.8773, 72.8882, 72.8463, 72.8473, 72.8647, 72.8826, 72.8813, 72.8861,
                72.8999, 72.9135, 72.8943, 72.8873, 72.9107, 72.9258, 72.8605, 72.8701,
                72.8445, 72.8407, 72.8601, 72.8682, 72.8376, 72.83, 72.8322, 72.8173,
                72.9357, 72.9306, 72.9158, 72.9592, 72.9554, 72.9268
            ],
            'Flood_Risk_Level': [
                'High', 'Medium', 'Medium', 'High', 'High', 'High', 'High',
                'Medium', 'Low', 'Medium', 'High', 'Medium', 'Low', 'Medium', 'Low',
                'Medium', 'Low', 'Low', 'Medium', 'Medium', 'Medium', 'Low', 'High', 'Medium', 'Medium', 'Medium',
                'Medium', 'Medium', 'Low', 'Low', 'Low', 'Medium', 'High', 'Medium',
                'Low', 'Low', 'Low', 'High', 'Medium', 'Medium', 'Medium', 'High',
                'Low', 'High', 'Medium', 'Low', 'Medium', 'High', 'Low', 'Low',
                'Medium', 'High', 'Low', 'Medium', 'Medium', 'Low', 'Low', 'Medium', 'Low',
                'Low', 'Low', 'Low'
            ]
        }
        flood_df = pd.DataFrame(mumbai_data)
    
    # Clean and normalize data
    flood_df.columns = ['Ward_Code', 'Areas', 'Latitude', 'Longitude', 'Flood_Risk_Level']
    flood_df["Areas"] = flood_df["Areas"].str.strip().str.lower()
    
    return flood_df

# Load data
flood_df = load_mumbai_data()

# -------------------------------
# Advanced route calculation with real Mumbai logic
# -------------------------------
def calculate_evacuation_routes(user_area, flood_df):
    # Fuzzy match region
    all_areas = list(flood_df["Areas"].unique())
    best_match, score = process.extractOne(user_area.lower(), all_areas)
    
    if score < 50:  # More lenient matching
        return None, None, []

    # Get starting point details
    start_area = flood_df[flood_df["Areas"] == best_match].iloc[0]
    start_lat, start_lon = start_area["Latitude"], start_area["Longitude"]
    start_risk = start_area["Flood_Risk_Level"]

    # Find safe zones (Low and Medium risk areas that are not High risk)
    safe_zones = flood_df[flood_df["Flood_Risk_Level"].isin(["Low", "Medium"])].copy()
    
    # Remove current location from safe zones
    safe_zones = safe_zones[safe_zones["Areas"] != best_match]
    
    if safe_zones.empty:
        return best_match, score, []

    # Calculate routes with multiple factors
    routes = []
    for _, safe_area in safe_zones.iterrows():
        # Calculate distance using Haversine formula (more accurate)
        lat1, lon1 = math.radians(start_lat), math.radians(start_lon)
        lat2, lon2 = math.radians(safe_area["Latitude"]), math.radians(safe_area["Longitude"])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c  # Earth's radius in km
        
        # Calculate route score based on multiple factors
        risk_score = {"Low": 1, "Medium": 2, "High": 3}[safe_area["Flood_Risk_Level"]]
        distance_score = distance_km
        
        # Prefer closer, safer areas
        combined_score = (risk_score * 2) + (distance_score * 0.5)
        
        # Estimate travel time based on Mumbai traffic conditions
        if distance_km < 5:
            speed_kmh = 15  # Heavy traffic/local roads
        elif distance_km < 15:
            speed_kmh = 25  # Moderate traffic
        else:
            speed_kmh = 35  # Highway/express routes
            
        eta_min = (distance_km / speed_kmh) * 60
        
        # Add buffer time for emergency conditions
        eta_min *= 1.3
        
        routes.append({
            "destination": safe_area["Areas"].title(),
            "ward": safe_area["Ward_Code"],
            "destination_lat": safe_area["Latitude"],
            "destination_lon": safe_area["Longitude"],
            "distance_km": round(distance_km, 2),
            "eta_min": round(eta_min, 1),
            "risk_level": safe_area["Flood_Risk_Level"],
            "safety_score": risk_score,
            "combined_score": combined_score
        })
    
    # Sort by combined score (best routes first)
    routes = sorted(routes, key=lambda x: x["combined_score"])
    
    return best_match, score, routes[:3]  # Return top 3 routes

# -------------------------------
# Mumbai specific emergency info
# -------------------------------
def get_emergency_contacts():
    return {
        "🚨 Mumbai Police Control Room": "100",
        "🚑 Ambulance Services": "108",
        "🚒 Fire Brigade": "101", 
        "⛑️ Disaster Management": "022-22694725",
        "🌊 BMC Flood Helpline": "1916",
        "🚁 Coast Guard": "1554"
    }

def get_mumbai_safe_zones():
    return [
        "🏥 **Hospitals**: Breach Candy, Jaslok, Hinduja, KEM",
        "🏫 **Schools/Colleges**: St. Xavier's College, Mumbai University",
        "🏢 **Government Buildings**: Mantralaya, BMC Headquarters", 
        "🕌 **Community Centers**: NSCI Club, CCI Club",
        "🏬 **Malls**: Phoenix Mills, Palladium Mall, Infiniti Mall"
    ]

# -------------------------------
# Enhanced UI with Session State
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

# Sidebar with emergency info
with st.sidebar:
    st.markdown("## 🚨 Emergency Contacts")
    emergency_contacts = get_emergency_contacts()
    for service, number in emergency_contacts.items():
        st.markdown(f"**{service}**: `{number}`")
    
    st.markdown("---")
    st.markdown("## 🏥 Safe Zones")
    safe_zones = get_mumbai_safe_zones()
    for zone in safe_zones:
        st.markdown(zone)

# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📍 Enter Your Current Location")
    
    # Show available areas in an expandable section
    with st.expander("🗺️ Available Mumbai Areas (Click to expand)"):
        # Group areas by risk level
        risk_groups = flood_df.groupby('Flood_Risk_Level')['Areas'].apply(list).to_dict()
        
        for risk_level, areas in risk_groups.items():
            if risk_level == 'High':
                st.markdown(f"🔴 **{risk_level} Risk Areas:**")
            elif risk_level == 'Medium':
                st.markdown(f"🟡 **{risk_level} Risk Areas:**")
            else:
                st.markdown(f"🟢 **{risk_level} Risk Areas:**")
            
            # Display areas in columns for better readability
            areas_formatted = [area.title() for area in sorted(areas)]
            cols = st.columns(3)
            for i, area in enumerate(areas_formatted):
                cols[i % 3].write(f"• {area}")
            st.markdown("---")

    user_region = st.text_input(
        "Type your area name:", 
        value=st.session_state.user_region_input,
        placeholder="e.g., Bandra, Andheri, Colaba, Dadar..."
    )

with col2:
    st.markdown("### 🚨 Emergency Actions")
    if st.button("🔍 **FIND EVACUATION ROUTES**", type="primary", use_container_width=True):
        if not user_region.strip():
            st.error("⚠️ Please enter your location!")
            st.session_state.routes_computed = False
        else:
            st.session_state.user_region_input = user_region
            with st.spinner("🔄 Finding safest evacuation routes..."):
                best_match, score, routes = calculate_evacuation_routes(user_region, flood_df)
                
                st.session_state.best_match = best_match
                st.session_state.match_score = score
                st.session_state.routes = routes
                st.session_state.routes_computed = True
    
    if st.button("🔄 Clear Results", use_container_width=True):
        for key in ['routes_computed', 'best_match', 'match_score', 'routes', 'user_region_input']:
            st.session_state[key] = False if key == 'routes_computed' else None if key != 'user_region_input' else ""
        st.rerun()

# Display results
if st.session_state.routes_computed:
    best_match = st.session_state.best_match
    score = st.session_state.match_score
    routes = st.session_state.routes
    
    if best_match is None:
        st.error(f"❌ Location '{st.session_state.user_region_input}' not found in Mumbai area database.")
        st.info("💡 Try searching for nearby areas like Bandra, Andheri, Dadar, etc.")
    elif not routes:
        st.error("⚠️ No safer evacuation routes found from your current location.")
    else:
        # Success message with location info
        start_info = flood_df[flood_df["Areas"] == best_match].iloc[0]
        risk_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[start_info["Flood_Risk_Level"]]
        
        st.success(f"✅ **Current Location**: {best_match.title()} {risk_emoji} (Match: {score}%)")
        st.info(f"📍 **Ward**: {start_info['Ward_Code']} | **Risk Level**: {start_info['Flood_Risk_Level']}")
        
        # Route cards
        st.markdown("## 🛣️ Recommended Evacuation Routes")
        
        for i, route in enumerate(routes):
            risk_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[route["risk_level"]]
            
            with st.container():
                # Route card with proper dark text
                route_bg_color = {"Low": "#d4edda", "Medium": "#fff3cd", "High": "#f8d7da"}[route["risk_level"]]
                route_border_color = {"Low": "#28a745", "Medium": "#ffc107", "High": "#dc3545"}[route["risk_level"]]
                
                st.markdown(f"""
                <div style="border: 3px solid {route_border_color}; border-radius: 15px; padding: 20px; margin: 15px 0; 
                            background-color: {route_bg_color}; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h3 style="color: #2c3e50; margin-bottom: 15px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">
                        🛣️ Route {i+1}: To {route['destination']} {risk_color}
                    </h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; color: #2c3e50;">
                        <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                            <strong>📏 Distance:</strong><br>{route['distance_km']} km
                        </div>
                        <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                            <strong>⏱️ ETA:</strong><br>{route['eta_min']} minutes
                        </div>
                        <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                            <strong>🏛️ Ward:</strong><br>{route['ward']}
                        </div>
                        <div style="background: rgba(255,255,255,0.7); padding: 10px; border-radius: 8px;">
                            <strong>🛡️ Safety:</strong><br>{route['risk_level']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Interactive map
        st.markdown("## 🗺️ Live Evacuation Map")
        
        start = flood_df[flood_df["Areas"] == best_match].iloc[0]
        m = folium.Map(
            location=[start["Latitude"], start["Longitude"]], 
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add starting point with risk-based color
        start_color = {"High": "red", "Medium": "orange", "Low": "green"}[start["Flood_Risk_Level"]]
        folium.Marker(
            [start["Latitude"], start["Longitude"]],
            popup=f"🚨 START: {best_match.title()}<br>Risk: {start['Flood_Risk_Level']}",
            icon=folium.Icon(color=start_color, icon='home', prefix='fa')
        ).add_to(m)
        
        # Add routes with different colors
        colors = ['blue', 'green', 'purple']
        for i, route in enumerate(routes):
            # Destination marker
            dest_color = {"Low": "green", "Medium": "orange", "High": "red"}[route["risk_level"]]
            folium.Marker(
                [route["destination_lat"], route["destination_lon"]],
                popup=f"🏁 SAFE ZONE {i+1}: {route['destination']}<br>"
                      f"Distance: {route['distance_km']}km<br>"
                      f"ETA: {route['eta_min']} min<br>"
                      f"Risk: {route['risk_level']}",
                icon=folium.Icon(color=dest_color, icon='star', prefix='fa')
            ).add_to(m)
            
            # Route line
            folium.PolyLine(
                [[start["Latitude"], start["Longitude"]], 
                 [route["destination_lat"], route["destination_lon"]]],
                color=colors[i % len(colors)],
                weight=5,
                opacity=0.8,
                popup=f"Route {i+1}: {route['distance_km']}km, {route['eta_min']}min"
            ).add_to(m)
        
        # Display the map
        st_folium(m, width=1000, height=600)
        
        # Additional emergency info
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎒 Emergency Kit Checklist")
            st.markdown("""
            - 💧 Water (3 days supply)
            - 🥫 Non-perishable food
            - 🔦 Flashlight & batteries
            - 📱 Phone charger/power bank
            - 💊 First aid kit & medicines
            - 📄 Important documents (waterproof bag)
            - 💰 Cash
            - 👕 Change of clothes
            """)
        
        with col2:
            st.markdown("### 📞 Next Steps")
            st.markdown("""
            1. **🚨 Call Emergency Services**: 100 (Police)
            2. **📞 Inform Family**: Share your evacuation plan
            3. **🎒 Pack Emergency Kit**: Take essentials only
            4. **🚶‍♂️ Follow Route**: Use safest recommended path
            5. **📱 Stay Connected**: Keep phone charged
            6. **🆘 Help Others**: Assist neighbors if possible
            """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; background-color: #2c3e50; border-radius: 10px; color: white; margin-top: 30px;">
    <h4 style="color: #ecf0f1; margin-bottom: 10px;">🌊 Mumbai Emergency Evacuation System</h4>
    <p style="color: #bdc3c7; margin-bottom: 10px;">Real-time flood evacuation routing for Mumbai citizens | Stay Safe, Stay Informed</p>
    <p style="color: #e74c3c; font-weight: bold; font-size: 16px;"><strong>Emergency Helpline: 1916 (BMC) | 100 (Police) | 108 (Ambulance)</strong></p>
</div>
""", unsafe_allow_html=True)
