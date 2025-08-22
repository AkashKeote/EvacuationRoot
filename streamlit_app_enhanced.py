import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from fuzzywuzzy import process
import math
import numpy as np
from datetime import datetime
import json
from folium.plugins import MiniMap, MarkerCluster
import branca.colormap as cm

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
    /* Force dark theme for all components */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Main header styling */
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
    
    /* Emergency alert styling */
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
    
    /* Force dark background for metrics */
    .stMetric {
        background: #1e2126 !important;
        color: #ffffff !important;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border: 1px solid #333;
    }
    
    /* Metric labels and values */
    .stMetric > div {
        color: #ffffff !important;
    }
    
    .stMetric label {
        color: #ffffff !important;
    }
    
    /* Route cards styling */
    div[data-testid="metric-container"] {
        background: #1e2126 !important;
        border: 1px solid #333 !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }
    
    /* All text in metrics should be white */
    div[data-testid="metric-container"] * {
        color: #ffffff !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #262730;
    }
    
    /* Column containers */
    .element-container {
        background: transparent;
    }
    
    /* Force white text everywhere */
    .stMarkdown, .stText, p, span, div {
        color: #ffffff !important;
    }
    
    /* Input fields */
    .stTextInput input {
        background-color: #1e2126 !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #dc3545, #c82333) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    /* Shelter info styling */
    .shelter-info {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        border: 2px solid #3498db;
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
# Mumbai Infrastructure Data
# -------------------------------
@st.cache_data
def load_infrastructure_data():
    """Load hospitals, bridges, and highways data"""
    
    # Major Hospitals in Mumbai
    hospitals_data = {
        'Name': [
            'KEM Hospital', 'Sion Hospital', 'Hinduja Hospital', 'Breach Candy Hospital',
            'Jaslok Hospital', 'Lilavati Hospital', 'Kokilaben Hospital', 'Fortis Hospital',
            'Wockhardt Hospital', 'Holy Family Hospital', 'Tata Memorial Hospital',
            'BYL Nair Hospital', 'Grant Medical College', 'Cama Hospital',
            'JJ Hospital', 'Rajawadi Hospital', 'Shatabdi Hospital', 'Bombay Hospital',
            'Asian Heart Institute', 'Global Hospital', 'Nanavati Hospital',
            'Cooper Hospital', 'Lokmanya Tilak Hospital', 'King Edward Memorial Hospital'
        ],
        'Latitude': [
            19.0273, 19.0435, 19.0176, 18.9658, 18.9596, 19.0544, 19.1276, 19.1171,
            19.0847, 19.0544, 19.0435, 18.9793, 18.9637, 18.9472, 18.9594, 19.1171,
            19.0845, 18.9354, 19.0802, 19.0176, 19.1074, 19.0949, 19.0440, 19.0273
        ],
        'Longitude': [
            72.8555, 72.8943, 72.8199, 72.8111, 72.8376, 72.8301, 72.8322, 72.8882,
            72.8773, 72.8301, 72.8943, 72.8355, 72.8443, 72.8272, 72.8376, 72.8882,
            72.9107, 72.8354, 72.8655, 72.8199, 72.8267, 72.8566, 72.8440, 72.8555
        ],
        'Type': ['Government', 'Government', 'Private', 'Private', 'Private', 'Private',
                 'Private', 'Private', 'Private', 'Private', 'Government', 'Government',
                 'Government', 'Government', 'Government', 'Government', 'Private',
                 'Private', 'Private', 'Private', 'Private', 'Government', 'Government', 'Government'],
        'Emergency_Services': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes',
                              'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes',
                              'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
        'Capacity': [1200, 800, 600, 400, 350, 500, 750, 400, 350, 300, 629, 900,
                    1000, 500, 800, 600, 400, 750, 300, 400, 600, 800, 1200, 1200]
    }
    
    # Major Bridges in Mumbai
    bridges_data = {
        'Name': [
            'Bandra-Worli Sea Link', 'Rajiv Gandhi Sea Link', 'Mahim Causeway',
            'King Circle Bridge', 'Tilak Bridge', 'Chembur Bridge', 'Mulund Bridge',
            'Gokhale Bridge', 'Andheri Bridge', 'Kandivali Bridge', 'Dahisar Bridge',
            'Vashi Bridge', 'Airoli Bridge', 'Thane Creek Bridge', 'Mumbra Bridge',
            'Ghatkopar Bridge', 'Kurla Bridge', 'Santacruz Bridge', 'Khar Bridge',
            'Bandra Bridge', 'JJ Flyover', 'Eastern Express Highway Bridge'
        ],
        'Latitude': [
            19.0336, 19.0336, 19.0440, 19.0272, 19.0195, 19.0443, 19.1741,
            19.1074, 19.1182, 19.2365, 19.2525, 19.0758, 19.1567, 19.2183,
            19.2144, 19.0845, 19.0727, 19.0833, 19.0717, 19.0544, 18.9594, 19.0727
        ],
        'Longitude': [
            72.8199, 72.8199, 72.8440, 72.8559, 72.8436, 72.8943, 72.9592,
            72.8267, 72.8463, 72.8322, 72.8601, 72.8589, 72.9268, 72.9781,
            73.0356, 72.9107, 72.8826, 72.8344, 72.8391, 72.8301, 72.8376, 72.8826
        ],
        'Type': ['Sea Link', 'Sea Link', 'Causeway', 'Railway Bridge', 'Road Bridge',
                'Road Bridge', 'Highway Bridge', 'Railway Bridge', 'Road Bridge',
                'Highway Bridge', 'Highway Bridge', 'Highway Bridge', 'Highway Bridge',
                'Highway Bridge', 'Railway Bridge', 'Road Bridge', 'Road Bridge',
                'Road Bridge', 'Road Bridge', 'Road Bridge', 'Flyover', 'Highway Bridge'],
        'Emergency_Access': ['Yes', 'Yes', 'Yes', 'Limited', 'Yes', 'Yes', 'Yes',
                            'Limited', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes',
                            'Limited', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
        'Flood_Resistance': ['High', 'High', 'Medium', 'Medium', 'Medium', 'High', 'High',
                            'Medium', 'Medium', 'High', 'High', 'High', 'High', 'High',
                            'Medium', 'Medium', 'Medium', 'Medium', 'Medium', 'Medium', 'Low', 'High']
    }
    
    # Major Highways in Mumbai
    highways_data = {
        'Name': [
            'Western Express Highway', 'Eastern Express Highway', 'Mumbai-Pune Expressway',
            'Mumbai-Nashik Highway', 'Sion-Panvel Highway', 'Link Road', 'SV Road',
            'Jogeshwari-Vikhroli Link Road', 'Mumbai-Ahmedabad Highway', 'Ghodbunder Road',
            'Palm Beach Road', 'Mumbai Trans Harbour Link', 'Coastal Road Project',
            'Andheri-Kurla Road', 'LBS Marg', 'Dr. Annie Besant Road'
        ],
        'Start_Lat': [19.2525, 19.0845, 19.0176, 19.2525, 19.0435, 19.0544, 19.0544,
                     19.1373, 19.2525, 19.2928, 19.0758, 19.0336, 18.9151, 19.1182, 19.0440, 19.0176],
        'Start_Lon': [72.8601, 72.9107, 72.8199, 72.8601, 72.8943, 72.8301, 72.8301,
                     72.8473, 72.8601, 72.7956, 72.8589, 72.8199, 72.8141, 72.8463, 72.8440, 72.8199],
        'End_Lat': [18.9151, 19.2183, 18.5074, 20.0111, 19.0758, 19.2365, 19.2365,
                   19.1031, 23.0225, 19.3611, 19.2756, 19.0758, 19.2525, 19.1031, 19.1741, 19.0833],
        'End_Lon': [72.8141, 72.9781, 73.5074, 73.7900, 72.8589, 72.8322, 72.8322,
                   72.8882, 72.5714, 72.8034, 72.8856, 72.8589, 72.8601, 72.8882, 72.9592, 72.8344],
        'Type': ['Highway', 'Highway', 'Expressway', 'Highway', 'Highway', 'Arterial Road',
                'Arterial Road', 'Link Road', 'Highway', 'Highway', 'Highway', 'Sea Link',
                'Coastal Road', 'Arterial Road', 'Arterial Road', 'Arterial Road'],
        'Emergency_Route': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes',
                           'Yes', 'Yes', 'Yes', 'Yes', 'Under Construction', 'Yes', 'Yes', 'Yes'],
        'Flood_Prone': ['Medium', 'High', 'Low', 'Low', 'High', 'High', 'High', 'Medium',
                       'Low', 'Medium', 'Medium', 'Low', 'Low', 'High', 'High', 'High']
    }
    
    return pd.DataFrame(hospitals_data), pd.DataFrame(bridges_data), pd.DataFrame(highways_data)

# -------------------------------
# Comprehensive Mumbai Flood Data with Shelter Types
# -------------------------------
@st.cache_data
def load_mumbai_data():
    """Complete Mumbai flood evacuation database with shelter information"""
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
        ],
        'Shelter_Type': [
            'Relief Camp', 'Government Building', 'School', 'Relief Camp', 'Naval Base',
            'Community Center', 'Religious Center', 'Community Hall', 'Religious Center',
            'Hotel', 'Government Building', 'Railway Station', 'Government Building',
            'Community Center', 'Hotel', 'Railway Station',
            'Hospital', 'Port Area', 'Industrial Shelter', 'Industrial Area',
            'School', 'College', 'Railway Station', 'School',
            'Corporate Building', 'Railway Station', 'Religious Center',
            'Railway Station', 'Sports Complex', 'Sports Complex', 'Community Center',
            'Hotel', 'Mall/Hotel', 'Mall/Hotel', 'Mall/Hotel',
            'College', 'College', 'Mall/Hotel', 'School',
            'Resort/Hotel', 'Mall/Hotel', 'Mall/Hotel', 'Mall/Hotel',
            'Corporate Building', 'IT Park', 'IT Park', 'Railway Station',
            'Resort/Hotel', 'Mall/Hotel', 'Resort/Hotel', 'Railway Station',
            'School', 'Community Center', 'Hospital',
            'Community Center', 'Industrial Area', 'Industrial Area',
            'Hospital', 'IT Park', 'Residential Complex',
            'IT Park', 'IT Park',
            'Community Center', 'IT Park', 'Resort/Hotel',
            'IT Park', 'Forest Rest House', 'National Park Facility',
            'Railway Station', 'Railway Station',
            'Railway Station', 'Railway Station',
            'Railway Station', 'Railway Station',
            'Railway Station', 'Railway Station', 'Railway Station',
            'Railway Station', 'Railway Station', 'Hill Station Resort'
        ],
        'Shelter_Capacity': [
            5000, 3000, 2000, 4000, 1500,
            6000, 4000, 3000, 3500,
            2500, 2000, 8000, 3000,
            4000, 2500, 6000,
            3000, 2000, 1500, 2500,
            3500, 4000, 8000, 3000,
            5000, 7000, 3000,
            10000, 5000, 4000, 8000,
            3000, 6000, 7000, 6000,
            4000, 5000, 6000, 4000,
            3000, 8000, 7000, 6000,
            6000, 8000, 9000, 8000,
            4000, 8000, 5000, 5000,
            7000, 5000, 4000,
            8000, 6000, 5000,
            5000, 7000, 6000,
            6000, 7000,
            4000, 7000, 3000,
            6000, 2000, 1500,
            7000, 4000,
            6000, 5000,
            4000, 3000,
            6000, 5000, 4000,
            4000, 3000, 2000
        ]
    }
    
    df = pd.DataFrame(mumbai_data)
    df["Area_Name"] = df["Area_Name"].str.strip().str.lower()
    return df

# Load data
flood_df = load_mumbai_data()

# -------------------------------
# Nearest Infrastructure Finder
# -------------------------------
def find_nearest_infrastructure(user_location, flood_df):
    """Find nearest hospitals, bridges, and highways"""
    
    hospitals_df, bridges_df, highways_df = load_infrastructure_data()
    
    # Get user coordinates
    user_data = flood_df[flood_df["Area_Name"] == user_location].iloc[0]
    user_lat, user_lon = user_data["Latitude"], user_data["Longitude"]
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate haversine distance"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371 * c  # Earth radius in km
    
    # Find nearest hospitals
    hospitals_df['distance'] = hospitals_df.apply(
        lambda row: calculate_distance(user_lat, user_lon, row['Latitude'], row['Longitude']), 
        axis=1
    )
    nearest_hospitals = hospitals_df.nsmallest(5, 'distance')
    
    # Find nearest bridges
    bridges_df['distance'] = bridges_df.apply(
        lambda row: calculate_distance(user_lat, user_lon, row['Latitude'], row['Longitude']), 
        axis=1
    )
    nearest_bridges = bridges_df.nsmallest(5, 'distance')
    
    # Find nearest highways
    highways_df['start_distance'] = highways_df.apply(
        lambda row: calculate_distance(user_lat, user_lon, row['Start_Lat'], row['Start_Lon']), 
        axis=1
    )
    highways_df['end_distance'] = highways_df.apply(
        lambda row: calculate_distance(user_lat, user_lon, row['End_Lat'], row['End_Lon']), 
        axis=1
    )
    highways_df['min_distance'] = highways_df[['start_distance', 'end_distance']].min(axis=1)
    nearest_highways = highways_df.nsmallest(5, 'min_distance')
    
    return nearest_hospitals, nearest_bridges, nearest_highways

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
            "transport": transport,
            "shelter_type": destination["Shelter_Type"],
            "shelter_capacity": destination["Shelter_Capacity"]
        })
    
    routes = sorted(routes, key=lambda x: x["route_score"])
    return best_match, score, routes[:5]

# -------------------------------
# Enhanced Map with Legend and Dark Theme
# -------------------------------
def create_advanced_evacuation_map(current_location, routes, flood_df):
    """Create an advanced evacuation map with all infrastructure"""
    
    # Load infrastructure data
    hospitals_df, bridges_df, highways_df = load_infrastructure_data()
    
    # Map center
    start_location = flood_df[flood_df["Area_Name"] == current_location].iloc[0]
    map_center = [start_location["Latitude"], start_location["Longitude"]]
    
    # Create map with dark tiles
    evacuation_map = folium.Map(
        location=map_center, 
        zoom_start=11,
        tiles=None
    )
    
    # Add dark tile layer
    folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>',
        name='Dark Theme',
        overlay=False,
        control=True
    ).add_to(evacuation_map)
    
    # Add OpenStreetMap as backup
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='Standard Map',
        overlay=False,
        control=True
    ).add_to(evacuation_map)
    
    # Risk level colors
    risk_colors = {
        'Critical': '#FF0000',
        'High': '#FF8C00', 
        'Medium': '#FFD700',
        'Low': '#32CD32'
    }
    
    # Shelter type icons
    shelter_icons = {
        'Relief Camp': 'home',
        'Government Building': 'building',
        'School': 'graduation-cap',
        'Hospital': 'plus-square',
        'Railway Station': 'train',
        'Community Center': 'users',
        'Religious Center': 'star',
        'Hotel': 'bed',
        'Mall/Hotel': 'shopping-cart',
        'IT Park': 'laptop',
        'Sports Complex': 'futbol',
        'Naval Base': 'anchor',
        'Corporate Building': 'building',
        'Industrial Area': 'industry',
        'Resort/Hotel': 'palm-tree',
        'College': 'university',
        'Port Area': 'ship',
        'Community Hall': 'home',
        'Industrial Shelter': 'wrench',
        'Residential Complex': 'home',
        'Forest Rest House': 'tree',
        'National Park Facility': 'tree',
        'Hill Station Resort': 'mountain'
    }
    
    # Create feature groups for different layers
    hospitals_group = folium.FeatureGroup(name="🏥 Hospitals", show=True)
    bridges_group = folium.FeatureGroup(name="🌉 Bridges", show=True)
    highways_group = folium.FeatureGroup(name="🛣️ Highways", show=True)
    shelters_group = folium.FeatureGroup(name="🏠 Shelters", show=True)
    routes_group = folium.FeatureGroup(name="🛣️ Evacuation Routes", show=True)
    
    # Add hospitals to map
    for _, hospital in hospitals_df.iterrows():
        hospital_color = 'red' if hospital['Type'] == 'Government' else 'blue'
        folium.Marker(
            [hospital['Latitude'], hospital['Longitude']],
            popup=f"""
            <div style="width: 280px;">
                <h4>🏥 {hospital['Name']}</h4>
                <b>Type:</b> {hospital['Type']}<br>
                <b>Emergency Services:</b> {hospital['Emergency_Services']}<br>
                <b>Capacity:</b> {hospital['Capacity']} beds<br>
                <b>24/7 Emergency:</b> Available
            </div>
            """,
            icon=folium.Icon(
                color=hospital_color,
                icon='plus-square',
                prefix='fa'
            )
        ).add_to(hospitals_group)
    
    # Add bridges to map
    for _, bridge in bridges_df.iterrows():
        bridge_color = 'green' if bridge['Emergency_Access'] == 'Yes' else 'orange'
        resistance_color = {'High': '#00FF00', 'Medium': '#FFFF00', 'Low': '#FF0000'}[bridge['Flood_Resistance']]
        
        folium.CircleMarker(
            [bridge['Latitude'], bridge['Longitude']],
            radius=8,
            popup=f"""
            <div style="width: 280px;">
                <h4>🌉 {bridge['Name']}</h4>
                <b>Type:</b> {bridge['Type']}<br>
                <b>Emergency Access:</b> {bridge['Emergency_Access']}<br>
                <b>Flood Resistance:</b> {bridge['Flood_Resistance']}<br>
                <b>Status:</b> Operational
            </div>
            """,
            color='white',
            fillColor=resistance_color,
            fillOpacity=0.8,
            weight=3
        ).add_to(bridges_group)
    
    # Add highways to map with better color coding
    for _, highway in highways_df.iterrows():
        # Use different colors for better distinction
        if highway['Flood_Prone'] == 'Low':
            highway_color = '#00BFFF'  # Deep Sky Blue for low flood risk
        elif highway['Flood_Prone'] == 'Medium':
            highway_color = '#FFD700'  # Gold for medium flood risk
        else:
            highway_color = '#FF4500'  # Orange Red for high flood risk
        
        # Make emergency routes thicker
        highway_weight = 8 if highway['Emergency_Route'] == 'Yes' else 5
        
        folium.PolyLine(
            [[highway['Start_Lat'], highway['Start_Lon']], [highway['End_Lat'], highway['End_Lon']]],
            color=highway_color,
            weight=highway_weight,
            opacity=0.8,
            popup=f"""
            <div style="width: 280px;">
                <h4>🛣️ {highway['Name']}</h4>
                <b>Type:</b> {highway['Type']}<br>
                <b>Emergency Route:</b> {highway['Emergency_Route']}<br>
                <b>Flood Risk:</b> {highway['Flood_Prone']}<br>
                <b>Status:</b> Active<br>
                <b>Line Color:</b> {highway['Flood_Prone']} Risk
            </div>
            """
        ).add_to(highways_group)
    
    # Current location marker
    current_info = flood_df[flood_df["Area_Name"] == current_location].iloc[0]
    current_risk_color = risk_colors.get(current_info["Flood_Risk"], '#FF0000')
    
    folium.Marker(
        map_center,
        popup=f"""
        <div style="width: 250px;">
            <h4>🚨 YOUR LOCATION</h4>
            <b>Area:</b> {current_location.title()}<br>
            <b>Ward:</b> {current_info['Ward']}<br>
            <b>Risk:</b> {current_info['Flood_Risk']}<br>
            <b>Priority:</b> {current_info['Evacuation_Priority']}<br>
            <b>Shelter:</b> {current_info['Shelter_Type']}<br>
            <b>Capacity:</b> {current_info['Shelter_Capacity']:,} people
        </div>
        """,
        icon=folium.Icon(
            color='red', 
            icon='home', 
            prefix='fa'
        )
    ).add_to(evacuation_map)
    
    # Route markers and lines with distinct colors
    route_colors = ['#8A2BE2', '#FF1493', '#00CED1', '#FF8C00', '#32CD32']  # Purple, DeepPink, DarkTurquoise, DarkOrange, LimeGreen
    route_names = ['Primary Route', 'Secondary Route', 'Alternate Route', 'Backup Route', 'Emergency Route']
    
    for i, route in enumerate(routes):
        dest_color = 'green' if route["risk_level"] == 'Low' else 'yellow'
        shelter_icon = shelter_icons.get(route["shelter_type"], 'star')
        
        # Destination marker
        folium.Marker(
            [route["destination_lat"], route["destination_lon"]],
            popup=f"""
            <div style="width: 300px;">
                <h4>🏁 {route_names[i % len(route_names)]}</h4>
                <b>Destination:</b> {route['destination']}<br>
                <b>Ward:</b> {route['ward']}<br>
                <b>Distance:</b> {route['distance_km']} km<br>
                <b>ETA:</b> {route['eta_minutes']} min<br>
                <b>Risk Level:</b> {route['risk_level']}<br>
                <b>Transport:</b> {route['transport']}<br>
                <b>Shelter Type:</b> {route['shelter_type']}<br>
                <b>Capacity:</b> {route['shelter_capacity']:,} people<br>
                <b>Safety Score:</b> {route['capacity_score']}/100
            </div>
            """,
            icon=folium.Icon(
                color=dest_color, 
                icon=shelter_icon, 
                prefix='fa'
            )
        ).add_to(routes_group)
        
        # Route line with distinct colors and patterns
        folium.PolyLine(
            [map_center, [route["destination_lat"], route["destination_lon"]]],
            color=route_colors[i % len(route_colors)],
            weight=6,
            opacity=0.9,
            dash_array='10,5' if i > 2 else None,  # Dashed lines for backup routes
            popup=f"{route_names[i % len(route_names)]}: {route['destination']} ({route['distance_km']} km)"
        ).add_to(routes_group)
    
    # Add all Mumbai areas as markers
    for _, area in flood_df.iterrows():
        if area["Area_Name"] != current_location:
            area_color = 'green' if area["Flood_Risk"] == 'Low' else 'orange' if area["Flood_Risk"] == 'Medium' else 'red'
            area_icon = shelter_icons.get(area["Shelter_Type"], 'circle')
            
            folium.CircleMarker(
                [area["Latitude"], area["Longitude"]],
                radius=5,
                popup=f"""
                <div style="width: 250px;">
                    <h4>{area['Area_Name'].title()}</h4>
                    <b>Ward:</b> {area['Ward']}<br>
                    <b>Risk:</b> {area['Flood_Risk']}<br>
                    <b>Priority:</b> {area['Evacuation_Priority']}<br>
                    <b>Shelter:</b> {area['Shelter_Type']}<br>
                    <b>Capacity:</b> {area['Shelter_Capacity']:,}<br>
                    <b>Population:</b> {area['Population_Density']:,}/km²
                </div>
                """,
                color='white',
                fillColor=risk_colors.get(area["Flood_Risk"], '#FFD700'),
                fillOpacity=0.7,
                weight=2
            ).add_to(shelters_group)
    
    # Add feature groups to map
    hospitals_group.add_to(evacuation_map)
    bridges_group.add_to(evacuation_map)
    highways_group.add_to(evacuation_map)
    shelters_group.add_to(evacuation_map)
    routes_group.add_to(evacuation_map)
    
    # Add minimap with proper attribution
    minimap_tile_layer = folium.TileLayer(
        tiles='https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png',
        attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
        name='Dark MiniMap'
    )
    
    minimap = MiniMap(
        tile_layer=minimap_tile_layer,
        position='bottomright',
        width=150,
        height=150,
        zoom_level_offset=-5
    )
    evacuation_map.add_child(minimap)
    
    # Enhanced legend HTML with infrastructure
    legend_html = f"""
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 320px; height: auto; 
                background-color: rgba(0, 0, 0, 0.9); border: 2px solid white;
                z-index:9999; font-size:13px; color: white; padding: 15px;
                border-radius: 10px; max-height: 80vh; overflow-y: auto;
                ">
    <h4 style="color: #FFD700; margin-top: 0;">🗺️ EVACUATION MAP LEGEND</h4>
    
    <p><b>� HOSPITALS:</b></p>
    <p><span style="color: red;">🏥</span> Government Hospital &nbsp;&nbsp; <span style="color: blue;">🏥</span> Private Hospital</p>
    
    <p><b>🌉 BRIDGES (Flood Resistance):</b></p>
    <p><span style="color: #00FF00;">●</span> High &nbsp;&nbsp; <span style="color: #FFFF00;">●</span> Medium &nbsp;&nbsp; <span style="color: #FF0000;">●</span> Low</p>
    
    <p><b>�️ HIGHWAYS (Flood Risk):</b></p>
    <p><span style="color: #00FF00;">━</span> Low Risk &nbsp;&nbsp; <span style="color: #FFFF00;">━</span> Medium Risk &nbsp;&nbsp; <span style="color: #FF0000;">━</span> High Risk</p>
    
    <p><b>🏠 SHELTER TYPES:</b></p>
    <p>🏥 Hospital &nbsp;&nbsp; 🏫 School/College &nbsp;&nbsp; 🏢 Govt Building</p>
    <p>🚉 Railway Station &nbsp;&nbsp; � Hotel/Mall &nbsp;&nbsp; 👥 Community Center</p>
    
    <p><b>🚨 FLOOD RISK LEVELS:</b></p>
    <p><span style="color: #FF0000;">●</span> Critical Risk - EVACUATE NOW</p>
    <p><span style="color: #FF8C00;">●</span> High Risk - Prepare to Leave</p>
    <p><span style="color: #FFD700;">●</span> Medium Risk - Stay Alert</p>
    <p><span style="color: #32CD32;">●</span> Low Risk - Safe Zone</p>
    
    <p><b>🛣️ ROUTE COLORS:</b></p>
    <p><span style="color: #8A2BE2;">●</span> Primary Route &nbsp;&nbsp; <span style="color: #FF1493;">●</span> Secondary Route &nbsp;&nbsp; <span style="color: #00CED1;">●</span> Alternate Route</p>
    <p><span style="color: #FF8C00;">●</span> Backup Route &nbsp;&nbsp; <span style="color: #32CD32;">●</span> Emergency Route</p>
    
    <p><b>📍 MARKERS:</b></p>
    <p>🏠 Your Location &nbsp;&nbsp; ⭐ Safe Destinations</p>
    
    <p><b>� MAP LAYERS:</b></p>
    <p>Toggle layers using the control panel on the map</p>
    </div>
    """
    
    evacuation_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl(position='topleft', collapsed=False).add_to(evacuation_map)
    
    return evacuation_map

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
    
    # Show nearest infrastructure if location is selected
    if st.session_state.routes_computed and st.session_state.best_match:
        nearest_hospitals, nearest_bridges, nearest_highways = find_nearest_infrastructure(
            st.session_state.best_match, flood_df
        )
        
        st.markdown("## 🏥 NEAREST HOSPITALS")
        for _, hospital in nearest_hospitals.iterrows():
            emergency_status = "🚨 24/7" if hospital['Emergency_Services'] == 'Yes' else "⏰ Limited"
            st.markdown(f"""
            **{hospital['Name']}** {emergency_status}  
            📍 {hospital['distance']:.1f} km away  
            🏥 {hospital['Type']} ({hospital['Capacity']} beds)
            """)
        
        st.markdown("---")
        st.markdown("## 🌉 NEAREST BRIDGES")
        for _, bridge in nearest_bridges.iterrows():
            resistance_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}[bridge['Flood_Resistance']]
            access_emoji = "✅" if bridge['Emergency_Access'] == 'Yes' else "⚠️"
            st.markdown(f"""
            **{bridge['Name']}** {resistance_emoji} {access_emoji}  
            📍 {bridge['distance']:.1f} km away  
            🌉 {bridge['Type']} - {bridge['Flood_Resistance']} flood resistance
            """)
        
        st.markdown("---")
        st.markdown("## 🛣️ NEAREST HIGHWAYS")
        for _, highway in nearest_highways.iterrows():
            flood_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[highway['Flood_Prone']]
            emergency_emoji = "✅" if highway['Emergency_Route'] == 'Yes' else "❌"
            st.markdown(f"""
            **{highway['Name']}** {flood_emoji} {emergency_emoji}  
            📍 {highway['min_distance']:.1f} km away  
            🛣️ {highway['Type']} - {highway['Flood_Prone']} flood risk
            """)
        
        st.markdown("---")
    
    st.markdown("## 🏥 EVACUATION CENTERS")
    for center in evacuation_centers:
        st.markdown(center)
    
    st.markdown("---")
    st.markdown("## 🎒 EMERGENCY KIT")
    for item in emergency_kit:
        st.markdown(f"- {item}")
    
    st.markdown("---")
    st.markdown("## 🏠 SHELTER TYPES AVAILABLE")
    shelter_types = flood_df['Shelter_Type'].unique()
    for shelter in sorted(shelter_types):
        count = len(flood_df[flood_df['Shelter_Type'] == shelter])
        total_capacity = flood_df[flood_df['Shelter_Type'] == shelter]['Shelter_Capacity'].sum()
        st.markdown(f"**{shelter}**: {count} locations ({total_capacity:,} capacity)")

# -------------------------------
# Main Interface
# -------------------------------

# Load infrastructure data for stats
hospitals_df, bridges_df, highways_df = load_infrastructure_data()

# Statistics Dashboard
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("📍 Areas Covered", len(flood_df))
with col2:
    critical_areas = len(flood_df[flood_df["Flood_Risk"] == "Critical"])
    st.metric("🔴 Critical Risk", critical_areas)
with col3:
    safe_areas = len(flood_df[flood_df["Flood_Risk"] == "Low"])
    st.metric("🟢 Safe Zones", safe_areas)
with col4:
    total_capacity = flood_df['Shelter_Capacity'].sum()
    st.metric("🏠 Total Shelter Capacity", f"{total_capacity:,}")
with col5:
    emergency_hospitals = len(hospitals_df[hospitals_df['Emergency_Services'] == 'Yes'])
    st.metric("🏥 Emergency Hospitals", emergency_hospitals)
with col6:
    emergency_routes = len(highways_df[highways_df['Emergency_Route'] == 'Yes'])
    st.metric("🛣️ Emergency Routes", emergency_routes)

st.markdown("---")

# Search Interface
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📍 ENTER YOUR CURRENT LOCATION")
    
    # Area selection
    with st.expander("🗺️ VIEW ALL MUMBAI AREAS BY RISK & SHELTER TYPE"):
        risk_order = ["Critical", "High", "Medium", "Low"]
        for risk_level in risk_order:
            areas_data = flood_df[flood_df["Flood_Risk"] == risk_level]
            emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[risk_level]
            
            st.markdown(f"### {emoji} {risk_level} Risk ({len(areas_data)} areas)")
            
            for _, area in areas_data.iterrows():
                shelter_emoji = {
                    'Hospital': '🏥', 'School': '🏫', 'College': '🏫', 
                    'Railway Station': '🚉', 'Hotel': '🏨', 'Mall/Hotel': '🏬',
                    'Community Center': '👥', 'Government Building': '🏢',
                    'Religious Center': '⭐', 'IT Park': '💼'
                }.get(area['Shelter_Type'], '🏠')
                
                st.markdown(f"• **{area['Area_Name'].title()}** {shelter_emoji} ({area['Shelter_Type']}, Capacity: {area['Shelter_Capacity']:,})")
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
        
        # Current shelter info
        shelter_emoji = {
            'Hospital': '🏥', 'School': '🏫', 'College': '🏫', 
            'Railway Station': '🚉', 'Hotel': '🏨', 'Mall/Hotel': '🏬',
            'Community Center': '👥', 'Government Building': '🏢',
            'Religious Center': '⭐', 'IT Park': '💼'
        }.get(current_info['Shelter_Type'], '🏠')
        
        # Location header with shelter info
        st.markdown(f"""
        <div class="shelter-info">
            <h3 style="color: #3498db; text-align: center; margin-bottom: 15px;">📍 Current Location Analysis</h3>
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px;">
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Location:</strong> {best_match.title()} {risk_emoji} (Match: {score}%)</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Ward:</strong> {current_info['Ward']} | <strong>Risk:</strong> {current_info['Flood_Risk']} | <strong>Priority:</strong> {current_info['Evacuation_Priority']} {priority_emoji}</p>
                <p style="margin: 5px 0; color: #ecf0f1;"><strong>Current Shelter:</strong> {shelter_emoji} {current_info['Shelter_Type']} (Capacity: {current_info['Shelter_Capacity']:,} people)</p>
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
        
        # Routes with shelter information
        st.markdown("## 🛣️ RECOMMENDED EVACUATION ROUTES WITH SHELTER INFO")
        st.markdown(f"**Found {len(routes)} optimal routes ranked by safety:**")
        
        for i, route in enumerate(routes):
            header_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
            risk_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}[route["risk_level"]]
            
            route_shelter_emoji = {
                'Hospital': '🏥', 'School': '🏫', 'College': '🏫', 
                'Railway Station': '🚉', 'Hotel': '🏨', 'Mall/Hotel': '🏬',
                'Community Center': '👥', 'Government Building': '🏢',
                'Religious Center': '⭐', 'IT Park': '💼'
            }.get(route['shelter_type'], '🏠')
            
            # Route header
            st.markdown(f"""
            <div style="background: {header_color}; color: white; padding: 15px; border-radius: 10px; margin: 20px 0; text-align: center; border: 2px solid #333;">
                <h2 style="margin: 0; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.7);">🛣️ ROUTE {i+1}: To {route['destination']} {risk_color}</h2>
                <h4 style="margin: 5px 0; color: white;">{route_shelter_emoji} {route['shelter_type']} Shelter (Capacity: {route['shelter_capacity']:,})</h4>
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
                st.metric("🏠 Shelter Capacity", f"{route['shelter_capacity']:,}")
            
            # Route details
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown(f"""
                <div style="background: #1e2126; padding: 15px; border-radius: 10px; border: 1px solid #333; margin: 10px 0;">
                    <p style="color: #ffffff; margin: 5px 0;"><strong>🛡️ Safety Level:</strong> {route['risk_level']}</p>
                    <p style="color: #ffffff; margin: 5px 0;"><strong>⚡ Priority:</strong> {route['evacuation_priority']}</p>
                    <p style="color: #ffffff; margin: 5px 0;"><strong>🚀 Safety Improvement:</strong> +{route['safety_improvement']} points</p>
                </div>
                """, unsafe_allow_html=True)
            
            with detail_col2:
                st.markdown(f"""
                <div style="background: #1e2126; padding: 15px; border-radius: 10px; border: 1px solid #333; margin: 10px 0;">
                    <p style="color: #ffffff; margin: 5px 0;"><strong>🚗 Transport:</strong> {route['transport']}</p>
                    <p style="color: #ffffff; margin: 5px 0;"><strong>🏠 Shelter Type:</strong> {route_shelter_emoji} {route['shelter_type']}</p>
                    <p style="color: #ffffff; margin: 5px 0;"><strong>⭐ Route Score:</strong> {route['route_score']} (lower = better)</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
        
        # Enhanced Interactive Map
        st.markdown("## 🗺️ LIVE EVACUATION MAP WITH ALL INFRASTRUCTURE")
        st.markdown("### 📍 Dark theme map with hospitals, bridges, highways, shelters, and detailed legend")
        
        evacuation_map = create_advanced_evacuation_map(best_match, routes, flood_df)
        st_folium(evacuation_map, width=1200, height=700)
        
        # Infrastructure Analysis
        st.markdown("---")
        st.markdown("## 🏗️ NEAREST CRITICAL INFRASTRUCTURE ANALYSIS")
        
        nearest_hospitals, nearest_bridges, nearest_highways = find_nearest_infrastructure(best_match, flood_df)
        
        infra_col1, infra_col2, infra_col3 = st.columns(3)
        
        with infra_col1:
            st.markdown("### 🏥 NEAREST HOSPITALS")
            for i, (_, hospital) in enumerate(nearest_hospitals.iterrows()):
                priority_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
                emergency_status = "🚨 24/7 Emergency" if hospital['Emergency_Services'] == 'Yes' else "⏰ Limited Hours"
                
                st.markdown(f"""
                <div style="background: {priority_color}; color: white; padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <h4 style="margin: 0; color: white;">{i+1}. {hospital['Name']}</h4>
                    <p style="margin: 5px 0; color: white;">📍 <strong>{hospital['distance']:.1f} km</strong> away</p>
                    <p style="margin: 5px 0; color: white;">🏥 {hospital['Type']} ({hospital['Capacity']} beds)</p>
                    <p style="margin: 5px 0; color: white;">{emergency_status}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with infra_col2:
            st.markdown("### 🌉 NEAREST BRIDGES")
            for i, (_, bridge) in enumerate(nearest_bridges.iterrows()):
                priority_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
                resistance_status = {"High": "🟢 High Flood Resistance", "Medium": "🟡 Medium Resistance", "Low": "🔴 Low Resistance"}[bridge['Flood_Resistance']]
                access_status = "✅ Emergency Access" if bridge['Emergency_Access'] == 'Yes' else "⚠️ Limited Access"
                
                st.markdown(f"""
                <div style="background: {priority_color}; color: white; padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <h4 style="margin: 0; color: white;">{i+1}. {bridge['Name']}</h4>
                    <p style="margin: 5px 0; color: white;">📍 <strong>{bridge['distance']:.1f} km</strong> away</p>
                    <p style="margin: 5px 0; color: white;">🌉 {bridge['Type']}</p>
                    <p style="margin: 5px 0; color: white;">{resistance_status}</p>
                    <p style="margin: 5px 0; color: white;">{access_status}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with infra_col3:
            st.markdown("### 🛣️ NEAREST HIGHWAYS")
            for i, (_, highway) in enumerate(nearest_highways.iterrows()):
                priority_color = "#dc3545" if i == 0 else "#ffc107" if i == 1 else "#28a745"
                flood_status = {"Low": "🟢 Low Flood Risk", "Medium": "🟡 Medium Flood Risk", "High": "🔴 High Flood Risk"}[highway['Flood_Prone']]
                emergency_status = "✅ Emergency Route" if highway['Emergency_Route'] == 'Yes' else "❌ Not Emergency Route"
                
                st.markdown(f"""
                <div style="background: {priority_color}; color: white; padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <h4 style="margin: 0; color: white;">{i+1}. {highway['Name']}</h4>
                    <p style="margin: 5px 0; color: white;">📍 <strong>{highway['min_distance']:.1f} km</strong> away</p>
                    <p style="margin: 5px 0; color: white;">🛣️ {highway['Type']}</p>
                    <p style="margin: 5px 0; color: white;">{flood_status}</p>
                    <p style="margin: 5px 0; color: white;">{emergency_status}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Shelter Statistics
        st.markdown("---")
        st.markdown("## 🏠 SHELTER ANALYSIS FOR YOUR ROUTES")
        
        shelter_col1, shelter_col2 = st.columns(2)
        
        with shelter_col1:
            st.markdown("### 🎯 Recommended Shelters")
            for i, route in enumerate(routes):
                route_shelter_emoji = {
                    'Hospital': '🏥', 'School': '🏫', 'College': '🏫', 
                    'Railway Station': '🚉', 'Hotel': '🏨', 'Mall/Hotel': '🏬',
                    'Community Center': '👥', 'Government Building': '🏢',
                    'Religious Center': '⭐', 'IT Park': '💼'
                }.get(route['shelter_type'], '🏠')
                
                st.markdown(f"""
                **Route {i+1}**: {route_shelter_emoji} **{route['shelter_type']}**  
                📍 {route['destination']} | 🏠 Capacity: {route['shelter_capacity']:,}  
                📏 {route['distance_km']} km | ⏱️ {route['eta_minutes']} min
                """)
        
        with shelter_col2:
            st.markdown("### 📊 Shelter Type Distribution")
            shelter_counts = flood_df['Shelter_Type'].value_counts()
            for shelter_type, count in shelter_counts.head(8).items():
                percentage = (count / len(flood_df)) * 100
                st.markdown(f"**{shelter_type}**: {count} locations ({percentage:.1f}%)")
        
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
    <p style="color: #bdc3c7; margin-bottom: 15px;">Advanced evacuation routing with shelter analysis for Mumbai flood emergencies</p>
    <div style="background: rgba(231, 76, 60, 0.2); padding: 15px; border-radius: 10px;">
        <h4 style="color: #e74c3c; margin-bottom: 10px;">🚨 24/7 EMERGENCY HELPLINES</h4>
        <p style="color: #ecf0f1; font-weight: bold; font-size: 18px;">
            Police: 100 | Medical: 108 | Fire: 101 | BMC: 1916
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
