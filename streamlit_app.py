import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process
import math
import numpy as np
from datetime import datetime

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(
    page_title="🚨 Mumbai Emergency Evacuation System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for emergency styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #dc3545, #fd7e14, #ffc107);
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 8px 16px rgba(0,0,0,0.3); }
        50% { box-shadow: 0 12px 24px rgba(220,53,69,0.4); }
        100% { box-shadow: 0 8px 16px rgba(0,0,0,0.3); }
    }
    
    .emergency-alert {
        background: #dc3545;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        font-weight: bold;
        animation: blink 1.5s infinite;
    }
    
    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.7; }
    }
    
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Emergency Header
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
        🚨 MUMBAI FLOOD EMERGENCY EVACUATION SYSTEM 🚨
    </h1>
    <h3 style="color: white; margin: 10px 0 0 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
        Advanced Route Planning for Life-Saving Evacuations
    </h3>
</div>
""", unsafe_allow_html=True)

# Real-time emergency alert
current_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="emergency-alert">
    🚨 FLOOD EMERGENCY ACTIVE | CURRENT TIME: {current_time} | SEEK IMMEDIATE EVACUATION 🚨
</div>
""", unsafe_allow_html=True)

# -------------------------------
# Comprehensive Mumbai Flood Data
# -------------------------------
@st.cache_data
def load_mumbai_data():
    """Complete Mumbai flood evacuation database"""
    mumbai_data = {
        'Ward': [
            'A', 'A', 'A', 'A', 'A',
            'B', 'B', 'B', 'B',
            'C', 'C', 'C', 'C',
            'D', 'D', 'D',
            'E', 'E', 'E', 'E',
            'F/N', 'F/N', 'F/N', 'F/N',
            'F/S', 'F/S', 'F/S',
            'G/N', 'G/N', 'G/N', 'G/N',
            'G/S', 'G/S', 'G/S', 'G/S',
            'H/E', 'H/E', 'H/E', 'H/E',
            'H/W', 'H/W', 'H/W', 'H/W',
            'K/E', 'K/E', 'K/E', 'K/E',
            'K/W', 'K/W', 'K/W', 'K/W',
            'L', 'L', 'L',
            'M/E', 'M/E', 'M/E',
            'M/W', 'M/W', 'M/W',
            'N', 'N',
            'P/N', 'P/N', 'P/N',
            'P/S', 'P/S', 'P/S',
            'R/N', 'R/N',
            'R/S', 'R/S',
            'R/C', 'R/C',
            'S', 'S', 'S',
            'T', 'T', 'T'
        ],
        'Area_Name': [
            'colaba', 'fort', 'ballard estate', 'cuffe parade', 'navy nagar',
            'dongri', 'mohammed ali road', 'null bazaar', 'bhendi bazaar',
            'marine lines', 'churchgate', 'cst area', 'azad maidan',
            'girgaon', 'opera house', 'charni road',
            'byculla', 'mazgaon', 'cotton green', 'sewri',
            'sion', 'matunga', 'king circle', 'mahim',
            'lower parel', 'elphinstone road', 'prabhadevi',
            'dadar east', 'dadar west', 'shivaji park', 'dharavi',
            'worli', 'bandra west', 'khar west', 'santacruz west',
            'kalina', 'vidya vihar', 'santacruz east', 'kurla east',
            'juhu', 'andheri west', 'jogeshwari west', 'vile parle west',
            'andheri east', 'marol', 'sakinaka', 'ghatkopar east',
            'versova', 'oshiwara', 'lokhandwala', 'borivali west',
            'kurla west', 'chunabhatti', 'chembur',
            'govandi', 'mankhurd', 'trombay',
            'chembur west', 'kanjurmarg', 'mulund west',
            'powai', 'vikhroli',
            'kurar village', 'malad east', 'marve',
            'goregaon east', 'aarey colony', 'sanjay gandhi national park',
            'dahisar east', 'kandivali east',
            'mira road', 'vasai',
            'navi mumbai', 'thane',
            'bhandup east', 'mulund east', 'nahur',
            'dombivli', 'ambarnath', 'karjat'
        ],
        'Latitude': [
            18.9151, 18.9354, 18.9496, 18.9225, 18.9188,
            18.9594, 18.9633, 18.9578, 18.9612,
            18.9458, 18.9346, 18.9472, 18.9487,
            18.9067, 18.9233, 18.9511,
            18.9793, 18.9637, 18.9866, 19.0049,
            19.0373, 19.0276, 19.0272, 19.0440,
            19.0172, 19.0098, 19.0144,
            19.0195, 19.0283, 19.0311, 19.0440,
            19.0176, 19.0544, 19.0717, 19.0833,
            19.0802, 19.0866, 19.0758, 19.0727,
            19.1074, 19.1182, 19.1373, 19.0947,
            19.1031, 19.1171, 19.1031, 19.0845,
            19.1100, 19.1482, 19.1336, 19.2365,
            19.0727, 19.0513, 19.0443,
            19.0572, 19.0435, 19.0054,
            19.0443, 19.1145, 19.1741,
            19.1171, 19.1058,
            19.1903, 19.1834, 19.2103,
            19.1613, 19.1758, 19.2103,
            19.2525, 19.2365,
            19.2928, 19.3611,
            19.2756, 19.2183,
            19.1436, 19.1741, 19.1567,
            19.2144, 19.2103, 18.9167
        ],
        'Longitude': [
            72.8141, 72.8354, 72.8414, 72.8312, 72.8288,
            72.8376, 72.8433, 72.8378, 72.8389,
            72.8238, 72.8284, 72.8272, 72.8356,
            72.8111, 72.8233, 72.8089,
            72.8355, 72.8443, 72.8566, 72.8397,
            72.8555, 72.8512, 72.8559, 72.8440,
            72.8337, 72.8319, 72.8244,
            72.8436, 72.8422, 72.8378, 72.8540,
            72.8199, 72.8301, 72.8391, 72.8344,
            72.8655, 72.8800, 72.8589, 72.8826,
            72.8267, 72.8463, 72.8473, 72.8647,
            72.8882, 72.8773, 72.8882, 72.9107,
            72.8189, 72.8273, 72.8436, 72.8322,
            72.8826, 72.8813, 72.8943,
            72.8999, 72.9135, 72.8873,
            72.8943, 72.9306, 72.9592,
            72.9158, 72.9258,
            72.8605, 72.8701, 72.7956,
            72.8407, 72.8756, 72.7956,
            72.8601, 72.8322,
            72.7956, 72.8034,
            72.8856, 72.9781,
            72.9357, 72.9554, 72.9268,
            73.0356, 73.1567, 73.3245
        ],
        'Flood_Risk': [
            'Critical', 'High', 'High', 'Critical', 'Critical',
            'Critical', 'Critical', 'Critical', 'Critical',
            'High', 'Medium', 'High', 'High',
            'Critical', 'High', 'High',
            'Medium', 'High', 'Low', 'High',
            'High', 'Low', 'High', 'Medium',
            'High', 'High', 'High',
            'High', 'Medium', 'Medium', 'Critical',
            'High', 'Low', 'Low', 'Low',
            'High', 'High', 'High', 'Critical',
            'Low', 'Low', 'Low', 'Low',
            'High', 'Critical', 'Critical', 'High',
            'Low', 'Medium', 'Low', 'Low',
            'Critical', 'High', 'Medium',
            'Critical', 'Critical', 'Critical',
            'Medium', 'Medium', 'Low',
            'Medium', 'Medium',
            'High', 'High', 'Medium',
            'Medium', 'Low', 'Low',
            'High', 'Low',
            'Medium', 'Low',
            'Low', 'Low',
            'Medium', 'Low', 'Low',
            'Low', 'Low', 'Low'
        ],
        'Evacuation_Priority': [
            'Immediate', 'Immediate', 'Immediate', 'Immediate', 'Immediate',
            'Immediate', 'Immediate', 'Immediate', 'Immediate',
            'Urgent', 'Standard', 'Urgent', 'Urgent',
            'Immediate', 'Urgent', 'Urgent',
            'Standard', 'Urgent', 'Safe', 'Urgent',
            'Urgent', 'Safe', 'Urgent', 'Standard',
            'Urgent', 'Urgent', 'Urgent',
            'Urgent', 'Standard', 'Standard', 'Immediate',
            'Urgent', 'Safe', 'Safe', 'Safe',
            'Urgent', 'Urgent', 'Urgent', 'Immediate',
            'Safe', 'Safe', 'Safe', 'Safe',
            'Urgent', 'Immediate', 'Immediate', 'Urgent',
            'Safe', 'Standard', 'Safe', 'Safe',
            'Immediate', 'Urgent', 'Standard',
            'Immediate', 'Immediate', 'Immediate',
            'Standard', 'Standard', 'Safe',
            'Standard', 'Standard',
            'Urgent', 'Urgent', 'Standard',
            'Standard', 'Safe', 'Safe',
            'Urgent', 'Safe',
            'Standard', 'Safe',
            'Safe', 'Safe',
            'Standard', 'Safe', 'Safe',
            'Safe', 'Safe', 'Safe'
        ],
        'Population_Density': [
            50000, 45000, 35000, 40000, 30000,
            55000, 60000, 45000, 50000,
            35000, 30000, 40000, 35000,
            45000, 35000, 40000,
            35000, 30000, 20000, 25000,
            40000, 25000, 35000, 30000,
            45000, 40000, 35000,
            50000, 40000, 30000, 80000,
            30000, 25000, 20000, 18000,
            35000, 30000, 40000, 70000,
            15000, 20000, 18000, 22000,
            45000, 60000, 55000, 40000,
            12000, 25000, 15000, 10000,
            65000, 50000, 35000,
            70000, 75000, 85000,
            30000, 35000, 20000,
            25000, 30000,
            35000, 40000, 20000,
            25000, 15000, 8000,
            30000, 15000,
            20000, 12000,
            10000, 8000,
            25000, 18000, 15000,
            12000, 10000, 5000
        ]
    }
    
    df = pd.DataFrame(mumbai_data)
    df["Area_Name"] = df["Area_Name"].str.strip().str.lower()
    return df

# Load data
flood_df = load_mumbai_data()

# -------------------------------
# Advanced Evacuation Route Calculator
# -------------------------------
def calculate_evacuation_routes(user_area, flood_df):
    """Calculate best evacuation routes from user location"""
    
    # Fuzzy matching
    all_areas = list(flood_df["Area_Name"].unique())
    best_match, score = process.extractOne(user_area.lower(), all_areas)
    
    if score < 40:
        return None, None, []
    
    # Get current location details
    current_location = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
    start_lat, start_lon = current_location["Latitude"], current_location["Longitude"]
    current_risk = current_location["Flood_Risk"]
    current_priority = current_location["Evacuation_Priority"]
    
    # Find safe evacuation destinations
    safe_zones = flood_df[
        (flood_df["Flood_Risk"].isin(["Low", "Medium"])) &
        (flood_df["Area_Name"] != best_match) &
        (flood_df["Evacuation_Priority"].isin(["Safe", "Standard"]))
    ].copy()
    
    if safe_zones.empty:
        return best_match, score, []
    
    # Calculate routes
    routes = []
    for _, destination in safe_zones.iterrows():
        # Haversine distance calculation
        lat1, lon1 = math.radians(start_lat), math.radians(start_lon)
        lat2, lon2 = math.radians(destination["Latitude"]), math.radians(destination["Longitude"])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = 6371 * c
        
        # Risk scoring
        risk_scores = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        safety_score = risk_scores.get(destination["Flood_Risk"], 2)
        current_risk_score = risk_scores.get(current_risk, 2)
        
        # Calculate route score
        distance_score = distance_km * 0.3
        safety_improvement = (current_risk_score - safety_score) * 2
        route_score = distance_score - safety_improvement
        
        # ETA calculation with Mumbai traffic
        if distance_km < 3:
            base_speed = 12
        elif distance_km < 8:
            base_speed = 18
        elif distance_km < 15:
            base_speed = 25
        else:
            base_speed = 35
        
        emergency_speed_factor = 0.7
        actual_speed = base_speed * emergency_speed_factor
        total_eta = ((distance_km / actual_speed) * 60) * 1.4
        
        # Transport recommendation
        if current_priority == "Immediate":
            if distance_km < 2:
                transport = "🚶‍♂️ Walk Fast"
            elif distance_km < 8:
                transport = "🚲 Bicycle/Auto"
            else:
                transport = "🚐 Emergency Vehicle"
        elif distance_km < 1:
            transport = "🚶‍♂️ Walk"
        elif distance_km < 5:
            transport = "🚲 Bicycle"
        elif distance_km < 12:
            transport = "🚗 Car/Taxi"
        else:
            transport = "🚌 Bus/Train"
        
        capacity_score = min(100, max(10, 100 - (destination["Population_Density"] / 1000)))
        
        routes.append({
            "destination": destination["Area_Name"].title(),
            "ward": destination["Ward"],
            "destination_lat": destination["Latitude"],
            "destination_lon": destination["Longitude"],
            "distance_km": round(distance_km, 2),
            "eta_minutes": round(total_eta, 1),
            "risk_level": destination["Flood_Risk"],
            "evacuation_priority": destination["Evacuation_Priority"],
            "safety_improvement": round(safety_improvement, 1),
            "capacity_score": round(capacity_score, 1),
            "route_score": round(route_score, 2),
            "population_density": destination["Population_Density"],
            "transport": transport
        })
    
    routes = sorted(routes, key=lambda x: x["route_score"])
    return best_match, score, routes[:5]

# -------------------------------
# Emergency Information
# -------------------------------
def get_emergency_info():
    """Get emergency contacts and resources"""
    
    emergency_contacts = {
        "🚨 Mumbai Police": "100",
        "🚑 Emergency Medical": "108", 
        "🚒 Fire Brigade": "101",
        "⛑️ Disaster Management": "022-22694725",
        "🌊 BMC Flood Control": "1916", 
        "🚁 Coast Guard": "1554"
    }
    
    evacuation_centers = [
        "🏥 **Hospitals**: KEM, Sion, Hinduja, Breach Candy",
        "🏫 **Education**: IIT Bombay, Mumbai University",
        "🏢 **Government**: Mantralaya, BMC Headquarters",
        "🏟️ **Sports**: NSCI Dome, Wankhede Stadium",
        "🏬 **Malls**: Phoenix Mills, Palladium (Upper Floors)"
    ]
    
    emergency_kit = [
        "💧 Water (4L per person)",
        "🥫 Food (3 days non-perishable)",
        "🔦 Flashlight + batteries",
        "📱 Phone + power bank",
        "💊 Medicines + first aid",
        "📄 Documents (waterproof)",
        "💰 Cash",
        "👕 Extra clothes"
    ]
    
    return emergency_contacts, evacuation_centers, emergency_kit

# -------------------------------
# Session State
# -------------------------------
if 'routes_computed' not in st.session_state:
    st.session_state.routes_computed = False
if 'best_match' not in st.session_state:
    st.session_state.best_match = None
if 'match_score' not in st.session_state:
    st.session_state.match_score = None
if 'routes' not in st.session_state:
    st.session_state.routes = None
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

# -------------------------------
# Sidebar
# -------------------------------
emergency_contacts, evacuation_centers, emergency_kit = get_emergency_info()

with st.sidebar:
    st.markdown("## 🚨 EMERGENCY CONTACTS")
    for service, number in emergency_contacts.items():
        if "Police" in service or "Medical" in service or "BMC" in service:
            st.markdown(f"**{service}**")
            st.markdown(f"### 📞 `{number}`")
        else:
            st.markdown(f"**{service}**: `{number}`")
    
    st.markdown("---")
    st.markdown("## 🏥 EVACUATION CENTERS")
    for center in evacuation_centers:
        st.markdown(center)
    
    st.markdown("---")
    st.markdown("## 🎒 EMERGENCY KIT")
    for item in emergency_kit:
        st.markdown(f"- {item}")

# -------------------------------
# Main Interface
# -------------------------------

# Statistics Dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📍 Areas Covered", len(flood_df))
with col2:
    critical_areas = len(flood_df[flood_df["Flood_Risk"] == "Critical"])
    st.metric("🔴 Critical Risk", critical_areas)
with col3:
    safe_areas = len(flood_df[flood_df["Flood_Risk"] == "Low"])
    st.metric("🟢 Safe Zones", safe_areas)
with col4:
    immediate = len(flood_df[flood_df["Evacuation_Priority"] == "Immediate"])
    st.metric("🚨 Immediate Evacuation", immediate)

st.markdown("---")

# Search Interface
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📍 ENTER YOUR CURRENT LOCATION")
    
    # Area selection
    with st.expander("🗺️ VIEW ALL MUMBAI AREAS BY RISK"):
        risk_order = ["Critical", "High", "Medium", "Low"]
        for risk_level in risk_order:
            areas = flood_df[flood_df["Flood_Risk"] == risk_level]["Area_Name"].tolist()
            emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[risk_level]
            
            st.markdown(f"### {emoji} {risk_level} Risk ({len(areas)} areas)")
            areas_formatted = [area.title() for area in sorted(areas)]
            area_cols = st.columns(4)
            for i, area in enumerate(areas_formatted):
                area_cols[i % 4].write(f"• {area}")
            st.markdown("---")
    
    user_region = st.text_input(
        "🔍 Type your area name:",
        value=st.session_state.user_input,
        placeholder="e.g., Bandra, Andheri, Colaba, Dadar..."
    )

with col2:
    st.markdown("### 🚨 EVACUATION CONTROL")
    
    if st.button("🔍 **FIND EVACUATION ROUTES**", type="primary", use_container_width=True):
        if not user_region.strip():
            st.error("⚠️ Please enter your location!")
        else:
            st.session_state.user_input = user_region
            with st.spinner("🔄 Finding evacuation routes..."):
                best_match, score, routes = calculate_evacuation_routes(user_region, flood_df)
                st.session_state.best_match = best_match
                st.session_state.match_score = score
                st.session_state.routes = routes
                st.session_state.routes_computed = True
    
    if st.button("🔄 Clear Results", use_container_width=True):
        st.session_state.routes_computed = False
        st.session_state.user_input = ""
        st.rerun()

# -------------------------------
# Results Display
# -------------------------------
if st.session_state.routes_computed:
    best_match = st.session_state.best_match
    score = st.session_state.match_score
    routes = st.session_state.routes
    
    if best_match is None:
        st.error(f"❌ Location '{st.session_state.user_input}' not found.")
        st.info("💡 Try nearby areas like Bandra, Andheri, Colaba, etc.")
    elif not routes:
        st.error("⚠️ No safer routes found. Contact emergency services!")
    else:
        # Current location info
        current_info = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
        risk_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[current_info["Flood_Risk"]]
        priority_emoji = {"Immediate": "🚨", "Urgent": "⚠️", "Standard": "📍", "Safe": "✅"}[current_info["Evacuation_Priority"]]
        
        # Location header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #34495e, #2c3e50); color: white; padding: 25px; border-radius: 15px; margin: 20px 0;">
            <h3 style="color: #ecf0f1; text-align: center; margin-bottom: 15px;">📍 Current Location Analysis</h3>
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Location:</strong> {best_match.title()} {risk_emoji} (Match: {score}%)</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Ward:</strong> {current_info['Ward']} | <strong>Risk:</strong> {current_info['Flood_Risk']} | <strong>Priority:</strong> {current_info['Evacuation_Priority']} {priority_emoji}</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Population:</strong> {current_info['Population_Density']:,}/km²</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Evacuation recommendation
        if current_info["Evacuation_Priority"] == "Immediate":
            st.error("🚨 **IMMEDIATE EVACUATION REQUIRED** - Leave NOW!")
        elif current_info["Evacuation_Priority"] == "Urgent": 
            st.warning("⚠️ **URGENT EVACUATION** - Prepare to leave within 30 minutes!")
        elif current_info["Evacuation_Priority"] == "Standard":
            st.info("📍 **PLAN EVACUATION** - Prepare route and emergency kit!")
        else:
            st.success("✅ **RELATIVELY SAFE** - Monitor and stay prepared!")
        
        # Routes
        st.markdown("## 🛣️ RECOMMENDED EVACUATION ROUTES")
        st.markdown(f"**Found {len(routes)} optimal routes ranked by safety:**")
        
        for i, route in enumerate(routes):
            header_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
            risk_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[route["risk_level"]]
            
            # Route header
            st.markdown(f"""
            <div style="background: {header_color}; color: white; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center;">
                <h2 style="margin: 0; color: white;">🛣️ ROUTE {i+1}: To {route['destination']} {risk_color}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Route metrics
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("📏 Distance", f"{route['distance_km']} km")
            with metric_col2:
                st.metric("⏱️ Travel Time", f"{route['eta_minutes']} min")
            with metric_col3:
                st.metric("🏛️ Ward", route['ward'])
            with metric_col4:
                st.metric("🏥 Safety Score", f"{route['capacity_score']}/100")
            
            # Route details
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown(f"""
                **🛡️ Safety Level:** {route['risk_level']}  
                **⚡ Priority:** {route['evacuation_priority']}  
                **🚀 Improvement:** +{route['safety_improvement']} points
                """)
            
            with detail_col2:
                st.markdown(f"""
                **🚗 Transport:** {route['transport']}  
                **👥 Population:** {route['population_density']:,}/km²  
                **⭐ Score:** {route['route_score']} (lower = better)
                """)
            
            st.markdown("---")
        
        # Interactive map
        st.markdown("## 🗺️ LIVE EVACUATION MAP")
        
        start_location = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
        map_center = [start_location["Latitude"], start_location["Longitude"]]
        
        evacuation_map = folium.Map(location=map_center, zoom_start=12)
        
        # Current location marker
        current_risk_color = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}[current_info["Flood_Risk"]]
        folium.Marker(
            map_center,
            popup=f"🚨 START: {best_match.title()}<br>Risk: {current_info['Flood_Risk']}",
            icon=folium.Icon(color=current_risk_color, icon='home')
        ).add_to(evacuation_map)
        
        # Route markers and lines
        colors = ['blue', 'green', 'purple', 'orange', 'red']
        for i, route in enumerate(routes):
            dest_color = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}[route["risk_level"]]
            
            folium.Marker(
                [route["destination_lat"], route["destination_lon"]],
                popup=f"🏁 SAFE ZONE {i+1}: {route['destination']}<br>Distance: {route['distance_km']}km<br>ETA: {route['eta_minutes']}min",
                icon=folium.Icon(color=dest_color, icon='star')
            ).add_to(evacuation_map)
            
            folium.PolyLine(
                [map_center, [route["destination_lat"], route["destination_lon"]]],
                color=colors[i % len(colors)],
                weight=5,
                opacity=0.8,
                popup=f"Route {i+1}: {route['destination']}"
            ).add_to(evacuation_map)
        
        st_folium(evacuation_map, width=1000, height=600)
        
        # Emergency guide
        st.markdown("---")
        st.markdown("## 🚨 EMERGENCY ACTION GUIDE")
        
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            st.markdown("### 🚨 Immediate Actions")
            st.markdown("""
            1. **🔊 Alert family** - Inform everyone immediately
            2. **📱 Share location** - Send your evacuation plan
            3. **⚡ Turn off utilities** - Gas, electricity, water
            4. **🎒 Pack essentials** - Emergency kit only
            5. **🚶‍♂️ Follow route** - Use recommended path
            6. **📞 Call help** - 100 (Police) / 1916 (BMC)
            """)
        
        with guide_col2:
            st.markdown("### 📞 Emergency Steps")
            st.markdown("""
            - **🚨 CALL 100** - Police emergency
            - **🚑 CALL 108** - Medical emergency  
            - **🌊 CALL 1916** - BMC flood control
            - **🆘 Help others** - Assist neighbors
            - **📱 Stay connected** - Keep phone charged
            - **🔄 Monitor updates** - Official announcements
            """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #2c3e50, #3498db); border-radius: 15px; color: white;">
    <h3 style="color: #ecf0f1; margin-bottom: 15px;">🌊 Mumbai Emergency Evacuation System</h3>
    <p style="color: #bdc3c7; margin-bottom: 15px;">Advanced evacuation routing for Mumbai flood emergencies</p>
    <div style="background: rgba(231, 76, 60, 0.2); padding: 15px; border-radius: 10px;">
        <h4 style="color: #e74c3c; margin-bottom: 10px;">🚨 24/7 EMERGENCY HELPLINES</h4>
        <p style="color: #ecf0f1; font-weight: bold; font-size: 18px;">
            Police: 100 | Medical: 108 | Fire: 101 | BMC: 1916
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
