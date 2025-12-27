import requests # type: ignore
import os
import sys
from datetime import datetime, timezone
import concurrent.futures
from dotenv import load_dotenv  # type: ignore # Added to load .env file

# --- CONFIGURATION ---
load_dotenv()  # This reads GH_TOKEN from your .env file
USERNAME = "frgnc-subash"
TOKEN = os.getenv("GH_TOKEN")
LANG_COUNT = 8

# Official Colors
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#2b7489",
    "HTML": "#e34c26", "CSS": "#563d7c", "Java": "#b07219", "C++": "#f34b7d",
    "C": "#555555", "C#": "#178600", "Go": "#00ADD8", "Rust": "#dea584",
    "PHP": "#4F5D95", "Ruby": "#701516", "Swift": "#ffac45", "Kotlin": "#F18E33",
    "Dart": "#00B4AB", "Shell": "#89e051", "Vue": "#2c3e50"
}
DEFAULT_COLORS = ["#2f80ed", "#ffb600", "#d92c2c", "#a040a0", "#38bdae"]

if not TOKEN:
    print("❌ Error: GH_TOKEN is missing. Check your .env file.")
    sys.exit(1)

headers = {"Authorization": f"token {TOKEN}"}

def fetch_url(url, session):
    try:
        return session.get(url, headers=headers).json()
    except:  # noqa: E722
        return {}

try:
    with requests.Session() as session:
        repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=all"
        resp = session.get(repos_url, headers=headers)
        resp.raise_for_status()
        repos = resp.json()

        languages = {}
        total_bytes = 0
        
        lang_urls = [repo['languages_url'] for repo in repos if not repo.get('fork', False)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda u: fetch_url(u, session), lang_urls))

        for repo_langs in results:
            for lang, bytes_count in repo_langs.items():
                languages[lang] = languages.get(lang, 0) + bytes_count
                total_bytes += bytes_count

    if total_bytes == 0:
        sys.exit(0)

    sorted_langs = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:LANG_COUNT]
    
    count = len(sorted_langs)
    midpoint = (count + 1) // 2
    
    start_y = 65
    row_height = 26
    padding_bottom = 15
    
    height = start_y + (midpoint * row_height) + padding_bottom
    width = 400
    center_x = width / 2
    
    date_str = datetime.now(timezone.utc).strftime("%d-%m-%y")
    
    svg_content = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      <style>
        .base {{ font-family: 'GeistMono Nerd Font', 'Geist Mono', 'Fira Code', monospace; }}
        .header {{ font-weight: 600; font-size: 18px; fill: #ffffff; }}
        .last-updated {{ font-weight: 400; font-size: 10px; fill: #555555; }}
        .lang-name {{ font-weight: 400; font-size: 13px; fill: #ffffff; }}
        .lang-percent {{ font-weight: 400; font-size: 13px; fill: #9ca3af; }} 
      </style>
      <rect x="0" y="0" width="{width}" height="{height}" fill="#000000" rx="0"/>
      <text x="{center_x}" y="32" text-anchor="middle" dominant-baseline="middle" class="base header">Most Used Languages</text>
      <text x="375" y="32" text-anchor="end" dominant-baseline="middle" class="base last-updated">{date_str}</text>
    """

    col_1_x = 25
    col_1_num = 185
    col_2_x = 215
    col_2_num = 375
    
    for i, (lang, bytes_count) in enumerate(sorted_langs):
        percent = (bytes_count / total_bytes) * 100
        color = LANG_COLORS.get(lang, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
        
        if i < midpoint:
            col_x = col_1_x
            num_x = col_1_num
            row = i
        else:
            col_x = col_2_x
            num_x = col_2_num
            row = i - midpoint
            
        y_pos = start_y + (row * row_height)
        display_name = lang if len(lang) < 18 else lang[:16] + ".."
        
        svg_content += f"""
      <g transform="translate(0, {y_pos})">
        <circle cx="{col_x + 5}" cy="6" r="5" fill="{color}"/>
        <text x="{col_x + 18}" y="10" class="base lang-name">{display_name}</text>
        <text x="{num_x}" y="10" class="base lang-percent" text-anchor="end">{percent:.1f}%</text>
      </g>
        """

    svg_content += "</svg>"

    with open("languages.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    
    print("✅ Stats generated! (Using .env)")

except Exception as e:
    print(e)