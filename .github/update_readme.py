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
    pattern = r'(<!-- TOTAL_DL_START -->\n\*\*Total downloads across my plugins:\*\* \*\*).*?(\*\* 🚀\n<!-- TOTAL_DL_END -->)'
    replacement = f'\\1{downloads}\\2'
    updated_content = re.sub(pattern, replacement, content)

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
