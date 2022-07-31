import streamlit as st
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json


# Functions
@st.cache
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


@st.cache(hash_funcs={'_json.Scanner': hash})
def load_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    df_small = df.sample(frac=0.2)
    with open(raw_data) as response:
        geojson = json.load(response)

    return df_small, geojson


def set_up_scattermap():
    colors = np.array(px.colors.sequential.Cividis)[[0, 3, 6, 9]]
    traces = [
        "cheapest",
        "below average",
        "above average",
        "most expensive",
    ]
    go_figure = go.Figure()
    return colors, traces, go_figure


def add_scattermap_traces(df, go_figure, colors, traces):
    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        go_figure.add_trace(
            go.Scattermapbox(
                lon=df_grouped["lon"],
                lat=df_grouped["lat"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=5, color=colors[cat], opacity=0.5),
                text=df_grouped["hover_strings_scatter"],
                hovertemplate="%{text}<extra></extra>",
                name=traces[cat],
                legendgroup=str(cat),
            )
        )
    return go_figure


def add_scattermap_layout(go_figure, geo_json, mapbox_token):
    go_figure.update_layout(
        margin={"r": 0, "t": 45, "l": 0, "b": 0},
        width=1100,
        height=660,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            center=go.layout.mapbox.Center(lat=46.8, lon=8.3),
            pitch=0,
            zoom=7,
            layers=[{"source": geo_json, "type": "line", "line_width": 1}],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            xanchor="center",
            x=0.5,
            font_size=16,
            itemsizing="constant",
        ),
        template="simple_white",
        title={"text": "Location of Listed Apartments",
               "font_size": 25,
               "x": 0.0},
    )
    return go_figure


def build_scattermap(df, geo_json, mapbox_token):
    colors, traces, go_figure = set_up_scattermap()
    go_figure = add_scattermap_traces(df, go_figure, colors, traces)
    go_figure = add_scattermap_layout(go_figure, geo_json, mapbox_token)
    return go_figure


def set_up_subplots():
    colors = np.array(px.colors.sequential.Cividis)[[0, 3, 6, 9]]
    go_figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=(
            "Apartments by Size and Rent",
            "Apartments per Canton",
        ),
        column_widths=[1.7, 1],
        horizontal_spacing=0.165,
    )
    return go_figure, colors


def add_scatter_traces(df, go_figure, colors):
    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        go_figure.add_trace(
            go.Scatter(
                x=df_grouped["Fläche"],
                y=df_grouped["Mietpreis_Brutto"],
                mode="markers",
                marker={"color": colors[cat], "opacity": 0.5},
                text=df_grouped["hover_strings_scatter"],
                hovertemplate="%{text}<extra></extra>",
                legendgroup=str(cat),
                showlegend=False,
            ),
            row=1,
            col=1,
        )
    return go_figure


def add_barplot_traces(df, go_figure, colors):
    df_grouped = (
        df.groupby(["Kanton", "Miete_Kategorie"])
        .size()
        .unstack(level=-1)
        .fillna(0)
        .sort_values("Kanton", ascending=False)
        .reset_index()
    )
    df_grouped["Total_Kanton"] = df_grouped.iloc[:, 1:].sum(axis=1)
    for cat in df["Miete_Kategorie"].unique():
        hover_strings = [
            f"{round(num_per_canton / total_canton * 100, 2)}%"
            for num_per_canton, total_canton in zip(
                df_grouped.loc[:, cat], df_grouped["Total_Kanton"]
            )
        ]
        go_figure.add_trace(
            go.Bar(
                y=df_grouped["Kanton"],
                x=df_grouped.loc[:, cat],
                orientation="h",
                marker_color=colors[cat],
                text=hover_strings,
                hovertemplate="%{text}<extra></extra>",
                legendgroup=str(cat),
                showlegend=False,
            ),
            row=1,
            col=2,
        )
    return go_figure


def define_figure_layout(go_figure):
    go_figure.update_layout(
        margin={"r": 0, "t": 45, "l": 0, "b": 0},
        width=875,
        height=550,
        hovermode="closest",
        template="simple_white",
        barmode="stack",
    )
    return go_figure


def build_combined_figure(df):
    go_figure, colors = set_up_subplots()
    # Scatter plot
    go_figure = add_scatter_traces(df, go_figure, colors)
    # Bar plot
    go_figure = add_barplot_traces(df, go_figure, colors)
    # Subplot title font size
    go_figure.layout.annotations[0].update(font_size=25, x=0.12, y=1.01)
    go_figure.layout.annotations[1].update(font_size=25, x=0.8, y=1.01)
    # Axis Labels
    go_figure.update_xaxes(
        title={"text": "Floor Space (m²)", "font_size": 16}, row=1, col=1
    )
    go_figure.update_yaxes(title={"text": "Rent (CHF)", "font_size": 16}, row=1, col=1)
    go_figure.update_xaxes(
        title={"text": "Number of Listings", "font_size": 16}, row=1, col=2
    )
    # Layout
    go_figure = define_figure_layout(go_figure)
    return go_figure


@st.cache
def convert_df(df):
    return df.drop(columns="hover_strings_scatter").to_csv().encode('utf-8')
