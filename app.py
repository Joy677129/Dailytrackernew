import streamlit as st
import pandas as pd

@st.cache_data
def load_data(path):
    return pd.read_excel(path, engine="openpyxl")

df = load_data("Daily_table_sun.xlsx")

st.title("Rice-Flow Calculator")

# --- inputs ---
date = st.number_input("Date (day of month)",
                      min_value=int(df.Date.min()),
                      max_value=int(df.Date.max()), step=1)
D_input   = st.number_input("গ্রহণের পরিমাণ (কেজি)", format="%.2f")
E_input   = st.number_input("বাকিতে নেওয়া (কেজি)", format="%.2f")
initial_G = st.number_input("Baseline চাল ব্যবহার (G₂)",
                            value=float(df.loc[df.Date==1, "চাল ব্যবহার"].iloc[0]),
                            format="%.2f")

# --- formulas as Python functions ---
def compute_G(df, initial_G):
    G = [initial_G]
    for i in range(1, len(df)):
        G.append(G[i-1]
                 - df.loc[i, "চাল প্রাপ্তি"]
                 + df.loc[i-1, "বাকিতে নেওয়া (কেজি)"])
    return pd.Series(G, index=df.index)

def compute_weekly_sums(df):
    D = df["গ্রহণের পরিমাণ (কেজি)"]
    I = pd.Series({i: D[i::7].sum() for i in df.index})
    J = pd.Series({i: D[i+1::7].sum() for i in df.index})
    K = pd.Series({i: D[i+2::7].sum() for i in df.index})
    return I, J, K

# overwrite the inputs for that date
df.loc[df.Date == date, "গ্রহণের পরিমাণ (কেজি)"] = D_input
df.loc[df.Date == date, "বাকিতে নেওয়া (কেজি)"]    = E_input

# recompute
df["G"] = compute_G(df, initial_G)
df["I"], df["J"], df["K"] = compute_weekly_sums(df)

# display the row
row = df[df.Date == date].iloc[0]
st.write("**G (চাল ব্যবহার):**", row.G)
st.write("**I (Mon/Thu):**", row.I)
st.write("**J (Tue/Fri):**", row.J)
st.write("**K (Wed/Sat):**", row.K)
