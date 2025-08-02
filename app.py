import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode
from calendar import monthrange
import datetime

# Page configuration
theme = 'alpine'
st.set_page_config(page_title="Rice-Flow Table", layout="wide")
st.title("📊 Monthly Rice-Flow Calculator")

# CSS for styling
st.markdown("""
<style>
  .header-dark .ag-header-cell-label { background-color: #424242 !important; color: white; }
  .header-blue .ag-header-cell-label { background-color: #0288d1 !important; color: white; }
  .header-green .ag-header-cell-label { background-color: #43a047 !important; color: white; }
  .header-day .ag-header-cell-label { background-color: #6a1b9a !important; color: white; }
  .header-red .ag-header-cell-label { background-color: #d32f2f !important; color: white; }
  .negative { color: red !important; font-weight: bold; }
  .total-row { background-color: #bbdefb !important; font-weight: bold; }
  .ag-theme-alpine .ag-row-even { background-color: #f9f9f9; }
  .ag-theme-alpine .ag-row-odd { background-color: white; }
</style>
""", unsafe_allow_html=True)

# Month and year selection
col1, col2 = st.columns(2)
with col1:
    month = st.selectbox("Select Month:", list(range(1, 13)), format_func=lambda x: datetime.date(2023, x, 1).strftime('%B'), index=7)  # August is index 7
with col2:
    year = st.selectbox("Select Year:", list(range(2020, 2031)), index=5)  # 2025 is index 5

# Get number of days in selected month
num_days = monthrange(year, month)[1]

# Weekday selection
weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
first_day = st.selectbox("Weekday of 1st of month:", weekdays, index=0)
offset = weekdays.index(first_day)

# Build template with correct number of days
dates = list(range(1, num_days + 1))
days = [weekdays[(offset + d - 1) % 7] for d in dates]

df = pd.DataFrame({
    'Date': dates,
    'Day': days,
    'গ্রহণের পরিমাণ (D)': 0.0,
    'বাকিতে নেওয়া (E)': 0.0,
    'চাল প্রাপ্তি (F)': 0.0,
    'G (চাল ব্যবহার)': 0.0
})

# Grid configuration
gb = GridOptionsBuilder.from_dataframe(df)
cols_cfg = [
    ('Date', False, 80, 'header-dark', '#f2f2f2', 'left'),
    ('Day', False, 100, 'header-day', '#ede7f6', 'left'),
    ('গ্রহণের পরিমাণ (D)', True, 140, 'header-blue', '#e0f7fa', None),
    ('বাকিতে নেওয়া (E)', True, 140, 'header-green', '#e8f5e9', None),
    ('চাল প্রাপ্তি (F)', False, 130, 'header-dark', '#fffde7', None),
    ('G (চাল ব্যবহার)', False, 130, 'header-red', '#ffebee', None)
]
for col, editable, width, cls, bg, pin in cols_cfg:
    opts = {'editable': editable, 'width': width, 'headerClass': cls, 'cellStyle': {'backgroundColor': bg}}
    if pin:
        opts['pinned'] = pin
    gb.configure_column(col, **opts)
    
grid_opts = gb.build()

# Enforce column order
df = df[[c[0] for c in cols_cfg]]

# Display input grid
st.markdown("### Enter D & E Values (leave blank for 0)")
resp = AgGrid(
    df,
    gridOptions=grid_opts,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    height=500,
    theme=theme
)
edf = pd.DataFrame(resp['data']).reset_index(drop=True)[[c[0] for c in cols_cfg]]

# Inputs section
st.subheader("Calculation Parameters")
col1, col2 = st.columns(2)
with col1:
    initial_g = st.number_input("Initial G (Before 1st day)", min_value=0.0, value=174.47, step=1.0, format="%.2f",
                               help="Starting balance (G value before the 1st day)")
with col2:
    custom_rate = st.number_input("Custom Rate (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5) / 100

# Compute on button click
if st.button("🚀 Calculate Rice Flow", use_container_width=True):
    df2 = edf.copy()
    
    # Convert to numeric and handle missing values
    df2['গ্রহণের পরিমাণ (D)'] = pd.to_numeric(df2['গ্রহণের পরিমাণ (D)'], errors='coerce').fillna(0)
    df2['বাকিতে নেওয়া (E)'] = pd.to_numeric(df2['বাকিতে নেওয়া (E)'], errors='coerce').fillna(0)
    
    # Calculate F column (চাল প্রাপ্তি) - 12% of D
    df2['চাল প্রাপ্তি (F)'] = df2['গ্রহণের পরিমাণ (D)'] * custom_rate
    
    # Calculate G column (চাল ব্যবহার) using corrected logic
    g_vals = []
    
    # For first day: G = Initial_G - F_current (no previous E)
    first_g = initial_g - df2.iloc[0]['চাল প্রাপ্তি (F)']
    g_vals.append(first_g)
    
    # For subsequent days: G_current = G_previous - F_current + E_previous
    for i in range(1, len(df2)):
        prev_g = g_vals[i-1]
        current_f = df2.iloc[i]['চাল প্রাপ্তি (F)']  # Current day's F
        prev_e = df2.iloc[i-1]['বাকিতে নেওয়া (E)']  # Previous day's E
        
        current_g = prev_g - current_f + prev_e
        g_vals.append(current_g)
    
    df2['G (চাল ব্যবহার)'] = g_vals
    
    # Weekly totals calculation - EXACTLY as in Excel
    st.subheader("📅 Weekly Totals (I, J, K Groups)")
    
    # Calculate weekly sums for D column (গ্রহণের পরিমাণ)
    group_i_days = ['Monday', 'Thursday']
    group_i_values = df2[df2['Day'].isin(group_i_days)]['গ্রহণের পরিমাণ (D)'].sum()
    
    group_j_days = ['Tuesday', 'Friday']
    group_j_values = df2[df2['Day'].isin(group_j_days)]['গ্রহণের পরিমাণ (D)'].sum()
    
    group_k_days = ['Wednesday', 'Saturday']
    group_k_values = df2[df2['Day'].isin(group_k_days)]['গ্রহণের পরিমাণ (D)'].sum()
    
    # Display the weekly group totals
    col1, col2, col3 = st.columns(3)
    col1.metric("I (Mon/Thu)", f"{group_i_values:.2f} kg")
    col2.metric("J (Tue/Fri)", f"{group_j_values:.2f} kg")
    col3.metric("K (Wed/Sat)", f"{group_k_values:.2f} kg")
    
    # Add summary row for totals
    summary_row = pd.DataFrame({
        'Date': [''],
        'Day': ['TOTAL'],
        'গ্রহণের পরিমাণ (D)': [df2['গ্রহণের পরিমাণ (D)'].sum()],
        'বাকিতে নেওয়া (E)': [df2['বাকিতে নেওয়া (E)'].sum()],
        'চাল প্রাপ্তি (F)': [df2['চাল প্রাপ্তি (F)'].sum()],
        'G (চাল ব্যবহার)': [df2['G (চাল ব্যবহার)'].sum()]
    })
    
    # Combine with main data
    df2 = pd.concat([df2, summary_row], ignore_index=True)
    
    # Display results table
    st.subheader("📊 Results Table")
    
    # Configure results grid
    gb_results = GridOptionsBuilder.from_dataframe(df2)
    
    # Create JavaScript functions for styling
    row_style_jscode = JsCode("""
        function(params) {
            if (params.data.Day === 'TOTAL') {
                return {
                    'backgroundColor': '#bbdefb',
                    'fontWeight': 'bold'
                };
            }
            return null;
        };
    """)
    
    cell_style_jscode = JsCode("""
        function(params) {
            if (params.colDef.field === 'G (চাল ব্যবহার)') {
                if (params.value < 0) {
                    return {
                        'color': 'red',
                        'fontWeight': 'bold'
                    };
                }
            }
            return null;
        };
    """)
    
    for col, _, width, cls, bg, pin in cols_cfg:
        opts = {
            'width': width, 
            'headerClass': cls, 
            'cellStyle': {'backgroundColor': bg}
        }
        if col == 'G (চাল ব্যবহার)':
            opts['cellStyle'] = cell_style_jscode
        if pin:
            opts['pinned'] = pin
        gb_results.configure_column(col, **opts)
    
    gb_results.configure_grid_options(
        rowStyle=row_style_jscode,
        suppressRowClickSelection=True,
        enableCellTextSelection=True,
        ensureDomOrder=True
    )
    grid_opts_results = gb_results.build()
    
    # Display the grid
    AgGrid(
        df2,
        gridOptions=grid_opts_results,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
        height=600,
        theme=theme,
        allow_unsafe_jscode=True
    )
    
    # Add export options
    st.subheader("💾 Export Results")
    csv = df2.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f'rice_flow_report_{month}_{year}.csv',
        mime='text/csv'
    )

# Sidebar information
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Select the **month and year**
    2. Select the **first weekday** of the month
    3. Enter values in:
       - **D (গ্রহণের পরিমাণ)**: Rice received
       - **E (বাকিতে নেওয়া)**: Rice taken on credit
    4. Set the **Initial G** (balance before 1st day)
    5. Click **Calculate Rice Flow**
    
    ### Calculation Formula
    - **F (চাল প্রাপ্তি)** = D × Rate
    - **G (চাল ব্যবহার)**:
      - Day 1: Initial_G - F₁
      - Day n: Gₙ = Gₙ₋₁ - Fₙ + Eₙ₋₁
    
    ### Key Relationships
    - E values affect the NEXT day's G calculation
    - E from day (i) is used in day (i+1) calculation
    - F values are calculated from current day's D
    
    ### Weekly Groups (D Column Sums)
    - **I**: Monday & Thursday
    - **J**: Tuesday & Friday
    - **K**: Wednesday & Saturday
    """)
    
    st.info("""
    **Note**: 
    - Negative G values are shown in red indicating deficit
    - 'Initial G' is the balance before the 1st day
    - E values from a day affect the next day's calculation
    - The last day's E value is not used (no next day)
    - Sunday is not included in any weekly group
    """)
