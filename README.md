# GitHub Contribution Breakout

Transforms your GitHub contribution graph into a Breakout-style SVG animation displayed on your profile README.

Each brick represents one day. Color intensity = contribution level. The ball and paddle are rendered as a static visual with a motion trail.

---

## Quick Setup (5 minutes)

### Step 1 — Copy the workflow file

Copy `.github/workflows/breakout.yml` into your profile repository (the repo named the same as your username, e.g. `octocat/octocat`).

If the `.github/workflows/` folder does not exist, create it.

### Step 2 — Run the action

Go to your repository on GitHub, click the **Actions** tab, select **Generate Breakout Game SVG**, and click **Run workflow**.

The action will:
1. Fetch your last 365 days of contributions via the GitHub API
2. Render `light.svg`, `dark.svg`, and `custom.svg`
3. Push them to a branch called `github-breakout`

### Step 3 — Add to your README

Paste this into your `README.md`, replacing `YOUR_USERNAME` and `YOUR_REPO` with your values:

```markdown
<picture>
  <source media="(prefers-color-scheme: dark)"
    srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/github-breakout/dark.svg" />
  <source media="(prefers-color-scheme: light)"
    srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/github-breakout/light.svg" />
  <img alt="GitHub Contribution Breakout"
    src="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/github-breakout/light.svg" />
</picture>
```

---

## Customization

You can set these in your workflow file or as GitHub Actions variables (Settings > Variables):

| Variable          | Default                                    | Description                                     |
|-------------------|--------------------------------------------|-------------------------------------------------|
| `PADDLE_COLOR`    | `#FF5722`                                  | Hex color of the paddle                         |
| `BALL_COLOR`      | `#FFEB3B`                                  | Hex color of the ball                           |
| `BRICKS_COLORS`   | `#EBEDF0,#9BE9A8,#40C463,#30A14E,#216E39` | 5 hex colors for contribution levels 0 through 4 |

To enable ghost bricks (show empty days as faint bricks), add `--enable-ghost-bricks` to the generate step in the workflow.

### Example custom colors (pink theme)

```yaml
--paddle-color "#FF4081"
--ball-color   "#F8BBD9"
--bricks-colors "#FCE4EC,#F48FB1,#F06292,#E91E63,#880E4F"
```

---

## Local Preview (no GitHub needed)

Run the preview script locally with Python 3.10+:

```bash
# With your GitHub token (real data)
python preview.py --username YOUR_USERNAME --token YOUR_GITHUB_TOKEN

# Without a token (uses random mock data)
python preview.py --username anyone

# Open the result
open output/light.svg    # macOS
start output/light.svg   # Windows
xdg-open output/light.svg  # Linux
```

---

## File Structure

    github-breakout/
    |-- action.yml                      Reusable Action definition
    |-- preview.py                      Local preview runner
    |-- src/
    |   |-- generate.py                 Core generator (fetch + render)
    |-- .github/
    |   |-- workflows/
    |       |-- breakout.yml            GitHub Action workflow
    |-- output/                         Generated SVGs go here (git-ignored)
    |-- README.md

---

## Contribution Level Color Mapping

| Level | Commits per Day | Default Color |
|-------|-----------------|---------------|
| 0     | 0               | #EBEDF0 (ghost / invisible) |
| 1     | 1 to 4          | #9BE9A8 |
| 2     | 5 to 9          | #40C463 |
| 3     | 10 to 19        | #30A14E |
| 4     | 20 or more      | #216E39 |

---

## Error Handling

| Situation                          | Behavior                                              |
|------------------------------------|-------------------------------------------------------|
| API rate limit hit                 | Retries up to 3 times with exponential backoff        |
| Invalid hex color provided         | Falls back to default green palette with a log warning |
| No GitHub token provided           | Uses randomly generated mock data                     |
| User has less than 365 days        | Fills missing days with level 0 (ghost bricks)        |
| Network timeout                    | Action fails with a clear error message               |

---

## Requirements

- Python 3.10 or higher
- No external libraries required (uses stdlib only)
- GitHub token with `repo` and `read:user` scopes (or the default `GITHUB_TOKEN` in Actions)
# github-breakout
