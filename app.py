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

# Define consistent color scheme
color_scale = alt.Scale(domain=["Female", "Male", "Diverse"], range=["#FF6B6B", "#4169E1", "#95B8D1"])

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
