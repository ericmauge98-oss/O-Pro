{\rtf1\ansi\ansicpg1252\cocoartf2867
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import streamlit as st\
import pandas as pd\
import requests\
from openai import OpenAI\
from st_supabase_connection import SupabaseConnection\
\
# --- 1. INITIAL SETUP ---\
st.set_page_config(page_title="O-Pro Marine", page_icon="\uc0\u55356 \u57098 ", layout="wide")\
\
# Connect to your Supabase "Brain"\
# These keys will be set in Streamlit Settings > Secrets later\
conn = st.connection("supabase", type=SupabaseConnection)\
\
# Connect to OpenAI for the Voice AI\
client = OpenAI(api_key=st.secrets["openai"]["api_key"])\
\
st.title("\uc0\u55356 \u57098  O-Pro: Marine Intelligence")\
\
# --- 2. SATELLITE PIER & ACCESS FINDER ---\
st.sidebar.header("Navigation")\
mode = st.sidebar.radio("Go to:", ["Live Map", "Report Hazard", "Community Feed"])\
\
# Default coordinates (Example: Miami/South FL area)\
# In a real app, we can use a geolocator to find the user\
user_lat, user_lon = 26.12, -80.14 \
\
if mode == "Live Map":\
    st.header("\uc0\u55357 \u56525  Nearby Fishing & Beach Access")\
    \
    # This pulls live data from OpenStreetMap\
    overpass_url = "http://overpass-api.de/api/interpreter"\
    overpass_query = f"""\
    [out:json];\
    (\
      node["leisure"="fishing"](around:10000,\{user_lat\},\{user_lon\});\
      node["amenity"="pier"](around:10000,\{user_lat\},\{user_lon\});\
    );\
    out center;\
    """\
    response = requests.get(overpass_url, params=\{'data': overpass_query\})\
    data = response.json()\
\
    if data.get('elements'):\
        piers = []\
        for p in data['elements']:\
            piers.append(\{\
                "name": p.get('tags', \{\}).get('name', 'Public Access'),\
                "latitude": p['lat'],\
                "longitude": p['lon']\
            \})\
        df = pd.DataFrame(piers)\
        st.map(df)\
        st.table(df)\
    else:\
        st.warning("No public piers found in this 10km radius.")\
\
# --- 3. VOICE REPORTING SYSTEM ---\
elif mode == "Report Hazard":\
    st.header("\uc0\u55356 \u57241 \u65039  Voice-Activated Hazard Report")\
    st.write("Record a quick note (e.g., 'Large seaweed patch at the pier' or 'Shark sighting')")\
    \
    # Streamlit's native audio input (requires browser mic permission)\
    audio_value = st.audio_input("Record your report")\
\
    if audio_value:\
        with st.spinner("AI Transcribing..."):\
            # Send audio to OpenAI Whisper\
            transcript = client.audio.transcriptions.create(\
                model="whisper-1", \
                file=audio_value\
            ).text\
            \
            st.success(f"Report Captured: \{transcript\}")\
            \
            # SAVE TO SUPABASE\
            # This sends data to the table you created!\
            try:\
                conn.table("public_reports").insert([\
                    \{\
                        "type": "Community Alert", \
                        "note": transcript, \
                        "lat": user_lat, \
                        "lon": user_lon\
                    \}\
                ]).execute()\
                st.balloons()\
                st.info("Report synced to the global community database.")\
            except Exception as e:\
                st.error(f"Error saving to database: \{e\}")\
\
# --- 4. GLOBAL COMMUNITY FEED ---\
elif mode == "Community Feed":\
    st.header("\uc0\u55356 \u57102  Global Alerts")\
    \
    # Pull reports from Supabase\
    reports = conn.table("public_reports").select("*").order("created_at", desc=True).execute()\
    \
    if reports.data:\
        df_reports = pd.DataFrame(reports.data)\
        st.map(df_reports)\
        for _, row in df_reports.iterrows():\
            with st.expander(f"\uc0\u9888 \u65039  \{row['type']\} - \{row['created_at'][:10]\}"):\
                st.write(row['note'])\
                st.caption(f"Location: \{row['lat']\}, \{row['lon']\}")\
    else:\
        st.info("No community reports yet. Be the first to report!")}