# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import json
from datetime import datetime
from pathlib import Path

from docutils import nodes

# Get version from git instead of PyPI
import subprocess
import os


def get_git_version():
    try:
        # Try to get version from git tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Remove 'v' prefix if present (e.g., v0.2.17 -> 0.2.17)
            return tag.lstrip("v")

        # Fallback: try to get from git log
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
        )
        if result.returncode == 0:
            return f"dev-{result.stdout.strip()}"

        # Final fallback
        return "unknown"
    except Exception:
        return "unknown"


# Set version for Sphinx
version_tag = get_git_version()
version = version_tag
release = version_tag

print(f"{version_tag=}")

# Generate the full link including text and url here
llama_stack_version_url = (
    f"https://github.com/llamastack/llama-stack/releases/tag/v{version_tag}"
)
llama_stack_version_link = f"<a href='{llama_stack_version_url}'>release notes</a>"

project = "llama-stack"
copyright = f"{datetime.now().year}, Meta"
author = "Meta"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_rtd_theme",
    "sphinx_rtd_dark_mode",
    "sphinx_tabs.tabs",
    "sphinxcontrib.redoc",
    "sphinxcontrib.mermaid",
    "sphinxcontrib.video",
    "sphinx_reredirects",
]

redirects = {
    "providers/post_training/index": "../../advanced_apis/post_training/index.html",
    "providers/eval/index": "../../advanced_apis/eval/index.html",
    "providers/scoring/index": "../../advanced_apis/scoring/index.html",
    "playground/index": "../../building_applications/playground/index.html",
    "openai/index": "../../providers/index.html#openai-api-compatibility",
    "introduction/index": "../concepts/index.html#llama-stack-architecture",
}

myst_enable_extensions = ["colon_fence"]

html_theme = "sphinx_rtd_theme"
html_use_relative_paths = True
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "attrs_block",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    # "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

myst_substitutions = {
    "docker_hub": "https://hub.docker.com/repository/docker/llamastack",
    "llama_stack_version": version_tag,
    "llama_stack_version_link": llama_stack_version_link,
}

suppress_warnings = ["myst.header"]

# Copy button settings
copybutton_prompt_text = "$ "  # for bash prompts
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True
copybutton_line_continuation_character = "\\"

# Source suffix
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"
html_theme_options = {
    "canonical_url": "https://github.com/llamastack/llama-stack",
    "collapse_navigation": False,
    # "style_nav_header_background": "#c3c9d4",
    "display_version": True,
    "version_selector": True,
}

default_dark_mode = False

html_static_path = ["../_static"]
# html_logo = "../_static/llama-stack-logo.png"
# html_style = "../_static/css/my_theme.css"


def setup(app):
    app.add_css_file("css/my_theme.css")
    app.add_js_file("js/detect_theme.js")
    app.add_js_file("js/keyboard_shortcuts.js")

    def dockerhub_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        url = f"https://hub.docker.com/r/llamastack/{text}"
        node = nodes.reference(rawtext, text, refuri=url, **options)
        return [node], []

    def repopath_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
        parts = text.split("::")
        if len(parts) == 2:
            link_text = parts[0]
            url_path = parts[1]
        else:
            link_text = text
            url_path = text

        url = f"https://github.com/llamastack/llama-stack/tree/main/{url_path}"
        node = nodes.reference(rawtext, link_text, refuri=url, **options)
        return [node], []

    app.add_role("dockerhub", dockerhub_role)
    app.add_role("repopath", repopath_role)


# Add sphinx-multiversion extension
extensions.append("sphinx_multiversion")

# Sphinx-multiversion configuration
smv_tag_whitelist = r"^v\d+\.\d+\.\d+.*$"  # Match v0.2.18, etc.
smv_branch_whitelist = r"^main$"  # Include main branch
smv_remote_whitelist = r"^origin$"  # Only origin remote
smv_released_pattern = r"^tags/v.*$"  # Released versions are tags starting with v
smv_outputdir_format = "{ref.name}"  # Output directory format


# Version selector configuration - read from versions.json
def load_versions():
    """Load versions from versions.json file."""
    try:
        versions_json_path = Path(__file__).parent.parent.parent / "versions.json"
        if versions_json_path.exists():
            with open(versions_json_path, "r") as f:
                versions_data = json.load(f)
                return versions_data.get("versions", [])
        else:
            # Fallback if versions.json doesn't exist
            return [
                {
                    "name": "latest",
                    "version": "latest",
                    "url": "/latest/",
                    "preferred": True,
                }
            ]
    except Exception as e:
        print(f"Warning: Could not load versions.json: {e}")
        return [
            {
                "name": "latest",
                "version": "latest",
                "url": "/latest/",
                "preferred": True,
            }
        ]


html_context = {
    "current_version": f"v{version_tag}" if version_tag != "unknown" else "latest",
    "versions": load_versions(),
    # RTD-compatible version data for JavaScript
    "rtd_versions": {
        "active": [
            {"slug": item["version"], "urls": {"documentation": item["url"]}}
            for item in load_versions()
        ],
        "current": {
            "slug": f"v{version_tag}" if version_tag != "unknown" else "latest"
        },
    },
}

# RTD theme configuration
html_theme_options = {
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
    # Enable the built-in version selector
    "canonical_url": "",
    "analytics_id": "",
    "analytics_anonymize_ip": False,
    "logo_only": False,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Enable version selector in RTD theme
html_context.update(
    {
        "READTHEDOCS": True,  # Enable RTD-specific features
        "DEBUG": True,  # Enable debug mode for version selector
        "theme_version_selector": True,  # Enable version selector
        "theme_language_selector": False,  # Disable language selector
    }
)

# Custom HTML context for version selector
html_context["version_selector_init"] = True
