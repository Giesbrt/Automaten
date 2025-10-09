# scripts/generate_coverage_badge.py
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent

COVERAGE_PATH = ROOT_DIR / "coverage.json"
BADGE_PATH = ROOT_DIR / "coverage-badge.svg"

def get_coverage_percentage(path):
    with open(path) as f:
        data = json.load(f)
        total = data["totals"]
        return total["percent_covered_display"]

def generate_svg(percent):
    color = "red"
    try:
        pct = float(percent)
        if pct >= 90:
            color = "brightgreen"
        elif pct >= 75:
            color = "yellow"
        elif pct >= 50:
            color = "orange"
    except:
        pass

    left_text = "coverage"
    right_text = f"{percent}%"
    left_width = 73
    right_width = 47
    total_width = left_width + right_width

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20">
              <linearGradient id="s" x2="0" y2="100%">
                <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
                <stop offset="1" stop-opacity=".1"/>
              </linearGradient>
              <clipPath id="r">
                <rect width="{total_width}" height="20" rx="3" fill="#fff"/>
              </clipPath>
              <g clip-path="url(#r)">
                <rect width="{left_width}" height="20" fill="#555"/>
                <rect x="{left_width}" width="{right_width}" height="20" fill="{color}"/>
                <rect width="{total_width}" height="20" fill="url(#s)"/>
              </g>
              <g fill="#fff" text-anchor="middle"
                 font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
                 font-size="11">
                <text x="{left_width // 2}" y="15">{left_text}</text>
                <text x="{left_width + right_width // 2}" y="15">{right_text}</text>
              </g>
            </svg>'''

if __name__ == "__main__":
    pct = get_coverage_percentage(COVERAGE_PATH)
    svg = generate_svg(pct)
    with open(BADGE_PATH, "w") as f:
        f.write(svg)
    print(f"Generated coverage badge with {pct}% coverage")
