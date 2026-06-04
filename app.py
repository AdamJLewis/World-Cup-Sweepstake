import os
import re
import base64
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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

st.set_page_config(
    page_title="World Cup 2026 Sweepstake",
    page_icon="🏆",
    layout="wide"
)


def get_google_sheet_csv_url(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", sheet_url)

    if not match:
        st.error("Could not read the Google Sheet ID.")
        st.stop()

    sheet_id = match.group(1)
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"


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


@st.cache_data
def image_to_base64(path):
    if not os.path.exists(path):
        return ""

    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def flag_html(flag_file):
    flag_path = os.path.join(ASSET_FOLDER, clean_value(flag_file))
    encoded = image_to_base64(flag_path)

    if not encoded:
        return ""

    return f'<img src="data:image/png;base64,{encoded}" class="flag-img">'


def status_html(status):
    status_clean = clean_value(status).lower()

    if status_clean == "eliminated":
        return '<span class="status eliminated">● Eliminated</span>'

    return '<span class="status active">● Active</span>'


def build_single_table_html(df):
    rows_html = ""

    for index, row in df.iterrows():
        number = index + 1
        nation = clean_value(row.get("Nation", ""))
        flag = clean_value(row.get("Flag", ""))
        owner = clean_value(row.get("Owned By", ""))
        status = clean_value(row.get("Status", ""))

        rows_html += f"""
        <tr>
            <td class="number-cell">{number}</td>
            <td class="team-cell">{flag_html(flag)}<span>{nation}</span></td>
            <td>{owner}</td>
            <td>{status_html(status)}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: transparent;
            }}

            .table-spacer {{
                height: 18px;
            }}

            .team-table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid #d9e6f5;
                font-size: 13px;
            }}

            .team-table th {{
                background: #061b3a;
                color: white;
                text-align: left;
                padding: 10px;
                font-size: 12px;
                text-transform: uppercase;
            }}

            .team-table td {{
                padding: 9px 10px;
                border-bottom: 1px solid #e5edf6;
                color: #0a1f44;
                vertical-align: middle;
            }}

            .team-table tr:nth-child(even) {{
                background: #f8fbff;
            }}

            .number-cell {{
                width: 38px;
                text-align: center;
                font-weight: 700;
            }}

            .team-cell {{
                display: flex;
                align-items: center;
                gap: 9px;
                font-weight: 600;
            }}

            .flag-img {{
                width: 24px;
                height: 16px;
                object-fit: cover;
                border-radius: 2px;
                box-shadow: 0 0 0 1px rgba(0,0,0,0.12);
                flex-shrink: 0;
            }}

            .status {{
                font-weight: 800;
                white-space: nowrap;
            }}

            .active {{
                color: #0a9d4f;
            }}

            .eliminated {{
                color: #e33b2e;
            }}

            @media (max-width: 900px) {{
                .table-spacer {{
                    height: 12px;
                }}

                .team-table {{
                    font-size: 11px;
                }}

                .team-table th {{
                    padding: 8px 5px;
                    font-size: 9px;
                }}

                .team-table td {{
                    padding: 7px 5px;
                }}

                .number-cell {{
                    width: 22px;
                }}

                .team-cell {{
                    gap: 5px;
                }}

                .flag-img {{
                    width: 19px;
                    height: 13px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="table-spacer"></div>

        <table class="team-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Team</th>
                    <th>Owned By</th>
                    <th>Status</th>
                </tr>
            </thead>

            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.6rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1600px;
    }

    .stApp {
        background: linear-gradient(180deg, #f3f7fb 0%, #ffffff 100%);
    }

    .banner-wrap img {
        border-radius: 12px;
        margin-bottom: 12px;
    }

    .section-card {
        background: white;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 6px 18px rgba(15, 35, 75, 0.08);
        border: 1px solid #d9e6f5;
        height: 185px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 10px;
    }

    .prize-card {
        height: 185px;
    }

    .event-title {
        color: #0a1f44;
        font-size: 12px;
        font-weight: 900;
        text-align: center;
        min-height: 28px;
    }

    .event-main {
        font-size: 30px;
        font-weight: 900;
        text-align: center;
        margin-top: 4px;
        min-height: 40px;
    }

    .event-sub {
        color: #0a1f44;
        font-size: 13px;
        text-align: center;
        margin-top: 4px;
        min-height: 20px;
    }

    .prize-title {
        text-align: center;
        color: #0a1f44;
        margin: 0 0 6px 0;
        font-size: 17px;
        font-weight: 900;
    }

    .prize-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e5edf6;
        padding: 4px 0;
        color: #0a1f44;
        font-size: 11px;
    }

    .prize-row:last-child {
        border-bottom: none;
    }

    .prize-amount {
        font-weight: 900;
        color: #0a1f44;
    }

    .footer-card {
        background: linear-gradient(90deg, #eef5fc, #ffffff);
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #d9e6f5;
        color: #0a1f44;
        font-size: 13px;
    }

    div[data-testid="stTextInput"] {
        margin-top: 0.4rem;
    }

    div[data-testid="stRadio"] {
        margin-bottom: 0.2rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 0.45rem;
            padding-right: 0.45rem;
            padding-top: 0.35rem;
        }

        .section-card {
            height: 118px;
            border-radius: 13px;
            padding: 10px;
            margin-bottom: 6px;
        }

        .prize-card {
            height: 150px;
        }

        .event-title {
            font-size: 10px;
            min-height: 18px;
        }

        .event-main {
            font-size: 23px;
            min-height: 30px;
            margin-top: 2px;
        }

        .event-sub {
            font-size: 11px;
            min-height: 16px;
            margin-top: 2px;
        }

        .prize-title {
            font-size: 12px;
            margin-bottom: 2px;
        }

        .prize-row {
            font-size: 9px;
            padding: 2px 0;
        }

        .footer-card {
            padding: 14px;
            font-size: 12px;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stRadio"] label {
            font-size: 12px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)


raw_df = load_raw_google_sheet()

teams_df = extract_table(raw_df, ["Nation", "Flag", "Owned By", "Status"])
events_df = extract_table(raw_df, ["Category", "Time", "Team", "Player"])

teams_df = teams_df[teams_df["Nation"] != ""].copy()
teams_df = teams_df.reset_index(drop=True)


banner_path = os.path.join(ASSET_FOLDER, BANNER_FILE)

if os.path.exists(banner_path):
    banner = Image.open(banner_path)
    st.markdown('<div class="banner-wrap">', unsafe_allow_html=True)
    st.image(banner, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
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

with top_cols[0]:
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
        <div class="section-card prize-card">
            <div class="prize-title">PRIZE BREAKDOWN</div>
            {prize_rows}
        </div>
        """,
        unsafe_allow_html=True
    )


event_items = [
    ("FASTEST GOAL", goal_main, goal_sub, "#0a9d4f"),
    ("EARLIEST YELLOW CARD", yellow_main, yellow_sub, "#f2a900"),
    ("EARLIEST RED CARD", red_main, red_sub, "#e33b2e"),
    ("TOURNAMENT FAVOURITE", fav_main, fav_sub, "#0066cc"),
]

for column, item in zip(top_cols[1:], event_items):
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


search = st.text_input("Search teams or owners", "")

filter_option = st.radio(
    "Filter",
    ["All", "Active", "Eliminated"],
    horizontal=True
)

filtered_df = teams_df.copy()

if search:
    search_lower = search.lower()

    filtered_df = filtered_df[
        filtered_df["Nation"].astype(str).str.lower().str.contains(search_lower)
        | filtered_df["Owned By"].astype(str).str.lower().str.contains(search_lower)
    ]

if filter_option == "Active":
    filtered_df = filtered_df[
        filtered_df["Status"].astype(str).str.lower().str.strip() == "active"
    ]

if filter_option == "Eliminated":
    filtered_df = filtered_df[
        filtered_df["Status"].astype(str).str.lower().str.strip() == "eliminated"
    ]

filtered_df = filtered_df.reset_index(drop=True)

table_html = build_single_table_html(filtered_df)
table_height = max(1700, len(filtered_df) * 36 + 120)

components.html(
    table_html,
    height=table_height,
    scrolling=False
)


st.markdown(
    """
    <div class="footer-card">
        <h3>ℹ How it works</h3>
        <p>
        Pick an available team for £5. Multiple entries allowed.
        The tracker updates from the Google Sheet and shows team ownership,
        tournament status, prize categories and live tournament milestones.
        </p>
        <p style="font-weight:900;">🏆 Good luck and enjoy the tournament!</p>
    </div>
    """,
    unsafe_allow_html=True
)
