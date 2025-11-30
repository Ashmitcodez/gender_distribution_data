import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Eng Spec Gender Dashboard",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("spec_gender_counts_2019_2023.csv")
    return df

df = load_data()

st.title("Engineering Specialisation Gender Dashboard")

st.caption(
    "Data for 2019 to 2023: Diverse indicates students counted in a diversity category."
)

# sidebar filters
years = st.sidebar.multiselect(
    "Select year(s)",
    options=sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)

specs = st.sidebar.multiselect(
    "Select specialisation(s)",
    options=sorted(df["Specialisation"].unique()),
    default=sorted(df["Specialisation"].unique())
)

view_mode = st.sidebar.radio(
    "View mode",
    ["By specialisation", "Year summary"]
)

filtered = df[df["Year"].isin(years) & df["Specialisation"].isin(specs)].copy()

# derive percentages
filtered["Female_pct"] = filtered["Female"] / filtered["Total_headcount"]
filtered["Male_pct"] = filtered["Male"] / filtered["Total_headcount"]
filtered["Diverse_pct"] = filtered["Diverse"] / filtered["Total_headcount"]

# top level metrics
total_headcount = filtered["Total_headcount"].sum()
total_female = filtered["Female"].sum()
total_male = filtered["Male"].sum()
total_diverse = filtered["Diverse"].sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total students", int(total_headcount))
col2.metric("Female share", f"{total_female / total_headcount:.1%}")
col3.metric("Male share", f"{total_male / total_headcount:.1%}")
col4.metric("Diverse count", int(total_diverse))

# Aggregate data for all selected years
yearly_agg = filtered.groupby("Year", as_index=False)[["Female", "Male", "Diverse"]].sum()
melted_agg = yearly_agg.melt(
    id_vars=["Year"],
    value_vars=["Female", "Male", "Diverse"],
    var_name="Gender",
    value_name="Count"
)

# Color configuration: palette source + colorblind option + custom picks
palette_source = st.sidebar.selectbox(
    "Palette source",
    ("Default (red/blue/lightblue)", "ColorBrewer (Paired)", "Okabe-Ito (Colorblind-friendly)", "Custom")
)

# Allow user to force colorblind-friendly palette
use_colorblind = st.sidebar.checkbox("Use colorblind-friendly palette (Okabe-Ito)", value=False)

# Prioritise explicit colorblind override
if use_colorblind:
    # Okabe-Ito palette (colorblind-safe)
    female_col = "#E69F00"  # orange
    male_col = "#0072B2"    # blue
    diverse_col = "#009E73" # green
    color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], range=[female_col, male_col, diverse_col])
else:
    if palette_source == "Default (red/blue/lightblue)":
        female_col = "#FF6B6B"  # red-ish
        male_col = "#4169E1"    # royal blue
        diverse_col = "#95B8D1" # light blue
        color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], range=[female_col, male_col, diverse_col])
    elif palette_source == "ColorBrewer (Paired)":
        # Use Altair/vega scheme name for ColorBrewer 'Paired' and also pick representative hexes
        # Representative first three colors from 'Paired' (for legend)
        female_col = "#a6cee3"
        male_col = "#1f78b4"
        diverse_col = "#b2df8a"
        color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], scheme="paired")
    elif palette_source == "Okabe-Ito (Colorblind-friendly)":
        female_col = "#E69F00"  # orange
        male_col = "#0072B2"    # blue
        diverse_col = "#009E73" # green
        color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], range=[female_col, male_col, diverse_col])
    else:
        # Custom palette: allow users to pick colors
        female_col = st.sidebar.color_picker("Female color", "#FF6B6B")
        male_col = st.sidebar.color_picker("Male color", "#4169E1")
        diverse_col = st.sidebar.color_picker("Diverse color", "#95B8D1")
        color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], range=[female_col, male_col, diverse_col])

if len(years) == 1:
    st.markdown("### Gender distribution (Selected year)")
    
    # Create pie chart for single year
    pie_data = pd.DataFrame({
        "Gender": ["Female", "Male", "Diverse"],
        "Count": [total_female, total_male, total_diverse]
    })
    
    pie_chart = alt.Chart(pie_data).mark_arc().encode(
        theta="Count:Q",
        color=alt.Color("Gender:N", scale=color_scale),
        tooltip=["Gender", "Count"]
    ).properties(height=400)
    
    st.altair_chart(pie_chart, use_container_width=True)
else:
    st.markdown("### Stacked bar chart (All selected years)")
    
    stacked_chart = alt.Chart(melted_agg).mark_bar().encode(
        x=alt.X("Year:O", title="Year"),
        y=alt.Y("Count:Q", title="Headcount"),
        color=alt.Color("Gender:N", scale=color_scale),
        tooltip=["Year", "Gender", "Count"]
    ).properties(height=400, width=600)
    
    st.altair_chart(stacked_chart, use_container_width=True)

# Ensure legend color variables exist (fallbacks) so the HTML legend can render
if "female_col" not in locals():
    female_col = "#FF6B6B"
if "male_col" not in locals():
    male_col = "#4169E1"
if "diverse_col" not in locals():
    diverse_col = "#95B8D1"

# Small legend to explain current palette
st.markdown("### Current colour mapping")
legend_html = f"""
<div style='display:flex;gap:12px;align-items:center'>
    <div style='display:flex;flex-direction:column;gap:4px'>
        <div><span style='display:inline-block;width:14px;height:14px;background:{female_col};border-radius:3px;margin-right:8px'></span>Female</div>
        <div><span style='display:inline-block;width:14px;height:14px;background:{male_col};border-radius:3px;margin-right:8px'></span>Male</div>
        <div><span style='display:inline-block;width:14px;height:14px;background:{diverse_col};border-radius:3px;margin-right:8px'></span>Diverse</div>
    </div>
    <div style='padding-left:12px;color:#555'>
        <small>Choose a palette or pick custom colours in the sidebar. Check "Use colorblind-friendly palette" to force a colorblind-safe set.</small>
    </div>
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)

st.markdown("### Stacked bar chart by specialisation (All years combined)")

# Aggregate data across all selected years by specialisation
spec_agg = filtered.groupby("Specialisation", as_index=False)[["Female", "Male", "Diverse"]].sum()
melted_spec = spec_agg.melt(
    id_vars=["Specialisation"],
    value_vars=["Female", "Male", "Diverse"],
    var_name="Gender",
    value_name="Count"
)

spec_stacked_chart = alt.Chart(melted_spec).mark_bar().encode(
    x=alt.X("Specialisation:N", title="Specialisation", sort="-y"),
    y=alt.Y("Count:Q", title="Headcount"),
    color=alt.Color("Gender:N", scale=color_scale),
    tooltip=["Specialisation", "Gender", "Count"]
).properties(height=400)

st.altair_chart(spec_stacked_chart, use_container_width=True)

st.markdown("### Gender distribution by specialisation (All years combined)")

# Calculate percentages for each specialisation
spec_pct = spec_agg.copy()
spec_pct["Total"] = spec_pct["Female"] + spec_pct["Male"] + spec_pct["Diverse"]
spec_pct["Female_pct"] = spec_pct["Female"] / spec_pct["Total"]
spec_pct["Male_pct"] = spec_pct["Male"] / spec_pct["Total"]
spec_pct["Diverse_pct"] = spec_pct["Diverse"] / spec_pct["Total"]

melted_pct = spec_pct.melt(
    id_vars=["Specialisation"],
    value_vars=["Female_pct", "Male_pct", "Diverse_pct"],
    var_name="Gender",
    value_name="Percentage"
)
melted_pct["Gender"] = melted_pct["Gender"].str.replace("_pct", "")

pct_stacked_chart = alt.Chart(melted_pct).mark_bar().encode(
    x=alt.X("Specialisation:N", title="Specialisation", sort="-y"),
    y=alt.Y("Percentage:Q", title="Percentage", stack="normalize", axis=alt.Axis(format="%")),
    color=alt.Color("Gender:N", scale=color_scale),
    tooltip=["Specialisation", "Gender", alt.Tooltip("Percentage:Q", format=".1%")]
).properties(height=400)

st.altair_chart(pct_stacked_chart, use_container_width=True)

st.markdown("### Stacked gender counts")

if view_mode == "By specialisation":
    base = alt.Chart(filtered).encode(
        x=alt.X("Specialisation:N", sort="-y"),
        y=alt.Y("sum(Count):Q"),
        color="Gender:N",
        tooltip=["Year", "Specialisation", "Gender", "Count"]
    )

    melted = filtered.melt(
        id_vars=["Year", "Specialisation", "Total_headcount"],
        value_vars=["Female", "Male", "Diverse"],
        var_name="Gender",
        value_name="Count"
    )

    chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X("Specialisation:N", sort="-y", title="Specialisation"),
        y=alt.Y("sum(Count):Q", title="Headcount"),
        color=alt.Color("Gender:N", scale=color_scale),
        column=alt.Column("Year:O", title="Year"),
        tooltip=["Year", "Specialisation", "Gender", "Count"]
    ).properties(width=180)

    st.altair_chart(chart, use_container_width=True)

else:
    # year summary view
    yearly = filtered.groupby("Year", as_index=False)[["Diverse", "Female", "Male"]].sum()
    melted = yearly.melt(
        id_vars=["Year"],
        value_vars=["Female", "Male", "Diverse"],
        var_name="Gender",
        value_name="Count"
    )

    chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X("Year:O"),
        y=alt.Y("Count:Q", stack="normalize", title="Share of headcount"),
        color=alt.Color("Gender:N", scale=color_scale),
        tooltip=["Year", "Gender", "Count"]
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

st.markdown("### Female percentage by specialisation and year")

female_chart = alt.Chart(filtered).mark_line(point=True).encode(
    x=alt.X("Year:O"),
    y=alt.Y("Female_pct:Q", axis=alt.Axis(format="%")),
    color="Specialisation:N",
    tooltip=["Year", "Specialisation", alt.Tooltip("Female_pct:Q", format=".1%")]
).properties(height=400)

st.altair_chart(female_chart, use_container_width=True)

st.markdown("### Raw table")

st.dataframe(
    filtered.sort_values(["Year", "Specialisation"]).reset_index(drop=True)
)
