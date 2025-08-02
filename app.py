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

# Build blank template for days 1–31
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

# Configure AgGrid options for input grid
gb = GridOptionsBuilder.from_dataframe(df_template)
b_settings = {"Date": (False,80,"header-dark","#f2f2f2","left"),
              "Day": (False,100,"header-day","#ede7f6","left"),
              "গ্রহণের পরিমাণ (D)": (True,140,"header-blue","#e0f7fa",None),
              "বাকিতে নেওয়া (E)": (True,140,"header-green","#e8f5e9",None),
              "চাল প্রাপ্তি (F)": (False,130,"header-dark","#fffde7",None),
              "G (চাল ব্যবহার)": (False,130,"header-dark","#fff9c4",None)}
for col,(ed,w,cls,bg,pin) in b_settings.items():
    opts={"editable":ed,"width":w,"headerClass":cls,"cellStyle":{"backgroundColor":bg}}
    if pin: opts["pinned"]=pin
    gb.configure_column(col,**opts)
grid_opts_input=gb.build()
# Enforce order
cols=list(b_settings.keys())
df_template=df_template[cols]

# Display input grid
st.markdown("### 1) Enter D & E values (blanks=0):")
response=AgGrid(df_template,gridOptions=grid_opts_input,data_return_mode=DataReturnMode.FILTERED_AND_SORTED,update_mode=GridUpdateMode.MODEL_CHANGED,fit_columns_on_grid_load=True,height=400,theme='alpine')
edited_df=pd.DataFrame(response["data"]).reset_index(drop=True)[cols]

# Baseline G₂ input
initial_G=st.number_input("Baseline চাল ব্যবহার (G₂, Day 1)",min_value=0.0,step=0.1,format="%.2f")

# Compute button
if st.button("Compute All G"):
    df2=edited_df.copy()
    df2["Date"],df2["Day"] = dates, days
    # Numeric coercion
    df2["গ্রহণের পরিমাণ (D)"], df2["বাকিতে নেওয়া (E)"] = \
        pd.to_numeric(df2["গ্রহণের পরিমাণ (D)"],errors='coerce').fillna(0),\
        pd.to_numeric(df2["বাকিতে নেওয়া (E)"],errors='coerce').fillna(0)
    # F calculation
    df2["চাল প্রাপ্তি (F)"]=df2["গ্রহণের পরিমাণ (D)"]*RATE
    # Revised G logic: today's E reduces usage
    G=[initial_G]
    for i in range(1,len(df2)):
        prev=G[-1]
        used= df2.at[i,"চাল প্রাপ্তি (F)"]
        taken= df2.at[i,"বাকিতে নেওয়া (E)"]
        # Subtract F and E for current day
        G.append(prev - used - taken)
    df2["G (চাল ব্যবহার)"]=G
    df2=df2[cols]

    # Totals
    st.markdown("### Weekly Totals:")
    days_map={"I":["Monday","Thursday"],"J":["Tuesday","Friday"],"K":["Wednesday","Saturday"]}
    for label,col,key in [("Remaining Mon/Thu (I)","G (চাল ব্যবহার)","I"),
                           ("Remaining Tue/Fri (J)","G (চাল ব্যবহার)","J"),
                           ("Remaining Wed/Sat (K)","G (চাল ব্যবহার)","K")]:
        tot=df2.loc[df2["Day"].isin(days_map[key]),col].sum()
        st.write(f"**{label}**: {tot:.2f}")

    st.markdown("### Results Table:")
    gb2=GridOptionsBuilder.from_dataframe(df2)
    gb2.configure_default_column(editable=False)
    AgGrid(df2,gridOptions=gb2.build(),fit_columns_on_grid_load=True,height=400,theme='alpine')
