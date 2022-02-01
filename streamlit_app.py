import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json


# Functions
@st.cache
def load_and_clean_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    df.drop(columns=["Bezugsdatum", "Quadratmeterpreis_Brutto"], inplace=True)
    df["Wohnungstyp"].fillna("Unbekannt", inplace=True)
    df.dropna(inplace=True)
    with open(raw_data) as response:
        geojson = json.load(response)
    return df, geojson


@st.cache
def create_scattermap(df, geojson, hover_strings, mapbox_token):
    scatter_map = go.Figure(
        go.Scattermapbox(
            lon=df["lon"],
            lat=df["lat"],
            mode="markers",
            marker=go.scattermapbox.Marker(size=4),
            text=hover_strings,
            hovertemplate='%{text}<extra></extra>'
        )
    )

    scatter_map.update_layout(
        margin={"r": 0, "t": 35, "l": 0, "b": 0},
        width=900,
        height=500,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            center=go.layout.mapbox.Center(lat=46.8, lon=8.3),
            pitch=0,
            zoom=6.7,
            layers=[{"source": geojson, "type": "line", "line_width": 1}],
        ),
    )
    return scatter_map


# User dependent variables
raw_data_path = "data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "data/processed/rents_with_coords_clean.csv"


# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]


# Load the data
df_proc, cantons = load_and_clean_data(raw_data_path, proc_data_path)
df_plotting = df_proc.copy()


# App layout
st.title("Apartment Rents in Switzerland (2019)")
st.header("How much should you expect to pay?")
left_column, right_column = st.columns([3, 1])


# Form with Widgets
with st.sidebar.form("Search Criteria"):
    max_rent = st.number_input("Max. Rent")

    submitted = st.form_submit_button("Submit")
    if submitted:
        df_plotting = df_plotting[df_plotting["Mietpreis_Brutto"] <= max_rent]


# Plotly Scatter Map
hovertext = [f'Address: {street}, {place},<br>Rooms: {rooms}, Size: {round(size)}m²,<br>Rent: CHF {rent}'
             for street, place, rooms, size, rent
             in zip(df_plotting["Adresse"], df_plotting["Ort"], df_plotting["Zimmer"],
                    df_plotting["Fläche"], df_plotting["Mietpreis_Brutto"])]

left_column.plotly_chart(create_scattermap(df_plotting, cantons, hovertext, mapbox_access_token))


# Show the data itself
if st.checkbox("Show Data"):
    st.dataframe(data=df_proc)

st.write("The data is freely available at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")
