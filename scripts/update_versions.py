# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Update versions.json with a new version entry and update the latest symlink.
"""

import json
import sys
from pathlib import Path


def get_latest_version(versions_data):
    """Get the latest version from versions data."""
    versions = versions_data.get("versions", [])
    if not versions:
        return None

    # Filter out empty versions and 'latest'
    valid_versions = []
    for v in versions:
        name = v.get("name", "").strip()
        version = v.get("version", "").strip()
        if name and version and name != "latest" and version != "latest":
            valid_versions.append(v)

    if not valid_versions:
        return None

    # Sort versions by name (assuming semantic versioning like v0.2.18)
    # Extract version numbers for proper sorting
    def version_key(version_dict):
        name = version_dict.get("name", "")
        if name.startswith("v"):
            try:
                # Parse v0.2.18 -> [0, 2, 18]
                parts = name[1:].split(".")
                return tuple(int(p) for p in parts)
            except ValueError:
                return (0, 0, 0)
        return (0, 0, 0)

    # Get the latest version (highest version number)
    latest_version = max(valid_versions, key=version_key)
    return latest_version.get("name")


def update_latest_symlink(docs_dir, latest_version):
    """Update the 'latest' symlink to point to the latest version."""
    if not latest_version:
        print("No valid latest version found", file=sys.stderr)
        return False

    docs_path = Path(docs_dir)
    latest_path = docs_path / "latest"
    target_path = docs_path / latest_version

    # Check if target directory exists
    if not target_path.exists():
        print(f"Target directory {target_path} does not exist", file=sys.stderr)
        return False

    # Remove existing symlink if it exists
    if latest_path.is_symlink():
        latest_path.unlink()
    elif latest_path.exists():
        print(f"Warning: {latest_path} exists but is not a symlink", file=sys.stderr)
        return False

    # Create new symlink
    try:
        latest_path.symlink_to(latest_version)
        print(f"✅ Updated 'latest' symlink to point to '{latest_version}'")
        return True
    except OSError as e:
        print(f"Error creating symlink: {e}", file=sys.stderr)
        return False


def sort_versions(versions_list):
    """Sort versions list with 'latest' first, then other versions in descending order."""
    latest_entries = []
    version_entries = []

    for v in versions_list:
        if v.get("name") == "latest":
            latest_entries.append(v)
        else:
            version_entries.append(v)

    # Sort version entries by version number (descending)
    def version_key(version_dict):
        name = version_dict.get("name", "")
        if name.startswith("v"):
            try:
                # Parse v0.2.18 -> [0, 2, 18]
                parts = name[1:].split(".")
                return tuple(int(p) for p in parts)
            except ValueError:
                return (0, 0, 0)
        return (0, 0, 0)

    version_entries.sort(key=version_key, reverse=True)

    # Return latest first, then sorted versions
    return latest_entries + version_entries


def main():
    if len(sys.argv) != 4:
        print("Usage: update_versions.py <versions_json_path> <version> <docs_dir>")
        sys.exit(1)

    versions_file = Path(sys.argv[1])
    version = sys.argv[2]
    docs_dir = sys.argv[3]

    new_version = {
        "name": version,
        "version": version,
        "url": f"/{version}/",
        "preferred": False,
    }

    # Load existing versions
    if versions_file.exists():
        with open(versions_file, "r") as f:
            data = json.load(f)
    else:
        data = {"versions": []}

    # Check if version already exists
    existing_versions = [v["version"] for v in data["versions"]]

    if version not in existing_versions:
        data["versions"].append(new_version)

        # Sort versions list (latest first, then descending order)
        data["versions"] = sort_versions(data["versions"])

        # Write back to file
        with open(versions_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Added {version} to versions.json")
    else:
        print(f"ℹ️  {version} already exists in versions.json")

    # Always sort versions before updating (ensures proper order even for existing versions)
    data["versions"] = sort_versions(data["versions"])

    # Update latest symlink and latest entry in JSON
    latest_version = get_latest_version(data)
    if latest_version:
        # Update the latest entry in versions.json to point to the actual latest version
        for v in data["versions"]:
            if v.get("name") == "latest":
                v["url"] = f"/{latest_version}/"
                break

        # Write updated JSON back to file
        with open(versions_file, "w") as f:
            json.dump(data, f, indent=2)

        # Update the symlink
        success = update_latest_symlink(docs_dir, latest_version)
        if not success:
            sys.exit(1)

        print(f"✅ Updated latest entry to point to {latest_version}")
    else:
        print("Warning: Could not determine latest version for symlink update")


if __name__ == "__main__":
    main()
