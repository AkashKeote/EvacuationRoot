import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process
import math
import numpy as np
from datetime import datetime
import time

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(
    page_title="🚨 Mumbai Flood Emergency Evacuation System", 
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
    
    .route-priority-high {
        border: 4px solid #dc3545;
        background: linear-gradient(135deg, #ffe6e6, #fff0f0);
    }
    
    .route-priority-medium {
        border: 4px solid #ffc107;
        background: linear-gradient(135deg, #fff8e1, #fffbf0);
    }
    
    .route-priority-low {
        border: 4px solid #28a745;
        background: linear-gradient(135deg, #e8f5e8, #f0fff0);
    }
    
    .evacuation-stats {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border-left: 5px solid #007bff;
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
def load_comprehensive_mumbai_data():
    """Complete Mumbai flood evacuation database"""
    mumbai_data = {
        'Ward': [
            'A', 'A', 'A', 'A', 'A', 'A',
            'B', 'B', 'B', 'B', 'B',
            'C', 'C', 'C', 'C', 'C',
            'D', 'D', 'D', 'D',
            'E', 'E', 'E', 'E', 'E',
            'F/N', 'F/N', 'F/N', 'F/N', 'F/N',
            'F/S', 'F/S', 'F/S', 'F/S',
            'G/N', 'G/N', 'G/N', 'G/N', 'G/N',
            'G/S', 'G/S', 'G/S', 'G/S',
            'H/E', 'H/E', 'H/E', 'H/E',
            'H/W', 'H/W', 'H/W', 'H/W', 'H/W',
            'K/E', 'K/E', 'K/E', 'K/E', 'K/E',
            'K/W', 'K/W', 'K/W', 'K/W', 'K/W',
            'L', 'L', 'L', 'L',
            'M/E', 'M/E', 'M/E', 'M/E',
            'M/W', 'M/W', 'M/W', 'M/W',
            'N', 'N', 'N',
            'P/N', 'P/N', 'P/N', 'P/N',
            'P/S', 'P/S', 'P/S', 'P/S',
            'R/N', 'R/N', 'R/N',
            'R/S', 'R/S', 'R/S',
            'R/C', 'R/C', 'R/C',
            'S', 'S', 'S', 'S',
            'T', 'T', 'T', 'T'
        ],
        'Area_Name': [
            'colaba', 'fort', 'ballard estate', 'cuffe parade', 'navy nagar', 'apollo bunder',
            'dongri', 'mohammed ali road', 'null bazaar', 'bhendi bazaar', 'masjid bunder',
            'marine lines', 'churchgate', 'cst area', 'azad maidan', 'oval maidan',
            'girgaon', 'opera house', 'charni road', 'grant road',
            'byculla', 'mazgaon', 'cotton green', 'sewri', 'wadala',
            'sion', 'matunga', 'king circle', 'mahim', 'dharavi',
            'lower parel', 'elphinstone road', 'prabhadevi', 'worli',
            'dadar east', 'dadar west', 'shivaji park', 'mahim causeway', 'bandra east',
            'bandra west', 'khar west', 'santacruz west', 'vile parle west',
            'kalina', 'vidya vihar', 'santacruz east', 'kurla east',
            'juhu', 'andheri west', 'jogeshwari west', 'goregaon west', 'malad west',
            'andheri east', 'marol', 'sakinaka', 'ghatkopar east', 'vikhroli east',
            'versova', 'oshiwara', 'lokhandwala', 'kandivali west', 'borivali west',
            'kurla west', 'chunabhatti', 'tilak nagar', 'chembur',
            'govandi', 'mankhurd', 'cheeta camp', 'trombay',
            'chembur west', 'kanjurmarg', 'bhandup west', 'mulund west',
            'powai', 'vikhroli', 'ghatkopar west',
            'kurar village', 'malad east', 'marve', 'aksa beach',
            'goregaon east', 'aarey colony', 'film city', 'sanjay gandhi national park',
            'dahisar east', 'borivali east', 'kandivali east',
            'mira road', 'bhayander', 'vasai',
            'navi mumbai', 'thane', 'kalyan',
            'bhandup east', 'mulund east', 'nahur', 'kanjurmarg east',
            'dombivli', 'ambarnath', 'badlapur', 'karjat'
        ],
        'Latitude': [
            18.9151, 18.9354, 18.9496, 18.9225, 18.9188, 18.9220,
            18.9594, 18.9633, 18.9578, 18.9612, 18.9556,
            18.9458, 18.9346, 18.9472, 18.9487, 18.9435,
            18.9067, 18.9233, 18.9511, 18.9625,
            18.9793, 18.9637, 18.9866, 19.0049, 18.9985,
            19.0373, 19.0276, 19.0272, 19.0440, 19.0440,
            19.0172, 19.0098, 19.0144, 19.0176,
            19.0195, 19.0283, 19.0311, 19.0410, 19.0544,
            19.0544, 19.0717, 19.0833, 19.0947,
            19.0802, 19.0866, 19.0758, 19.0727,
            19.1074, 19.1182, 19.1373, 19.1613, 19.1598,
            19.1031, 19.1171, 19.1031, 19.0845, 19.1058,
            19.1100, 19.1482, 19.1336, 19.2064, 19.2365,
            19.0727, 19.0513, 19.0888, 19.0443,
            19.0572, 19.0435, 19.0654, 19.0054,
            19.0443, 19.1145, 19.1436, 19.1741,
            19.1171, 19.1058, 19.0845,
            19.1903, 19.1834, 19.2103, 19.1556,
            19.1613, 19.1758, 19.1667, 19.2103,
            19.2525, 19.2536, 19.2365,
            19.2928, 19.3017, 19.3611,
            19.2756, 19.2183, 19.0433,
            19.1436, 19.1741, 19.1567, 19.1145,
            19.2144, 19.2103, 19.3507, 18.9167
        ],
        'Longitude': [
            72.8141, 72.8354, 72.8414, 72.8312, 72.8288, 72.8320,
            72.8376, 72.8433, 72.8378, 72.8389, 72.8412,
            72.8238, 72.8284, 72.8272, 72.8356, 72.8298,
            72.8111, 72.8233, 72.8089, 72.8167,
            72.8355, 72.8443, 72.8566, 72.8397, 72.8440,
            72.8555, 72.8512, 72.8559, 72.8440, 72.8540,
            72.8337, 72.8319, 72.8244, 72.8199,
            72.8436, 72.8422, 72.8378, 72.8445, 72.8301,
            72.8301, 72.8391, 72.8344, 72.8647,
            72.8655, 72.8800, 72.8589, 72.8826,
            72.8267, 72.8463, 72.8473, 72.8407, 72.8445,
            72.8882, 72.8773, 72.8882, 72.9107, 72.9258,
            72.8189, 72.8273, 72.8436, 72.8376, 72.8322,
            72.8826, 72.8813, 72.8861, 72.8943,
            72.8999, 72.9135, 72.9089, 72.8873,
            72.8943, 72.9306, 72.9357, 72.9592,
            72.9158, 72.9258, 72.9107,
            72.8605, 72.8701, 72.7956, 72.7889,
            72.8407, 72.8756, 72.8678, 72.7956,
            72.8601, 72.8682, 72.8322,
            72.7956, 72.8156, 72.8034,
            72.8856, 72.9781, 73.1625,
            72.9357, 72.9554, 72.9268, 72.9306,
            73.0356, 73.1567, 73.2267, 73.3245
        ],
        'Flood_Risk': [
            'Critical', 'High', 'High', 'Critical', 'Critical', 'Critical',
            'Critical', 'Critical', 'Critical', 'Critical', 'High',
            'High', 'Medium', 'High', 'High', 'Medium',
            'Critical', 'High', 'High', 'High',
            'Medium', 'High', 'Low', 'High', 'Medium',
            'High', 'Low', 'High', 'Medium', 'Critical',
            'High', 'High', 'High', 'High',
            'High', 'Medium', 'Medium', 'High', 'Medium',
            'Low', 'Low', 'Low', 'Low',
            'High', 'High', 'High', 'Critical',
            'Low', 'Low', 'Low', 'Low', 'Low',
            'High', 'Critical', 'Critical', 'High', 'Medium',
            'Low', 'Medium', 'Low', 'Low', 'Low',
            'Critical', 'High', 'High', 'Medium',
            'Critical', 'Critical', 'Critical', 'Critical',
            'Medium', 'Medium', 'Medium', 'Low',
            'Medium', 'Medium', 'High',
            'High', 'High', 'Medium', 'Low',
            'Medium', 'Low', 'Low', 'Low',
            'High', 'Medium', 'Low',
            'Medium', 'Medium', 'Low',
            'Low', 'Low', 'Low',
            'Medium', 'Low', 'Low', 'Medium',
            'Low', 'Low', 'Low', 'Low'
        ],
        'Evacuation_Priority': [
            'Immediate', 'Immediate', 'Immediate', 'Immediate', 'Immediate', 'Immediate',
            'Immediate', 'Immediate', 'Immediate', 'Immediate', 'Urgent',
            'Urgent', 'Standard', 'Urgent', 'Urgent', 'Standard',
            'Immediate', 'Urgent', 'Urgent', 'Urgent',
            'Standard', 'Urgent', 'Safe', 'Urgent', 'Standard',
            'Urgent', 'Safe', 'Urgent', 'Standard', 'Immediate',
            'Urgent', 'Urgent', 'Urgent', 'Urgent',
            'Urgent', 'Standard', 'Standard', 'Urgent', 'Standard',
            'Safe', 'Safe', 'Safe', 'Safe',
            'Urgent', 'Urgent', 'Urgent', 'Immediate',
            'Safe', 'Safe', 'Safe', 'Safe', 'Safe',
            'Urgent', 'Immediate', 'Immediate', 'Urgent', 'Standard',
            'Safe', 'Standard', 'Safe', 'Safe', 'Safe',
            'Immediate', 'Urgent', 'Urgent', 'Standard',
            'Immediate', 'Immediate', 'Immediate', 'Immediate',
            'Standard', 'Standard', 'Standard', 'Safe',
            'Standard', 'Standard', 'Urgent',
            'Urgent', 'Urgent', 'Standard', 'Safe',
            'Standard', 'Safe', 'Safe', 'Safe',
            'Urgent', 'Standard', 'Safe',
            'Standard', 'Standard', 'Safe',
            'Safe', 'Safe', 'Safe',
            'Standard', 'Safe', 'Safe', 'Standard',
            'Safe', 'Safe', 'Safe', 'Safe'
        ],
        'Population_Density': [
            50000, 45000, 35000, 40000, 30000, 25000,
            55000, 60000, 45000, 50000, 40000,
            35000, 30000, 40000, 35000, 25000,
            45000, 35000, 40000, 45000,
            35000, 30000, 20000, 25000, 30000,
            40000, 25000, 35000, 30000, 80000,
            45000, 40000, 35000, 30000,
            50000, 40000, 30000, 35000, 40000,
            25000, 20000, 18000, 22000,
            35000, 30000, 40000, 70000,
            15000, 20000, 18000, 16000, 14000,
            45000, 60000, 55000, 40000, 35000,
            12000, 25000, 15000, 12000, 10000,
            65000, 50000, 45000, 35000,
            70000, 75000, 80000, 85000,
            30000, 35000, 30000, 20000,
            25000, 30000, 40000,
            35000, 40000, 20000, 8000,
            25000, 15000, 12000, 8000,
            30000, 25000, 15000,
            20000, 18000, 12000,
            10000, 8000, 6000,
            25000, 18000, 15000, 20000,
            12000, 10000, 8000, 5000
        ]
    }
    
    df = pd.DataFrame(mumbai_data)
    df["Area_Name"] = df["Area_Name"].str.strip().str.lower()
    return df

# Load data
flood_df = load_comprehensive_mumbai_data()

# -------------------------------
# Advanced Evacuation Route Calculator
# -------------------------------
def calculate_advanced_evacuation_routes(user_area, flood_df):
    """Advanced evacuation route calculation with multiple factors"""
    
    # Fuzzy matching with better tolerance
    all_areas = list(flood_df["Area_Name"].unique())
    best_match, score = process.extractOne(user_area.lower(), all_areas)
    
    if score < 40:  # More lenient matching
        return None, None, []
    
    # Get current location details
    current_location = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
    start_lat, start_lon = current_location["Latitude"], current_location["Longitude"]
    current_risk = current_location["Flood_Risk"]
    current_priority = current_location["Evacuation_Priority"]
    current_density = current_location["Population_Density"]
    
    # Find evacuation destinations based on safety criteria
    safe_zones = flood_df[
        (flood_df["Flood_Risk"].isin(["Low", "Medium"])) &
        (flood_df["Area_Name"] != best_match) &
        (flood_df["Evacuation_Priority"].isin(["Safe", "Standard"]))
    ].copy()
    
    if safe_zones.empty:
        return best_match, score, []
    
    # Calculate comprehensive route analysis
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
        
        # Risk scoring system
        risk_scores = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        safety_score = risk_scores.get(destination["Flood_Risk"], 2)
        current_risk_score = risk_scores.get(current_risk, 2)
        
        # Population density factor (lower is better for evacuation)
        density_factor = destination["Population_Density"] / 100000
        
        # Evacuation urgency multiplier
        urgency_multiplier = {"Immediate": 3, "Urgent": 2, "Standard": 1.5, "Safe": 1}[current_priority]
        
        # Calculate advanced route score
        distance_score = distance_km * 0.3
        safety_improvement = (current_risk_score - safety_score) * 2
        density_penalty = density_factor * 0.5
        
        # Final route score (lower is better)
        route_score = (distance_score - safety_improvement + density_penalty) * urgency_multiplier
        
        # Mumbai traffic-adjusted ETA calculation
        if distance_km < 3:
            base_speed = 12  # Local roads, heavy traffic
        elif distance_km < 8:
            base_speed = 18  # Main roads
        elif distance_km < 15:
            base_speed = 25  # Arterial roads
        else:
            base_speed = 35  # Highways
        
        # Emergency conditions adjustment
        emergency_speed_factor = 0.7  # Slower due to flood conditions
        actual_speed = base_speed * emergency_speed_factor
        
        # Calculate ETA with emergency buffer
        base_eta = (distance_km / actual_speed) * 60
        emergency_buffer = base_eta * 0.4  # 40% buffer for emergency conditions
        total_eta = base_eta + emergency_buffer
        
        # Capacity and safety assessment
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
            "recommended_transport": get_transport_recommendation(distance_km, current_priority)
        })
    
    # Sort by route score (best routes first)
    routes = sorted(routes, key=lambda x: x["route_score"])
    
    return best_match, score, routes[:5]  # Return top 5 routes

def get_transport_recommendation(distance_km, priority):
    """Recommend transport mode based on distance and urgency"""
    if priority == "Immediate":
        if distance_km < 2:
            return "🚶‍♂️ Walk Fast"
        elif distance_km < 8:
            return "🚲 Bicycle/Auto"
        else:
            return "🚐 Emergency Vehicle"
    elif distance_km < 1:
        return "🚶‍♂️ Walk"
    elif distance_km < 5:
        return "🚲 Bicycle"
    elif distance_km < 12:
        return "🚗 Car/Taxi"
    else:
        return "🚌 Bus/Train"

# -------------------------------
# Emergency Resources and Information
# -------------------------------
def get_emergency_resources():
    """Get comprehensive emergency information"""
    
    emergency_contacts = {
        "🚨 Mumbai Police Control Room": "100",
        "🚑 Emergency Medical Services": "108", 
        "🚒 Fire Brigade": "101",
        "⛑️ Disaster Management Cell": "022-22694725",
        "🌊 BMC Flood Control Room": "1916", 
        "🚁 Coast Guard Rescue": "1554",
        "📞 Women's Helpline": "1091",
        "👶 Child Helpline": "1098"
    }
    
    evacuation_centers = [
        "🏥 **Major Hospitals**: KEM, Sion, Hinduja, Breach Candy, Jaslok",
        "🏫 **Educational Safe Zones**: IIT Bombay, Mumbai University, TIFR",
        "🏢 **Government Buildings**: Mantralaya, BMC HQ, Collectorate",
        "🏟️ **Sports Complexes**: NSCI Dome, Brabourne Stadium, Wankhede",
        "🕌 **Community Centers**: Various Religious Centers, NGO Facilities",
        "🏬 **Shopping Malls**: Phoenix Mills, Palladium, Infiniti (Upper Floors)"
    ]
    
    survival_guide = {
        "🎒 Emergency Kit": [
            "💧 Water (4 liters per person)",
            "🥫 Non-perishable food (3 days)",
            "🔦 Waterproof flashlight + batteries",
            "📱 Fully charged phone + power bank",
            "💊 Essential medicines + first aid",
            "📄 Important documents (waterproof bag)",
            "💰 Cash in small denominations",
            "👕 Extra clothes in waterproof bag",
            "🧴 Personal hygiene items",
            "📻 Battery-powered radio"
        ],
        "🚨 Immediate Actions": [
            "🔊 Alert family members immediately",
            "📱 Share location with emergency contacts",
            "⚡ Turn off electricity and gas",
            "🚪 Lock house securely",
            "🎒 Take only essential emergency kit",
            "👥 Help elderly/disabled neighbors",
            "📞 Inform authorities of your evacuation",
            "🗺️ Follow recommended route strictly"
        ]
    }
    
    return emergency_contacts, evacuation_centers, survival_guide

# -------------------------------
# Session State Management
# -------------------------------
def initialize_session_state():
    """Initialize all session state variables"""
    default_states = {
        'routes_computed': False,
        'best_match': None,
        'match_score': None,
        'routes': None,
        'user_region_input': "",
        'emergency_mode': False,
        'last_search_time': None
    }
    
    for key, default_value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

initialize_session_state()

# -------------------------------
# Sidebar - Emergency Information
# -------------------------------
emergency_contacts, evacuation_centers, survival_guide = get_emergency_resources()

with st.sidebar:
    st.markdown("## 🚨 EMERGENCY CONTACTS")
    st.markdown("**CALL IMMEDIATELY IN EMERGENCY:**")
    
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
    
    # Real-time emergency mode toggle
    emergency_mode = st.toggle("🚨 EMERGENCY MODE", value=st.session_state.emergency_mode)
    if emergency_mode != st.session_state.emergency_mode:
        st.session_state.emergency_mode = emergency_mode
        st.rerun()

# -------------------------------
# Main Interface
# -------------------------------

# Emergency mode styling
if st.session_state.emergency_mode:
    st.markdown("""
    <div style="background: #dc3545; color: white; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center; font-weight: bold; font-size: 18px;">
        🚨 EMERGENCY MODE ACTIVATED - PRIORITY EVACUATION REQUIRED 🚨
    </div>
    """, unsafe_allow_html=True)

# Statistics Dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_areas = len(flood_df)
    st.metric("📍 Areas Covered", total_areas)

with col2:
    critical_areas = len(flood_df[flood_df["Flood_Risk"] == "Critical"])
    st.metric("🔴 Critical Risk Areas", critical_areas)

with col3:
    safe_areas = len(flood_df[flood_df["Flood_Risk"] == "Low"])
    st.metric("🟢 Safe Zones", safe_areas)

with col4:
    immediate_evacuation = len(flood_df[flood_df["Evacuation_Priority"] == "Immediate"])
    st.metric("🚨 Immediate Evacuation", immediate_evacuation)

st.markdown("---")

# Main search interface
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📍 ENTER YOUR CURRENT LOCATION")
    
    # Available areas organized by risk level
    with st.expander("🗺️ VIEW ALL MUMBAI AREAS BY RISK LEVEL"):
        risk_order = ["Critical", "High", "Medium", "Low"]
        for risk_level in risk_order:
            areas_in_risk = flood_df[flood_df["Flood_Risk"] == risk_level]["Area_Name"].tolist()
            emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[risk_level]
            
            st.markdown(f"### {emoji} {risk_level} Risk Areas ({len(areas_in_risk)} locations)")
            
            # Show areas in columns
            areas_formatted = [area.title() for area in sorted(areas_in_risk)]
            area_cols = st.columns(4)
            for i, area in enumerate(areas_formatted):
                area_cols[i % 4].write(f"• {area}")
            st.markdown("---")
    
    # Search input
    user_region = st.text_input(
        "🔍 Search your area (Type area name):",
        value=st.session_state.user_region_input,
        placeholder="e.g., Bandra, Andheri, Colaba, Dadar, Powai...",
        help="Enter your current location to find the best evacuation routes"
    )
    
    # Quick location buttons for common areas
    st.markdown("**Quick Select Popular Areas:**")
    quick_areas = ["Bandra West", "Andheri East", "Colaba", "Dadar West", "Powai", "Kurla", "Malad West", "Borivali West"]
    quick_cols = st.columns(4)
    
    for i, area in enumerate(quick_areas):
        if quick_cols[i % 4].button(area, key=f"quick_{area}"):
            st.session_state.user_region_input = area.lower()
            st.rerun()

with col2:
    st.markdown("### 🚨 EVACUATION CONTROL")
    
    search_button_text = "🔍 **FIND EVACUATION ROUTES**" if not st.session_state.emergency_mode else "🚨 **EMERGENCY EVACUATION**"
    
    if st.button(search_button_text, type="primary", use_container_width=True):
        if not user_region.strip():
            st.error("⚠️ Please enter your current location!")
            st.session_state.routes_computed = False
        else:
            st.session_state.user_region_input = user_region
            st.session_state.last_search_time = datetime.now()
            
            with st.spinner("🔄 Calculating optimal evacuation routes..."):
                # Add realistic delay for processing
                time.sleep(2)
                best_match, score, routes = calculate_advanced_evacuation_routes(user_region, flood_df)
                
                st.session_state.best_match = best_match
                st.session_state.match_score = score
                st.session_state.routes = routes
                st.session_state.routes_computed = True
    
    if st.button("🔄 Clear Results", use_container_width=True):
        for key in ['routes_computed', 'best_match', 'match_score', 'routes', 'user_region_input']:
            st.session_state[key] = False if key == 'routes_computed' else "" if key == 'user_region_input' else None
        st.rerun()
    
    if st.session_state.last_search_time:
        time_since_search = datetime.now() - st.session_state.last_search_time
        st.caption(f"Last search: {time_since_search.seconds}s ago")

# -------------------------------
# Results Display
# -------------------------------
if st.session_state.routes_computed:
    best_match = st.session_state.best_match
    score = st.session_state.match_score
    routes = st.session_state.routes
    
    if best_match is None:
        st.error(f"❌ Location '{st.session_state.user_region_input}' not found in Mumbai evacuation database.")
        st.info("💡 **Suggestions:** Try searching for nearby major areas like Bandra, Andheri, Colaba, etc.")
        
        # Suggest similar areas
        all_areas = flood_df["Area_Name"].tolist()
        suggestions = process.extract(st.session_state.user_region_input.lower(), all_areas, limit=5)
        if suggestions:
            st.markdown("**Did you mean:**")
            for suggestion, score in suggestions:
                if st.button(f"📍 {suggestion.title()} ({score}% match)", key=f"suggest_{suggestion}"):
                    st.session_state.user_region_input = suggestion
                    st.rerun()
                    
    elif not routes:
        st.error("⚠️ No safer evacuation routes found from your current location.")
        st.info("🏥 **Immediate Action:** Contact emergency services at **100** or **1916**")
        
    else:
        # Current location information
        current_info = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
        risk_emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[current_info["Flood_Risk"]]
        priority_emoji = {"Immediate": "🚨", "Urgent": "⚠️", "Standard": "📍", "Safe": "✅"}[current_info["Evacuation_Priority"]]
        
        # Location status header
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #34495e, #2c3e50); color: white; padding: 25px; border-radius: 15px; margin: 20px 0; box-shadow: 0 6px 12px rgba(0,0,0,0.2);">
            <h3 style="color: #ecf0f1; margin-bottom: 15px; text-align: center;">📍 Current Location Analysis</h3>
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Location:</strong> {best_match.title()} {risk_emoji} (Match: {score}%)</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Ward:</strong> {current_info['Ward']} | <strong>Risk Level:</strong> {current_info['Flood_Risk']} | <strong>Priority:</strong> {current_info['Evacuation_Priority']} {priority_emoji}</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Population Density:</strong> {current_info['Population_Density']:,} people/km² | <strong>Evacuation Urgency:</strong> {current_info['Evacuation_Priority']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Evacuation recommendation based on risk
        if current_info["Evacuation_Priority"] == "Immediate":
            st.error("🚨 **IMMEDIATE EVACUATION REQUIRED** - Leave now with emergency kit!")
        elif current_info["Evacuation_Priority"] == "Urgent": 
            st.warning("⚠️ **URGENT EVACUATION RECOMMENDED** - Prepare to leave within 30 minutes!")
        elif current_info["Evacuation_Priority"] == "Standard":
            st.info("📍 **STANDARD EVACUATION** - Plan evacuation route and prepare kit!")
        else:
            st.success("✅ **RELATIVELY SAFE AREA** - Monitor conditions and be prepared!")
        
        # Route recommendations
        st.markdown("## 🛣️ RECOMMENDED EVACUATION ROUTES")
        st.markdown(f"**Found {len(routes)} optimal evacuation routes ranked by safety and accessibility:**")
        
        for i, route in enumerate(routes):
            route_priority = "high" if i == 0 else "medium" if i == 1 else "low"
            risk_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[route["risk_level"]]
            
            # Route header
            header_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
            
            st.markdown(f"""
            <div style="border: 4px solid {header_color}; border-radius: 15px; padding: 25px; margin: 20px 0; background: linear-gradient(135deg, #f8f9fa, #e9ecef); box-shadow: 0 6px 12px rgba(0,0,0,0.1);">
                <div style="background: {header_color}; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
                    <h2 style="margin: 0; color: white;">🛣️ ROUTE {i+1}: To {route['destination']} {risk_color}</h2>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Route details in Streamlit columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📏 Distance", f"{route['distance_km']} km")
            with col2:
                st.metric("⏱️ Travel Time", f"{route['eta_minutes']} min")
            with col3:
                st.metric("🏛️ Ward", route['ward'])
            with col4:
                st.metric("🏥 Safety Score", f"{route['capacity_score']}/100")
            
            # Additional details
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown(f"""
                **🛡️ Safety Level:** {route['risk_level']}  
                **⚡ Priority:** {route['evacuation_priority']}  
                **🚀 Safety Improvement:** +{route['safety_improvement']} points
                """)
            
            with detail_col2:
                st.markdown(f"""
                **🚗 Transport:** {route['recommended_transport']}  
                **👥 Population:** {route['population_density']:,}/km²  
                **⭐ Route Score:** {route['route_score']} (lower is better)
                """)
            
            st.markdown("---")
        
        # Interactive evacuation map
        st.markdown("## 🗺️ LIVE EVACUATION MAP")
        st.markdown("**Interactive map showing your location and all recommended evacuation routes:**")
        
        # Create the map
        start_location = flood_df[flood_df["Area_Name"] == best_match].iloc[0]
        map_center = [start_location["Latitude"], start_location["Longitude"]]
        
        # Create map with emergency styling
        evacuation_map = folium.Map(
            location=map_center,
            zoom_start=12,
            tiles='OpenStreetMap'
        )
        
        # Add current location marker
        current_risk_color = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}[current_info["Flood_Risk"]]
        folium.Marker(
            map_center,
            popup=folium.Popup(f"""
                <div style='width: 200px; text-align: center;'>
                    <h4>🚨 CURRENT LOCATION</h4>
                    <p><strong>{best_match.title()}</strong></p>
                    <p>Risk: {current_info['Flood_Risk']}</p>
                    <p>Priority: {current_info['Evacuation_Priority']}</p>
                    <p>Population: {current_info['Population_Density']:,}/km²</p>
                </div>
            """, max_width=300),
            icon=folium.Icon(color=current_risk_color, icon='home', prefix='fa', icon_size=(30, 30))
        ).add_to(evacuation_map)
        
        # Add evacuation route markers and lines
        route_colors = ['blue', 'green', 'purple', 'orange', 'red']
        for i, route in enumerate(routes):
            # Destination marker
            dest_color = {"Critical": "red", "High": "orange", "Medium": "yellow", "Low": "green"}[route["risk_level"]]
            
            folium.Marker(
                [route["destination_lat"], route["destination_lon"]],
                popup=folium.Popup(f"""
                    <div style='width: 250px; text-align: center;'>
                        <h4>🏁 EVACUATION ZONE {i+1}</h4>
                        <p><strong>{route['destination']}</strong></p>
                        <p>📏 Distance: {route['distance_km']} km</p>
                        <p>⏱️ ETA: {route['eta_minutes']} minutes</p>
                        <p>🛡️ Safety: {route['risk_level']}</p>
                        <p>🚗 Transport: {route['recommended_transport']}</p>
                        <p>⭐ Score: {route['route_score']}</p>
                    </div>
                """, max_width=350),
                icon=folium.Icon(color=dest_color, icon='star', prefix='fa')
            ).add_to(evacuation_map)
            
            # Route line
            folium.PolyLine(
                [map_center, [route["destination_lat"], route["destination_lon"]]],
                color=route_colors[i % len(route_colors)],
                weight=6,
                opacity=0.8,
                popup=f"Route {i+1}: {route['destination']} - {route['distance_km']}km, {route['eta_minutes']}min"
            ).add_to(evacuation_map)
        
        # Display the map
        st_folium(evacuation_map, width=1000, height=600)
        
        # Emergency action guide
        st.markdown("---")
        st.markdown("## 🚨 EMERGENCY ACTION GUIDE")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎒 Emergency Kit Checklist")
            for item in survival_guide["🎒 Emergency Kit"]:
                st.markdown(f"- {item}")
        
        with col2:
            st.markdown("### 🚨 Immediate Actions")
            for action in survival_guide["🚨 Immediate Actions"]:
                st.markdown(f"- {action}")
        
        # Additional emergency information
        if st.session_state.emergency_mode:
            st.markdown("""
            <div style="background: #dc3545; color: white; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h4>🚨 EMERGENCY MODE - CRITICAL INSTRUCTIONS</h4>
                <ul>
                    <li><strong>EVACUATE IMMEDIATELY</strong> - Do not delay</li>
                    <li><strong>CALL 100 or 1916</strong> - Inform authorities of your evacuation</li>
                    <li><strong>FOLLOW ROUTE 1</strong> - Highest priority route recommended</li>
                    <li><strong>STAY TOGETHER</strong> - Keep family/group together</li>
                    <li><strong>AVOID FLOODED ROADS</strong> - Even if they seem passable</li>
                    <li><strong>CONTACT FAMILY</strong> - Share your evacuation route</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# Footer with emergency information
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #2c3e50, #3498db); border-radius: 15px; color: white; margin-top: 40px;">
    <h3 style="color: #ecf0f1; margin-bottom: 15px;">🌊 Mumbai Flood Emergency Evacuation System</h3>
    <p style="color: #bdc3c7; margin-bottom: 15px; font-size: 16px;">Advanced AI-powered evacuation routing for life-saving emergency response</p>
    <div style="background: rgba(231, 76, 60, 0.2); padding: 15px; border-radius: 10px; margin: 15px 0;">
        <h4 style="color: #e74c3c; margin-bottom: 10px;">🚨 24/7 EMERGENCY HELPLINES</h4>
        <p style="color: #ecf0f1; font-weight: bold; font-size: 18px;">
            Police: 100 | Medical: 108 | Fire: 101 | BMC Flood Control: 1916
        </p>
    </div>
    <p style="color: #95a5a6; font-size: 14px;">Stay Safe | Stay Informed | Save Lives</p>
</div>
""", unsafe_allow_html=True)
