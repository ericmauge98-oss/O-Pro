import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
from st_supabase_connection import SupabaseConnection

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="O-Pro Marine", page_icon="🌊", layout="wide")

# Connect to your Supabase "Brain"
conn = st.connection("supabase", type=SupabaseConnection)

# Connect to OpenAI for the Voice AI
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

st.title("🌊 O-Pro: Marine Intelligence")

# --- 2. SATELLITE PIER & ACCESS FINDER ---
st.sidebar.header("Navigation")
mode = st.sidebar.radio("Go to:", ["Live Map", "Report Hazard", "Community Feed"])

user_lat, user_lon = 26.12, -80.14 

if mode == "Live Map":
    st.header("📍 Nearby Fishing & Access")
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["leisure"="fishing"](around:10000,{user_lat},{user_lon});
      node["amenity"="pier"](around:10000,{user_lat},{user_lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
        if data.get('elements'):
            piers = [{"name": p.get('tags', {}).get('name', 'Public Access'), "latitude": p['lat'], "longitude": p['lon']} for p in data['elements']]
            df = pd.DataFrame(piers)
            st.map(df)
            st.table(df)
        else:
            st.warning("No public access found in this 10km radius.")
    except:
        st.error("Map service temporarily unavailable.")

# --- 3. VOICE REPORTING SYSTEM ---
elif mode == "Report Hazard":
    st.header("🎙️ Voice-Activated Hazard Report")
    audio_value = st.audio_input("Record your report")

    if audio_value:
        with st.spinner("AI Transcribing..."):
            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_value).text
            st.success(f"Report Captured: {transcript}")
            try:
                conn.table("public_reports").insert([{"type": "Community Alert", "note": transcript, "lat": user_lat, "lon": user_lon}]).execute()
                st.balloons()
            except Exception as e:
                st.error(f"Error saving to database: {e}")

# --- 4. GLOBAL COMMUNITY FEED ---
elif mode == "Community Feed":
    st.header("🌎 Global Alerts")
    reports = conn.table("public_reports").select("*").order("created_at", desc=True).execute()
    if reports.data:
        df_reports = pd.DataFrame(reports.data)
        st.map(df_reports)
        for _, row in df_reports.iterrows():
            with st.expander(f"⚠️ {row['type']} - {row['created_at'][:10]}"):
                st.write(row['note'])
    else:
        st.info("No community reports yet.")
