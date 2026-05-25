
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title = 'Geospatial Dashboard',
    page_icon = '	:globe_with_meridians:',
    layout = 'wide'
)
df = pd.read_csv('clean_data2026May.csv')

with st.sidebar:
  st.title(':globe_with_meridians: Geospatial Dashboard')

  # A. CONTINENT
  continent_lst = list(df['sensor_name'].unique())
  select_continent = st.multiselect('Select a Station', continent_lst)
  if select_continent:
    df = df[df['sensor_name'].isin(select_continent)]
  else:
    df = df.copy()

  # B. Country
  country_lst = list(df['station_id'].unique())
  select_country = st.multiselect('Select a Station_ID', country_lst)
  if select_country:
    df = df[df['station_id'].isin(select_country)]
  else:
    df = df.copy()

# --- GLOBAL DATA CLEANING PIPELINE ---
# We clean and sort the filtered data ONCE right here so all charts below pull from the same clean data stream
df_clean = df.dropna(subset=['latitude', 'longitude', 'predicted_pm2.5', 'year_week']).copy()
df_clean = df_clean.sort_values('year_week')

st.subheader('💨 Spatiotemporal Air Quality Heatmap: $PM_{2.5}$ Trends')

# 1. Compile the interactive animated Mapbox heatmap layer matrix
fig1 = px.density_mapbox(
    df_clean,
    lat='latitude',
    lon='longitude',
    z='predicted_pm2.5',            # Color density intensity determined by PM2.5 metric
    radius=25,                     # Controls the pixel blur radius overlap between tracking nodes
    center=dict(lat=5.6037, lon=-0.1870), # Centers viewport explicitly over Greater Accra coordinates
    zoom=10,                       # Perfect local zoom window height scale for your study region
    animation_frame='year_week',   # Creates the automated timeline slider engine controls
    hover_name='sensor_name',       # Shows the monitoring node name on hover cursor actions
    hover_data={'predicted_pm2.5': ':.2f', 'latitude': False, 'longitude': False},
    color_continuous_scale='Inferno', # Smooth dark-to-bright color gradient transition line
    mapbox_style='carto-darkmatter'   # Clean, professional dark baseline maps matrix background
)

# 2. Global UI/Layout visual parameter configurations
fig1.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0}, # Minimizes empty padding whitespace blocks
    coloraxis_colorbar=dict(
        title="$PM_{2.5}$ (μg/m³)",
        thicknessmode="pixels", thickness=15,
        lenmode="fraction", len=0.6,
        yanchor="top", y=0.9,
        xanchor="left", x=0.02
    )
)

# 3. Push the compiled asset onto your active Streamlit window layout container
st.plotly_chart(fig1, use_container_width=True)


# --- LOWER METRICS & TIMELINE LAYOUT SPLIT ---
block1, block2 = st.columns((1, 2))

# Injection CSS for the public health metric card styling
st.markdown("""
  <style>
  .card {
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0px;
    background-color: #1e1e1e;
    border: 1px solid #333;
    color: white;
    text-align: center;
  }
  .metric-title {
    font-size: 14px;
    color: #aaa;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .value {
    font-size: 36px;
    font-weight: bold;
    margin: 10px 0;
  }
  .change-positive {
    color: #ff4d4d; /* Red indicates pollution increase */
    font-size: 18px;
    font-weight: bold;
  }
  .change-negative {
    color: #00cc66; /* Green indicates air quality improvement */
    font-size: 18px;
    font-weight: bold;
  }
  </style>
""", unsafe_allow_html=True)

with block1:
    st.subheader('📈 Regional WoW Trend')
    
    # Calculate global Week-over-Week trend metrics across Accra using our clean data stream
    weekly_avg = df_clean.groupby('year_week')['predicted_pm2.5'].mean().reset_index()
    
    if len(weekly_avg) >= 2:
        prev_week_val = weekly_avg.iloc[-2]['predicted_pm2.5']
        curr_week_val = weekly_avg.iloc[-1]['predicted_pm2.5']
        wow_growth = ((curr_week_val - prev_week_val) / prev_week_val) * 100
    else:
        curr_week_val = df_clean['predicted_pm2.5'].mean() if not df_clean.empty else 0.0
        wow_growth = 0.0

    # Handle inverse alert states (Growth = Bad for pollution metrics)
    growth_class = 'change-positive' if wow_growth > 0 else 'change-negative'
    growth_symbol = '↑' if wow_growth > 0 else '↓'
    trend_type = "Increase" if wow_growth > 0 else "Reduction"

    card_html = f"""
    <div class='card'>
        <div class='metric-title'>Current Avg $PM_{{2.5}}$</div>
        <div class='value'>{curr_week_val:.2f} μg/m³</div>
        <div class='{growth_class}'>{growth_symbol} {abs(wow_growth):.1f}% {trend_type}<br><span style='font-size:12px; color:#777;'>vs Prev Week</span></div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

with block2:
    st.subheader('📊 Weekly Sensor Tracking (Timeline View)')
    
    # Animated line graph showing PM2.5 trends accumulating over time
    fig2 = px.line(
        df_clean,
        x='year_week',
        y='predicted_pm2.5',
        color='sensor_name',
        title='Station-Level PM2.5 Accumulation',
        labels={'year_week': 'Timeline (Year-Week)', 'predicted_pm2.5': 'PM2.5 (μg/m³)'}
    )
    
    # Add a critical safety context line highlighting the WHO 24-hr Threshold limit
    fig2.add_hline(
        y=15.0, 
        line_dash="dash", 
        line_color="red", 
        annotation_text="WHO Guideline Max (15 μg/m³)", 
        annotation_position="top left"
    )
    
    fig2.update_layout(
        template='plotly_dark',
        xaxis={'type': 'category'},
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig2, use_container_width=True)


# --- LOWER HEATMAP SECTION ---
st.subheader('🔥 Spatiotemporal Density Heat Chart')

# Density heatmap aggregations cleanly sidestep the sparse NaN environment gaps
fig3 = px.density_heatmap(
    df_clean,
    x='year_week',
    y='sensor_name',
    z='predicted_pm2.5',
    histfunc='avg',
    color_continuous_scale='Inferno',
    title='Pollution Intensity Matrix Across Observation Windows',
    labels={'year_week': 'Timeline (Year_Week)', 'sensor_name': 'Monitoring Station', 'predicted_pm2.5': 'Avg PM2.5'}
)

fig3.update_layout(
    template='plotly_dark',
    xaxis={'type': 'category'},
    coloraxis_colorbar=dict(title="PM2.5 (μg/m³)")
)

st.plotly_chart(fig3, use_container_width=True)
