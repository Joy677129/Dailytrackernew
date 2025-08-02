import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

# Page configuration
theme = 'alpine'
st.set_page_config(page_title="Rice-Flow Table", layout="wide")
st.title("📊 Monthly Rice-Flow Calculator")

# CSS for header styling
st.markdown("""
<style>
  .header-dark .ag-header-cell-label { background-color: #424242 !important; color: white; }
  .header-blue .ag-header-cell-label { background-color: #0288d1 !important; color: white; }
  .header-green .ag-header-cell-label { background-color: #43a047 !important; color: white; }
  .header-day .ag-header-cell-label { background-color: #6a1b9a !important; color: white; }
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
    ('G (চাল ব্যবহার)', False, 130, 'header-dark', '#fff9c4', None)
]
for col, editable, width, cls, bg, pin in cols_cfg:
    opts = {'editable': editable, 'width': width, 'headerClass': cls, 'cellStyle': {'backgroundColor': bg}}
    if pin:
        opts['pinned'] = pin
    gb.configure_column(col, **opts)
grid_opts = gb.build()
# enforce column order
df = df[[c[0] for c in cols_cfg]]

# Display input grid
st.markdown("### Enter D & E (blanks → 0)")
resp = AgGrid(
    df,
    gridOptions=grid_opts,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    height=400,
    theme=theme
)
edf = pd.DataFrame(resp['data']).reset_index(drop=True)[[c[0] for c in cols_cfg]]

# Baseline G input
g0 = st.number_input("Baseline G (Day 1)", min_value=0.0, step=0.1, format="%.2f")

# Compute on button click
if st.button("Compute"):
    df2 = edf.copy()
    # Enforce Date and Day columns
    df2['Date'] = dates
    df2['Day'] = days

    # Numeric coercion
    df2['গ্রহণের পরিমাণ (D)'] = pd.to_numeric(df2['গ্রহণের পরিমাণ (D)'], errors='coerce').fillna(0)
    df2['বাকিতে নেওয়া (E)'] = pd.to_numeric(df2['বাকিতে নেওয়া (E)'], errors='coerce').fillna(0)

    # Calculate F column
    df2['চাল প্রাপ্তি (F)'] = df2['গ্রহণের পরিমাণ (D)'] * RATE

    # Revised G logic based on Excel’s E behaviour:
    G_vals = [g0]
    for i in range(1, len(df2)):
        prev = G_vals[-1]
        F_i = df2.at[i, 'চাল প্রাপ্তি (F)']
        next_E = df2.at[i + 1, 'বাকিতে নেওয়া (E)'] if i + 1 < len(df2) else 0
        G_vals.append(prev - F_i + next_E)
    df2['G (চাল ব্যবহার)'] = G_vals

    # Reorder columns
    df2 = df2[[c[0] for c in cols_cfg]]

    # Weekly totals of G
    st.markdown("### Weekly Remaining G Totals")
    week_map = {'I': ['Monday', 'Thursday'], 'J': ['Tuesday', 'Friday'], 'K': ['Wednesday', 'Saturday']}
    for label, key in [('Mon/Thu (I)', 'I'), ('Tue/Fri (J)', 'J'), ('Wed/Sat (K)', 'K')]:
        tot = df2.loc[df2['Day'].isin(week_map[key]), 'G (চাল ব্যবহার)'].sum()
        st.write(f"**{label}**: {tot:.2f}")

    # Display results table
    st.markdown("### Results Table")
    gb2 = GridOptionsBuilder.from_dataframe(df2)
    gb2.configure_default_column(editable=False)
    AgGrid(
        df2,
        gridOptions=gb2.build(),
        fit_columns_on_grid_load=True,
        height=400,
        theme=theme
    )
