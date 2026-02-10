import requests
import os
import sys
from datetime import datetime, timezone, timedelta
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()
USERNAME = "frgnc-subash"
TOKEN = os.getenv("GH_TOKEN")
LANG_COUNT = 8

LANG_COLORS = {
    "Python": "#3776AB", "JavaScript": "#F7DF1E", "TypeScript": "#3178C6",
    "HTML": "#E44D26", "CSS": "#264DE4", "Java": "#ED8B00", "C++": "#00599C",
    "C": "#283593", "C#": "#512BD4", "Go": "#00ADD8", "Rust": "#CE422B",
    "PHP": "#777BB4", "Ruby": "#CC342D", "Swift": "#FA7343", "Kotlin": "#7F52FF",
    "Dart": "#0175C2", "Shell": "#4EAA25", "Vue": "#41B883", "Lua": "#08097F",
}

DEFAULT_COLORS = ["#2f80ed", "#ffb600", "#d92c2c", "#a040a0", "#38bdae"]

if not TOKEN:
    sys.exit(1)

headers = {"Authorization": f"token {TOKEN}"}

def fetch_url(url, session):
    try:
        return session.get(url, headers=headers).json()
    except:
        return {}

def get_streak(session):
    query = """
    query($userName:String!) {
      user(login: $userName) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    try:
        resp = session.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"userName": USERNAME}},
            headers=headers
        )
        if resp.status_code != 200:
            return 0
        
        data = resp.json()
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        days = [day for week in weeks for day in week["contributionDays"]]
        
        days.sort(key=lambda x: x["date"], reverse=True)
        
        streak = 0
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        
        has_started = False
        
        for day in days:
            date = day["date"]
            count = day["contributionCount"]
            
            if not has_started:
                if date == today and count > 0:
                    streak += 1
                    has_started = True
                elif date == yesterday and count > 0:
                    streak += 1
                    has_started = True
                elif date < yesterday:
                    break
            else:
                if count > 0:
                    streak += 1
                else:
                    break
        return streak
    except:
        return 0

try:
    with requests.Session() as session:
        repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=all"
        resp = session.get(repos_url, headers=headers)
        resp.raise_for_status()
        repos = resp.json()

        languages = {}
        total_bytes = 0
        lang_urls = [repo["languages_url"] for repo in repos if not repo.get("fork", False)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda u: fetch_url(u, session), lang_urls))

        for repo_langs in results:
            for lang, bytes_count in repo_langs.items():
                languages[lang] = languages.get(lang, 0) + bytes_count
                total_bytes += bytes_count

        current_streak = get_streak(session)

    if total_bytes == 0: sys.exit(0)

    sorted_langs = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:LANG_COUNT]

    count = len(sorted_langs)
    rows_count = (count + 1) // 2

    start_y = 65
    row_height = 26
    padding_bottom = 35 

    height = start_y + (rows_count * row_height) + padding_bottom
    width = 400
    center_x = width / 2

    date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")

    svg_content = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      <style>
        .base {{ font-family: 'DepartureMonoNerdFontMono', 'Geist Mono', 'Fira Code', monospace; }}
        .header {{ 
            font-weight: 600; 
            font-size: 16px; 
            fill: #84ACF0; 
            letter-spacing: 2.5px; 
            text-transform: uppercase;
        }}
        .footer-text {{ font-weight: 400; font-size: 10px; fill: #555555; }}
        .streak {{ font-weight: 600; font-size: 10px; fill: #41B883; }}
        .lang-name {{ font-weight: 400; font-size: 13px; fill: #ffffff; }}
        .lang-percent {{ font-weight: 400; font-size: 13px; fill: #9ca3af; }} 
      </style>
      <rect x="0" y="0" width="{width}" height="{height}" fill="#000000" rx="0"/>
      
      <text x="{center_x}" y="32" text-anchor="middle" dominant-baseline="middle" class="base header">Language Stats</text>
    """

    col_1_x = 25; col_1_num = 185
    col_2_x = 215; col_2_num = 375

    for i, (lang, bytes_count) in enumerate(sorted_langs):
        percent = (bytes_count / total_bytes) * 100
        color = LANG_COLORS.get(lang, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])

        if i % 2 == 0: col_x = col_1_x; num_x = col_1_num
        else: col_x = col_2_x; num_x = col_2_num

        row = i // 2
        y_pos = start_y + (row * row_height)
        display_name = lang if len(lang) < 18 else lang[:16] + ".."

        svg_content += f"""
      <g transform="translate(0, {y_pos})">
        <circle cx="{col_x + 5}" cy="6" r="5" fill="{color}"/>
        <text x="{col_x + 18}" y="10" class="base lang-name">{display_name}</text>
        <text x="{num_x}" y="10" class="base lang-percent" text-anchor="end">{percent:.1f}%</text>
      </g>
        """

    svg_content += f"""
      <text x="25" y="{height - 12}" text-anchor="start" class="base footer-text">streak: <tspan class="streak">{current_streak} days</tspan></text>
      <text x="375" y="{height - 12}" text-anchor="end" class="base footer-text">last updated: {date_str}</text>
    </svg>
    """

    with open("languages.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("Stats generated!")

except Exception as e:
    print(e)