import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from copy import deepcopy


# Functions
@st.cache
def load_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    with open(raw_data) as response:
        geojson = json.load(response)

    return df, geojson


def set_up_subplots():
    colors = px.colors.qualitative.Bold

    traces = [
        "below CHF 1200",
        "between CHF 1200-2000",
        "between CHF 2000-2800",
        "above CHF 2800",
    ]

    go_figure = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"colspan": 2, "type": "mapbox"}, None], [{}, {}]],
        horizontal_spacing=0.07,
        vertical_spacing=0.07,
        subplot_titles=("First Subplot", "Second Subplot", "Third Subplot"),
    )
    return go_figure, colors, traces


def add_scattermap_traces(df, go_figure, colors, traces):
    hover_strings = [
        f"Address: {street}, {place},<br>Rooms: {rooms}, Size: {round(size)}m²,<br>Rent: CHF {rent}"
        for street, place, rooms, size, rent in zip(
            df["Adresse"],
            df["Ort"],
            df["Zimmer"],
            df["Fläche"],
            df["Mietpreis_Brutto"],
        )
    ]

    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        go_figure.add_trace(
            go.Scattermapbox(
                lon=df_grouped["lon"],
                lat=df_grouped["lat"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=5, color=colors[cat], opacity=0.6),
                text=hover_strings,
                hovertemplate="%{text}<extra></extra>",
                name=traces[cat],
                legendgroup=str(cat),
            ),
            row=1,
            col=1,
        )
    return go_figure


def add_barplot_traces(df, go_figure, colors, traces):
    df_grouped = (
        df.groupby(["Kanton", "Miete_Kategorie"])
        .size()
        .unstack(level=-1)
        .fillna(0)
        .sort_values("Kanton", ascending=False)
        .reset_index()
    )
    for cat in df["Miete_Kategorie"].unique():
        go_figure.add_trace(
            go.Bar(
                y=df_grouped["Kanton"],
                x=df_grouped.loc[:, cat],
                name=traces[cat],
                orientation="h",
                marker_color=colors[cat],
                legendgroup=str(cat),
                showlegend=False,
            ),
            row=2,
            col=2,
        )
    return go_figure


def define_figure_layout(go_figure, mapbox_token):
    go_figure.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        # autosize=True,
        width=750,
        height=1000,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            center=go.layout.mapbox.Center(lat=46.8, lon=8.3),
            pitch=0,
            zoom=6.7,
            layers=[{"source": cantons, "type": "line", "line_width": 1}],
        ),
        legend=dict(orientation="h", yanchor="top", y=0.53, xanchor="center", x=0.5),
        template="simple_white",
        barmode="stack",
    )
    return go_figure


def build_combined_figure(df, mapbox_token):
    go_figure, colors, traces = set_up_subplots()

    # Scattermapbox
    go_figure = add_scattermap_traces(
        df,
        go_figure,
        colors,
        traces,
    )

    # Bar plot
    go_figure = add_barplot_traces(df, go_figure, colors, traces)

    # Layout
    go_figure = define_figure_layout(go_figure, mapbox_token)

    return go_figure


# User dependent variables
raw_data_path = "data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "data/processed/rents_with_coords_clean.csv"


# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]


# Load the data
df_proc, cantons = load_data(raw_data_path, proc_data_path)
df_plotting = deepcopy(df_proc)


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


# Plotly Combined Plot
joint_fig = build_combined_figure(df=df_plotting, mapbox_token=mapbox_access_token)
st.plotly_chart(joint_fig)


# Show the data itself
if st.checkbox("Show Data"):
    st.dataframe(data=df_proc)

st.write("The data is freely available at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")
