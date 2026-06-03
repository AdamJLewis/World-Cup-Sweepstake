import os
import re
import pandas as pd
import streamlit as st
from PIL import Image

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1GDI1_PquleJILX6fRqbib8Zalhbb2ua9klO5OUTIG4M/edit?usp=sharing"

ASSET_FOLDER = "Assets"
BANNER_FILE = "Page_Banner.png"

PRIZES = {
    "Tournament Winner": "£100",
    "Tournament Runner Up": "£50",
    "Earliest Goal": "£30",
    "Earliest Yellow Card": "£30",
    "Earliest Red Card": "£30",
}

st.set_page_config(page_title="World Cup 2026 Sweepstake", page_icon="🏆", layout="wide")


def get_google_sheet_csv_url(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not match:
        st.error("Could not read the Google Sheet ID.")
        st.stop()
    return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/gviz/tq?tqx=out:csv"


@st.cache_data(ttl=60)
def load_raw_google_sheet():
    try:
        return pd.read_csv(get_google_sheet_csv_url(GOOGLE_SHEET_URL), header=None)
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
    required_headers_clean = [h.lower().replace(" ", "") for h in required_headers]

    for row_index, row in raw_df.iterrows():
        row_values = [clean_value(v).lower().replace(" ", "") for v in row.tolist()]
        if all(header in row_values for header in required_headers_clean):
            return row_index, row_values

    return None, None


def extract_table(raw_df, required_headers):
    header_row, cleaned_headers = find_header_row(raw_df, required_headers)

    if header_row is None:
        st.error(f"Could not find table with headers: {required_headers}")
        st.stop()

    column_indexes = [
        cleaned_headers.index(header.lower().replace(" ", ""))
        for header in required_headers
    ]

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


def event_line(time_value, team, player):
    if time_value and team and player:
        return f"{time_value}’", f"{player} ({team})"
    if team and player:
        return team, player
    if team:
        return team, ""
    return "Awaiting result", ""


st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f3f7fb 0%, #ffffff 100%);
    }

    .section-card {
        background: white;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(15, 35, 75, 0.08);
        border: 1px solid #d9e6f5;
        height: 210px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .event-title {
        color: #0a1f44;
        font-size: 13px;
        font-weight: 900;
        text-align: center;
        min-height: 32px;
    }

    .event-main {
        font-size: 34px;
        font-weight: 900;
        text-align: center;
        margin-top: 6px;
        min-height: 48px;
    }

    .event-sub {
        color: #0a1f44;
        font-size: 14px;
        text-align: center;
        margin-top: 6px;
        min-height: 24px;
    }

    .prize-title {
        text-align: center;
        color: #0a1f44;
        margin: 0 0 8px 0;
        font-size: 21px;
        font-weight: 900;
    }

    .prize-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e5edf6;
        padding: 6px 0;
        color: #0a1f44;
        font-size: 13px;
    }

    .prize-row:last-child {
        border-bottom: none;
    }

    .prize-amount {
        font-weight: 900;
        color: #0a1f44;
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

teams_df = extract_table(raw_df, ["Nation", "Flag", "Owned By", "Status"])
events_df = extract_table(raw_df, ["Category", "Time", "Team", "Player"])

teams_df = teams_df[teams_df["Nation"] != ""].copy()

total_teams = len(teams_df)
taken_teams = teams_df["Owned By"].apply(owner_is_taken).sum()


banner_path = os.path.join(ASSET_FOLDER, BANNER_FILE)

if os.path.exists(banner_path):
    st.image(Image.open(banner_path), use_container_width=True)
else:
    st.title("🏆 World Cup 2026 Sweepstake")


earliest_goal_time, earliest_goal_team, earliest_goal_player = get_event(events_df, "Earliest Goal")
yellow_time, yellow_team, yellow_player = get_event(events_df, "Earliest Yellow Card")
red_time, red_team, red_player = get_event(events_df, "Earliest Red Card")
favourite_time, favourite_team, favourite_player = get_event(events_df, "Tournament Favourite")

goal_main, goal_sub = event_line(earliest_goal_time, earliest_goal_team, earliest_goal_player)
yellow_main, yellow_sub = event_line(yellow_time, yellow_team, yellow_player)
red_main, red_sub = event_line(red_time, red_team, red_player)
fav_main, fav_sub = event_line("", favourite_team, favourite_player)

top_cols = st.columns(5)

event_items = [
    ("FASTEST GOAL", goal_main, goal_sub, "#0a9d4f"),
    ("EARLIEST YELLOW CARD", yellow_main, yellow_sub, "#f2a900"),
    ("EARLIEST RED CARD", red_main, red_sub, "#e33b2e"),
    ("TOURNAMENT FAVOURITE", fav_main, fav_sub, "#0066cc"),
]

for column, item in zip(top_cols[:4], event_items):
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

with top_cols[4]:
    prize_rows = ""

    for prize, amount in PRIZES.items():
        prize_rows += f"""
        <div class="prize-row">
            <span>{prize}</span>
            <span class="prize-amount">{amount}</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="section-card">
            <div class="prize-title">PRIZE BREAKDOWN</div>
            {prize_rows}
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

filter_option = st.radio("Filter", ["All", "Available", "Taken"], horizontal=True)

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

st.dataframe(filtered_df, use_container_width=True, hide_index=True, height=650)

st.markdown(
    """
    <div class="footer-card">
        <h3>ℹ How it works</h3>
        <p>
        Pick an available team for £5. Multiple entries allowed.
        The tracker updates from the Google Sheet and shows team ownership,
        prize categories and live tournament milestones.
        </p>
        <p style="font-weight:900;">🏆 Good luck and enjoy the tournament!</p>
    </div>
    """,
    unsafe_allow_html=True
)
