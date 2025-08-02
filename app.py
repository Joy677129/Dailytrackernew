import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

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
  .header-orange .ag-header-cell-label { background-color: #f57c00 !important; color: white; }
  .highlight-row { background-color: #e3f2fd !important; }
  .footer-row { font-weight: bold !important; background-color: #bbdefb !important; }
  .negative { color: red !important; font-weight: bold; }
  @media print {
    body { zoom: 0.8; }
    .no-print { display: none; }
  }
</style>
""", unsafe_allow_html=True)

# Weekday selection
weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
first_day = st.selectbox("Weekday of 1st of month:", weekdays, index=0)
offset = weekdays.index(first_day)

# Build template
dates = list(range(1,32))
days = [weekdays[(offset + d - 1) % 7] for d in dates]
RATE = 0.12

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
    
# Add row styling for weekends
def row_style(params):
    if params.data['Day'] == 'Friday':
        return {'backgroundColor': '#e8f5e9'}
    if params.data['Day'] in ['Saturday', 'Sunday']:
        return {'backgroundColor': '#ffebee'}
    return None

gb.configure_grid_options(rowStyle=row_style)
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
    theme=theme,
    allow_unsafe_jscode=True
)
edf = pd.DataFrame(resp['data']).reset_index(drop=True)[[c[0] for c in cols_cfg]]

# Inputs section
st.subheader("Calculation Parameters")
col1, col2 = st.columns(2)
with col1:
    g0 = st.number_input("Baseline G (Day 1)", min_value=0.0, value=100.0, step=1.0, format="%.2f")
with col2:
    custom_rate = st.number_input("Custom Rate (%)", min_value=0.0, max_value=100.0, value=12.0, step=0.5) / 100

# Compute on button click
if st.button("🚀 Calculate Rice Flow", use_container_width=True):
    df2 = edf.copy()
    # Enforce correct data types
    df2['গ্রহণের পরিমাণ (D)'] = pd.to_numeric(df2['গ্রহণের পরিমাণ (D)'], errors='coerce').fillna(0)
    df2['বাকিতে নেওয়া (E)'] = pd.to_numeric(df2['বাকিতে নেওয়া (E)'], errors='coerce').fillna(0)
    
    # Calculate F column with custom rate
    df2['চাল প্রাপ্তি (F)'] = df2['গ্রহণের পরিমাণ (D)'] * custom_rate
    
    # Calculate G column
    G_vals = [g0 - df2.at[0, 'চাল প্রাপ্তি (F)']]
    for i in range(1, len(df2)):
        prev_G = G_vals[-1]
        F_i = df2.at[i, 'চাল প্রাপ্তি (F)']
        E_prev = df2.at[i-1, 'বাকিতে নেওয়া (E)']
        G_vals.append(prev_G - F_i + E_prev)
    df2['G (চাল ব্যবহার)'] = G_vals
    
    # Add formatting for negative values
    df2['G (চাল ব্যবহার)'] = df2['G (চাল ব্যবহার)'].apply(
        lambda x: f"<span class='negative'>{x:.2f}</span>" if x < 0 else f"{x:.2f}"
    )
    
    # Weekly totals of G
    st.subheader("📅 Weekly Remaining G Totals")
    week_map = {
        'I (Mon/Thu)': ['Monday', 'Thursday'],
        'J (Tue/Fri)': ['Tuesday', 'Friday'],
        'K (Wed/Sat)': ['Wednesday', 'Saturday']
    }
    
    # Convert G to float for calculation
    df2['G_float'] = pd.to_numeric(df2['G (চাল ব্যবহার)'].str.extract(r'([-]?\d+\.\d+)')[0], errors='coerce')
    
    # Calculate totals and format
    totals = {}
    for label, days_list in week_map.items():
        days_df = df2[df2['Day'].isin(days_list)]
        total = days_df['G_float'].sum()
        totals[label] = total
        st.metric(label, f"{total:.2f}")
    
    # Add summary row
    summary_row = pd.DataFrame({
        'Date': [''],
        'Day': ['TOTAL'],
        'গ্রহণের পরিমাণ (D)': [df2['গ্রহণের পরিমাণ (D)'].sum()],
        'বাকিতে নেওয়া (E)': [df2['বাকিতে নেওয়া (E)'].sum()],
        'চাল প্রাপ্তি (F)': [df2['চাল প্রাপ্তি (F)'].sum()],
        'G (চাল ব্যবহার)': [df2['G_float'].sum()],
        'G_float': [df2['G_float'].sum()]
    })
    
    # Format summary row
    summary_row['G (চাল ব্যবহার)'] = summary_row['G (চাল ব্যবহার)'].apply(
        lambda x: f"<span class='negative'>{x:.2f}</span>" if x < 0 else f"{x:.2f}"
    )
    
    # Combine with main data
    df2 = pd.concat([df2, summary_row], ignore_index=True)
    df2.drop(columns=['G_float'], inplace=True)
    
    # Display results table
    st.subheader("📊 Results Table")
    
    # Configure results grid
    gb_results = GridOptionsBuilder.from_dataframe(df2)
    for col, _, width, cls, bg, _ in cols_cfg:
        gb_results.configure_column(
            col, 
            width=width, 
            headerClass=cls, 
            cellStyle={'backgroundColor': bg}
        )
    
    # Add styling for summary row
    gb_results.configure_grid_options(
        rowStyle=row_style,
        getRowStyle=lambda params: {'fontWeight': 'bold', 'backgroundColor': '#bbdefb'} 
        if params.data['Day'] == 'TOTAL' else row_style(params)
    )
    
    # Display the grid
    AgGrid(
        df2,
        gridOptions=gb_results.build(),
        fit_columns_on_grid_load=True,
        height=600,
        theme=theme,
        allow_unsafe_html=True,
        enable_enterprise_modules=False
    )
    
    # Add export options
    st.subheader("💾 Export Results")
    csv = df2.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name='rice_flow_report.csv',
        mime='text/csv'
    )

# Sidebar information
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Select the **first weekday** of the month
    2. Enter values in:
       - **D (গ্রহণের পরিমাণ)**: Rice received
       - **E (বাকিতে নেওয়া)**: Rice taken on credit
    3. Set the **Baseline G** (starting balance)
    4. Click **Calculate Rice Flow**
    
    ### Calculation Formula
    - **F (চাল প্রাপ্তি)** = D × Rate
    - **G (চাল ব্যবহার)**:
      - Day 1: G0 - F₁
      - Day n: Gₙ₋₁ - Fₙ + Eₙ₋₁
    
    ### Weekly Groups
    - **I**: Monday & Thursday
    - **J**: Tuesday & Friday
    - **K**: Wednesday & Saturday
    """)
    
    st.info("Note: Negative G values are shown in red indicating deficit")
