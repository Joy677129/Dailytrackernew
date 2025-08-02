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
  .negative { color: red !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Weekday selection
weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
first_day = st.selectbox("Weekday of 1st of month:", weekdays, index=0)
offset = weekdays.index(first_day)

# Build template
dates = list(range(1,32))
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
    
    # Calculate F column (চাল প্রাপ্তি)
    df2['চাল প্রাপ্তি (F)'] = df2['গ্রহণের পরিমাণ (D)'] * custom_rate
    
    # Calculate G column (চাল ব্যবহার) using Excel logic
    g_vals = []
    
    # For first day: G = Initial_G - F_current + E_previous
    # But there's no E_previous before first day, so E_previous = 0
    first_g = initial_g - df2.at[0, 'চাল প্রাপ্তি (F)']
    g_vals.append(first_g)
    
    # For subsequent days: G_current = G_previous - F_current + E_previous
    # Where E_previous is from the previous day
    for i in range(1, len(df2)):
        prev_g = g_vals[i-1]
        current_f = df2.at[i, 'চাল প্রাপ্তি (F)']
        prev_e = df2.at[i-1, 'বাকিতে নেওয়া (E)']
        current_g = prev_g - current_f + prev_e
        g_vals.append(current_g)
    
    df2['G (চাল ব্যবহার)'] = g_vals
    
    # Weekly totals calculation
    st.subheader("📅 Weekly Remaining G Totals")
    week_map = {
        'I (Mon/Thu)': ['Monday', 'Thursday'],
        'J (Tue/Fri)': ['Tuesday', 'Friday'],
        'K (Wed/Sat)': ['Wednesday', 'Saturday']
    }
    
    # Calculate and display weekly sums
    weekly_totals = {}
    for label, days_list in week_map.items():
        days_df = df2[df2['Day'].isin(days_list)]
        total = days_df['G (চাল ব্যবহার)'].sum()
        weekly_totals[label] = total
        st.metric(label, f"{total:.2f}")
    
    # Add summary row
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
    
    # Create a copy for display with formatted values
    display_df = df2.copy()
    
    # Format numeric columns
    num_cols = ['গ্রহণের পরিমাণ (D)', 'বাকিতে নেওয়া (E)', 'চাল প্রাপ্তি (F)', 'G (চাল ব্যবহার)']
    for col in num_cols:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x)
    
    # Format negative values and totals row
    for i in range(len(display_df)):
        if display_df.at[i, 'Day'] == 'TOTAL':
            # Bold entire totals row
            for col in display_df.columns:
                display_df.at[i, col] = f"**{display_df.at[i, col]}**"
        else:
            # Format negative G values in red
            g_val = df2.at[i, 'G (চাল ব্যবহার)']
            if isinstance(g_val, (int, float)) and g_val < 0:
                display_df.at[i, 'G (চাল ব্যবহার)'] = f":red[**{display_df.at[i, 'G (চাল ব্যবহার)']}**]"
    
    # Display as Markdown table
    st.markdown(display_df.to_markdown(index=False), unsafe_allow_html=True)
    
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
    3. Set the **Initial G** (balance before 1st day)
    4. Click **Calculate Rice Flow**
    
    ### Calculation Formula
    - **F (চাল প্রাপ্তি)** = D × Rate
    - **G (চাল ব্যবহার)**:
      - Day 1: Initial_G - F₁
      - Day n: Gₙ₋₁ - Fₙ + Eₙ₋₁
    
    ### Key Relationships
    - E values affect the NEXT day's G calculation
    - E from day (i) is used in day (i+1) calculation
    
    ### Weekly Groups
    - **I**: Monday & Thursday
    - **J**: Tuesday & Friday
    - **K**: Wednesday & Saturday
    """)
    
    st.info("""
    **Note**: 
    - Negative G values are shown in red indicating deficit
    - 'Initial G' is the balance before the 1st day (like Excel's G2)
    - E values from a day affect the next day's calculation
    """)
