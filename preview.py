#!/usr/bin/env python3
"""
Local preview script — run this to generate SVGs on your machine
without needing GitHub Actions.

Usage:
    python preview.py --username YOUR_GITHUB_USERNAME --token YOUR_TOKEN

If no token is given, mock data is used.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from generate import (
    fetch_contributions, generate_mock_data, build_grid,
    render_svg, parse_colors, validate_hex,
    DEFAULT_GREEN, DEFAULT_DARK
)
import argparse

def main():
    parser = argparse.ArgumentParser(description="Local Breakout SVG preview")
    parser.add_argument("--username", default="octocat", help="GitHub username")
    parser.add_argument("--token", default="", help="GitHub personal access token")
    parser.add_argument("--output", default="./output", help="Output folder")
    parser.add_argument("--paddle-color", default="#FF5722")
    parser.add_argument("--ball-color", default="#FFEB3B")
    parser.add_argument("--bricks-colors", default=",".join(DEFAULT_GREEN))
    parser.add_argument("--enable-ghost-bricks", action="store_true", default=False)
    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN", "")

    if token:
        try:
            print(f"Fetching contributions for '{args.username}'...")
            days = fetch_contributions(args.username, token)
            print(f"Fetched {len(days)} days.")
        except Exception as e:
            print(f"Fetch failed: {e}. Using mock data.")
            days = generate_mock_data()
    else:
        print("No token — using mock data.")
        days = generate_mock_data()

    grid = build_grid(days)

    brick_colors = parse_colors(args.bricks_colors, DEFAULT_GREEN)
    paddle_color = validate_hex(args.paddle_color, "#FF5722")
    ball_color   = validate_hex(args.ball_color, "#FFEB3B")
    ghost        = args.enable_ghost_bricks

    os.makedirs(args.output, exist_ok=True)

    for filename, theme, colors in [
        ("light.svg",  "light", brick_colors),
        ("dark.svg",   "dark",  parse_colors(args.bricks_colors, DEFAULT_DARK)),
        ("custom.svg", "light", brick_colors),
    ]:
        svg = render_svg(grid, theme, colors, paddle_color, ball_color, ghost)
        path = os.path.join(args.output, filename)
        with open(path, "w") as f:
            f.write(svg)
        print(f"Saved: {path}")

    print("\nOpen output/light.svg or output/dark.svg in your browser to preview.")

if __name__ == "__main__":
    main()
