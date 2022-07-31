import streamlit as st
from streamlit_lottie import st_lottie
from copy import deepcopy
import helpers as hp


# App layout
st.set_page_config(layout="wide")
st.markdown("<h1 style='color: #00224e'>Apartment Listings in Switzerland (2019)</h1>", unsafe_allow_html=True)
st.subheader("Objective")
st.markdown("""With this app you can explore a collection of Swiss apartment listings from 2019 and 
find out how different factors influence the rent.""")
st.markdown("---")
st.subheader("Analysis")
left_col, right_col = st.columns([3, 1])
left_col.markdown("""The listings were categorized based on the rent per square meter of floor space. 
You can calculate this indicator for your own apartment and see in what category it falls.

The following partitioning seemed to give interesting insights:
* `< CHF 15.70/m²` — the cheapest 15% of all listings (lowest rent per square meter)
* `≥ CHF 15.70 but < CHF 19.70/m²` — 35% of apartments below the average, but not within the cheapest 15%
* `≥ CHF 19.70 but < CHF 26.10/m²` — 35% of apartments above the average, but not within the top 15%
* `≥ CHF 26.10/m²` — the most expensive 15% of all listings (highest rent per square meter)

In the plots below you can see **(A)** how these apartments are distributed geographically, 
**(B)** how their floor space is related to their rent and **(C)** what cantons have most listings and in what 
categories they fall.

Finally, you can use the Selection Criteria on the left to explore more in detail which places on the map offer 
what types of apartments or you can filter listings based on maximum rent or minimum number of rooms. 
""")

with right_col.form("Rent/m²", clear_on_submit=True):
    user_rent = st.number_input("Rent (CHF)", 0)
    user_floor_space = st.number_input("Floor Space (m²)", 0)
    submitted = st.form_submit_button("Calculate")
    if submitted:
        if user_floor_space == 0:
            st.write("Please enter floor space")
        else:
            rent_per_m2 = user_rent / user_floor_space
            st.write(f"Rent/m²: CHF {round(rent_per_m2, 2)}")
st.text("")

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

st.text("")

st.markdown("---")
st.subheader("Data Source")
# Show the data itself
if st.checkbox("Show Processed Data (first 10 rows)"):
    st.dataframe(data=df_proc.drop(columns="hover_strings_scatter").head(10))

# Download button and link for data
csv = hp.convert_df(df_proc)
st.download_button(
    label="Download Processed Data (csv)",
    data=csv,
    file_name='swiss_rents_df.csv',
    mime='text/csv',
)
st.write("The unprocessed data was made available for use for any purpose (including commercial) under a creative commons license at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")

st.markdown("---")
st.markdown("<b>A Streamlit web app by Angela Niederberger.</b>", unsafe_allow_html=True)
st.markdown("""I love getting feedback! 
The code for this app is available on [GitHub](https://github.com/Alessine/swiss_rents) and you can reach out to me on [LinkedIn](https://www.linkedin.com/in/angela-niederberger).""")
