import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# User dependent variables
raw_data = "/app/swiss_rents/data/raw"
proc_data = "/app/swiss_rents/data/processed"

# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]

# Dataset
df_proc = pd.read_csv(f"{proc_data}/rents_with_coords_clean.csv", sep=",")

# Handle missing values
df_proc.drop(columns=["Bezugsdatum", "Quadratmeterpreis_Brutto"], inplace=True)
df_proc["Wohnungstyp"].fillna("Unbekannt", inplace=True)
df_proc.dropna(inplace=True)

# Geographic features
with open(f"{raw_data}/georef-switzerland-kanton.geojson") as response:
    cantons = json.load(response)

# App layout
st.title("Apartment Rents in Switzerland (2019)")
st.header("How much should you expect to pay?")

if st.checkbox("Show Dataframe"):
    st.subheader("Raw Dataset:")
    st.dataframe(data=df_proc)

# Setting up columns
left_column, middle_column, right_column = st.columns([3, 1, 1])

# Plotly Scatter Map
scatter_map = go.Figure(
    go.Scattermapbox(
        lon=df_proc["lon"],
        lat=df_proc["lat"],
        mode="markers",
        marker=go.scattermapbox.Marker(size=4),
        text=df_proc["Adresse"],
    )
)

scatter_map.update_layout(
    margin={"r": 0, "t": 35, "l": 0, "b": 0},
    width=900,
    height=500,
    title="Apartments for Rent in Switzerland (2019)",
    hovermode="closest",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(lat=46.8, lon=8.3),
        pitch=0,
        zoom=6.7,
        layers=[{"source": cantons, "type": "line", "line_width": 1}],
    ),
)

st.plotly_chart(scatter_map)
