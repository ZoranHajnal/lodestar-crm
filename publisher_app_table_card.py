import streamlit as st
import pandas as pd
import io
import re

# ─── Page Configuration ───────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Publisher CRM – Table + Card View with Pagination")

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
            return int(float(text.split("m")[0].strip()) * 1000000)
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
   import streamlit as st
import pandas as pd
import io
import re

# ─── Page Configuration ───────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Publisher CRM – Table + Card View")

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
            return int(float(text.split("m")[0].strip()) * 1000000)
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
all_genres = sorted({g.strip() for row in grouped_df["Genres"] if row for g in row.split(";")})
platform_list = ["PC", "Console", "Mobile", "VR"]

# ─── Sidebar Filters ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔍 Filter Options")
    selected_genres = st.multiselect("🎮 Select Genre(s):", all_genres)
    selected_platforms = st.multiselect("🕹️ Select Platform(s):", platform_list)
    max_budget = st.slider("💰 Max Budget ($)", 0, 5_000_000, 300_000, step=50_000)
    only_with_contacts = st.checkbox("✅ Only if contact name or email exists")
    keyword = st.text_input("🔎 Keyword (Publisher / Genre / Platform):", "")

filtered_df = grouped_df.copy()

if selected_genres:
    filtered_df = filtered_df[
        filtered_df["Genres"].apply(lambda g: any(gen.lower() in g.lower() for gen in selected_genres))
    ]

if selected_platforms:
    filtered_df = filtered_df[
        filtered_df["Platforms"].apply(lambda p: all(pl.lower() in p.lower() for pl in selected_platforms))
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

# ─── Session State for Tags & Pagination ─────────────────────────────────────────
tags_dict = st.session_state.get("tags_dict", {})
if "page_num" not in st.session_state:
    st.session_state.page_num = 0
PAGE_SIZE = 50

total_count = len(filtered_df)
total_pages = (total_count // PAGE_SIZE) + (1 if total_count % PAGE_SIZE else 0)

tabs = st.tabs(["📋 All Publishers", "📌 Follow-Up View"])

# ─── ALL PUBLISHERS: Table + Card with Centered Pagination ───────────────────────
with tabs[0]:
    st.title("🎮 All Publishers (Table + Card View)")
    start_idx = st.session_state.page_num * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    st.subheader(f"📋 Showing {start_idx+1}-{min(end_idx, total_count)} of {total_count} publishers")

    # Centered pagination controls
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("◀ Previous") and st.session_state.page_num > 0:
            st.session_state.page_num -= 1
    with col2:
        page_text = f"Page {st.session_state.page_num+1} of {total_pages}"
        st.markdown(f"<div style='text-align: center; font-weight: bold;'>{page_text}</div>", unsafe_allow_html=True)
    with col3:
        if st.button("Next ▶") and st.session_state.page_num < total_pages - 1:
            st.session_state.page_num += 1

    page_df = filtered_df.iloc[start_idx:end_idx]

    sub_tabs = st.tabs(["Table View", "Card View"])

    with sub_tabs[0]:
        st.write("#### Table View of Publishers")
        st.dataframe(
            page_df[["Publisher", "Genres", "Platforms", "budget range", "Contact name", "email"]],
            use_container_width=True
        )
    with sub_tabs[1]:
        st.write("#### Card View of Publishers")
        cols = st.columns(3)
        for idx, row in page_df.iterrows():
            col = cols[idx % 3]
            with col:
                with st.expander(f"{row['Publisher']}"):
                    st.write(f"🎯 **Genres**: {row['Genres']}")
                    st.write(f"🖥️ **Platforms**: {row['Platforms']}")
                    st.write(f"💸 **Budget**: {row['budget range']}")
                    st.write(f"👤 **Contacts**: {row['Contact name']}")
                    st.write(f"📧 **Emails**: {row['email']}")
                    raw_key = f"{row['Publisher']}_{row['email'].split(';')[0]}"
                    safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", raw_key)
                    tags = st.multiselect(
                        "🏷️ Tags:",
                        ["Top priority", "Contacted", "Waiting reply", "Not interested", "Good fit"],
                        default=tags_dict.get(row["Publisher"], []),
                        key=f"tag_{safe_key}"
                    )
                    tags_dict[row["Publisher"]] = tags

        st.session_state["tags_dict"] = tags_dict

    st.markdown("### 📥 Download Current Page Results")
    excel_buffer = io.BytesIO()
    page_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        label="Download as Excel",
        data=excel_buffer,
        file_name=f"filtered_publishers_page_{st.session_state.page_num+1}.xlsx",
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
     )
    ]

# ─── Session State for Tags & Pagination ─────────────────────────────────────────
tags_dict = st.session_state.get("tags_dict", {})
if "page_num" not in st.session_state:
    st.session_state.page_num = 0
PAGE_SIZE = 50

# Calculate total pages
total_count = len(filtered_df)
total_pages = (total_count // PAGE_SIZE) + (1 if total_count % PAGE_SIZE != 0 else 0)

# Slice for current page
start_idx = st.session_state.page_num * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE
page_df = filtered_df.iloc[start_idx:end_idx]

# ─── Tabs ─────────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📋 All Publishers", "📌 Follow-Up View"])

# ─── ALL PUBLISHERS: Table + Card with Pagination ─────────────────────────────────
with tabs[0]:
    st.title("🎮 All Publishers (Table + Card View)")
    st.subheader(f"📋 Showing {start_idx+1}-{min(end_idx, total_count)} of {total_count} publishers")

    # Pagination controls at top
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("◀ Previous") and st.session_state.page_num > 0:
            st.session_state.page_num -= 1
    with col2:
        st.markdown(f"**Page {st.session_state.page_num+1} of {total_pages}**")
    with col3:
        if st.button("Next ▶") and st.session_state.page_num < total_pages - 1:
            st.session_state.page_num += 1

    # Internal sub-tabs: Table View vs Card View
    sub_tabs = st.tabs(["Table View", "Card View"])

    # ─ Table View ───────────────────────────────────────────────────────────────
    with sub_tabs[0]:
        st.write("#### Table View of Publishers")
        st.dataframe(
            page_df[["Publisher", "Genres", "Platforms", "budget range", "Contact name", "email"]],
            use_container_width=True
        )

    # ─ Card View ────────────────────────────────────────────────────────────────
    with sub_tabs[1]:
        st.write("#### Card View of Publishers")
        cols = st.columns(3)
        for idx, row in page_df.iterrows():
            col = cols[idx % 3]
            with col:
                with st.expander(f"{row['Publisher']}"):
                    st.write(f"🎯 **Genres**: {row['Genres']}")
                    st.write(f"🖥️ **Platforms**: {row['Platforms']}")
                    st.write(f"💸 **Budget**: {row['budget range']}")
                    st.write(f"👤 **Contacts**: {row['Contact name']}")
                    st.write(f"📧 **Emails**: {row['email']}")
                    raw_key = f"{row['Publisher']}_{row['email'].split(';')[0]}"
                    safe_key = re.sub(r"[^a-zA-Z0-9_]", "_", raw_key)
                    tags = st.multiselect(
                        "🏷️ Tags:",
                        ["Top priority", "Contacted", "Waiting reply", "Not interested", "Good fit"],
                        default=tags_dict.get(row["Publisher"], []),
                        key=f"tag_{safe_key}"
                    )
                    tags_dict[row["Publisher"]] = tags

        # Persist tags back into session state
        st.session_state["tags_dict"] = tags_dict

    # Download button at bottom
    st.markdown("### 📥 Download Current Page Results")
    excel_buffer = io.BytesIO()
    page_df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        label="Download as Excel",
        data=excel_buffer,
        file_name=f"filtered_publishers_page_{st.session_state.page_num+1}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
