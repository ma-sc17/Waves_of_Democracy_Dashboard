import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pycountry


df = pd.read_csv("data/processed/vdem_panel.csv")

st.title("Waves of Democracy Tracker")


variable_labels = {
    "v2x_libdem": "Liberal Democracy Index",
    "v2x_polyarchy": "Electoral Democracy / Polyarchy",
    "v2x_partipdem": "Participatory Democracy",
    "v2x_delibdem": "Deliberative Democracy",
    "v2x_egaldem": "Egalitarian Democracy"
}

selected_var = st.selectbox(
    "Choose V-Dem measure of democracy",
    list(variable_labels.keys()),
    format_func=lambda x: variable_labels[x]
)

# Country selector
country = st.selectbox(
    "Choose a country",
    sorted(df["country_name"].dropna().unique())
)
sub_country = df[df["country_name"] == country].sort_values("year")

# Country trend chart
st.subheader("Country trend")
fig_line = px.line(
    sub_country,
    x="year",
    y=selected_var,
    title=f"{selected_var}: {country}"
)

fig_line.update_yaxes(range = [0,1])

st.plotly_chart(fig_line, width="stretch")

#Data table

st.subheader("Selected data")
st.dataframe(sub_country)

# Map section
st.subheader("World map")

year = st.slider(
    "Select year",
    int(df["year"].min()),
    int(df["year"].max()),
    int(df["year"].max())
)

sub_year = df[df["year"] == year].dropna(subset=["country_text_id"])

fig_map = px.choropleth(
    sub_year.dropna(subset=["country_text_id"]),
    locations="country_text_id",
    color=selected_var,
    hover_name="country_name",
    locationmode="ISO-3",
    color_continuous_scale=[
        [0.0, "#002f61"],
        [0.5, "#00b599"],
        [1.0, "#97f554"]
    ],
    projection="natural earth",
    title=f"{selected_var} {year}"
)
#color scale    #002f61, #005f85, #008b98, #00b599, #18dc82, #97f554, #ffff00

fig_map.update_layout(
    title_text='Democracy Levels',
    geo=dict(
        showframe=False,
        showcoastlines=False,
        projection_type='equirectangular',
        showocean=True, oceancolor="#0e1117",
    ),
    annotations = [dict(
        x=0.55,
        y=0.1,
        xref='paper',
        yref='paper',
        text='Source: <a href="https://www.v-dem.net/data/the-v-dem-dataset/">\
            The V-Dem Dataset</a>',
        showarrow = False
    )]
)

fig_map.update_layout(
    template="seaborn",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    margin=dict(l=0, r=0, t=30, b=0),
)

#cleaner country edges
fig_map.update_traces(
    marker_line_color='white',
    marker_line_width=0.5
)

st.plotly_chart(fig_map, width="stretch")

#Visualizer Global Waves

st.subheader("Country-level change")

min_year = int(df["year"].min())
max_year = int(df["year"].max())

if "year" not in st.session_state:
    st.session_state.year = max_year

def sync_from_slider():
    st.session_state.year_input = st.session_state.year_slider

def sync_from_input():
    st.session_state.year_slider = st.session_state.year_input

st.slider(
    "Select year",
    min_value=min_year,
    max_value=max_year,
    value=st.session_state.year,
    key="year_slider",
    on_change=sync_from_slider
)

st.number_input(
    "Type year",
    min_value=min_year,
    max_value=max_year,
    value=st.session_state.year,
    step=1,
    key="year_input",
    on_change=sync_from_input
)

year = st.session_state.year_slider

selected_var = st.selectbox(
    "Choose V-Dem variable",
    ["v2x_libdem", "v2x_polyarchy", "v2x_partipdem", "v2x_delibdem", "v2x_egaldem"],
    format_func=lambda x: variable_labels[x]
)

current = df[df["year"] == year][["country_text_id", "country_name", selected_var]].rename(
    columns={selected_var: "current_value"}
)

previous = df[df["year"] == year - 1][["country_text_id", selected_var]].rename(
    columns={selected_var: "previous_value"}
)

chg = current.merge(previous, on="country_text_id", how="inner")
chg["direction"] = chg["current_value"] - chg["previous_value"]

increased = (chg["direction"] > 0).sum()
decreased = (chg["direction"] < 0).sum()
unchanged = (chg["direction"] == 0).sum()

summary = pd.DataFrame({
    "direction": ["Increased", "Unchanged", "Decreased"],
    "count": [increased, unchanged, decreased]
})

fig_change = px.bar(
    summary,
    x="direction",
    y="count",
    color="direction",
    color_discrete_map={
        "Increased": "#18dc82",
        "Unchanged": "#00b599",
        "Decreased": "#002f61"
    },
    title=f"Countries changing in {variable_labels[selected_var]}: {year} vs {year - 1}"
)

st.plotly_chart(fig_change, theme=None, width="stretch")

#Wave visualizer

st.subheader("Waves of Democratization/Autocratization?")

selected_var = st.selectbox(
    "Choose V-Dem variable",
    ["v2x_libdem", "v2x_polyarchy", "v2x_partipdem"],
    format_func=lambda x: variable_labels[x]
)

# Calculate year-over-year changes
df_yearfilter = df[df["year"] >= 1900].copy()
df_sorted = df_yearfilter.sort_values(["country_text_id", "year"])
df_sorted[f"{selected_var}_change"] = df_sorted.groupby("country_text_id")[selected_var].diff()

# Count improvers/decliners per year

change_counts = df_sorted.dropna(subset=[f"{selected_var}_change"]).groupby("year").agg({
    f"{selected_var}_change": ["sum", lambda x: (x > 0).sum(), lambda x: (x < 0).sum()]
}).round(1)

change_counts.columns = ["total_change", "improved_countries", "declined_countries"]
change_counts = change_counts.reset_index()

# Wave visualization

fig_wave = px.bar(
    change_counts,
    x="year",
    y=["improved_countries", "declined_countries"],
    barmode="stack",
    title=f"Countries Improving vs Declining in {variable_labels[selected_var]}",
    color_discrete_map={
        "improved_countries": "#18dc82",
        "declined_countries": "#002f61"
    }
)

fig_wave.update_layout(
    yaxis=dict(range=[0, 190], tickformat=".0f"),
    xaxis=dict(range=[1900,2024]),
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117"
)
st.plotly_chart(fig_wave, theme=None, width="stretch")


#Percentage Waves


st.subheader("Waves of Democratization/Autocratization (Stacked % of Countries)")

# Calculate percentages and smooth averages from your change_counts
change_counts["total_countries"] = change_counts["improved_countries"] + change_counts["declined_countries"]
change_counts["improved_pct"] = (change_counts["improved_countries"] / change_counts["total_countries"] * 100).round(1)
change_counts["declined_pct"] = (change_counts["declined_countries"] / change_counts["total_countries"] * 100).round(1)

# 3-year rolling averages
change_counts["improved_pct_smooth"] = change_counts["improved_pct"].rolling(3, center=True).mean().round(1)
change_counts["declined_pct_smooth"] = change_counts["declined_pct"].rolling(3, center=True).mean().round(1)

# Stacked area chart (100% total)
fig_area = px.area(
    change_counts,
    x="year",
    y=["improved_pct_smooth", "declined_pct_smooth"],
    title=f"% Countries Improving vs Declining in {variable_labels[selected_var]}",
    color_discrete_map={
        "improved_pct_smooth": "#18dc82",
        "declined_pct_smooth": "#002f61"
    }
)

fig_area.update_layout(
    yaxis=dict(range=[0, 100], tickformat=".0f", ticksuffix="%"),
    xaxis=dict(range=[1900,2024]),
    template="plotly_dark",
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117"
)


#Year highlighting with annotations

highlight_years = [1914, 1939, 1974, 1989, 2001, 2008, 2016]
for year in highlight_years:
    fig_area.add_shape(
        type="line",
        x0=year, x1=year,
        y0=0, y1=100,
        xref="x", yref="y",
        line=dict(color="#97f554", width=2, dash="dot")
    )

highlight_years = {
    1914: "World War I starts",
    1939: "World War II ends",
    1974: "Global Oil crisis",
    1989: "Cold War ends",
    2001: "9/11 attacks",
    2008: "Global financial crisis",
    2016: "Brexit & Election of Donald Trump",
}

for i, (year, event) in enumerate(highlight_events.items()):
    fig_area.add_annotation(
        x=year,
        y=1.05,
        yref="paper",
        text=event,
        textangle=-45,
        font=dict(color="white", size=11),
        showarrow=True,
        arrowcolor="#97f554",
        arrowwidth=2,
        arrowhead=2,
        xanchor="center",
        yanchor="bottom",
        bgcolor="rgba(0,0,0,0.7)"
    )
st.plotly_chart(fig_area, theme=None, width="stretch")
