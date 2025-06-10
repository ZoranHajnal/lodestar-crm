import streamlit as st
import pandas as pd
import io
import re

# ─── Page Configuration ─────────────────────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Publisher Search App")

# ─── Load & Preprocess Data ──────────────────────────────────────────────────────

# Make sure this file is in the same folder as "Master publishers contact list .xlsx"
df = pd.read_excel("Master publishers contact list .xlsx")

# Normalize text columns
df["Platforms"] = df["Platforms"].fillna("").str.lower()
df["Genres"] = df["Genres"].fillna("").str.lower()
df["Contact name"] = df["Contact name"].fillna("").astype(str)
df["email"] = df["email"].fillna("").astype(str)

# Extract numeric "Budget Min" from "budget range" (e.g. "300K" → 300000)
def parse_budget_min(budget_str):
    if pd.isna(budget_str):
        return None
    text = str(budget_str).lower().replace("+", "").replace("&", "").replace("<", "").replace(">", "")
    # If contains "k" (thousands)
    if "k" in text:
        try:
            return int(float(text.split("k")[0].strip()) * 1000)
        except:
            return None
    # If contains "m" (millions)
    if "m" in text:
        try:
            return int(float(text.split("m")[0].strip()) * 1000000)
        except:
            return None
    return None

df["Budget Min"] = df["budget range"].apply(parse_budget_min)

# Group all contacts by Publisher: combine names/emails with semicolons
grouped_df = df.groupby("Publisher", as_index=False).agg({
    "Genres": "first",
    "Platforms": "first",
    "budget range": "first",
    "Budget Min": "first",
    "Contact name": lambda x: "; ".join(filter(None, x.unique())),
    "email": lambda x: "; ".join(filter(None, x.unique()))
})

# Build list of all available genres and platforms for filters
# (split semicolon strings, dedupe)
all_genres = set()
for g in grouped_df["Genres"].dropna():
    for piece in g.split(";"):
        all_genres.add(piece.strip())
genres_list = sorted(all_genres)

platform_list = ["PC", "Console", "Mobile", "VR"]

# ─── Sidebar Filters ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔍 Filter Options")

    selected_genres = st.multiselect(
        "🎮 Select Genre(s):", genres_list
    )
    selected_platforms = st.multiselect(
        "🕹️ Select Platforms:", platform_list
    )
    max_budget = st.slider(
        "💰 Max Budget ($)", 0, 5000000, 300000, step=50000
    )
    only_with_contacts = st.checkbox(
        "✅ Show only if contact name or email exists"
    )
    keyword = st.text_input(
        "🔎 Keyword search (Publisher, Genre, Platform):", ""
    )

# ─── Filtering Logic ─────────────────────────────────────────────────────────────

filtered_df = grouped_df.copy()

# 1. Genre filter
if selected_genres:
    filtered_df = filtered_df[
        filtered_df["Genres"].apply(
            lambda g: any(gen.lower() in g for gen in selected_genres)
        )
    ]

# 2. Platform filter
if selected_platforms:
    filtered_df = filtered_df[
        filtered_df["Platforms"].apply(
            lambda p: all(pl.lower() in p for pl in selected_platforms)
        )
    ]

# 3. Budget filter
filtered_df = filtered_df[
    filtered_df["Budget Min"].fillna(0) <= max_budget
]

# 4. Contact/email existence filter
if only_with_contacts:
    filtered_df = filtered_df[
        (filtered_df["Contact name"].str.strip() != "") |
        (filtered_df["email"].str.strip() != "")
    ]

# 5. Keyword search (search in Publisher, Genres, Platforms)
if keyword:
    kw = keyword.lower()
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: (
                kw in str(row["Publisher"]).lower()
                or kw in str(row["Genres"]).lower()
                or kw in str(row["Platforms"]).lower()
            ),
            axis=1,
        )
    ]

# ─── Tagging Setup ───────────────────────────────────────────────────────────────

# Initialize or load tags dictionary (per session)
tags_dict = st.session_state.get("tags_dict", {})

# ─── App Title & Results Count ───────────────────────────────────────────────────

st.title("🎮 Publisher Search App")
st.subheader(f"📋 Filtered Results: {len(filtered_df)} matches")

# ─── Display Each Publisher as an Expander Card ──────────────────────────────────

for idx, row in filtered_df.iterrows():
    # Build a “safe” key combining Publisher and email, stripping non-alphanumeric
    raw_key = f"{row['Publisher']}_{row['email']}"
    safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", raw_key)

    with st.expander(f"{row['Publisher']}", expanded=False):
        col1, col2 = st.columns([2, 3])

        with col1:
            st.write(f"🎯 **Genres**: {row['Genres']}")
            st.write(f"🖥️ **Platforms**: {row['Platforms']}")
            st.write(f"💸 **Budget**: {row['budget range']}")

        with col2:
            st.write(f"👤 **Contacts**: {row['Contact name']}")
            st.write(f"📧 **Emails**: {row['email']}")

            # Tagging widget
            tags = st.multiselect(
                "🏷️ Tags:",
                [
                    "Top priority",
                    "Contacted",
                    "Waiting reply",
                    "Not interested",
                    "Good fit"
                ],
                default=tags_dict.get(row["Publisher"], []),
                key=f"tag_{safe_key}"
            )
            tags_dict[row["Publisher"]] = tags

# Save tags back into session state
st.session_state["tags_dict"] = tags_dict

# ─── Download Filtered Results as Excel ──────────────────────────────────────────

st.markdown("### 📥 Download Filtered Results")
excel_buffer = io.BytesIO()
filtered_df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0)

st.download_button(
    label="Download as Excel",
    data=excel_buffer,
    file_name="filtered_publishers_grouped.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
