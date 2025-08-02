import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

# Page configuration
st.set_page_config(page_title="Rice-Flow Table", layout="wide")
st.title("📊 Monthly Rice-Flow Calculator")

# Custom CSS for header styling
st.markdown("""
<style>
  .header-dark .ag-header-cell-label { background-color: #424242 !important; color: white; }
  .header-blue .ag-header-cell-label { background-color: #0288d1 !important; color: white; }
  .header-green .ag-header-cell-label { background-color: #43a047 !important; color: white; }
  .header-day .ag-header-cell-label { background-color: #6a1b9a !important; color: white; }
</style>
""", unsafe_allow_html=True)

# Ask user for the weekday of the 1st of the month
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
first_day = st.selectbox("Select the weekday of the 1st of the month:", weekdays, index=0)
first_index = weekdays.index(first_day)

# Build blank template for days 1–31, default numeric to 0
dates = list(range(1, 32))
days = [weekdays[(first_index + d - 1) % 7] for d in dates]
RATE = 0.12  # Fixed rate for চাল প্রাপ্তি calculation

# Ensure column order matches Excel: D, E, F, then G
df_template = pd.DataFrame({
    "Date": dates,
    "Day": days,
    "গ্রহণের পরিমাণ (D)": 0.0,
    "বাকিতে নেওয়া (E)": 0.0,
    "চাল প্রাপ্তি (F)": 0.0,
    "G (চাল ব্যবহার)": 0.0,
})

# Configure AgGrid options for input grid in desired column order
gb = GridOptionsBuilder.from_dataframe(df_template)
gb.configure_grid_options(suppressRowDrag=True)
col_order = [
    ("Date", False, 80, "header-dark", "#f2f2f2", 'left'),
    ("Day", False, 100, "header-day", "#ede7f6", 'left'),
    ("গ্রহণের পরিমাণ (D)", True, 140, "header-blue", "#e0f7fa", None),
    ("বাকিতে নেওয়া (E)", True, 140, "header-green", "#e8f5e9", None),
    ("চাল প্রাপ্তি (F)", False, 130, "header-dark", "#fffde7", None),
    ("G (চাল ব্যবহার)", False, 130, "header-dark", "#fff9c4", None),
]
for col, editable, width, headerClass, bg, pinned in col_order:
    gopts = {"editable": editable, "width": width, "headerClass": headerClass, "cellStyle": {"backgroundColor": bg}}
    if pinned:
        gopts["pinned"] = pinned
    gb.configure_column(col, **gopts)
grid_opts_input = gb.build()
# Enforce order in DataFrame itself when rendering
df_template = df_template[[c[0] for c in col_order]]

# Display input grid
st.markdown("### 1) Enter D & E values in the table below (F auto-calculated):")
response = AgGrid(
    df_template,
    gridOptions=grid_opts_input,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    height=400,
    theme='alpine'
)
edited_df = pd.DataFrame(response["data"])[[c[0] for c in col_order]]

# Baseline G₂ input
initial_G = st.number_input("Baseline চাল ব্যবহার (G₂, Day 1)", min_value=0.0, step=0.1, format="%.2f")

# Compute button
if st.button("Compute All G"):
    # Prepare working copy and reset index
    df2 = edited_df.copy().reset_index(drop=True)
    # Assign Date and Day to maintain structure
    df2["Date"] = dates
    df2["Day"] = days
    # Coerce inputs
    df2["গ্রহণের পরিমাণ (D)"] = pd.to_numeric(df2["গ্রহণের পরিমাণ (D)"], errors="coerce").fillna(0)
    df2["বাকিতে নেওয়া (E)"] = pd.to_numeric(df2["বাকিতে নেওয়া (E)"], errors="coerce").fillna(0)
    # Calculate F then G
    df2["চাল প্রাপ্তি (F)"] = df2["গ্রহণের পরিমাণ (D)"].astype(float) * RATE
    G_vals = [initial_G]
    for i in range(1, len(df2)):
        prev = G_vals[-1]
        rec = df2.iloc[i]["চাল প্রাপ্তি (F)"]
        car = df2.iloc[i-1]["বাকিতে নেওয়া (E)"]
        G_vals.append(prev - rec + car)
    df2["G (চাল ব্যবহার)"] = G_vals

    # Reorder columns before display
    df2 = df2[[c[0] for c in col_order]]

    # Show weekly totals and results
    st.markdown("### Weekly Totals from D & E:")
    days_map = {"I": ["Monday", "Thursday"], "J": ["Tuesday", "Friday"], "K": ["Wednesday", "Saturday"]}
    labels = [
        ("D Mon/Thu (I)", "গ্রহণের পরিমাণ (D)", "I"),
        ("D Tue/Fri (J)", "গ্রহণের পরিমাণ (D)", "J"),
        ("D Wed/Sat (K)", "গ্রহণের পরিমাণ (D)", "K"),
        ("E Mon/Thu (I)", "বাকিতে নেওয়া (E)", "I"),
        ("E Tue/Fri (J)", "বাকিতে নেওয়া (E)", "J"),
        ("E Wed/Sat (K)", "বাকিতে নেওয়া (E)", "K"),
    ]
    for label, col_key, grp in labels:
        total = df2.loc[df2["Day"].isin(days_map[grp]), col_key].sum()
        st.write(f"**{label}**: {total:.2f}")

    st.markdown("### Results Table:")
    gb2 = GridOptionsBuilder.from_dataframe(df2)
    gb2.configure_default_column(editable=False)
    AgGrid(
        df2,
        gridOptions=gb2.build(),
        fit_columns_on_grid_load=True,
        height=400,
        theme='alpine'
    )
