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

    # Update the download count in the README
    # First check if the pattern exists
    if '<!-- TOTAL_DL_START -->' in content and '<!-- TOTAL_DL_END -->' in content:
        pattern = r'(<!-- TOTAL_DL_START -->\n\*\*Total downloads across my plugins:\*\* \*\*).*?(\*\* 🚀\n<!-- TOTAL_DL_END -->)'
        replacement = f'\\1{downloads}\\2'
        updated_content = re.sub(pattern, replacement, content)
    else:
        # If the pattern doesn't exist or is broken, recreate the entire section
        start_marker = '<!-- TOTAL_DL_START -->'
        end_marker = '<!-- TOTAL_DL_END -->'
        new_section = f'{start_marker}\n**Total downloads across my plugins:** **{downloads}** 🚀\n{end_marker}'
        
        # Try to find the section between markers even if it's malformed
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos >= 0 and end_pos >= 0 and end_pos > start_pos:
            # Replace the entire section
            updated_content = content[:start_pos] + new_section + content[end_pos + len(end_marker):]
        elif '## 📊 Downloads Summary' in content:
            # Find the downloads summary section and add after it
            summary_pos = content.find('## 📊 Downloads Summary')
            badge_line = '![Total Downloads](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ruslanlap/ruslanlap/master/stats/total_downloads_shield.json)'
            badge_pos = content.find(badge_line, summary_pos)
            
            if badge_pos >= 0:
                insert_pos = badge_pos + len(badge_line) + 2  # +2 for newlines
                updated_content = content[:insert_pos] + '\n' + new_section + '\n' + content[insert_pos:]
            else:
                # Can't find the right place, just append to the end
                updated_content = content
                print("Could not find the right place to insert download stats", file=sys.stderr)
        else:
            # Can't find any markers, don't update
            updated_content = content
            print("Could not find download stats markers in README", file=sys.stderr)

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
