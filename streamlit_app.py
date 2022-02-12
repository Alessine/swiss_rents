import streamlit as st
from streamlit_lottie import st_lottie
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import requests
from copy import deepcopy


# Functions
@st.cache
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


@st.cache
def load_data(raw_data, proc_data):
    df = pd.read_csv(proc_data)
    with open(raw_data) as response:
        geojson = json.load(response)

    return df, geojson


def set_up_figure(mapbox_token, geojson):
    go_figure = make_subplots(
        rows=2,
        cols=2,
        specs=[[{"colspan": 2, "type": "mapbox"}, None], [{}, {}]],
        horizontal_spacing=0.15,
        vertical_spacing=0.11,
        subplot_titles=("<b>Location of Listed Apartments</b>",
                        "<b>Apartments by Size and Rent</b>",
                        "<b>Apartments per Canton</b>"),
        column_widths=[2, 1],
    )

    # Subplot title font size
    go_figure.layout.annotations[0].update(font_size=24, x=0.175, y=1.01)
    go_figure.layout.annotations[1].update(font_size=24, x=0.17, y=0.455)
    go_figure.layout.annotations[2].update(font_size=24, x=0.8, y=0.455)

    # Axis Labels
    go_figure.update_xaxes(title={"text": "Floor Space (m²)", "font_size": 16}, row=2, col=1)
    go_figure.update_yaxes(title={"text": "Rent (CHF)", "font_size": 16}, row=2, col=1)
    go_figure.update_xaxes(title={"text": "Number of Listings", "font_size": 16}, row=2, col=2)

    go_figure.update_layout(
        margin={"r": 30, "t": 50, "l": 65, "b": 65},
        height=1200,
        hovermode="closest",
        mapbox=dict(
            accesstoken=mapbox_token,
            bearing=0,
            center=go.layout.mapbox.Center(lat=46.8, lon=8.3),
            pitch=0,
            zoom=6.7,
            layers=[{"source": geojson, "type": "line", "line_width": 1}],
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.54,
            xanchor="center",
            x=0.5,
            font_size=16,
            itemsizing="constant",
        ),
        template="simple_white",
        barmode="stack",
    )

    return go_figure


def list_scattermap_traces(df, colors, trace_names):
    scattermap_trace_list = []
    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        scattermap_trace_list.append(
            go.Scattermapbox(
                lon=df_grouped["lon"],
                lat=df_grouped["lat"],
                mode="markers",
                marker=go.scattermapbox.Marker(size=5, color=colors[cat], opacity=0.5),
                text=df_grouped["hover_strings_scatter"],
                hovertemplate="%{text}<extra></extra>",
                name=trace_names[cat],
                legendgroup=str(cat),
            )
        )
    return scattermap_trace_list


def list_scatter_traces(df, colors, trace_names):
    scatter_trace_list = []
    for cat, df_grouped in df.groupby("Miete_Kategorie"):
        scatter_trace_list.append(
            go.Scatter(
                x=df_grouped["Fläche"],
                y=df_grouped["Mietpreis_Brutto"],
                mode="markers",
                marker={"color": colors[cat], "opacity": 0.5},
                text=df_grouped["hover_strings_scatter"],
                hovertemplate="%{text}<extra></extra>",
                name=trace_names[cat],
                legendgroup=str(cat),
                showlegend=False,
            )
        )
    return scatter_trace_list


def list_barplot_traces(df, colors, trace_names):
    df_grouped = (
        df.groupby(["Kanton", "Miete_Kategorie"])
            .size()
            .unstack(level=-1)
            .fillna(0)
            .sort_values("Kanton", ascending=False)
            .reset_index()
    )
    df_grouped["Total_Kanton"] = df_grouped.iloc[:, 1:].sum(axis=1)
    barplot_trace_list = []

    for cat in df["Miete_Kategorie"].unique():
        hover_strings = [
            f"{round(num_per_canton / total_canton * 100, 2)}%"
            for num_per_canton, total_canton in zip(
                df_grouped.loc[:, cat], df_grouped["Total_Kanton"]
            )
        ]
        barplot_trace_list.append(
            go.Bar(
                y=df_grouped["Kanton"],
                x=df_grouped.loc[:, cat],
                orientation="h",
                marker_color=colors[cat],
                text=hover_strings,
                hovertemplate="%{text}<extra></extra>",
                name=trace_names[cat],
                legendgroup=str(cat),
                showlegend=False,
            )
        )
    return barplot_trace_list


def build_combined_figure(df, mapbox_token, geojson):
    colors = px.colors.qualitative.Bold

    trace_names = [
        "cheapest",
        "below average",
        "above average",
        "most expensive",
    ]

    # Create lists with traces
    scattermap_traces = list_scattermap_traces(df, colors, trace_names)
    scatter_traces = list_scatter_traces(df, colors, trace_names)
    barplot_traces = list_barplot_traces(df, colors, trace_names)

    # Put them all into one figure
    go_figure = set_up_figure(mapbox_token, geojson)
    go_figure.add_traces(scattermap_traces, rows=1, cols=1)
    go_figure.add_traces(scatter_traces, rows=2, cols=1)
    go_figure.add_traces(barplot_traces, rows=2, cols=2)

    return go_figure


@st.cache
def convert_df(df):
    return df.drop(columns="hover_strings_scatter").to_csv().encode('utf-8')


# App layout
st.set_page_config(layout="wide")

st.markdown("<h1 style='color: #7F3C8D'>Apartment Listings in Switzerland (2019)</h1>", unsafe_allow_html=True)

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
            st.write(f"Rent/m²: {user_rent / user_floor_space}")

st.text("")

# User dependent variables
raw_data_path = "data/raw/georef-switzerland-kanton.geojson"
proc_data_path = "data/processed/rents_with_coords_clean.csv"

# Secrets
mapbox_access_token = st.secrets["MAPBOX_ACCESS_TOKEN"]

# Load the data
df_proc, cantons = load_data(raw_data_path, proc_data_path)
df_plotting = deepcopy(df_proc)

# Sidebar
# Lottie icon
lottie_url = "https://assets10.lottiefiles.com/packages/lf20_7ttkwwdk.json"
lottie_pin = load_lottieurl(lottie_url)
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
            st.write(f"There are no apartment listings in {place_sel}.")

        else:
            df_plotting = df_plotting[(df_plotting["Ort"] == place_sel) &
                                      (df_plotting["Mietpreis_Brutto"] <= max_rent) &
                                      (df_plotting["Zimmer"] >= num_rooms)]

try:
    assert len(df_plotting.index) > 0, "Dataframe is empty."
    # Plotly Combined Plot
    joint_fig = build_combined_figure(df=df_plotting, mapbox_token=mapbox_access_token, geojson=cantons)
    st.plotly_chart(joint_fig, use_container_width=True)
except AssertionError:
    st.sidebar.write("There are no apartment listings that meet these criteria.")
    df_plotting = deepcopy(df_proc)

st.text("")

st.markdown("---")
st.subheader("Data Source")
# Show the data itself
if st.checkbox("Show Processed Data (first 10 rows)"):
    st.dataframe(data=df_proc.drop(columns="hover_strings_scatter").head(10))

# Download button and link for data
csv = convert_df(df_proc)
st.download_button(
    label="Download Processed Data (csv)",
    data=csv,
    file_name='swiss_rents_df.csv',
    mime='text/csv',
)
st.write("The unprocessed data is freely available at: https://datenportal.info/wohnungsmarkt/wohnungsmieten/")

st.markdown("---")
st.markdown("<b>A Streamlit web app by Angela Niederberger.</b>", unsafe_allow_html=True)
st.markdown("""I love getting feedback! 
The code for this app is available on [GitHub](https://github.com/Alessine/swiss_rents). 
You can reach out to me on [LinkedIn](https://www.linkedin.com/in/angela-niederberger) 
or [Twitter](https://twitter.com/angie_k_n).""")
