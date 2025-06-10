import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import plotly.graph_objects as go
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt

st.set_page_config(page_title="Violència Armada als EUA", layout="wide")

# --- Carrega el dataset ---
@st.cache_data
def load_data():
    df = pd.read_csv("final.csv", parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df

df = load_data()

# --- Filtres laterals ---
# (Eliminat: no hi ha filtres laterals)
# states = df["state"].unique()
# selected_states = st.sidebar.multiselect("Selecciona estat(s)", options=states, default=list(states))
# df = df[df["state"].isin(selected_states)]
states = df["state"].unique()

# --- Títol ---
st.title("🔫 Anàlisi de la Violència Armada als EUA")

# --- Evolució temporal ---
st.header("🗓️ Evolució temporal d'incidents")
monthly = df.groupby("month")["incident_id"].count().reset_index(name="incidents")
fig1 = px.line(monthly, x="month", y="incidents", title="Incidents mensuals")
st.plotly_chart(fig1, use_container_width=True)

# --- Evolució temporal interactiva ---
# Preparar llista d'anys i mesos
MESOS_CAT = [
    "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
    "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
]

df["year"] = df["date"].dt.year
# Mes com a número (1-12)
df["month_num"] = df["date"].dt.month

# Selecció d'any i estat (ara a la pàgina, no a la barra lateral)
st.header("📅 Evolució temporal interactiva d'incidents")
col1, col2 = st.columns(2)
anys = sorted(df["year"].unique())
anys_options = ["Tots"] + [str(a) for a in anys]
estats_options = ["Tots"] + list(states)
with col1:
    selected_year = st.selectbox("Selecciona any", anys_options, index=0, key="interactive_year")
with col2:
    selected_state = st.selectbox("Selecciona estat", estats_options, index=0, key="interactive_state")

# Filtrar segons selecció
filtered_df = df.copy()
if selected_year != "Tots":
    filtered_df = filtered_df[filtered_df["year"] == int(selected_year)]
if selected_state != "Tots":
    filtered_df = filtered_df[filtered_df["state"] == selected_state]

# Ensure numeric
filtered_df["state_month_firearm_background_checks"] = pd.to_numeric(
    filtered_df["state_month_firearm_background_checks"], errors="coerce"
)

# Drop duplicates so each state/month/year is only counted once
checks_unique = filtered_df.drop_duplicates(subset=["state", "year", "month_num"])

# Now group by month and sum (for all states, or just one if filtered)
checks_by_month = (
    checks_unique.groupby("month_num")["state_month_firearm_background_checks"].sum()
    .reindex(range(1, 13), fill_value=0)
    .reset_index()
)

checks_by_month["month_cat"] = checks_by_month["month_num"].apply(lambda x: MESOS_CAT[x-1])

# Incidents per month (as before)
monthly_interactive = (
    filtered_df.groupby("month_num")["incident_id"].count()
    .reindex(range(1, 13), fill_value=0)
    .reset_index()
)
monthly_interactive["month_cat"] = monthly_interactive["month_num"].apply(lambda x: MESOS_CAT[x-1])

# Plot both lines
fig_interactive = go.Figure()

# Incidents (left y-axis)
fig_interactive.add_trace(go.Scatter(
    x=monthly_interactive["month_cat"],
    y=monthly_interactive["incident_id"],
    mode="lines+markers",
    name="Incidents",
    yaxis="y1"
))

# Background checks (right y-axis)
fig_interactive.add_trace(go.Scatter(
    x=checks_by_month["month_cat"],
    y=checks_by_month["state_month_firearm_background_checks"],
    mode="lines+markers",
    name="Comprovacions antecedents d'armes",
    yaxis="y2"
))

fig_interactive.update_layout(
    title="Incidents i comprovacions d'antecedents per mes",
    xaxis_title="Mes",
    yaxis=dict(
        title=dict(text="Incidents", font=dict(color="#1f77b4")),
        tickfont=dict(color="#1f77b4"),
        anchor="x"
    ),
    yaxis2=dict(
        title=dict(text="Comprovacions antecedents d'armes", font=dict(color="#ff7f0e")),
        tickfont=dict(color="#ff7f0e"),
        overlaying="y",
        side="right"
    ),
    legend_title="Línia",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    ),
)
fig_interactive.update_xaxes(categoryorder="array", categoryarray=MESOS_CAT)
st.plotly_chart(fig_interactive, use_container_width=True)

# --- Evolució anual per mesos ---
st.header("📈 Evolució anual d'incidents per mes")
col_yearly = st.columns(1)
with col_yearly[0]:
    selected_state_yearly = st.selectbox(
        "Selecciona estat per evolució anual", ["Tots"] + list(states), index=0, key="yearly_state"
    )

# Filtrar segons selecció d'estat
filtered_df_yearly = df.copy()
if selected_state_yearly != "Tots":
    filtered_df_yearly = filtered_df_yearly[filtered_df_yearly["state"] == selected_state_yearly]

# Agrupar per any i mes
incidents_per_year_month = (
    filtered_df_yearly.groupby(["year", "month_num"])["incident_id"].count().reset_index()
)

# Assegurar que tots els mesos hi són per cada any
all_years = incidents_per_year_month["year"].unique()
full_index = pd.MultiIndex.from_product([all_years, range(1, 13)], names=["year", "month_num"])
incidents_per_year_month = incidents_per_year_month.set_index(["year", "month_num"]).reindex(full_index, fill_value=0).reset_index()
incidents_per_year_month["month_cat"] = incidents_per_year_month["month_num"].apply(lambda x: MESOS_CAT[x-1])

# Gràfic: cada línia és un any
fig_yearly = go.Figure()
for year in sorted(all_years):
    data = incidents_per_year_month[incidents_per_year_month["year"] == year]
    fig_yearly.add_trace(go.Scatter(
        x=data["month_cat"],
        y=data["incident_id"],
        mode="lines+markers",
        name=str(year)
    ))
fig_yearly.update_layout(
    title="Incidents per mes per any",
    xaxis_title="Mes",
    yaxis_title="Incidents",
    legend_title="Any",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    ),
)
fig_yearly.update_xaxes(categoryorder="array", categoryarray=MESOS_CAT)
st.plotly_chart(fig_yearly, use_container_width=True)

# --- Visualització: Evolució d'incidents i taxa d'atur ---
st.header("📉 Evolució d'incidents i taxa d'atur")
col_evol_year, col_evol_state = st.columns(2)
with col_evol_year:
    anys_evol = sorted(df["year"].unique())
    anys_options_evol = ["Tots"] + [str(a) for a in anys_evol]
    selected_year_evol = st.selectbox("Selecciona any", anys_options_evol, index=0, key="evolunemp_year")
with col_evol_state:
    estats_options_evol = ["Tots"] + list(states)
    selected_state_evol = st.selectbox("Selecciona estat", estats_options_evol, index=0, key="evolunemp_state")

filtered_df_evol = df.copy()
if selected_year_evol != "Tots":
    filtered_df_evol = filtered_df_evol[filtered_df_evol["year"] == int(selected_year_evol)]
if selected_state_evol != "Tots":
    filtered_df_evol = filtered_df_evol[filtered_df_evol["state"] == selected_state_evol]

MESOS_CAT = [
    "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
    "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
]

# Incidents per month
filtered_df_evol["month_num"] = filtered_df_evol["date"].dt.month
incidents_by_month = (
    filtered_df_evol.groupby("month_num")["incident_id"].count()
    .reindex(range(1, 13), fill_value=0)
    .reset_index()
)
incidents_by_month["month_cat"] = incidents_by_month["month_num"].apply(lambda x: MESOS_CAT[x-1])

# Unemployment rate per month (mean if multiple states, but deduplicate by state/year/month_num)
filtered_df_evol["state_month_employment_rate"] = pd.to_numeric(filtered_df_evol["state_month_employment_rate"], errors="coerce")
# Deduplicate so each state/month/year is only counted once
unemp_unique = filtered_df_evol.drop_duplicates(subset=["state", "year", "month_num"])
unemp_unique["state_month_unemployment_rate"] = 100 - unemp_unique["state_month_employment_rate"]
unemp_by_month = (
    unemp_unique.groupby("month_num")["state_month_unemployment_rate"].mean()
    .reindex(range(1, 13), fill_value=None)
    .reset_index()
)
unemp_by_month["month_cat"] = unemp_by_month["month_num"].apply(lambda x: MESOS_CAT[x-1])

fig_evol = go.Figure()
fig_evol.add_trace(go.Scatter(
    x=incidents_by_month["month_cat"],
    y=incidents_by_month["incident_id"],
    mode="lines+markers",
    name="Incidents",
    yaxis="y1"
))
fig_evol.add_trace(go.Scatter(
    x=unemp_by_month["month_cat"],
    y=unemp_by_month["state_month_unemployment_rate"],
    mode="lines+markers",
    name="Taxa d'atur (%)",
    yaxis="y2"
))
fig_evol.update_layout(
    title="Evolució mensual d'incidents i taxa d'atur",
    xaxis_title="Mes",
    yaxis=dict(
        title="Incidents",
        tickfont=dict(color="#1f77b4"),
        anchor="x"
    ),
    yaxis2=dict(
        title="Taxa d'atur (%)",
        tickfont=dict(color="#ff7f0e"),
        overlaying="y",
        side="right"
    ),
    legend_title="Línia",
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3,
        xanchor="center",
        x=0.5
    ),
)
fig_evol.update_xaxes(categoryorder="array", categoryarray=MESOS_CAT)
st.plotly_chart(fig_evol, use_container_width=True)

# --- Heatmap d'incidents per estat ---
st.header("🗺️ Incidents per estat als EUA")
col_heatmap1, col_heatmap2 = st.columns([2, 1])
with col_heatmap1:
    anys_heatmap = sorted(df["year"].unique())
    anys_options_heatmap = ["Tots"] + [str(a) for a in anys_heatmap]
    selected_year_heatmap = st.selectbox("Selecciona any per mapa", anys_options_heatmap, index=0, key="heatmap_year")
with col_heatmap2:
    show_election = st.checkbox("Mostra guanyador eleccions 2020 (D/R)", value=True, key="heatmap_election")
    map_metric = st.selectbox(
        "Mètrica a mostrar",
        [
            "Incidents",
            "Incidents per 100.000 habitants",
            "Víctimes mortals per la policia",
            "Víctimes mortals per la policia per 100.000 habitants"
        ],
        index=0,
        key="heatmap_metric"
    )

filtered_df_heatmap = df.copy()
if selected_year_heatmap != "Tots":
    filtered_df_heatmap = filtered_df_heatmap[filtered_df_heatmap["year"] == int(selected_year_heatmap)]

if map_metric == "Incidents":
    incidents_by_state = filtered_df_heatmap.groupby("state")["incident_id"].count().reset_index(name="incidents")
    color_col = "incidents"
    colorbar_title = "Incidents"
elif map_metric == "Incidents per 100.000 habitants":
    pop_by_state_year = filtered_df_heatmap.drop_duplicates(subset=["state", "year"])[["state", "year", "state_year_population"]]
    pop_by_state_year["state_year_population"] = pd.to_numeric(pop_by_state_year["state_year_population"], errors="coerce")
    incidents = filtered_df_heatmap.groupby(["state", "year"])["incident_id"].count().reset_index(name="incidents")
    incidents = incidents.merge(pop_by_state_year, on=["state", "year"], how="left")
    incidents_by_state = incidents.groupby("state").agg({
        "incidents": "sum",
        "state_year_population": "mean"
    }).reset_index()
    incidents_by_state["incidents_per_100k"] = (1e5 * incidents_by_state["incidents"]) / incidents_by_state["state_year_population"]
    color_col = "incidents_per_100k"
    colorbar_title = "Incidents per 100k"
elif map_metric == "Víctimes mortals per la policia":
    filtered_df_heatmap["state_month_total_police_murders"] = pd.to_numeric(filtered_df_heatmap["state_month_total_police_murders"], errors="coerce")
    unique_police = filtered_df_heatmap.drop_duplicates(subset=["state", "year", "month_num"])
    police_by_state = unique_police.groupby("state")["state_month_total_police_murders"].sum().reset_index(name="police_murders")
    incidents_by_state = police_by_state
    color_col = "police_murders"
    colorbar_title = "Víctimes mortals per la policia"
else:  # "Víctimes mortals per la policia per 100.000 habitants"
    filtered_df_heatmap["state_month_total_police_murders"] = pd.to_numeric(filtered_df_heatmap["state_month_total_police_murders"], errors="coerce")
    unique_police = filtered_df_heatmap.drop_duplicates(subset=["state", "year", "month_num"])
    pop_by_state_year = unique_police.drop_duplicates(subset=["state", "year"])[["state", "year", "state_year_population"]]
    pop_by_state_year["state_year_population"] = pd.to_numeric(pop_by_state_year["state_year_population"], errors="coerce")
    police_by_state = unique_police.groupby(["state", "year"])["state_month_total_police_murders"].sum().reset_index(name="police_murders")
    police_by_state = police_by_state.merge(pop_by_state_year, on=["state", "year"], how="left")
    police_by_state = police_by_state.groupby("state").agg({
        "police_murders": "sum",
        "state_year_population": "mean"
    }).reset_index()
    police_by_state["police_murders_per_100k"] = (1e5 * police_by_state["police_murders"]) / police_by_state["state_year_population"]
    incidents_by_state = police_by_state
    color_col = "police_murders_per_100k"
    colorbar_title = "Víctimes mortals per la policia per 100k"

# Mapping from state names to codes
state_name_to_code = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL',
    'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
    'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
    'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
    'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
    'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA',
    'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}

# After incidents_by_state is created, map state names to codes
incidents_by_state['state_code'] = incidents_by_state['state'].map(state_name_to_code)

# Ensure population is numeric (if present)
if 'state_year_population' in incidents_by_state.columns:
    incidents_by_state['state_year_population'] = pd.to_numeric(incidents_by_state['state_year_population'], errors='coerce')

# Merge 2020 election data into incidents_by_state
votes_2020 = df.drop_duplicates(subset=["state"])[["state", "state_votes_democrats_2020", "state_votes_republicans_2020"]]
incidents_by_state = incidents_by_state.merge(votes_2020, on="state", how="left")

# Determine 2020 election winner for each state
incidents_by_state['winner_2020'] = incidents_by_state.apply(
    lambda row: 'D' if pd.to_numeric(row.get('state_votes_democrats_2020', 0), errors='coerce') >= pd.to_numeric(row.get('state_votes_republicans_2020', 0), errors='coerce') else 'R', axis=1
)

# State centroids for annotation (lat/lon)
state_centroids = {
    'AL': (32.806671, -86.791130), 'AK': (61.370716, -152.404419), 'AZ': (33.729759, -111.431221),
    'AR': (34.969704, -92.373123), 'CA': (36.116203, -119.681564), 'CO': (39.059811, -105.311104),
    'CT': (41.597782, -72.755371), 'DE': (39.318523, -75.507141), 'DC': (38.897438, -77.026817),
    'FL': (27.766279, -81.686783), 'GA': (33.040619, -83.643074), 'HI': (21.094318, -157.498337),
    'ID': (44.240459, -114.478828), 'IL': (40.349457, -88.986137), 'IN': (39.849426, -86.258278),
    'IA': (42.011539, -93.210526), 'KS': (38.526600, -96.726486), 'KY': (37.668140, -84.670067),
    'LA': (31.169546, -91.867805), 'ME': (44.693947, -69.381927), 'MD': (39.063946, -76.802101),
    'MA': (42.230171, -71.530106), 'MI': (43.326618, -84.536095), 'MN': (45.694454, -93.900192),
    'MS': (32.741646, -89.678696), 'MO': (38.456085, -92.288368), 'MT': (46.921925, -110.454353),
    'NE': (41.125370, -98.268082), 'NV': (38.313515, -117.055374), 'NH': (43.452492, -71.563896),
    'NJ': (40.298904, -74.521011), 'NM': (34.840515, -106.248482), 'NY': (42.165726, -74.948051),
    'NC': (35.630066, -79.806419), 'ND': (47.528912, -99.784012), 'OH': (40.388783, -82.764915),
    'OK': (35.565342, -96.928917), 'OR': (44.572021, -122.070938), 'PA': (40.590752, -77.209755),
    'RI': (41.680893, -71.511780), 'SC': (33.856892, -80.945007), 'SD': (44.299782, -99.438828),
    'TN': (35.747845, -86.692345), 'TX': (31.054487, -97.563461), 'UT': (40.150032, -111.862434),
    'VT': (44.045876, -72.710686), 'VA': (37.769337, -78.169968), 'WA': (47.400902, -121.490494),
    'WV': (38.491226, -80.954570), 'WI': (44.268543, -89.616508), 'WY': (42.755966, -107.302490)
}

# Create the base figure
fig_map = go.Figure()

# Add the choropleth
fig_map.add_trace(go.Choropleth(
    locations=incidents_by_state["state_code"],
    z=incidents_by_state[color_col],
    locationmode="USA-states",
    colorscale="Greens",
    colorbar_title=colorbar_title,
    text=incidents_by_state["state"],
    hovertext=incidents_by_state["state"],
    hoverinfo="text+z"
))

# Overlay D/R if checked
if show_election:
    for _, row in incidents_by_state.iterrows():
        code = row['state_code']
        winner = row['winner_2020']
        if code in state_centroids and winner in ['D', 'R']:
            lat, lon = state_centroids[code]
            fig_map.add_trace(go.Scattergeo(
                lon=[lon], lat=[lat],
                text=winner,
                mode='text',
                textfont=dict(
                    size=22,
                    color='blue' if winner == 'D' else 'red',
                    family='Arial Black'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))

fig_map.update_layout(
    geo=dict(
        scope='usa',
        bgcolor='rgba(0,0,0,0)',
        projection=go.layout.geo.Projection(type='albers usa'),
        showland=True,
        landcolor='white',
        showcountries=False,
        showlakes=False,
        lakecolor='white',
    ),
    margin=dict(l=0, r=0, t=40, b=0),
    title="Mapa d'incidents per estat"
)
st.plotly_chart(fig_map, use_container_width=True)

# --- Incidents per ciutat ---
st.header("🏙️ Ciutats amb més incidents")
col_cities1, col_cities2 = st.columns(2)
with col_cities1:
    anys_cities = sorted(df["year"].unique())
    anys_options_cities = ["Tots"] + [str(a) for a in anys_cities]
    selected_year_cities = st.selectbox("Selecciona any per ciutats", anys_options_cities, index=0, key="cities_year")
with col_cities2:
    estats_options_cities = ["Tots"] + list(states)
    selected_state_cities = st.selectbox("Selecciona estat per ciutats", estats_options_cities, index=0, key="cities_state")

filtered_df_cities = df.copy()
if selected_year_cities != "Tots":
    filtered_df_cities = filtered_df_cities[filtered_df_cities["year"] == int(selected_year_cities)]
if selected_state_cities != "Tots":
    filtered_df_cities = filtered_df_cities[filtered_df_cities["state"] == selected_state_cities]

top_cities = filtered_df_cities["city_or_county"].value_counts().head(10)
fig2 = px.bar(top_cities, x=top_cities.values, y=top_cities.index, orientation="h", title="Top 10 ciutats")
fig2.update_layout(
    xaxis_title="Nombre d'incidents",
    yaxis_title="Ciutat o Comtat"
)
st.plotly_chart(fig2, use_container_width=True)

# --- Barplot: Edat i gènere per tipus de participant ---
st.header("👥 Edat i gènere per tipus de participant")
col_parttype, col_year, col_state = st.columns(3)
with col_parttype:
    participant_type_options = ["Victim", "Subject-Suspect"]
    selected_participant_type = st.selectbox(
        "Selecciona tipus de participant", participant_type_options, index=0, key="participant_type_bar"
    )
with col_year:
    anys_part = sorted(df["year"].unique())
    anys_options_part = ["Tots"] + [str(a) for a in anys_part]
    selected_year_part = st.selectbox("Selecciona any", anys_options_part, index=0, key="participant_year")
with col_state:
    estats_options_part = ["Tots"] + list(states)
    selected_state_part = st.selectbox("Selecciona estat", estats_options_part, index=0, key="participant_state")

filtered_df_part = df.copy()
if selected_year_part != "Tots":
    filtered_df_part = filtered_df_part[filtered_df_part["year"] == int(selected_year_part)]
if selected_state_part != "Tots":
    filtered_df_part = filtered_df_part[filtered_df_part["state"] == selected_state_part]

# Parse participant_age_group and participant_gender for selected type
age_groups = []
genders = []
for _, row in filtered_df_part.iterrows():
    if pd.isna(row["participant_type"]) or pd.isna(row["participant_age_group"]) or pd.isna(row["participant_gender"]):
        continue
    types = str(row["participant_type"]).split("||")
    age_groups_raw = str(row["participant_age_group"]).split("||")
    genders_raw = str(row["participant_gender"]).split("||")
    for i, t in enumerate(types):
        if selected_participant_type in t:
            # Find matching index for age group and gender
            age_group = None
            gender = None
            # Find age group for this index
            for ag in age_groups_raw:
                if ag.startswith(f"{i}::"):
                    age_group = ag.split("::", 1)[-1]
                    break
            # Find gender for this index
            for g in genders_raw:
                if g.startswith(f"{i}::"):
                    gender = g.split("::", 1)[-1]
                    break
            if age_group and gender:
                age_groups.append(age_group)
                genders.append(gender)

# Build DataFrame for plotting
plot_df = pd.DataFrame({
    "age_group": age_groups,
    "gender": genders
})
plot_df = plot_df.dropna()

# Get all unique age groups in sorted order (Child 0-11, Teen 12-17, Adult 18+)
age_group_order = ["Child 0-11", "Teen 12-17", "Adult 18+", "+65"]
all_age_groups = sorted(plot_df["age_group"].unique(), key=lambda x: age_group_order.index(x) if x in age_group_order else x)

# Count incidents by age group and gender, ensure all bins present
bar_data = plot_df.groupby(["age_group", "gender"]).size().unstack(fill_value=0).reindex(all_age_groups, fill_value=0)

# Translate age group labels to Catalan
age_group_translation = {
    "Child 0-11": "Infant 0-11",
    "Teen 12-17": "Adolescent 12-17",
    "Adult 18+": "Adult 18+"
}
bar_data.index = [age_group_translation.get(x, x) for x in bar_data.index]

if bar_data.sum().sum() == 0:
    st.info("No hi ha participants per aquests filtres.")
else:
    # Barplot with stacked bars (Dona first, then Home), native background, log scale, lighter grid
    fig_part = go.Figure()
    colors = {"Dona": "#ff7f0e", "Home": "#1f77b4"}
    gender_map = {"Female": "Dona", "Male": "Home"}
    for gender in ["Female", "Male"]:
        if gender in bar_data.columns:
            cat_gender = gender_map[gender]
            fig_part.add_trace(go.Bar(
                x=bar_data.index,
                y=bar_data[gender],
                name=cat_gender,
                marker_color=colors.get(cat_gender, None),
                opacity=0.85
            ))
    fig_part.update_layout(
        barmode="relative",  # Stacked bars
        title="Incidents per edat i gènere dels participants",
        xaxis_title="Grup d'edat",
        yaxis_title="Nombre d'incidents",
        legend_title="Gènere",
        yaxis_type="log",
        yaxis=dict(gridcolor="rgba(200,200,200,0.3)", griddash="dot"),
        xaxis=dict(tickmode="array", tickvals=bar_data.index, ticktext=bar_data.index)
    )
    st.plotly_chart(fig_part, use_container_width=True)

# --- Barplot: Víctimes mortals per la policia per gènere i mes ---
st.header("👮‍♂️ Víctimes mortals per la policia per gènere i mes")
col_police_year, col_police_state = st.columns([1,1])
with col_police_year:
    anys_police = sorted(df["year"].unique())
    anys_options_police = ["Tots"] + [str(a) for a in anys_police]
    selected_year_police = st.selectbox("Selecciona any", anys_options_police, index=0, key="police_year")
with col_police_state:
    estats_options_police = ["Tots"] + list(states)
    selected_state_police = st.selectbox("Selecciona estat", estats_options_police, index=0, key="police_state")

filtered_df_police = df.copy()
if selected_year_police != "Tots":
    filtered_df_police = filtered_df_police[filtered_df_police["year"] == int(selected_year_police)]
if selected_state_police != "Tots":
    filtered_df_police = filtered_df_police[filtered_df_police["state"] == selected_state_police]

# Ensure numeric and fillna
for col in ["state_month_police_murders_male_victims", "state_month_police_murders_female_victims"]:
    filtered_df_police[col] = pd.to_numeric(filtered_df_police[col], errors="coerce").fillna(0)

filtered_df_police["month_num"] = filtered_df_police["date"].dt.month

# Deduplicate by state/year/month_num to avoid double counting
police_unique = filtered_df_police.drop_duplicates(subset=["state", "year", "month_num"])

grouped = police_unique.groupby("month_num").agg({
    "state_month_police_murders_male_victims": "sum",
    "state_month_police_murders_female_victims": "sum"
})
male = grouped["state_month_police_murders_male_victims"]
female = grouped["state_month_police_murders_female_victims"]

# Prepare DataFrame for plotting
months = range(1, 13)
MESOS_CAT = [
    "Gener", "Febrer", "Març", "Abril", "Maig", "Juny",
    "Juliol", "Agost", "Setembre", "Octubre", "Novembre", "Desembre"
]
bar_df = pd.DataFrame({
    "Mes": [MESOS_CAT[m-1] for m in months],
    "Home": male.reindex(months, fill_value=0).values,
    "Dona": female.reindex(months, fill_value=0).values
})

if bar_df[["Home", "Dona"]].sum().sum() == 0:
    st.info("No hi ha víctimes mortals per la policia per aquests filtres.")
else:
    fig_police = go.Figure()
    fig_police.add_trace(go.Bar(
        x=bar_df["Mes"],
        y=bar_df["Home"],
        name="Home",
        marker_color="#1f77b4",
        opacity=0.85
    ))
    fig_police.add_trace(go.Bar(
        x=bar_df["Mes"],
        y=bar_df["Dona"],
        name="Dona",
        marker_color="#ff7f0e",
        opacity=0.85
    ))
    fig_police.update_layout(
        barmode="overlay",  # Overlapped bars
        title="Víctimes mortals per la policia per gènere i mes",
        xaxis_title="Mes",
        yaxis_title="Nombre de víctimes",
        legend_title="Gènere",
        yaxis=dict(gridcolor="rgba(200,200,200,0.3)", griddash="dot"),
        xaxis=dict(tickmode="array", tickvals=bar_df["Mes"], ticktext=bar_df["Mes"])
    )
    st.plotly_chart(fig_police, use_container_width=True)

# --- Barplot: Top 3 armes més utilitzades ---
st.header("🔫 Top 3 armes més utilitzades")
col_weapon_year, col_weapon_state = st.columns(2)
with col_weapon_year:
    anys_weapon = sorted(df["year"].unique())
    anys_options_weapon = ["Tots"] + [str(a) for a in anys_weapon]
    selected_year_weapon = st.selectbox("Selecciona any", anys_options_weapon, index=0, key="weapon_year")
with col_weapon_state:
    estats_options_weapon = ["Tots"] + list(states)
    selected_state_weapon = st.selectbox("Selecciona estat", estats_options_weapon, index=0, key="weapon_state")

filtered_df_weapon = df.copy()
if selected_year_weapon != "Tots":
    filtered_df_weapon = filtered_df_weapon[filtered_df_weapon["year"] == int(selected_year_weapon)]
if selected_state_weapon != "Tots":
    filtered_df_weapon = filtered_df_weapon[filtered_df_weapon["state"] == selected_state_weapon]

# Parse gun_type (index::value||index::value...)
weapon_counts = {}
for _, row in filtered_df_weapon.iterrows():
    if pd.isna(row["gun_type"]):
        continue
    gun_types = str(row["gun_type"]).split("||")
    for gt in gun_types:
        if "::" in gt:
            weapon = gt.split("::", 1)[-1]
            if weapon and weapon.strip().lower() != "unknown":
                weapon_norm = weapon.strip().lower()
                if weapon_norm in ["handgun", "9mm"]:
                    weapon = "Handgun/9mm"
                weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1

# Get top 3 weapons
import collections
top_weapons = collections.Counter(weapon_counts).most_common(3)
if not top_weapons:
    st.info("No s'han trobat armes per aquests filtres.")
else:
    weapons, counts = zip(*top_weapons)
    fig_weapons = go.Figure(go.Bar(
        x=counts,
        y=weapons,
        orientation="h",
        marker_color="#1f77b4"
    ))
    fig_weapons.update_layout(
        title="Top 3 armes més utilitzades",
        xaxis_title="Nombre d'incidents",
        yaxis_title="Arma"
    )
    st.plotly_chart(fig_weapons, use_container_width=True)

# --- Barplot: Incidents amb armes robades vs legals ---
st.header("🔒 Incidents amb armes robades vs legals")
col_stolen_year, col_stolen_state = st.columns(2)
with col_stolen_year:
    anys_stolen = sorted(df["year"].unique())
    anys_options_stolen = ["Tots"] + [str(a) for a in anys_stolen]
    selected_year_stolen = st.selectbox("Selecciona any", anys_options_stolen, index=0, key="stolen_year")
with col_stolen_state:
    estats_options_stolen = ["Tots"] + list(states)
    selected_state_stolen = st.selectbox("Selecciona estat", estats_options_stolen, index=0, key="stolen_state")

filtered_df_stolen = df.copy()
if selected_year_stolen != "Tots":
    filtered_df_stolen = filtered_df_stolen[filtered_df_stolen["year"] == int(selected_year_stolen)]
if selected_state_stolen != "Tots":
    filtered_df_stolen = filtered_df_stolen[filtered_df_stolen["state"] == selected_state_stolen]

stolen_count = 0
not_stolen_count = 0
for _, row in filtered_df_stolen.iterrows():
    if pd.isna(row["gun_stolen"]):
        continue
    gun_stolen_types = str(row["gun_stolen"]).split("||")
    has_stolen = any(gt.split("::", 1)[-1].strip().lower() == "stolen" for gt in gun_stolen_types if "::" in gt)
    has_not_stolen = any(gt.split("::", 1)[-1].strip().lower() == "not-stolen" for gt in gun_stolen_types if "::" in gt)
    if has_stolen:
        stolen_count += 1
    if has_not_stolen:
        not_stolen_count += 1

bar_x = ["Arma robada", "Arma legal"]
bar_y = [stolen_count, not_stolen_count]

fig_stolen = go.Figure(go.Bar(
    x=bar_x,
    y=bar_y,
    marker_color=["#d62728", "#2ca02c"]
))
fig_stolen.update_layout(
    title="Incidents amb armes robades vs legals",
    xaxis_title="Tipus d'arma",
    yaxis_title="Nombre d'incidents"
)
st.plotly_chart(fig_stolen, use_container_width=True)

# --- Visualització: Relació entre nombre d'armes i nombre de víctimes ---
st.header("📈 Relació entre nombre d'armes i nombre de víctimes")
col_line_year, col_line_state = st.columns(2)
with col_line_year:
    anys_line = sorted(df["year"].unique())
    anys_options_line = ["Tots"] + [str(a) for a in anys_line]
    selected_year_line = st.selectbox("Selecciona any", anys_options_line, index=0, key="lineweap_year")
with col_line_state:
    estats_options_line = ["Tots"] + list(states)
    selected_state_line = st.selectbox("Selecciona estat", estats_options_line, index=0, key="lineweap_state")

filtered_df_line = df.copy()
if selected_year_line != "Tots":
    filtered_df_line = filtered_df_line[filtered_df_line["year"] == int(selected_year_line)]
if selected_state_line != "Tots":
    filtered_df_line = filtered_df_line[filtered_df_line["state"] == selected_state_line]

line_data = []
for _, row in filtered_df_line.iterrows():
    if pd.isna(row["gun_type"]) or pd.isna(row["n_killed"]):
        continue
    gun_types = [gt for gt in str(row["gun_type"]).split("||") if "::" in gt and gt.split("::", 1)[-1].strip().lower() != "unknown" and gt.split("::", 1)[-1].strip()]
    num_weapons = len(set(["Handgun/9mm" if gt.split("::", 1)[-1].strip().lower() in ["handgun", "9mm"] else gt.split("::", 1)[-1].strip() for gt in gun_types]))
    try:
        num_victims = int(row["n_killed"])
    except:
        continue
    if num_weapons > 6:
        num_weapons = '6+'
    line_data.append((num_weapons, num_victims))
import pandas as pd
if line_data:
    line_df = pd.DataFrame(line_data, columns=["num_weapons", "num_victims"])
    # Ensure '6+' is last and all 1-6 are present
    order = [1,2,3,4,5,6,'6+']
    total_victims = line_df.groupby("num_weapons")["num_victims"].sum().reindex(order, fill_value=0).reset_index()
    fig_line = go.Figure(go.Scatter(
        x=total_victims["num_weapons"],
        y=total_victims["num_victims"],
        mode="lines+markers",
        line=dict(color="#1f77b4"),
        marker=dict(size=8)
    ))
    fig_line.update_layout(
        title="Total de víctimes segons nombre d'armes",
        xaxis_title="Nombre d'armes",
        yaxis_title="Total de víctimes"
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("No hi ha dades suficients per mostrar la relació.")

# --- Wordcloud: Notes i Característiques de l'incident ---
st.header("☁️ Paraules més freqüents en notes i característiques d'incidents")

# Merge notes and incident_characteristics, handle NaN
text_data = (
    df["notes"].fillna("") + " " + df["incident_characteristics"].fillna("")
).str.cat(sep=" ")

# Add custom stopwords if desired
stopwords = set(STOPWORDS)
stopwords.update(["unknown", "nan", "none", "unspecified", "other", "n/a", "not", "gun", "guns", "shot", "firearm", "firearms"])

# Generate wordcloud
wordcloud = WordCloud(
    width=900, height=400,
    background_color="white",
    stopwords=stopwords,
    collocations=False,
    max_words=150
).generate(text_data)

fig_wc, ax_wc = plt.subplots(figsize=(12, 5))
ax_wc.imshow(wordcloud, interpolation="bilinear")
ax_wc.axis("off")
plt.tight_layout(pad=0)
st.pyplot(fig_wc)