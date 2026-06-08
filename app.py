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

DRAW_VIDEO_URL = "https://drive.google.com/file/d/1OG5E4v4hIy6Br6bCWTIcCYTUsstXxU4a/view?usp=sharing"

PRIZES = {
    "Tournament Winner": "£100",
    "Tournament Runner Up": "£50",
    "Fastest Goal": "£30",
    "Fastest Yellow Card": "£30",
    "Fastest Red Card": "£30",
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

            .team-table {{
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
                border-radius: 14px;
                overflow: hidden;
                border: 1px solid #0fd084;
                font-size: 13px;
                box-shadow: 0 8px 22px rgba(0, 232, 150, 0.12);
            }}

            .team-table th {{
                background: linear-gradient(90deg, #020b1f, #06244a);
                color: #ffffff;
                text-align: left;
                padding: 10px;
                font-size: 12px;
                text-transform: uppercase;
                border-bottom: 2px solid #d8a23a;
            }}

            .team-table td {{
                padding: 9px 10px;
                border-bottom: 1px solid #dce8ef;
                color: #07142c;
                vertical-align: middle;
            }}

            .team-table tr:nth-child(even) {{
                background: #f2fff9;
            }}

            .number-cell {{
                width: 38px;
                text-align: center;
                font-weight: 700;
                color: #061b3a;
            }}

            .team-cell {{
                display: flex;
                align-items: center;
                gap: 9px;
                font-weight: 700;
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
                font-weight: 900;
                white-space: nowrap;
            }}

            .active {{
                color: #00a95c;
            }}

            .eliminated {{
                color: #ef3340;
            }}

            @media (max-width: 900px) {{
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


def build_prize_card_html():
    prize_rows = ""

    for prize, amount in PRIZES.items():
        prize_rows += f"""
        <div class="prize-row">
            <span>{prize}</span>
            <span class="prize-amount">{amount}</span>
        </div>
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

            .section-card {{
                background: linear-gradient(180deg, #ffffff 0%, #f6fff9 100%);
                border-radius: 16px;
                padding: 16px;
                box-shadow: 0 8px 24px rgba(0, 232, 150, 0.12);
                border: 1px solid #0fd084;
                min-height: 150px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }}

            .section-card::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 5px;
                background: linear-gradient(90deg, #00c875, #d8a23a, #005bbb);
            }}

            .prize-title {{
                text-align: center;
                color: #061b3a;
                margin: 0 0 6px 0;
                font-size: 17px;
                font-weight: 900;
                letter-spacing: 0.3px;
            }}

            .prize-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #dce8ef;
                padding: 5px 0;
                color: #07142c;
                font-size: 12px;
            }}

            .prize-row:last-child {{
                border-bottom: none;
            }}

            .prize-amount {{
                font-weight: 900;
                color: #d8a23a;
            }}

            @media (max-width: 900px) {{
                .section-card {{
                    min-height: 122px;
                    border-radius: 13px;
                    padding: 10px;
                }}

                .prize-title {{
                    font-size: 14px;
                    margin-bottom: 3px;
                }}

                .prize-row {{
                    font-size: 10px;
                    padding: 3px 0;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="section-card">
            <div class="prize-title">PRIZE BREAKDOWN</div>
            {prize_rows}
        </div>
    </body>
    </html>
    """


def build_event_cards_html(
    goal_main,
    goal_sub,
    yellow_main,
    yellow_sub,
    red_main,
    red_sub,
    fav_main,
    fav_sub
):
    return f"""
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: transparent;
            }}

            .event-grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
            }}

            .section-card {{
                background: linear-gradient(180deg, #ffffff 0%, #f6fff9 100%);
                border-radius: 16px;
                padding: 16px;
                box-shadow: 0 8px 24px rgba(0, 232, 150, 0.12);
                border: 1px solid #0fd084;
                height: 170px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }}

            .section-card::before {{
                content: "";
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 5px;
                background: linear-gradient(90deg, #00c875, #d8a23a, #005bbb);
            }}

            .event-title {{
                color: #061b3a;
                font-size: 12px;
                font-weight: 900;
                text-align: center;
                min-height: 28px;
                letter-spacing: 0.3px;
            }}

            .event-main {{
                font-size: 30px;
                font-weight: 900;
                text-align: center;
                margin-top: 4px;
                min-height: 40px;
            }}

            .event-sub {{
                color: #07142c;
                font-size: 13px;
                text-align: center;
                margin-top: 4px;
                min-height: 20px;
            }}

            @media (max-width: 900px) {{
                .event-grid {{
                    grid-template-columns: 1fr 1fr;
                    gap: 8px;
                }}

                .section-card {{
                    height: 108px;
                    border-radius: 13px;
                    padding: 10px;
                }}

                .event-title {{
                    font-size: 9px;
                    min-height: 16px;
                    line-height: 1.15;
                }}

                .event-main {{
                    font-size: 22px;
                    min-height: 28px;
                    margin-top: 2px;
                }}

                .event-sub {{
                    font-size: 10px;
                    min-height: 14px;
                    margin-top: 1px;
                }}
            }}
        </style>
    </head>

    <body>
        <div class="event-grid">
            <div class="section-card">
                <div class="event-title">FASTEST GOAL</div>
                <div class="event-main" style="color:#00a95c;">{goal_main}</div>
                <div class="event-sub">{goal_sub}</div>
            </div>

            <div class="section-card">
                <div class="event-title">FASTEST YELLOW CARD</div>
                <div class="event-main" style="color:#d8a23a;">{yellow_main}</div>
                <div class="event-sub">{yellow_sub}</div>
            </div>

            <div class="section-card">
                <div class="event-title">FASTEST RED CARD</div>
                <div class="event-main" style="color:#ef3340;">{red_main}</div>
                <div class="event-sub">{red_sub}</div>
            </div>

            <div class="section-card">
                <div class="event-title">TOURNAMENT FAVOURITE</div>
                <div class="event-main" style="color:#005bbb;">{fav_main}</div>
                <div class="event-sub">{fav_sub}</div>
            </div>
        </div>
    </body>
    </html>
    """


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1600px;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(0, 200, 117, 0.22), transparent 28%),
            radial-gradient(circle at top right, rgba(216, 162, 58, 0.20), transparent 26%),
            linear-gradient(180deg, #07142c 0%, #0b1831 18%, #f4fff8 54%, #ffffff 100%);
    }

    .banner-wrap img {
        border-radius: 14px;
        margin-bottom: 12px;
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(0, 232, 150, 0.45);
    }

    .video-link-card {
        background: linear-gradient(180deg, #ffffff 0%, #f6fff9 100%);
        border-radius: 16px;
        padding: 14px;
        border: 1px solid #0fd084;
        box-shadow: 0 8px 24px rgba(0, 232, 150, 0.12);
        margin-top: -20px;
        text-align: center;
    }

    .video-title {
        text-align: center;
        font-size: 14px;
        font-weight: 900;
        color: #061b3a;
        margin-bottom: 10px;
    }

    .video-link-button {
        display: block;
        text-decoration: none !important;
        background: linear-gradient(90deg, #061b3a, #09284d);
        color: #ffffff !important;
        padding: 13px 12px;
        border-radius: 12px;
        font-weight: 900;
        font-size: 13px;
        border: 1px solid #0fd084;
        box-shadow: 0 6px 16px rgba(0, 232, 150, 0.18);
    }

    .video-link-button:hover {
        background: linear-gradient(90deg, #09284d, #061b3a);
        color: #f4b83f !important;
    }

    .video-note {
        color: #07142c;
        font-size: 11px;
        margin-top: 8px;
        line-height: 1.25;
    }

    .footer-card {
        background: linear-gradient(90deg, #061b3a, #09284d);
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #0fd084;
        color: #ffffff;
        font-size: 13px;
        box-shadow: 0 8px 22px rgba(0, 232, 150, 0.12);
        margin-top: -20px;
    }

    .footer-card h3 {
        color: #f4b83f;
        margin-top: 0;
    }

    .footer-card p {
        color: #ffffff;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 0.45rem;
            padding-right: 0.45rem;
            padding-top: 1rem;
        }

        .video-link-card {
            margin-top: -24px;
            margin-bottom: 18px;
            padding: 12px;
        }

        .video-title {
            font-size: 12px;
        }

        .video-link-button {
            font-size: 12px;
            padding: 12px 10px;
        }

        .footer-card {
            padding: 14px;
            font-size: 12px;
            margin-top: -30px;
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


st.markdown(
    """
    <div style="height:30px;"></div>
    """,
    unsafe_allow_html=True
)


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


left_col, right_col = st.columns([1.15, 4])

with left_col:
    components.html(
        build_prize_card_html(),
        height=160,
        scrolling=False
    )

    st.markdown(
        f"""
        <div class="video-link-card">
            <div class="video-title">DRAW VIDEO</div>
            <a class="video-link-button" href="{DRAW_VIDEO_URL}" target="_blank">
                ▶ Watch the Draw
            </a>
            <div class="video-note">
                Opens in Google Drive
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with right_col:
    components.html(
        build_event_cards_html(
            goal_main,
            goal_sub,
            yellow_main,
            yellow_sub,
            red_main,
            red_sub,
            fav_main,
            fav_sub
        ),
        height=250,
        scrolling=False
    )


table_html = build_single_table_html(teams_df)
table_height = len(teams_df) * 30 + 20

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
