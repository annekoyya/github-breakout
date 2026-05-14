name: "Generate Breakout Game SVG"

on:
  schedule:
    - cron: "0 0 * * *"   # Daily at midnight UTC
  workflow_dispatch:        # Allow manual runs from the Actions tab

jobs:
  build:
    name: Generate Contribution Breakout SVG
    runs-on: ubuntu-latest
    permissions:
      contents: write       # Needed to push to github-breakout branch

    steps:
      # ── 1. Checkout ──────────────────────────────────────────────────────────
      - name: Checkout repository
        uses: actions/checkout@v4

      # ── 2. Set up Python ─────────────────────────────────────────────────────
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # ── 3. Generate SVGs ─────────────────────────────────────────────────────
      - name: Generate SVG files
        run: |
          python src/generate.py \
            --username "${{ github.repository_owner }}" \
            --token "${{ secrets.GITHUB_TOKEN }}" \
            --output "./output" \
            --paddle-color "${{ vars.PADDLE_COLOR || '#FF5722' }}" \
            --ball-color "${{ vars.BALL_COLOR || '#FFEB3B' }}" \
            --bricks-colors "${{ vars.BRICKS_COLORS || '#EBEDF0,#9BE9A8,#40C463,#30A14E,#216E39' }}"
        # To enable ghost bricks, add: --enable-ghost-bricks

      # ── 4. Deploy to github-breakout branch ──────────────────────────────────
      - name: Deploy SVGs to github-breakout branch
        run: |
          git config --global user.name  "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

          # Save SVG files to a temp location
          cp output/light.svg  /tmp/light.svg
          cp output/dark.svg   /tmp/dark.svg
          cp output/custom.svg /tmp/custom.svg

          # Create or switch to orphan branch
          git fetch origin github-breakout 2>/dev/null || true
          if git show-ref --quiet refs/remotes/origin/github-breakout; then
            git checkout github-breakout
          else
            git checkout --orphan github-breakout
            git rm -rf . --quiet || true
          fi

          # Copy SVGs back and commit
          cp /tmp/light.svg  light.svg
          cp /tmp/dark.svg   dark.svg
          cp /tmp/custom.svg custom.svg

          git add light.svg dark.svg custom.svg
          git diff --cached --quiet || git commit -m "chore: update breakout SVGs [$(date -u '+%Y-%m-%d %H:%M UTC')]"
          git push origin github-breakout --force

      # ── 5. Summary ───────────────────────────────────────────────────────────
      - name: Print README snippet
        run: |
          echo "### Add this to your README.md ###"
          echo ""
          echo '<picture>'
          echo '  <source media="(prefers-color-scheme: dark)"  srcset="https://raw.githubusercontent.com/${{ github.repository_owner }}/${{ github.event.repository.name }}/github-breakout/dark.svg" />'
          echo '  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/${{ github.repository_owner }}/${{ github.event.repository.name }}/github-breakout/light.svg" />'
          echo '  <img alt="GitHub Contribution Breakout" src="https://raw.githubusercontent.com/${{ github.repository_owner }}/${{ github.event.repository.name }}/github-breakout/light.svg" />'
          echo '</picture>'
