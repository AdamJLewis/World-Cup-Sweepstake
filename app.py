import os
import re
import pandas as pd
import streamlit as st
from PIL import Image

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GDI1_PquleJILX6fRqbib8Zalhbb2ua9klO5OUTIG4M/edit?usp=sharing"

ASSET_FOLDER = "Assets"
BANNER_FILE = "Page_Banner.png"

PRICE_PER_TEAM = 5

PRIZES = {
    "Tournament Winner": "£100",
    "Tournament Runner Up": "£50",
    "Earliest Goal": "£30",
    "Earliest Yellow Card": "£30",
    "Earliest Red Card": "£30",
}


st.set_page_config(
    page_title="World Cup 2026 Sweepstake",
    page_icon="🏆",
    layout="wide"
)


def get_google_sheet_csv_url(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)

    if not match:
        st.error("Could not read the Google Sheet ID from the link.")
        st.stop()

    sheet_id = match.group(1)

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"


@st.cache_data(ttl=60)
def load_raw_google_sheet():
    csv_url = get_google_sheet_csv_url(GOOGLE_SHEET_URL)

    try:
        return pd.read_csv(csv_url, header=None)
    except Exception as error:
        st.error("Could not load the Google Sheet.")
        st.write(error)
        st.info("Make sure the Google Sheet is shared as Anyone with the link can view.")
        st.stop()


def clean_value(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def find_header_row(raw_df, required_headers):
    required_headers = [header.lower().replace(" ", "") for header in required_headers]

    for row_index, row in raw_df.iterrows():
        row_values = [
            clean_value(value).lower().replace(" ", "")
            for value in row.tolist()
        ]

        if all(header in row_values for header in required_headers):
            return row_index, row_values

    return None, None


def extract_table(raw_df, required_headers):
    header_row, cleaned_headers = find_header_row(raw_df, required_headers)

    if header_row is None:
        st.error(f"Could not find table with headers: {required_headers}")
        st.stop()

    column_indexes = []

    for required_header in required_headers:
        clean_required = required_header.lower().replace(" ", "")
        column_indexes.append(cleaned_headers.index(clean_required))

    rows = []

    for row_number in range(header_row + 1, len(raw_df)):
        row_data = {}

        for header, column_index in zip(required_headers, column_indexes):
            row_data[header] = clean_value(raw_df.iloc[row_number, column_index])

        if all(value == "" for value in row_data.values()):
            break

        rows.append(row_data)

    return pd.DataFrame(rows)


def owner_is_taken(owner):
    return clean_value(owner) != ""


def get_event(events_df, category):
    match = events_df[
        events_df["Category"].astype(str).str.strip().str.lower()
        == category.strip().lower()
    ]

    if match.empty:
        return "", "", ""

    row = match.iloc[0]

    return (
        clean_value(row.get("Time", "")),
        clean_value(row.get("Team", "")),
        clean_value(row.get("Player", "")),
    )


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f3f7fb 0%, #ffffff 100%);
    }

    .main-card {
        background: white;
        border-radius: 18px;
        padding: 24px;
        box-shadow: 0 8px 24px rgba(15, 35, 75, 0.08);
        border: 1px solid #d9e6f5;
        text-align: center;
        min-height: 170px;
    }

    .section-card {
        background: white;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 8px 24px rgba(15, 35, 75, 0.08);
        border: 1px solid #d9e6f5;
        margin-bottom: 18px;
    }

    .metric-title {
        font-size: 15px;
        color: #0a1f44;
        font-weight: 700;
        margin-top: 6px;
    }

    .metric-value-blue {
        font-size: 42px;
        color: #0066cc;
        font-weight: 900;
    }

    .metric-value-green {
        font-size: 42px;
        color: #0a9d4f;
        font-weight: 900;
    }

    .metric-value-gold {
        font-size: 42px;
        color: #f2a900;
        font-weight: 900;
    }

    .event-title {
        color: #0a1f44;
        font-size: 14px;
        font-weight: 900;
        text-align: center;
    }

    .event-main {
        font-size: 34px;
        font-weight: 900;
        text-align: center;
    }

    .event-sub {
        color: #0a1f44;
        font-size: 14px;
        text-align: center;
    }

    .taken-badge {
        background: #eef5fc;
        border-radius: 12px;
        padding: 14px;
        text-align: center;
        color: #0a1f44;
        font-weight: 900;
        font-size: 20px;
        border: 1px solid #d9e6f5;
    }

    .footer-card {
        background: linear-gradient(90deg, #eef5fc, #ffffff);
        border-radius: 18px;
        padding: 24px;
        border: 1px solid #d9e6f5;
        color: #0a1f44;
    }
    </style>
    """,
    unsafe_allow_html=True
)


raw_df = load_raw_google_sheet()

teams_df = extract_table(
    raw_df,
    ["Nation", "Flag", "Owned By", "Status"]
)

events_df = extract_table(
    raw_df,
    ["Category", "Time", "Team", "Player"]
)

teams_df = teams_df[teams_df["Nation"] != ""].copy()

total_teams = len(teams_df)
taken_teams = teams_df["Owned By"].apply(owner_is_taken).sum()
prize_fund = total_teams * PRICE_PER_TEAM


banner_path = os.path.join(ASSET_FOLDER, BANNER_FILE)

if os.path.exists(banner_path):
    banner = Image.open(banner_path)
    st.image(banner, use_container_width=True)
else:
    st.title("🏆 World Cup 2026 Sweepstake")


col1, col2, col3, col4 = st.columns([1, 1, 1, 1.45])

with col1:
    st.markdown(
        f"""
        <div class="main-card">
            <div style="font-size: 48px;">⚽</div>
            <div class="metric-value-blue">{total_teams}</div>
            <div class="metric-title">Teams Available</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="main-card">
            <div style="font-size: 48px;">💷</div>
            <div class="metric-value-green">£{PRICE_PER_TEAM}</div>
            <div class="metric-title">Per Team</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="main-card">
            <div style="font-size: 48px;">🏆</div>
            <div class="metric-value-gold">£{prize_fund}</div>
            <div class="metric-title">Total Prize Fund</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    prize_html = """
    <div class="section-card">
        <h4 style="text-align:center;color:#0a1f44;">PRIZE BREAKDOWN</h4>
    """

    for prize, amount in PRIZES.items():
        prize_html += f"""
        <div style="display:flex;justify-content:space-between;border-bottom:1px solid #e5edf6;padding:7px 0;color:#0a1f44;">
            <span>{prize}</span>
            <strong>{amount}</strong>
        </div>
        """

    prize_html += "</div>"

    st.markdown(prize_html, unsafe_allow_html=True)


earliest_goal_time, earliest_goal_team, earliest_goal_player = get_event(events_df, "Earliest Goal")
yellow_time, yellow_team, yellow_player = get_event(events_df, "Earliest Yellow Card")
red_time, red_team, red_player = get_event(events_df, "Earliest Red Card")
favourite_time, favourite_team, favourite_player = get_event(events_df, "Tournament Favourite")

event_items = [
    (
        "FASTEST GOAL",
        f"{earliest_goal_time}’" if earliest_goal_time else "",
        f"{earliest_goal_player} ({earliest_goal_team})",
        "#0a9d4f"
    ),
    (
        "EARLIEST YELLOW CARD",
        f"{yellow_time}’" if yellow_time else "",
        f"{yellow_player} ({yellow_team})",
        "#f2a900"
    ),
    (
        "EARLIEST RED CARD",
        f"{red_time}’" if red_time else "",
        f"{red_player} ({red_team})",
        "#e33b2e"
    ),
    (
        "TOURNAMENT FAVOURITE",
        favourite_team,
        favourite_player,
        "#0066cc"
    ),
]

event_cols = st.columns(4)

for column, item in zip(event_cols, event_items):
    title, main, sub, colour = item

    with column:
        st.markdown(
            f"""
            <div class="section-card">
                <div class="event-title">{title}</div>
                <div class="event-main" style="color:{colour};">{main}</div>
                <div class="event-sub">{sub}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


left, right = st.columns([3, 1])

with left:
    st.markdown("## 🏆 Team Selections")

with right:
    st.markdown(
        f"""
        <div class="taken-badge">
            <span style="color:#0a9d4f;">{taken_teams}</span> / {total_teams} Teams Taken
        </div>
        """,
        unsafe_allow_html=True
    )


display_df = teams_df.copy()

display_df["Owned By"] = display_df["Owned By"].apply(
    lambda owner: clean_value(owner) if owner_is_taken(owner) else "Available"
)

display_df["Status"] = display_df["Owned By"].apply(
    lambda owner: "🟢 Taken" if owner != "Available" else "⚪ Available"
)

display_df.insert(0, "#", range(1, len(display_df) + 1))

display_df = display_df[["#", "Nation", "Owned By", "Status"]]
display_df = display_df.rename(columns={"Nation": "Team"})

search = st.text_input("Search teams or owners", "")

filter_option = st.radio(
    "Filter",
    ["All", "Available", "Taken"],
    horizontal=True
)

filtered_df = display_df.copy()

if search:
    search_lower = search.lower()

    filtered_df = filtered_df[
        filtered_df["Team"].astype(str).str.lower().str.contains(search_lower)
        | filtered_df["Owned By"].astype(str).str.lower().str.contains(search_lower)
    ]

if filter_option == "Available":
    filtered_df = filtered_df[filtered_df["Owned By"] == "Available"]

if filter_option == "Taken":
    filtered_df = filtered_df[filtered_df["Owned By"] != "Available"]

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    height=650
)


st.markdown(
    """
    <div class="footer-card">
        <h3>ℹ How it works</h3>
        <p>
        Pick an available team for £5. Multiple entries allowed.
        Winners are decided by the tournament winner, runner up and earliest in game events.
        </p>
        <p style="font-weight:900;">🏆 Good luck and enjoy the tournament!</p>
    </div>
    """,
    unsafe_allow_html=True
)
