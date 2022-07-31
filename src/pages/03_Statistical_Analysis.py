import streamlit as st
from copy import deepcopy
from streamlit_lottie import st_lottie
import helpers as hp

# User dependent variables
raw_data_path = "./data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "./data/processed/rents_with_coords_clean.csv"

# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]

# Load the data
df_proc, cantons = hp.load_data(raw_data_path, proc_data_path)
df_plotting = deepcopy(df_proc)

# Sidebar
# Lottie icon
lottie_url = "https://assets3.lottiefiles.com/packages/lf20_fgne1q0e.json"
lottie_pin = hp.load_lottieurl(lottie_url)
with st.sidebar:
    st_lottie(lottie_pin, speed=1, height=100)

st.dataframe(df_plotting)
