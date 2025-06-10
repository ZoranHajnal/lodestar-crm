import streamlit as st
import pandas as pd
import io
import re

# ─── Apply wide layout + custom theming ──────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Publisher Search & Follow-Up App")

# ─── Inject Lodestar’s Montserrat font + CSS tweaks ─────────────────────────────

st.markdown(
    """
    <style>
      /* ─── Lodestar Montserrat Font ───────────────────────────────────────────── */
      @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

      /* Apply Montserrat globally */
      html, body, [class*="css"] {
          font-family: 'Montserrat', sans-serif;
      }

      /* ─── Sidebar Header Background ───────────────────────────────────────────── */
      [data-testid="stSidebar"] .css-15tx938 {
          background-color: #F0F4F8;  /* Matches secondaryBackgroundColor */
          padding: 1rem;
          border-radius: 0.5rem;
      }

      /* ─── Expander & Card Styles ──────────────────────────────────────────────── */
      .streamlit-expanderHeader {
          background-color: #FFFFFF;       /* White expander header */
          color: #002F6C !important;       /* Dark navy text */
          font-weight: 600;                /* Semi‐bold Montserrat */
          border: 1px solid #E0E4EA;       /* Light border */
          border-radius: 0.5rem 0.5rem 0 0;
      }
      .streamlit-expander {
          background-color: #FFFFFF;       /* White interior */
          border: 1px solid #E0E4EA;       /* Light border around expanders */
          border-radius: 0.5rem;
          margin-bottom: 1rem;
      }

      /* ─── Button & Checkbox Accent ────────────────────────────────────────────── */
      button[kind="primary"], .st-bf {
          background-color: #FFC72C !important;  /* Lodestar gold */
          color: #002F6C !important;             /* Dark navy text */
      }
      input[type="checkbox"] + label::before {
          border-color: #FFC72C !important;      /* Checkbox border */
      }
      input[type="checkbox"]:checked + label::after {
          background-color: #FFC72C !important;  /* Checked box fill */
      }

      /* ─── DataFrame Header ───────────────────────────────────────────────────── */
      .css-1lcbmhc th {
          background-color: #002F6C !important;  /* Dark navy header */
          color: #FFFFFF !important;             /* White header text */
      }

      /* ─── Page Background ─────────────────────────────────────────────────────── */
      .main {
          background-color: #FFFFFF;  /* White page background */
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Load & Preprocess Data ──────────────────────────────────────────────────────

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

# ── Group contacts per publisher (merge multiple rows) ──────────────────────────

grouped_df = df.groupby("Publisher", as_index=False).agg({
    "Genres": "first",
    "Platforms": "first",
    "budget range": "first",
    "Budget Min": "first",
    "Contact name": lambda x: "; ".join(filter(None, x.unique())),
    "email": lambda x: "; ".join(filter(None, x.unique()))
})

# Build filter options
all_genres = set()
for g in grouped_df["Genres"].dropna():
    for piece in g.split(";"):
        all_genres.add(piece.strip())
genres_list = sorted(all_genres)

platform_list = ["PC", "Console", "Mobile", "VR"]

# ─── Build Tabs ─────────────────────────────────────────────────────────────────

tabs = st.tabs(["📋 All Publishers", "📌 Follow-Up View"])

# ─── Sidebar Filters (applies to All Publishers) ────────────────────────────────

with st.sidebar:
    st.header("🔍 Filter Options")
    selected_genres = st.multiselect("🎮 Select Genre(s):", genres_list)
    selected_platforms = st.multiselect("🕹️ Select Platform(s):", platform_list)
    max_budget = st.slider("💰 Max Budget ($)", 0, 5_000_000, 300_000, step=50_000)
    only_with_contacts = st.checkbox("✅ Show only if contact name or email exists")
    keyword = st.text_input("🔎 Keyword search (Publisher, Genre, Platform):", "")

# ─── Apply Filters ───────────────────────────────────────────────────────────────

filtered_df = grouped_df.copy()

if selected_genres:
    filtered_df = filtered_df[
        filtered_df["Genres"].apply(lambda g: any(gen.lower() in g for gen in selected_genres))
    ]

if selected_platforms:
    filtered_df = filtered_df[
        filtered_df["Platforms"].apply(lambda p: all(pl.lower() in p for pl in selected_platforms))
    ]

filtered_df = filtered_df[filtered_df["Budget Min"] <= max_budget]

if only_with_contacts:
    filtered_df = filtered_df[
        (filtered_df["Contact name"].str.strip() != "") |
        (filtered_df["email"].str.strip() != "")
    ]

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

# ─── Session‐State Tagging Dict ──────────────────────────────────────────────────

tags_dict = st.session_state.get("tags_dict", {})

# ─── Tab 1: All Publishers ───────────────────────────────────────────────────────

with tabs[0]:
    st.title("🎮 All Publishers")
    st.subheader(f"📋 Filtered Results: {len(filtered_df)} matches")

    for idx, row in filtered_df.iterrows():
        raw_key = f"{row['Publisher']}_{row['email'].split(';')[0]}"
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
                tags = st.multiselect(
                    "🏷️ Tags:",
                    ["Top priority", "Contacted", "Waiting reply", "Not interested", "Good fit"],
                    default=tags_dict.get(row["Publisher"], []),
                    key=f"tag_{safe_key}"
                )
                tags_dict[row["Publisher"]] = tags

    st.session_state["tags_dict"] = tags_dict

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

# ─── Tab 2: Follow-Up View ─────────────────────────────────────────────────────────

with tabs[1]:
    st.title("📌 Follow-Up View")
    st.subheader("Filter by tag and plan next contact")

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
