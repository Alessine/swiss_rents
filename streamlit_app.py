import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json


# Functions
@st.cache
def load_and_clean_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    df.drop(columns=["Bezugsdatum", "Quadratmeterpreis_Brutto"], inplace=True)
    df["Wohnungstyp"].fillna("Unbekannt", inplace=True)
    df.dropna(inplace=True)
    cantons_dict = {'TG': 'Thurgau', 'GR': 'Graubünden', 'LU': 'Luzern', 'BE': 'Bern', 'VS': 'Valais',
                    'BL': 'Basel-Landschaft', 'SO': 'Solothurn', 'VD': 'Vaud', 'SH': 'Schaffhausen', 'ZH': 'Zürich',
                    'AG': 'Aargau', 'UR': 'Uri', 'NE': 'Neuchâtel', 'TI': 'Ticino', 'SG': 'St. Gallen', 'GE': 'Genève',
                    'GL': 'Glarus', 'JU': 'Jura', 'ZG': 'Zug', 'OW': 'Obwalden', 'FR': 'Fribourg', 'SZ': 'Schwyz',
                    'AR': 'Appenzell Ausserrhoden', 'AI': 'Appenzell Innerrhoden', 'NW': 'Nidwalden',
                    'BS': 'Basel-Stadt'}
    df["Kanton"] = df["KT"].map(cantons_dict)
    df["Miete_Kategorie"] = np.where(df["Mietpreis_Brutto"] <= 1200, "low",
                                     np.where((df["Mietpreis_Brutto"] > 1200) &
                                              (df["Mietpreis_Brutto"] <= 2000), "medium",
                                              np.where((df["Mietpreis_Brutto"] > 2000) &
                                                       (df["Mietpreis_Brutto"] <= 2800), "high", "very high")))

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
        title="Location of Free Apartments",
        width=800,
        height=600,
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


@st.cache
def create_barplot(df):
    df_grouped = df.groupby(["Kanton", "Miete_Kategorie"]).size().unstack(level=-1).fillna(0)\
        .sort_values("Kanton", ascending=False).reset_index()

    colors = px.colors.qualitative.Bold

    barplot = go.Figure()

    if "low" in df_grouped.columns:
        barplot.add_trace(go.Bar(
            y=df_grouped["Kanton"],
            x=df_grouped["low"],
            name='rent below CHF 1200',
            orientation='h',
            marker_color=colors[0]
            ))
    if "medium" in df_grouped.columns:
        barplot.add_trace(go.Bar(
            y=df_grouped["Kanton"],
            x=df_grouped["medium"],
            name='rent between CHF 1200-2000',
            orientation='h',
            marker_color=colors[1]
            ))
    if "high" in df_grouped.columns:
        barplot.add_trace(go.Bar(
            y=df_grouped["Kanton"],
            x=df_grouped["high"],
            name='rent between CHF 2000-2800',
            orientation='h',
            marker_color=colors[2]
            ))
    if "very high" in df_grouped.columns:
        barplot.add_trace(go.Bar(
            y=df_grouped["Kanton"],
            x=df_grouped["very high"],
            name='rent above CHF 2800',
            orientation='h',
            marker_color=colors[3]
            ))

    barplot.update_layout(
        barmode='stack',
        margin={"r": 0, "t": 35, "l": 0, "b": 0},
        title="Number of Listings by Kanton",
        width=400,
        height=600,
        template="simple_white",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="left",
            x=-0.05)
    )

    return barplot


# User dependent variables
raw_data_path = "data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "data/processed/rents_with_coords_clean.csv"


# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]


# Load the data
df_proc, cantons = load_and_clean_data(raw_data_path, proc_data_path)
df_plotting = df_proc.copy()


# App layout
st.title("Apartment Listings in Switzerland (2019)")
st.header("How Rents vary across the Country")


# Form with Widgets
st.sidebar.subheader("Selection Criteria")
with st.sidebar.form("Search Criteria"):
    max_rent = st.number_input("Max. Rent", value=0)
    num_rooms = st.number_input("Min. Number of Rooms", value=0)
    submitted = st.form_submit_button("Submit")
    if submitted:
        df_plotting = df_plotting[(df_plotting["Mietpreis_Brutto"] <= max_rent) &
                                  (df_plotting["Zimmer"] >= num_rooms)]


# Plotly Scatter Map
hovertext = [f'Address: {street}, {place},<br>Rooms: {rooms}, Size: {round(size)}m²,<br>Rent: CHF {rent}'
             for street, place, rooms, size, rent
             in zip(df_plotting["Adresse"], df_plotting["Ort"], df_plotting["Zimmer"],
                    df_plotting["Fläche"], df_plotting["Mietpreis_Brutto"])]

st.plotly_chart(create_scattermap(df_plotting, cantons, hovertext, mapbox_access_token))


# Plotly Bar Chart
left_column, right_column = st.columns([1, 1])
right_column.plotly_chart(create_barplot(df_plotting))


# Show the data itself
if st.checkbox("Show Data"):
    st.dataframe(data=df_proc)

st.write("The data is freely available at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")
