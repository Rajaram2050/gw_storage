import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable
import contextily as ctx
from PIL import Image

# Configuration
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = DATA_DIR / "storage_change"
EXPORT_DIR = DATA_DIR / "exports"
LOGO_PATH = ASSETS_DIR / "de_logo.png"

# Page configuration
st.set_page_config(page_title="Groundwater Storage Change Explorer", layout="wide")

# Custom polished header with logo and icons
header_col1, header_col2 = st.columns([3, 1.2])

with header_col1:
    st.markdown(
        """
        <div style="padding-top: 12px; padding-bottom: 8px;">
            <h1 style="font-size: 42px; color: #1f2937; margin-bottom: 6px;">
                Sacramento Groundwater Explorer 💧
            </h1>
            <p style="font-size: 21px; color: #6b7280; margin-top: 0;">
                Making the unseen seen
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_col2:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=210)
    else:
        st.markdown(
            "<div style='padding: 20px; text-align: center; color: #9ca3af;'>"
            "<p style='font-size: 14px;'>DE Logo</p></div>",
            unsafe_allow_html=True
        )

st.markdown("---")


def get_paths(aoi, aquifer, period):
    """Return paths to data files based on selections."""
    excel_file = STORAGE_DIR / f"{aoi}_{aquifer}_{period}_annual_storage_change_summary.xlsx"
    gpkg_file = EXPORT_DIR / f"{aoi}_{aquifer}_{period}_storage_polygon_data.gpkg"
    mp4_file = STORAGE_DIR / f"{aoi}_{aquifer}_{period}_storage_change_timeseries.mp4"
    return excel_file, gpkg_file, mp4_file


def load_annual_summary(excel_path):
    """Load annual summary from Excel file."""
    if not excel_path.exists():
        st.error(f"File not found: {excel_path}")
        st.stop()
    
    df = pd.read_excel(excel_path)
    return df


def load_water_year_type():
    """Load water year type data from reference file."""
    wyi_path = DATA_DIR / "Sac_SJ_Valley_WYI_v1.0.xlsx"
    
    if not wyi_path.exists():
        st.error(f"Water year type file not found: {wyi_path}")
        st.stop()
    
    df = pd.read_excel(wyi_path, sheet_name="sac_valley_wyi")
    return df[["wy", "wy_type"]].rename(columns={"wy": "year"})


def merge_water_year_type(annual_df, wyi_df):
    """Merge water year type into annual summary."""
    return annual_df.merge(wyi_df, on="year", how="left")


def load_polygon_data(gpkg_path):
    """Load polygon GeoPackage."""
    if not gpkg_path.exists():
        st.error(f"File not found: {gpkg_path}")
        st.stop()
    
    gdf = gpd.read_file(gpkg_path)
    return gdf


def plot_annual_cumulative_interactive(annual_df):
    """Create interactive annual/cumulative plot with visible water-year shading."""

    wy_colors = {
        "W":  "#b3d9ff",
        "AN": "#d6f5d6",
        "BN": "#fff2b3",
        "D":  "#ffd6a5",
        "C":  "#ffb3b3",
    }

    wy_labels = {
        "W": "Wet",
        "AN": "Above Normal",
        "BN": "Below Normal",
        "D": "Dry",
        "C": "Critical",
    }

    # Clean and prepare data
    annual_df = annual_df.sort_values("year").copy()
    annual_df["year"] = pd.to_numeric(annual_df["year"], errors="coerce")
    annual_df = annual_df.dropna(subset=["year"])
    annual_df["year"] = annual_df["year"].astype(int)
    annual_df["wy_type"] = annual_df["wy_type"].astype(str).str.strip().str.upper()

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.20,
        subplot_titles=(
            "Annual Storage Change",
            "Cumulative Storage Change"
        )
    )

    # Add background shading using fig.add_shape() with explicit subplot references
    for _, row in annual_df.iterrows():
        year = int(row["year"])
        wy_type = row.get("wy_type", None)

        if pd.notna(wy_type) and wy_type in wy_colors:
            color = wy_colors[wy_type]

            # Top panel shading
            fig.add_shape(
                type="rect",
                x0=year - 0.5,
                x1=year + 0.5,
                y0=0,
                y1=1,
                xref="x",
                yref="y domain",
                fillcolor=color,
                opacity=0.30,
                layer="below",
                line_width=0
            )

            # Bottom panel shading
            fig.add_shape(
                type="rect",
                x0=year - 0.5,
                x1=year + 0.5,
                y0=0,
                y1=1,
                xref="x2",
                yref="y2 domain",
                fillcolor=color,
                opacity=0.30,
                layer="below",
                line_width=0
            )

    # Annual storage change bars
    fig.add_trace(
        go.Bar(
            x=annual_df["year"],
            y=annual_df["vol_delta_af_sum"],
            name="Annual Change",
            marker_color="#1f77b4",
            marker_line_color="white",
            marker_line_width=0.4,
            hovertemplate=(
                "<b>Year: %{x}</b><br>"
                "Annual Change: %{y:,.0f} AF"
                "<extra></extra>"
            ),
            showlegend=False
        ),
        row=1,
        col=1
    )

    # Cumulative storage change bars
    fig.add_trace(
        go.Bar(
            x=annual_df["year"],
            y=annual_df["cum_delta_af"],
            name="Cumulative Change",
            marker_color="#1f77b4",
            marker_line_color="white",
            marker_line_width=0.4,
            hovertemplate=(
                "<b>Year: %{x}</b><br>"
                "Cumulative Change: %{y:,.0f} AF"
                "<extra></extra>"
            ),
            showlegend=False
        ),
        row=2,
        col=1
    )

    # Zero reference lines
    fig.add_hline(y=0, line_color="black", line_width=1, row=1, col=1)
    fig.add_hline(y=0, line_color="black", line_width=1, row=2, col=1)

    # Add legend entries for water-year types
    for wy_type, color in wy_colors.items():
        fig.add_trace(
            go.Bar(
                x=[None],
                y=[None],
                marker_color=color,
                opacity=0.5,
                name=f"{wy_type}: {wy_labels[wy_type]}"
            ),
            row=1,
            col=1
        )

    # Y-axis formatting
    fig.update_yaxes(
        title_text="Annual change (AF)",
        tickformat=",.0f",
        gridcolor="rgba(200,200,200,0.35)",
        zeroline=False,
        row=1,
        col=1
    )

    fig.update_yaxes(
        title_text="Cumulative change (AF)",
        tickformat=",.0f",
        gridcolor="rgba(200,200,200,0.35)",
        zeroline=False,
        row=2,
        col=1
    )

    # Improve year ticks: show every 5 years plus first and last
    years = annual_df["year"].astype(int).tolist()
    tick_years = [yr for yr in years if yr % 5 == 0]
    if years[0] not in tick_years:
        tick_years = [years[0]] + tick_years
    if years[-1] not in tick_years:
        tick_years = tick_years + [years[-1]]
    tick_years = sorted(tick_years)

    fig.update_xaxes(
        title_text="Year",
        tickmode="array",
        tickvals=tick_years,
        ticktext=[str(y) for y in tick_years],
        tickangle=45,
        showticklabels=True,
        row=1,
        col=1
    )

    fig.update_xaxes(
        title_text="Year",
        tickmode="array",
        tickvals=tick_years,
        ticktext=[str(y) for y in tick_years],
        tickangle=45,
        showticklabels=True,
        row=2,
        col=1
    )

    fig.update_layout(
        height=820,
        hovermode="x unified",
        barmode="overlay",
        bargap=0.25,
        plot_bgcolor="rgba(248,248,250,1)",
        paper_bgcolor="white",
        font=dict(size=12),
        margin=dict(l=75, r=40, t=80, b=90),
        legend=dict(
            title="Water Year Type",
            orientation="v",
            x=0.01,
            y=0.99,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.80)",
            bordercolor="rgba(200,200,200,0.6)",
            borderwidth=1,
            font=dict(size=10)
        )
    )

    return fig


def plot_selected_year_map_interactive(gdf, selected_year, aoi, aquifer, period):
    """Create map for selected year using matplotlib with custom colormap."""
    gdf_year = gdf[gdf["year_cur"] == selected_year].copy()
    
    if gdf_year.empty:
        st.warning(f"No polygon data available for year {selected_year}")
        return None
    
    # Calculate color scale based on 90th percentile (consistent across all years)
    abs_values = gdf["vol_delta_af"].abs()
    vmax = abs_values.quantile(0.90)
    if pd.isna(vmax) or vmax == 0:
        vmax = abs_values.max()
    vmin = -vmax
    
    # Custom colormap: Orange -> Gray -> Blue (from your original code)
    neg_color = "#f59e0b"    # orange
    mid_color = "#f0f0f0"    # light gray
    pos_color = "#2b6cb0"    # blue
    cmap = LinearSegmentedColormap.from_list("orange_to_blue", [neg_color, mid_color, pos_color], N=256)
    
    # Create figure with compact size
    fig, ax = plt.subplots(figsize=(4, 4), dpi=120)
    
    # Create colorbar axis (narrower)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="2.5%", pad=0.04)
    
    # Plot polygons with custom colormap
    gdf_year.plot(
        column="vol_delta_af",
        ax=ax,
        legend=True,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        edgecolor="gray",
        linewidth=0.15,
        alpha=0.65,
        cax=cax,
        legend_kwds={"label": "Groundwater Storage Change Volume (AF)"}
    )
    
    # Add OSM basemap after plotting (so it's behind)
    try:
        ctx.add_basemap(ax, crs=gdf_year.crs, source=ctx.providers.OpenStreetMap.Mapnik, zoom=9, alpha=0.3, attribution=False)
    except Exception as e:
        pass  # Continue without basemap if it fails
    
    # Replot polygons on top to ensure visibility
    gdf_year.plot(
        column="vol_delta_af",
        ax=ax,
        legend=False,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        edgecolor="gray",
        linewidth=0.15,
        alpha=0.65
    )
    
    # Format colorbar
    cax.tick_params(labelsize=6)
    cax.tick_params(length=0)
    cax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    cax.set_ylabel("Storage Change (AF)", fontsize=6, labelpad=6)
    
    # Plot polygon boundaries (dashed like original)
    gdf_year.boundary.plot(
        ax=ax,
        linestyle="dashed",
        color="gray",
        linewidth=0.1,
        alpha=0.3
    )
    
    # Add well points with minimal visibility
    if "site_code" in gdf_year.columns:
        gdf_year_points = gdf_year.copy()
        gdf_year_points.geometry = gdf_year_points.geometry.centroid
        gdf_year_points.plot(
            ax=ax,
            color="black",
            markersize=0.8,
            alpha=0.35,
            zorder=5
        )
    
    # Title only - no axis labels
    ax.set_title(
        f"{aoi} | {aquifer} | {period.capitalize()} {int(selected_year)}",
        fontsize=8,
        fontweight="bold",
        pad=6
    )
    
    # Remove all axis labels and ticks
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(labelsize=0, length=0)
    
    # Light grid
    ax.grid(alpha=0.1, linestyle=":", linewidth=0.15)
    
    # Tight layout
    plt.tight_layout()
    
    return fig


def get_year_summary(annual_summary, year):
    """Get summary row for a specific year."""
    row = annual_summary[annual_summary["year"] == year]
    if row.empty:
        return None
    return row.iloc[0]


# ============================================================================
# SIDEBAR CONTROLS
# ============================================================================
st.sidebar.header("Controls")

aoi = st.sidebar.selectbox("AOI", ["Sacramento"])
aquifer = st.sidebar.selectbox("Aquifer", ["Primary"])
period = st.sidebar.selectbox("Storage Period", ["spring", "fall"])

# Load data to populate year dropdown
excel_path, gpkg_path, mp4_path = get_paths(aoi, aquifer, period)
annual_summary = load_annual_summary(excel_path)

selected_year = st.sidebar.selectbox("Selected Year (for map)", sorted(annual_summary["year"].unique()))

# ============================================================================
# LOAD AND PREPARE DATA
# ============================================================================
wyi_data = load_water_year_type()
annual_summary = merge_water_year_type(annual_summary, wyi_data)
polygon_data = load_polygon_data(gpkg_path)

# ============================================================================
# OVERALL RESULTS SECTION
# ============================================================================
st.header("📊 Overall Results")

latest_year = annual_summary["year"].max()
latest_row = annual_summary[annual_summary["year"] == latest_year].iloc[0]

# Find largest decline and recovery
largest_decline_idx = annual_summary["vol_delta_af_sum"].idxmin()
largest_decline_year = annual_summary.loc[largest_decline_idx, "year"]
largest_decline_value = annual_summary.loc[largest_decline_idx, "vol_delta_af_sum"]

largest_recovery_idx = annual_summary["vol_delta_af_sum"].idxmax()
largest_recovery_year = annual_summary.loc[largest_recovery_idx, "year"]
largest_recovery_value = annual_summary.loc[largest_recovery_idx, "vol_delta_af_sum"]

avg_wells = annual_summary["num_wells_used"].mean()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Latest Year", int(latest_year))
with col2:
    st.metric("Latest Annual Change (AF)", f"{latest_row['vol_delta_af_sum']:,.0f}")
with col3:
    st.metric("Cumulative Change (AF)", f"{latest_row['cum_delta_af']:,.0f}")

col4, col5, col6 = st.columns(3)
with col4:
    st.metric("Largest Decline (AF)", f"{largest_decline_value:,.0f}", f"Year: {int(largest_decline_year)}")
with col5:
    st.metric("Largest Recovery (AF)", f"{largest_recovery_value:,.0f}", f"Year: {int(largest_recovery_year)}")
with col6:
    st.metric("Avg Wells per Year", f"{avg_wells:.0f}")

# Annual summary table in Overall Results
st.subheader("Annual Summary")
display_cols = ["year", "wy_type", "num_wells_used", "vol_delta_af_sum", "cum_delta_af"]
summary_table = annual_summary[display_cols].copy()
summary_table.columns = ["Year", "WY Type", "Num Wells", "Annual Change (AF)", "Cumulative Change (AF)"]
summary_table["Year"] = summary_table["Year"].astype(int)

st.dataframe(summary_table, use_container_width=True, hide_index=True)

# Interactive trend plot
st.subheader("Annual and Cumulative Storage Change")
fig_trend = plot_annual_cumulative_interactive(annual_summary)
st.plotly_chart(fig_trend, use_container_width=True)

# ============================================================================
# SELECTED-YEAR EXPLORER SECTION
# ============================================================================
st.header("🔍 Selected-Year Explorer")

selected_row = annual_summary[annual_summary["year"] == selected_year].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Annual Storage Change (AF)", f"{selected_row['vol_delta_af_sum']:,.0f}")

with col2:
    st.metric("Cumulative Storage Change (AF)", f"{selected_row['cum_delta_af']:,.0f}")

with col3:
    wy_type = selected_row.get("wy_type", "Unknown")
    st.metric("Water Year Type", wy_type)

with col4:
    st.metric("Number of Wells Used", int(selected_row["num_wells_used"]))

# Annual storage change map with side-by-side layout
st.subheader("Annual Storage Change Map")
map_col, info_col = st.columns([0.75, 1.25])

with map_col:
    map_obj = plot_selected_year_map_interactive(polygon_data, selected_year, aoi, aquifer, period)
    if map_obj:
        st.pyplot(map_obj, use_container_width=True)

with info_col:
    st.markdown("### Selected Year Summary")
    period_formatted = "Spring-to-Spring" if period == "spring" else "Fall-to-Fall"
    st.markdown(f"**Year:** {int(selected_year)}")
    st.markdown(f"**AOI:** {aoi}")
    st.markdown(f"**Aquifer:** {aquifer}")
    st.markdown(f"**Period:** {period_formatted}")
    st.markdown("---")
    st.markdown(f"**Annual Change:** {selected_row['vol_delta_af_sum']:,.0f} AF")
    st.markdown(f"**Cumulative Change:** {selected_row['cum_delta_af']:,.0f} AF")
    st.markdown(f"**Water Year Type:** {selected_row.get('wy_type', 'Unknown')}")
    st.markdown(f"**Wells Used:** {int(selected_row['num_wells_used'])}")

# ============================================================================
# THREE-YEAR SPATIAL MAP COMPARISON
# ============================================================================
st.header("🗺️ Compare Three Years Spatially")

# Available years for comparison
available_years = sorted(polygon_data["year_cur"].unique())

# Default years: largest decline, middle year, and latest year
largest_decline_idx = annual_summary["vol_delta_af_sum"].idxmin()
default_year_a = int(annual_summary.loc[largest_decline_idx, "year"])
middle_idx = len(available_years) // 2
default_year_b = available_years[middle_idx]
default_year_c = int(annual_summary["year"].max())

# Ensure defaults are in available years
if default_year_a not in available_years:
    default_year_a = available_years[0]
if default_year_b not in available_years:
    default_year_b = available_years[middle_idx]
if default_year_c not in available_years:
    default_year_c = available_years[-1]

col_sel1, col_sel2, col_sel3 = st.columns(3)
with col_sel1:
    compare_year_a = st.selectbox("Comparison Year A", available_years, index=available_years.index(default_year_a), key="compare_year_a")
with col_sel2:
    compare_year_b = st.selectbox("Comparison Year B", available_years, index=available_years.index(default_year_b), key="compare_year_b")
with col_sel3:
    compare_year_c = st.selectbox("Comparison Year C", available_years, index=available_years.index(default_year_c), key="compare_year_c")

# Display three-way comparison
compare_col1, compare_col2, compare_col3 = st.columns(3)

with compare_col1:
    st.markdown("### Year A")
    summary_a = get_year_summary(annual_summary, compare_year_a)
    if summary_a is not None:
        st.markdown(f"**Year:** {int(compare_year_a)}")
        st.markdown(f"**WY Type:** {summary_a.get('wy_type', 'Unknown')}")
        st.markdown(f"**Annual Change:** {summary_a['vol_delta_af_sum']:,.0f} AF")
        st.markdown(f"**Cumulative Change:** {summary_a['cum_delta_af']:,.0f} AF")
        st.markdown(f"**Wells Used:** {int(summary_a['num_wells_used'])}")
    else:
        st.info("Summary not available for this year")
    
    map_a = plot_selected_year_map_interactive(polygon_data, compare_year_a, aoi, aquifer, period)
    if map_a:
        st.pyplot(map_a, use_container_width=True)

with compare_col2:
    st.markdown("### Year B")
    summary_b = get_year_summary(annual_summary, compare_year_b)
    if summary_b is not None:
        st.markdown(f"**Year:** {int(compare_year_b)}")
        st.markdown(f"**WY Type:** {summary_b.get('wy_type', 'Unknown')}")
        st.markdown(f"**Annual Change:** {summary_b['vol_delta_af_sum']:,.0f} AF")
        st.markdown(f"**Cumulative Change:** {summary_b['cum_delta_af']:,.0f} AF")
        st.markdown(f"**Wells Used:** {int(summary_b['num_wells_used'])}")
    else:
        st.info("Summary not available for this year")
    
    map_b = plot_selected_year_map_interactive(polygon_data, compare_year_b, aoi, aquifer, period)
    if map_b:
        st.pyplot(map_b, use_container_width=True)

with compare_col3:
    st.markdown("### Year C")
    summary_c = get_year_summary(annual_summary, compare_year_c)
    if summary_c is not None:
        st.markdown(f"**Year:** {int(compare_year_c)}")
        st.markdown(f"**WY Type:** {summary_c.get('wy_type', 'Unknown')}")
        st.markdown(f"**Annual Change:** {summary_c['vol_delta_af_sum']:,.0f} AF")
        st.markdown(f"**Cumulative Change:** {summary_c['cum_delta_af']:,.0f} AF")
        st.markdown(f"**Wells Used:** {int(summary_c['num_wells_used'])}")
    else:
        st.info("Summary not available for this year")
    
    map_c = plot_selected_year_map_interactive(polygon_data, compare_year_c, aoi, aquifer, period)
    if map_c:
        st.pyplot(map_c, use_container_width=True)

# ============================================================================
# STORAGE CHANGE ANIMATION
# ============================================================================
st.header("🎬 Storage Change Animation")

# Simply load the pre-made MP4 file
if mp4_path.exists():
    st.info(f"✅ Loading pre-made animation: {mp4_path.name}")
    
    video_left, video_center, video_right = st.columns([0.15, 0.70, 0.15])
    
    with video_center:
        st.video(str(mp4_path))
        st.caption("Storage change time-series animation")
else:
    st.warning(f"⚠️ Animation file not found: {mp4_path.name}")
    st.info(f"Expected location: `{mp4_path}`")

# ============================================================================
# DOWNLOAD BUTTONS
# ============================================================================
st.subheader("📥 Download Data")

col1, col2 = st.columns(2)

with col1:
    csv_annual = annual_summary[display_cols].to_csv(index=False)
    st.download_button(
        label="📥 Annual Summary CSV",
        data=csv_annual,
        file_name=f"{aoi}_{aquifer}_{period}_annual_summary.csv",
        mime="text/csv"
    )

with col2:
    polygon_year = polygon_data[polygon_data["year_cur"] == selected_year]
    if not polygon_year.empty:
        polygon_csv = polygon_year.drop(columns="geometry").to_csv(index=False)
        st.download_button(
            label=f"📥 {int(selected_year)} Polygon CSV",
            data=polygon_csv,
            file_name=f"{aoi}_{aquifer}_{period}_{int(selected_year)}_polygons.csv",
            mime="text/csv"
        )
