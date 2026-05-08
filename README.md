# Sacramento Groundwater Storage Change Explorer 💧

A Streamlit dashboard for exploring groundwater storage changes in the Sacramento region. This application visualizes annual and cumulative storage changes, water year types, and spatial comparisons across different aquifers.

## Features

- **Overall Results**: Summary statistics and annual trends
- **Annual/Cumulative Charts**: Interactive visualizations with water year type shading
- **Selected-Year Explorer**: Detailed maps and statistics for individual years
- **Three-Year Comparison**: Side-by-side spatial maps for comparing multiple years
- **Storage Change Animation**: Time-series animation of storage changes
- **Data Downloads**: Export annual summaries and polygon data as CSV

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Rajaram2050/gw_storage.git
cd gw_storage
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Structure

The application expects the following directory structure:

```
gw_storage/
├── app.py
├── requirements.txt
├── README.md
├── assets/
│   └── de_logo.png
└── data/
    ├── Sac_SJ_Valley_WYI_v1.0.xlsx
    ├── storage_change/
    │   ├── Sacramento_Primary_spring_annual_storage_change_summary.xlsx
    │   └── gif_frames/
    └── exports/
        └── Sacramento_Primary_spring_storage_polygon_data.gpkg
```

## Running the Application

```bash
streamlit run app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

## Data Files Required

- **Excel files**: Annual storage change summaries with columns:
  - `year`: Water year
  - `vol_delta_af_sum`: Annual storage change in acre-feet
  - `cum_delta_af`: Cumulative storage change
  - `num_wells_used`: Number of wells used in calculation

- **GeoPackage files**: Polygon data with columns:
  - `year_cur`: Year of measurement
  - `vol_delta_af`: Storage change volume
  - `geometry`: Polygon geometries

- **Water Year Index**: Excel file with water year type classifications (W, AN, BN, D, C)

## Controls

- **AOI**: Area of Interest (Sacramento)
- **Aquifer**: Aquifer type (Primary)
- **Storage Period**: Spring or Fall measurements
- **Selected Year**: Choose a year for detailed analysis

## Features Overview

### 📊 Overall Results
- Latest year metrics
- Largest decline and recovery years
- Average number of wells used
- Complete annual summary table

### 🔍 Selected-Year Explorer
- Detailed storage change map
- Year-specific statistics
- Water year type information

### 🗺️ Compare Three Years Spatially
- Side-by-side map comparison
- Individual year statistics for each map

### 🎬 Storage Change Animation
- Time-series animation from PNG frames
- MP4 video generation for browser viewing

## Technologies Used

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation
- **GeoPandas**: Geospatial data analysis
- **Plotly**: Interactive visualizations
- **Matplotlib**: Static maps and visualizations
- **Contextily**: Basemap tiles
- **ImageIO**: Video creation

## License

MIT License

## Contact

For questions or issues, please open an issue on GitHub.
