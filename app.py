import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode

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
</style>
""", unsafe_allow_html=True)

# Weekday selection
days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
first_day = st.selectbox("Weekday of 1st of month:", days_of_week, index=0)
offset = days_of_week.index(first_day)

# Build template DataFrame
dates = list(range(1, 32))
days = [days_of_week[(offset + d - 1) % 7] for d in dates]

template = pd.DataFrame({
    'Date': dates,
    'Day': days,
    'গ্রহণের পরিমাণ (D)': 0.0,
    'বাকিতে নেওয়া (E)': 0.0,
    'চাল প্রাপ্তি (F)': 0.0,
    'G (চাল ব্যবহার)': 0.0
})

# Configure AgGrid for inputs
gb = GridOptionsBuilder.from_dataframe(template)
col_settings = [
    ('Date', False, 80, 'header-dark', '#f2f2f2'),
    ('Day', False, 100, 'header-day', '#ede7f6'),
    ('গ্রহণের পরিমাণ (D)', True, 140, 'header-blue', '#e0f7fa'),
    ('বাকিতে নেওয়া (E)', True, 140, 'header-green', '#e8f5e9'),
    ('চাল প্রাপ্তি (F)', False, 130, 'header-dark', '#fffde7'),
    ('G (চাল ব্যবহার)', False, 130, 'header-red', '#ffebee')
]
for col, editable, width, cls, bg in col_settings:
    opts = {'editable': editable, 'width': width, 'headerClass': cls, 'cellStyle': {'backgroundColor': bg}}
    gb.configure_column(col, **opts)
grid_options = gb.build()

# Show input grid
st.markdown("### Enter D & E Values (leave blank for 0)")
response = AgGrid(
    template,
    gridOptions=grid_options,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    height=450,
    theme=theme
)
inputs_df = pd.DataFrame(response['data']).reset_index(drop=True)

# User parameters
st.subheader("Calculation Parameters")
col1, col2 = st.columns(2)
with col1:
    initial_balance = st.number_input("Initial G (Before 1st day)", min_value=0.0,
                                      value=174.47, step=1.0, format="%.2f")
with col2:
    rate = st.number_input("Custom Rate (%)", min_value=0.0, max_value=100.0,
                           value=12.0, step=0.5) / 100

# Calculate on button click
if st.button("🚀 Calculate Rice Flow", use_container_width=True):
    df = inputs_df.copy()

    # Ensure numeric for D and E
    df['গ্রহণের পরিমাণ (D)'] = pd.to_numeric(df['গ্রহণের পরিমাণ (D)'], errors='coerce').fillna(0)
    df['বাকিতে নেওয়া (E)'] = pd.to_numeric(df['বাকিতে নেওয়া (E)'], errors='coerce').fillna(0)

    # F = D * rate
    df['চাল প্রাপ্তি (F)'] = df['গ্রহণের পরিমাণ (D)'] * rate

    # Compute running G
    g_values = []
    g_values.append(initial_balance - df.at[0, 'চাল প্রাপ্তি (F)'])
    for i in range(1, len(df)):
        prev = g_values[-1]
        f_curr = df.at[i, 'চাল প্রাপ্তি (F)']
        e_prev = df.at[i-1, 'বাকিতে নেওয়া (E)']
        g_values.append(prev - f_curr + e_prev)
    df['G (চাল ব্যবহার)'] = g_values

    # Weekly totals
    st.subheader("📅 Weekly Remaining G Totals")
    groups = {
        'I (Mon/Thu)': ['Monday', 'Thursday'],
        'J (Tue/Fri)': ['Tuesday', 'Friday'],
        'K (Wed/Sat)': ['Wednesday', 'Saturday']
    }
    for label, days in groups.items():
        total = df[df['Day'].isin(days)]['G (চাল ব্যবহার)'].sum()
        st.metric(label, f"{total:.2f}")

    # Summary row
    summary = {
        'Date': '',
        'Day': 'TOTAL',
        'গ্রহণের পরিমাণ (D)': df['গ্রহণের পরিমাণ (D)'].sum(),
        'বাকিতে নেওয়া (E)': df['বাকিতে নেওয়া (E)'].sum(),
        'চাল প্রাপ্তি (F)': df['চাল প্রাপ্তি (F)'].sum(),
        'G (চাল ব্যবহার)': df['G (চাল ব্যবহার)'].sum()
    }
    df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)

    # Display results with styling
    st.subheader("📊 Results Table")
    gb2 = GridOptionsBuilder.from_dataframe(df)
    highlight_total = JsCode("""
        function(params) {
            return params.data.Day === 'TOTAL' ? { 'backgroundColor': '#bbdefb', 'fontWeight': 'bold' } : null;
        }
    """)
    highlight_neg = JsCode("""
        function(params) {
            return params.value < 0 ? { 'color': 'red', 'fontWeight': 'bold' } : null;
        }
    """)
    for col, _, width, cls, bg in col_settings:
        opts = {'width': width, 'headerClass': cls, 'cellStyle': {'backgroundColor': bg}}
        if col == 'G (চাল ব্যবহার)': opts['cellStyle'] = highlight_neg
        gb2.configure_column(col, **opts)
    gb2.configure_grid_options(rowStyle=highlight_total)

    AgGrid(
        df,
        gridOptions=gb2.build(),
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.NO_UPDATE,
        fit_columns_on_grid_load=True,
        height=550,
        theme=theme,
        allow_unsafe_jscode=True
    )

    # Export
    st.subheader("💾 Export Results")
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download as CSV", data=csv_data, file_name='rice_flow_report.csv', mime='text/csv')

# Sidebar
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
1. Select the **first weekday** of the month
2. Enter values for **D** (received) and **E** (credit taken)
3. Set **Initial G** (balance before day 1)
4. Click **Calculate Rice Flow**

**Tips**:
- Negative G in red = deficit
- E affects next day's balance
""")
