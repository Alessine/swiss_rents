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
    st.markdown("<h1 style='text-align: center; '>Selection Criteria</h1>", unsafe_allow_html=True)

# Form with Widgets
with st.sidebar.form("Selection Criteria"):
    place_sel = st.text_input(label="Place", value="All")
    max_rent = st.number_input("Max. Rent (CHF / month)", value=16500)
    num_rooms = st.number_input("Min. Number of Rooms", value=1)
    submitted = st.form_submit_button("Submit")
    if submitted:
        if place_sel == "All":
            df_plotting = df_plotting[(df_plotting["Mietpreis_Brutto"] <= max_rent) &
                                      (df_plotting["Zimmer"] >= num_rooms)]

        elif place_sel not in list(df_plotting["Ort"].drop_duplicates()):
            st.write(f"<b style='color: #FF6B6B'>There are no apartment listings in {place_sel}.</b>",
                     unsafe_allow_html=True)

        else:
            df_plotting = df_plotting[(df_plotting["Ort"] == place_sel) &
                                      (df_plotting["Mietpreis_Brutto"] <= max_rent) &
                                      (df_plotting["Zimmer"] >= num_rooms)]

try:
    assert len(df_plotting.index) > 0, "Dataframe is empty."
    map_fig = hp.build_scattermap(df=df_plotting, geo_json=cantons, mapbox_token=mapbox_access_token)
    st.plotly_chart(map_fig, use_container_width=True)

    joint_fig = hp.build_combined_figure(df=df_plotting)
    st.plotly_chart(joint_fig, use_container_width=True)

except AssertionError:
    st.sidebar.write("There are no apartment listings that meet these criteria.")
    df_plotting = deepcopy(df_proc)
