#!/usr/bin/env python3
"""
update_readme.py
---------------------------------
Updates the README.md file with the latest download statistics.
"""

import json
import re
import os
import sys
from datetime import datetime

def update_readme_downloads(readme_path, stats_json_path):
    """Update the README.md file with the latest download statistics."""
    # Read the stats file
    try:
        with open(stats_json_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            downloads = stats.get('grand_total_human', '0')
            growth = stats.get('growth', {})
            monthly_growth = growth.get('monthly_growth', 'N/A')
            weekly_avg = growth.get('weekly_avg', 'N/A')
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading stats file: {e}", file=sys.stderr)
        return False

    # Read the README file
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError as e:
        print(f"Error reading README file: {e}", file=sys.stderr)
        return False

    # Define markers
    start_marker = '<!-- TOTAL_DL_START -->'
    end_marker = '<!-- TOTAL_DL_END -->'
    growth_badge = '![Monthly Growth](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ruslanlap/ruslanlap/master/stats/growth_shield.json)'
    growth_text = f'\n\n**Monthly Growth:** {monthly_growth} 📈 | **Weekly Avg:** {weekly_avg} downloads'

    def format_number(value):
        """Format integers with thousands separators."""
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)

    def extract_plugin_name(repo_name):
        """Create a human-friendly plugin name from a repository identifier."""
        if not isinstance(repo_name, str):
            return "Unknown"

        prefixes = [
            'PowerToysRun-',
            'CommunityPowerToysRunPlugin-',
            'PowerToysRunPlugin-',
        ]
        for prefix in prefixes:
            if repo_name.startswith(prefix):
                repo_name = repo_name[len(prefix):]
                break

        repo_name = repo_name.replace('-', ' ').replace('_', ' ')
        repo_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', repo_name)
        repo_name = re.sub(r'\s+', ' ', repo_name).strip()
        return repo_name or "Unknown"

    def repo_icon(repo_name):
        """Return an emoji icon for known plugins."""
        icon_map = {
            'VideoDownloader': '🎥',
            'SpeedTest': '⚡',
            'Definition': '📚',
            'Weather': '🌤️',
            'Pomodoro': '🍅',
            'QuickNotes': '📝',
            'Hotkeys': '⌨️',
            'Translator': '🈯',
            'CurrencyConverter': '💱',
            'Timer': '⏱️',
        }
        base_name = extract_plugin_name(repo_name).replace(' ', '')
        return icon_map.get(base_name, '🔹')

    def latest_release_info(releases):
        """Return a concise latest release summary if available."""
        latest = None
        latest_dt = None
        for release in releases or []:
            published_at = release.get('published_at')
            if not published_at:
                continue
            try:
                release_dt = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                continue
            if latest_dt is None or release_dt > latest_dt:
                latest_dt = release_dt
                latest = release

        if latest and latest_dt:
            tag = latest.get('tag') or latest.get('name') or 'Latest release'
            return f"{tag} ({latest_dt.strftime('%b %d, %Y')})"
        return '—'

    repos = stats.get('repos', [])
    top_repos = repos[:5]
    grand_total = stats.get('grand_total', 0)
    active_repos = [repo for repo in repos if repo.get('downloads', 0) > 0]
    active_count = len(active_repos)
    average_downloads = grand_total / active_count if active_count else 0
    leader_downloads = top_repos[0]['downloads'] if top_repos else 0
    leader_share = (leader_downloads / grand_total * 100) if grand_total else 0
    top_five_total = sum(repo.get('downloads', 0) for repo in top_repos)
    top_five_share = (top_five_total / grand_total * 100) if grand_total else 0

    rank_labels = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
    table_rows = []
    for index, repo in enumerate(top_repos):
        rank = rank_labels[index] if index < len(rank_labels) else f"{index + 1}"
        name = extract_plugin_name(repo.get('repo', 'Unknown'))
        icon = repo_icon(repo.get('repo', ''))
        downloads_formatted = format_number(repo.get('downloads', 0))
        share = repo.get('downloads', 0) / grand_total * 100 if grand_total else 0
        share_display = f"{share:.1f}%"
        latest_info = latest_release_info(repo.get('releases'))
        plugin_link = repo.get('html_url')
        if plugin_link:
            plugin_display = f"{icon} **[{name}]({plugin_link})**"
        else:
            plugin_display = f"{icon} **{name}**"

        table_rows.append(
            f"| {rank} | {plugin_display} | {downloads_formatted} | {share_display} | {latest_info} |"
        )

    generated_at = stats.get('generated_at')
    last_updated = 'Unknown'
    if generated_at:
        try:
            generated_dt = datetime.strptime(generated_at, "%Y-%m-%dT%H:%M:%SZ")
            last_updated = generated_dt.strftime('%b %d, %Y')
        except ValueError:
            last_updated = generated_at

    table_lines = [
        "### 🏆 Top Performing Plugins",
        "",
        "| 🏅 Rank | Plugin | Downloads | Share of Total | Latest Release |",
        "|---------|--------|-----------|----------------|----------------|",
    ]
    table_lines.extend(table_rows or ["| — | — | — | — | — |"])
    table_lines.extend(
        [
            "",
            f"*📊 Smart analytics updated weekly via automated workflows • Last updated: {last_updated}*",
            "",
            "<details>",
            "<summary>📈 View Detailed Analytics & Trends</summary>",
            "",
            "### 📊 Download Trends",
            "- **Historical Data**: [View complete download history](https://github.com/ruslanlap/ruslanlap/tree/master/stats)",
            "- **Growth Insights**: Monthly and weekly download patterns",
            "- **Plugin Performance**: Individual plugin download trends",
            "",
            "### 🎯 Key Metrics",
            f"- **Total Downloads**: {format_number(grand_total)} across all plugins",
            f"- **Active Plugins**: {active_count} repositories with downloads",
            f"- **Average per Active Plugin**: {format_number(round(average_downloads)) if average_downloads else '0'} downloads",
            (
                f"- **Top Performer**: {extract_plugin_name(top_repos[0]['repo'])} "
                f"({leader_share:.1f}% of total downloads)"
                if top_repos
                else "- **Top Performer**: —"
            ),
            (
                f"- **Top 5 Combined**: {format_number(top_five_total)} "
                f"({top_five_share:.1f}% of total downloads)"
                if top_repos
                else "- **Top 5 Combined**: —"
            ),
            "",
            "### 🔍 Plugin Details",
            "Click on any plugin name to view its repository and release notes:",
            "- [🎥 VideoDownloader](https://github.com/ruslanlap/PowerToysRun-VideoDownloader) - Latest: v1.0.11",
            "- [⚡ SpeedTest](https://github.com/ruslanlap/PowerToysRun-SpeedTest) - Latest: v1.0.7",
            "- [📚 Definition](https://github.com/ruslanlap/PowerToysRun-Definition) - Latest: v1.2.1",
            "- [🌤️ Weather](https://github.com/ruslanlap/PowerToysRun-Weather) - Latest: v1.0.1",
            "- [🍅 Pomodoro](https://github.com/ruslanlap/PowerToysRun-Pomodoro) - Latest: v1.0.0",
            "",
            "</details>",
        ]
    )

    table_section = "\n".join(table_lines)

    section_lines = [
        start_marker,
        f"**Total downloads across my plugins:** **{downloads}** 🚀",
        "",
        f"**Monthly Growth:** {monthly_growth} 📈 | **Weekly Avg:** {weekly_avg} downloads",
        "",
        table_section,
        end_marker,
    ]

    new_section = "\n".join(section_lines)
    
    # Find the markers in the content
    start_pos = content.find(start_marker)
    end_pos = content.find(end_marker)
    
    if start_pos >= 0 and end_pos >= 0 and end_pos > start_pos:
        # Replace the entire section between markers
        updated_content = content[:start_pos] + new_section + content[end_pos + len(end_marker):]
    elif '## 📊 Downloads Summary' in content:
        # Find the downloads summary section and add after it
        summary_pos = content.find('## 📊 Downloads Summary')
        badge_line = '![Total Downloads](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ruslanlap/ruslanlap/master/stats/total_downloads_shield.json)'
        badge_pos = content.find(badge_line, summary_pos)
        growth_badge_line = '![Monthly Growth](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ruslanlap/ruslanlap/master/stats/growth_shield.json)'
        # Insert growth badge after total badge if section exists
        if badge_pos >= 0:
            insert_pos = content.find('\n', badge_pos) + 1
            # Check if growth badge already exists after
            if growth_badge_line not in content[insert_pos:insert_pos+200]:
                updated_content = content[:insert_pos] + f'\n{growth_badge}' + content[insert_pos:]
            else:
                updated_content = content
        else:
            # Fallback to original
            updated_content = content
        
        if badge_pos >= 0:
            insert_pos = badge_pos + len(badge_line) + 1
            updated_content = content[:insert_pos] + '\n\n' + new_section + content[insert_pos:]
        else:
            # Can't find the right place, don't update
            print("Could not find the badge line in README", file=sys.stderr)
            return False
    else:
        # Can't find any markers or section, don't update
        print("Could not find download stats section in README", file=sys.stderr)
        return False

    # Write the updated content back to the README
    if updated_content != content:
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"Updated README.md with {downloads} downloads")
            return True
        except IOError as e:
            print(f"Error writing to README file: {e}", file=sys.stderr)
            return False
    else:
        print("No changes needed to README.md")
        return False

if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    readme_path = os.path.join(repo_root, 'README.md')
    stats_json_path = os.path.join(repo_root, 'stats', 'total_downloads.json')
    
    update_readme_downloads(readme_path, stats_json_path)
