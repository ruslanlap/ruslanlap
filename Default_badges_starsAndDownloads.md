# 📖 How to Use My Counters & Badges

This repository includes automated counters (Stars, Forks, Downloads, Growth, etc.) that are updated via **GitHub Actions** and displayed with **Shields.io dynamic JSON badges**.

You can easily copy this setup into your own profile repo (usually `username/username`) or any other project.

---

## 1️⃣ Copy the Workflow

1. Create a `.github/workflows` folder in your repository (if it doesn’t exist).  
2. Copy the workflows from my repo (look inside `.github/workflows/`).  
   - Example: `total-stars.yml`, `downloads.yml`, `growth.yml`  
3. These workflows run automatically (on schedule) and generate `.json` files with your stats inside a `stats/` folder in your repo.

---

## 2️⃣ Generated Files

The workflows will generate JSON files inside `stats/`, for example:

- `stats/stars.json` → total stars across all repos  
- `stats/total_downloads_shield.json` → total plugin downloads  
- `stats/growth_shield.json` → monthly growth  

These JSON files are committed to your repo so you can use them in badges.

---

## 3️⃣ Add the Badges

Use **Shields.io dynamic JSON** badges that read the numbers from your JSON files.

Example for **Total Stars**:

```md
[![Total Stars](https://img.shields.io/badge/dynamic/json
  ?url=https://raw.githubusercontent.com/<USERNAME>/<REPO>/master/stats/stars.json
  &query=$.stars
  &label=Stars
  &logo=github
  &style=for-the-badge
  &color=FFD700
  &labelColor=0057B7)](https://github.com/<USERNAME>?tab=repositories&sort=stargazers)

if you have some questions or ideas, please contact me 