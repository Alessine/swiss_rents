import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json


# Functions
@st.cache
def load_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    with open(raw_data) as response:
        geojson = json.load(response)
    colors_qual = px.colors.qualitative.Bold

    return df, geojson, colors_qual


@st.cache
def create_scattermap(df, geojson, hover_strings, mapbox_token, colors):
    trace_names = [
        "below CHF 1200",
        "between CHF 1200-2000",
        "between CHF 2000-2800",
        "above CHF 2800",
    ]

    scatter_map = go.Figure()

    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        scatter_map.add_trace(
            go.Scattermapbox(
                lon=df_grouped["lon"],
                lat=df_grouped["lat"],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=5, color=colors[cat], opacity=0.5
                ),
                text=hover_strings,
                hovertemplate="%{text}<extra></extra>",
                name=trace_names[cat],
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
def create_barplot(df, colors):
    df_grouped = (
        df.groupby(["Kanton", "Miete_Kategorie"])
        .size()
        .unstack(level=-1)
        .fillna(0)
        .sort_values("Kanton", ascending=False)
        .reset_index()
    )

    barplot = go.Figure()

    trace_names = [
        "below CHF 1200",
        "between CHF 1200-2000",
        "between CHF 2000-2800",
        "above CHF 2800",
    ]
    for cat in df["Miete_Kategorie"].unique():
        barplot.add_trace(
            go.Bar(
                y=df_grouped["Kanton"],
                x=df_grouped.loc[:, cat],
                name=trace_names[cat],
                orientation="h",
                marker_color=colors[cat],
            )
        )

    barplot.update_layout(
        barmode="stack",
        margin={"r": 0, "t": 35, "l": 0, "b": 0},
        title="Number of Listings by Kanton",
        width=400,
        height=600,
        template="simple_white",
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="left", x=-0.05),
    )

    return barplot


# User dependent variables
raw_data_path = "data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "data/processed/rents_with_coords_clean.csv"


# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]


# Load the data
df_proc, cantons, quali_colorscale = load_data(raw_data_path, proc_data_path)
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

st.plotly_chart(create_scattermap(df_plotting, cantons, hovertext, mapbox_access_token, quali_colorscale))


# Plotly Bar Chart
left_column, right_column = st.columns([1, 1])
right_column.plotly_chart(create_barplot(df_plotting, quali_colorscale))


# Show the data itself
if st.checkbox("Show Data"):
    st.dataframe(data=df_proc)

st.write("The data is freely available at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")
