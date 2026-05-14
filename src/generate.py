#!/usr/bin/env python3
"""
GitHub Contribution Breakout Game Generator
Fetches contribution data and renders it as a Breakout-style SVG.
"""

import os
import sys
import json
import time
import math
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timedelta


# ─── Constants ────────────────────────────────────────────────────────────────

BRICK_W = 12
BRICK_H = 8
BRICK_GAP = 2
COLS = 52
ROWS = 7
PADDING_LEFT = 20
PADDING_TOP = 20
PADDLE_W = 60
PADDLE_H = 8
BALL_RADIUS = 5
TRAIL_COUNT = 5

SVG_W = COLS * (BRICK_W + BRICK_GAP) + PADDING_LEFT * 2
SVG_H = ROWS * (BRICK_H + BRICK_GAP) + PADDING_TOP * 2 + 60  # 60 for paddle area

DEFAULT_GREEN = ["#EBEDF0", "#9BE9A8", "#40C463", "#30A14E", "#216E39"]
DEFAULT_DARK   = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

LEVEL_THRESHOLDS = [0, 1, 5, 10, 20]


# ─── Data Fetching ────────────────────────────────────────────────────────────

GRAPHQL_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions(username: str, token: str, retries: int = 3) -> list[dict]:
    """Fetch contribution data from GitHub GraphQL API."""
    url = "https://api.github.com/graphql"
    payload = json.dumps({
        "query": GRAPHQL_QUERY,
        "variables": {"username": username}
    }).encode("utf-8")

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "github-breakout/1.0",
    }

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if "errors" in data:
                raise ValueError(f"GraphQL errors: {data['errors']}")

            weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            days = []
            for week in weeks:
                for day in week["contributionDays"]:
                    days.append({
                        "date": day["date"],
                        "count": day["contributionCount"],
                    })
            return days

        except urllib.error.HTTPError as e:
            if e.code == 403:
                wait = 2 ** attempt
                print(f"Rate limited. Waiting {wait}s before retry {attempt + 1}/{retries}...")
                time.sleep(wait)
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("Max retries reached. Could not fetch contribution data.")


def generate_mock_data() -> list[dict]:
    """Generate 365 days of mock contribution data as fallback."""
    import random
    days = []
    today = datetime.today()
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        count = random.choices(
            [0, random.randint(1, 4), random.randint(5, 9),
             random.randint(10, 19), random.randint(20, 30)],
            weights=[40, 25, 20, 10, 5]
        )[0]
        days.append({"date": d.strftime("%Y-%m-%d"), "count": count})
    return days


# ─── Data Processing ──────────────────────────────────────────────────────────

def quantize_level(count: int) -> int:
    """Map contribution count to level 0-4."""
    for level in range(len(LEVEL_THRESHOLDS) - 1, -1, -1):
        if count >= LEVEL_THRESHOLDS[level]:
            return level
    return 0


def build_grid(days: list[dict]) -> list[list[int]]:
    """
    Build a 52x7 grid of contribution levels.
    grid[col][row] = level (0-4)
    Col 0 = oldest week, col 51 = newest week.
    Row 0 = Sunday, row 6 = Saturday.
    """
    grid = [[0] * ROWS for _ in range(COLS)]

    # Pad to 364 days (52 * 7)
    while len(days) < COLS * ROWS:
        days.insert(0, {"date": "", "count": 0})
    days = days[-(COLS * ROWS):]

    for idx, day in enumerate(days):
        col = idx // ROWS
        row = idx % ROWS
        if col < COLS and row < ROWS:
            grid[col][row] = quantize_level(day["count"])

    return grid


# ─── Ball Trajectory ──────────────────────────────────────────────────────────

def compute_ball_path(grid: list[list[int]], enable_ghost: bool) -> list[tuple]:
    """
    Simulate a simple ball trajectory across the brick grid.
    Returns a list of (x, y) positions for the trail.
    """
    # Find the first non-zero brick to aim at
    target_col, target_row = COLS // 2, ROWS // 2
    for row in range(ROWS):
        for col in range(COLS):
            if grid[col][row] > 0:
                target_col, target_row = col, row
                break
        else:
            continue
        break

    bx = PADDING_LEFT + target_col * (BRICK_W + BRICK_GAP) + BRICK_W // 2
    by = PADDING_TOP + target_row * (BRICK_H + BRICK_GAP) + BRICK_H // 2

    # Paddle center
    paddle_cx = SVG_W // 2
    paddle_cy = SVG_H - 20

    # Ball position: midpoint along path
    ball_x = (bx + paddle_cx) // 2
    ball_y = (by + paddle_cy) // 2

    # Trail: points along the path from paddle toward ball
    trail = []
    for i in range(TRAIL_COUNT + 1):
        t = i / TRAIL_COUNT
        tx = int(paddle_cx + (ball_x - paddle_cx) * t)
        ty = int(paddle_cy + (ball_y - paddle_cy) * t)
        trail.append((tx, ty))

    return trail, ball_x, ball_y, paddle_cx, paddle_cy


# ─── SVG Rendering ────────────────────────────────────────────────────────────

def hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def validate_hex(color: str, fallback: str) -> str:
    try:
        color = color.strip()
        if not color.startswith("#"):
            color = "#" + color
        hex_to_rgb(color)
        return color
    except Exception:
        print(f"Warning: Invalid color '{color}', using fallback '{fallback}'")
        return fallback


def render_svg(
    grid: list[list[int]],
    theme: str,
    brick_colors: list[str],
    paddle_color: str,
    ball_color: str,
    enable_ghost: bool,
) -> str:
    """Render the full Breakout SVG for a given theme."""

    is_dark = theme == "dark"
    bg_color = "#0d1117" if is_dark else "transparent"
    ghost_color = "#21262d" if is_dark else "#EBEDF0"
    ghost_opacity = "0.4" if enable_ghost else "0.0"

    trail_data, ball_x, ball_y, paddle_cx, paddle_cy = compute_ball_path(grid, enable_ghost)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')

    # Defs: gradient for paddle, glow filter
    lines.append("""  <defs>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <filter id="ball-glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>""")

    # Background
    if bg_color != "transparent":
        lines.append(f'  <rect width="{SVG_W}" height="{SVG_H}" fill="{bg_color}" rx="8"/>')
    else:
        lines.append(f'  <rect width="{SVG_W}" height="{SVG_H}" fill="none"/>')

    # Bricks
    for col in range(COLS):
        for row in range(ROWS):
            level = grid[col][row]
            x = PADDING_LEFT + col * (BRICK_W + BRICK_GAP)
            y = PADDING_TOP + row * (BRICK_H + BRICK_GAP)

            if level == 0:
                color = ghost_color
                opacity = ghost_opacity
            else:
                color = brick_colors[level]
                opacity = "1"

            lines.append(
                f'  <rect x="{x}" y="{y}" width="{BRICK_W}" height="{BRICK_H}" '
                f'rx="2" fill="{color}" opacity="{opacity}" stroke="{bg_color if bg_color != "transparent" else "#ffffff10"}" stroke-width="0.5"/>'
            )

    # Ball trail
    for i, (tx, ty) in enumerate(trail_data[:-1]):
        alpha = int(40 + (i / TRAIL_COUNT) * 120)
        alpha_hex = format(alpha, '02x')
        r = max(1, int(BALL_RADIUS * (i / TRAIL_COUNT) * 0.8))
        lines.append(
            f'  <circle cx="{tx}" cy="{ty}" r="{r}" fill="{ball_color}{alpha_hex}" filter="url(#glow)"/>'
        )

    # Ball
    lines.append(
        f'  <circle cx="{ball_x}" cy="{ball_y}" r="{BALL_RADIUS}" '
        f'fill="{ball_color}" filter="url(#ball-glow)"/>'
    )
    # Ball highlight
    lines.append(
        f'  <circle cx="{ball_x - 2}" cy="{ball_y - 2}" r="1.5" fill="white" opacity="0.7"/>'
    )

    # Paddle
    px = paddle_cx - PADDLE_W // 2
    py = paddle_cy - PADDLE_H // 2
    lines.append(
        f'  <rect x="{px}" y="{py}" width="{PADDLE_W}" height="{PADDLE_H}" '
        f'rx="4" fill="{paddle_color}" filter="url(#glow)"/>'
    )
    # Paddle shine
    lines.append(
        f'  <rect x="{px + 4}" y="{py + 1}" width="{PADDLE_W - 8}" height="2" '
        f'rx="1" fill="white" opacity="0.35"/>'
    )

    lines.append('</svg>')
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def parse_colors(raw: str, default: list[str]) -> list[str]:
    parts = [p.strip() for p in raw.split(",")]
    if len(parts) != 5:
        print(f"Warning: Expected 5 brick colors, got {len(parts)}. Using defaults.")
        return default
    return [validate_hex(p, default[i]) for i, p in enumerate(parts)]


def main():
    parser = argparse.ArgumentParser(description="GitHub Contribution Breakout SVG Generator")
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--token", default="", help="GitHub token")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--paddle-color", default="#FF5722", help="Paddle hex color")
    parser.add_argument("--ball-color", default="#FFEB3B", help="Ball hex color")
    parser.add_argument(
        "--bricks-colors",
        default=",".join(DEFAULT_GREEN),
        help="Comma-separated list of 5 hex colors (level 0-4)"
    )
    parser.add_argument("--enable-ghost-bricks", action="store_true", default=False)
    args = parser.parse_args()

    # Resolve token
    token = args.token or os.environ.get("GITHUB_TOKEN", "")

    # Fetch data
    if token:
        try:
            print(f"Fetching contributions for '{args.username}'...")
            days = fetch_contributions(args.username, token)
            print(f"Fetched {len(days)} contribution days.")
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Falling back to mock data.")
            days = generate_mock_data()
    else:
        print("No token provided. Using mock data.")
        days = generate_mock_data()

    # Build grid
    grid = build_grid(days)

    # Parse colors
    brick_colors_light  = parse_colors(args.bricks_colors, DEFAULT_GREEN)
    brick_colors_dark   = parse_colors(args.bricks_colors, DEFAULT_DARK)
    brick_colors_custom = parse_colors(args.bricks_colors, DEFAULT_GREEN)

    paddle_color = validate_hex(args.paddle_color, "#FF5722")
    ball_color   = validate_hex(args.ball_color, "#FFEB3B")
    ghost        = args.enable_ghost_bricks

    # Render
    os.makedirs(args.output, exist_ok=True)

    themes = {
        "light.svg":  ("light",  brick_colors_light),
        "dark.svg":   ("dark",   brick_colors_dark),
        "custom.svg": ("light",  brick_colors_custom),
    }

    for filename, (theme, colors) in themes.items():
        svg = render_svg(grid, theme, colors, paddle_color, ball_color, ghost)
        path = os.path.join(args.output, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Written: {path}")

    print("\nDone! Add this to your README.md:")
    print("""
```markdown
<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/github-breakout/dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/github-breakout/light.svg" />
  <img alt="GitHub Contribution Breakout" src="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/github-breakout/light.svg" />
</picture>
```
""")


if __name__ == "__main__":
    main()
