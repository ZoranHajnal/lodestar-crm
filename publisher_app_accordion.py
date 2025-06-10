import streamlit as st
import pandas as pd
import io
import re
import string
from collections import defaultdict

# ─── Page Configuration ───────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Publisher CRM – A–Z Accordion View")

# ─── Load & Preprocess Data ───────────────────────────────────────────────────────
df = pd.read_excel("Master publishers contact list .xlsx")
df["Platforms"] = df["Platforms"].fillna("").str.lower()
df["Genres"] = df["Genres"].fillna("").str.lower()
df["Contact name"] = df["Contact name"].fillna("").astype(str)
df["email"] = df["email"].fillna("").astype(str)

def parse_budget_min(budget_str):
    if pd.isna(budget_str):
        return 0
    text = str(budget_str).lower().replace("+", "").replace("&", "").replace("<", "").replace(">", "")
    try:
        if "k" in text:
            return int(float(text.split("k")[0].strip()) * 1000)
        if "m" in text:
            return int(float(text.split("m")[0].strip()) * 1_000_000)
    except:
        pass
    return 0

df["Budget Min"] = df["budget range"].apply(parse_budget_min)

grouped_df = df.groupby("Publisher", as_index=False).agg({
    "Genres": "first",
    "Platforms": "first",
    "budget range": "first",
    "Budget Min": "first",
    "Contact name": lambda x: "; ".join(filter(None, x.unique())),
    "email": lambda x: "; ".join(filter(None, x.unique()))
})

# Build filter option lists
all_genres = set()
for g in grouped_df["Genres"].dropna():
    for piece in g.split(";"):
        all_genres.add(piece.strip())
genres_list = sorted(all_genres)
platform_list = ["PC", "Console", "Mobile", "VR"]

# ─── Sidebar Filters ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filter Options")
    selected_genres = st.multiselect("🎮 Select Genre(s):", genres_list)
    selected_platforms = st.multiselect("🕹️ Select Platform(s):", platform_list)
    max_budget = st.slider("💰 Max Budget ($)", 0, 5_000_000, 300_000, step=50_000)
    only_with_contacts = st.checkbox("✅ Only if contact/email exists")
    keyword = st.text_input("🔎 Keyword (Publisher / Genre / Platform):", "")

filtered_df = grouped_df.copy()

# Apply Genre filter
if selected_genres:
    filtered_df = filtered_df[
        filtered_df["Genres"].apply(lambda g: any(gen.lower() in g for gen in selected_genres))
    ]

# Apply Platform filter
if selected_platforms:
    filtered_df = filtered_df[
        filtered_df["Platforms"].apply(lambda p: all(pl.lower() in p for pl in selected_platforms))
    ]

# Apply Budget filter
filtered_df = filtered_df[filtered_df["Budget Min"] <= max_budget]

# Apply Contact presence filter
if only_with_contacts:
    filtered_df = filtered_df[
        (filtered_df["Contact name"].str.strip() != "") |
        (filtered_df["email"].str.strip() != "")
    ]

# Apply Keyword search
if keyword:
    kw = keyword.lower()
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: (
                kw in str(row["Publisher"]).lower()
                or kw in str(row["Genres"]).lower()
                or kw in str(row["Platforms"]).lower()
            ), axis=1
        )
    ]

# ─── Session State for Tags ───────────────────────────────────────────────────────
tags_dict = st.session_state.get("tags_dict", {})

# ─── Tabs ─────────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📋 All Publishers", "📌 Follow-Up View"])

# ─── ALL PUBLISHERS: A–Z Accordion ────────────────────────────────────────────────
with tabs[0]:
    st.title("🎮 All Publishers (A–Z Accordion)")
    st.subheader(f"📋 {len(filtered_df)} matches")

    # Group publishers by first character (digits grouped under "0–9")
    groups = defaultdict(list)
    for _, row in filtered_df.iterrows():
        first_char = row["Publisher"][0].upper()
        if not first_char.isalpha():
            first_char = "0–9"
        groups[first_char].append(row)

    # Iterate letters in order
    for letter in ["0–9"] + list(string.ascii_uppercase):
        if letter in groups:
            with st.expander(letter, expanded=False):
                for row in groups[letter]:
                    st.write(f"• **{row['Publisher']}**  —  Genres: {row['Genres']}, Platforms: {row['Platforms']}")
                st.write("")  # spacing

    # Download button at the end
    st.markdown("### 📥 Download Filtered Results")
    excel_buffer = io.BytesIO()
    filtered_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        label="Download as Excel",
        data=excel_buffer,
        file_name="filtered_publishers_az.xlsx",
        mime="application/vnd.openxmlformats-officedocument-spreadsheetml.sheet"
    )

# ─── FOLLOW-UP VIEW ────────────────────────────────────────────────────────────────
with tabs[1]:
    st.title("📌 Follow-Up View")
    st.subheader("Filter by tag and schedule next contact")

    followup_tag = st.selectbox(
        "🧷 Select tag to view:",
        ["Top priority", "Contacted", "Waiting reply", "Good fit", "Not interested"]
    )

    count_follow = 0
    for idx, row in filtered_df.iterrows():
        tag_set = tags_dict.get(row["Publisher"], [])
        if followup_tag in tag_set:
            count_follow += 1
            raw_key2 = f"{row['Publisher']}_{row['email'].split(';')[0]}"
            safe_key2 = re.sub(r"[^a-zA-Z0-9_]", "_", raw_key2)

            with st.expander(f"📍 {row['Publisher']}", expanded=False):
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.write(f"🎯 **Genres**: {row['Genres']}")
                    st.write(f"🖥️ **Platforms**: {row['Platforms']}")
                    st.write(f"💸 **Budget**: {row['budget range']}")
                with col2:
                    st.write(f"👤 **Contacts**: {row['Contact name']}")
                    st.write(f"📧 **Emails**: {row['email']}")
                    last_contacted = st.date_input(
                        "📅 Last Contacted", key=f"last_contact_{safe_key2}"
                    )
                    next_contact = st.date_input(
                        "🗓️ Next Contact Date", key=f"next_contact_{safe_key2}"
                    )
    if count_follow == 0:
        st.write("No publishers found with that tag.")
