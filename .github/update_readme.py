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
    new_section = f'{start_marker}\n**Total downloads across my plugins:** **{downloads}** 🚀{growth_text}\n{end_marker}'
    
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
