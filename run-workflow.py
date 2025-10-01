#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
# ]
# ///

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

"""
Local runner for GitHub Actions workflow
Parses and executes steps from the workflow YAML file locally
"""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict

import yaml


class WorkflowRunner:
    def __init__(self, workflow_file: str = ".github/workflows/build-and-deploy.yml"):
        self.workflow_file = workflow_file
        self.env = os.environ.copy()
        self.temp_dir = None
        self.venv_activated = False

    def load_workflow(self) -> Dict[str, Any]:
        """Load and parse the workflow YAML file"""
        with open(self.workflow_file, "r") as f:
            return yaml.safe_load(f)

    def setup_runner_context(self):
        """Set up GitHub Actions runner context variables"""
        self.temp_dir = tempfile.mkdtemp(prefix="workflow-runner-")
        self.github_env_file = os.path.join(self.temp_dir, "github_env")

        # Create empty GITHUB_ENV file
        with open(self.github_env_file, "w") as _:
            pass

        self.env.update(
            {
                "RUNNER_TEMP": self.temp_dir,
                "GITHUB_WORKSPACE": os.getcwd(),
                "CI": "true",
                "GITHUB_ENV": self.github_env_file,
            }
        )
        print(f"📁 Temp directory: {self.temp_dir}")

    def cleanup(self):
        """Clean up temporary resources"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def replace_variables(self, text: str) -> str:
        """Replace GitHub Actions variables with their values"""
        # Load any environment variables from GITHUB_ENV file
        github_env_vars = {}
        if hasattr(self, "github_env_file") and os.path.exists(self.github_env_file):
            try:
                with open(self.github_env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line:
                            key, value = line.split("=", 1)
                            github_env_vars[key] = value
            except Exception:
                pass

        replacements = {
            "${{ runner.temp }}": self.env.get("RUNNER_TEMP", ""),
            "${{ github.workspace }}": self.env.get("GITHUB_WORKSPACE", ""),
            "${{ github.event.inputs.version }}": self.env.get(
                "INPUT_VERSION", "latest"
            ),
            "${{ github.event.inputs.version || 'latest' }}": self.env.get(
                "INPUT_VERSION", "latest"
            ),
            "${{ env.TEMP_DIR }}": github_env_vars.get("TEMP_DIR", ""),
            "${{ env.BUILDING_LATEST }}": github_env_vars.get("BUILDING_LATEST", ""),
            "${{ env.VERSION_TAG }}": github_env_vars.get("VERSION_TAG", ""),
        }

        for key, value in replacements.items():
            text = text.replace(key, value)
        return text

    def run_command(self, cmd: str, name: str = None) -> bool:
        """Execute a shell command"""
        if name:
            print(f"\n🔧 {name}")
            print(
                f"   Command: {cmd[:100]}..."
                if len(cmd) > 100
                else f"   Command: {cmd}"
            )

        # Replace GitHub Actions variables FIRST
        cmd = self.replace_variables(cmd)

        # Handle multi-line commands with venv activation
        lines = cmd.strip().split("\n")

        # Check if first line creates venv
        if lines and "uv venv" in lines[0]:
            # Run venv creation separately
            result = subprocess.run(
                lines[0],
                shell=True,
                executable="/bin/bash",
                env=self.env,
                capture_output=False,
                text=True,
            )
            if result.returncode != 0:
                return False

            # Mark venv as activated for subsequent commands
            self.venv_activated = True

            # Process remaining lines
            if len(lines) > 1:
                remaining_cmd = "\n".join(lines[1:])
                # Skip the 'source .venv/bin/activate' line if present
                if "source .venv/bin/activate" in remaining_cmd:
                    remaining_cmd = remaining_cmd.replace(
                        "source .venv/bin/activate\n", ""
                    )
                    remaining_cmd = remaining_cmd.replace(
                        "source .venv/bin/activate", ""
                    )

                if remaining_cmd.strip():
                    # Run with venv activated
                    cmd = f"source .venv/bin/activate && {remaining_cmd}"
                else:
                    return True
            else:
                return True

        # Only use venv for Python/Sphinx commands, not for file operations
        needs_venv = any(
            keyword in cmd for keyword in ["sphinx", "pip", "python", "uv pip"]
        )

        # If venv is activated and command needs it, prepend activation
        if self.venv_activated and needs_venv:
            if not cmd.startswith("source .venv/bin/activate"):
                cmd = f"source .venv/bin/activate && {cmd}"

        # Source GITHUB_ENV file to make environment variables available
        if hasattr(self, "github_env_file") and os.path.exists(self.github_env_file):
            # Check if file has content
            try:
                with open(self.github_env_file, "r") as f:
                    content = f.read().strip()
                if content:
                    cmd = f"source {self.github_env_file} && {cmd}"
            except Exception:
                pass

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                executable="/bin/bash",
                env=self.env,
                capture_output=False,
                text=True,
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False

    def should_skip_step(self, step: Dict[str, Any]) -> bool:
        """Determine if a step should be skipped in local execution"""
        name = step.get("name", "").lower()

        # Skip GitHub-specific steps
        skip_patterns = [
            "checkout this repository",  # We're already in the repo
            "setup github pages",
            "upload pages artifact",
            "deploy to github pages",
            "commit and push changes",  # Don't auto-commit in local mode
            "set up python",  # We'll use uv directly
        ]

        for pattern in skip_patterns:
            if pattern in name.lower():
                return True

        # Skip steps that use GitHub Actions (except setup actions we can handle)
        if "uses" in step:
            uses = step.get("uses", "")
            # Allow setup actions we can handle
            if not any(
                allowed in uses
                for allowed in ["setup-uv", "setup-node", "actions/setup-node"]
            ):
                return True

        return False

    def run_step(self, step: Dict[str, Any]) -> bool:
        """Execute a single workflow step"""
        name = step.get("name", "Unnamed step")

        if self.should_skip_step(step):
            print(f"⏭️  Skipping: {name} (GitHub-specific)")
            return True

        # Handle 'run' steps
        if "run" in step:
            # Handle multi-line run commands
            commands = step["run"].strip()
            return self.run_command(commands, name)

        # Handle setup-uv action
        if "uses" in step and "setup-uv" in step["uses"]:
            print(f"\n🔧 {name}")
            # Check if uv is installed
            if shutil.which("uv"):
                print("   ✓ uv is already installed")
                return True
            else:
                print("   Installing uv...")
                return self.run_command(
                    "curl -LsSf https://astral.sh/uv/install.sh | sh", None
                )

        # Handle setup-node action
        if "uses" in step and (
            "setup-node" in step["uses"] or "actions/setup-node" in step["uses"]
        ):
            print(f"\n🔧 {name}")
            # Check if node is installed
            if shutil.which("node") and shutil.which("npm"):
                print("   ✓ Node.js and npm are already installed")
                return True
            else:
                print("   ⚠️  Node.js/npm not found. Please install Node.js 20+ first.")
                print("       Visit: https://nodejs.org/")
                return False

        return True

    def run(self):
        """Run the workflow"""
        print("🚀 GitHub Actions Workflow Runner")
        print("=" * 50)

        try:
            # Load workflow
            workflow = self.load_workflow()
            print(f"📄 Loaded workflow: {workflow.get('name', 'Unnamed')}")

            # Set up runner context
            self.setup_runner_context()

            # Find the main job (first job in the workflow)
            jobs = workflow.get("jobs", {})
            if not jobs:
                print("❌ No jobs found in workflow")
                return False

            job_name = list(jobs.keys())[0]
            job = jobs[job_name]
            print(f"📋 Running job: {job_name}")

            # Execute steps
            steps = job.get("steps", [])
            total_steps = len(steps)

            for i, step in enumerate(steps, 1):
                print(f"\n[{i}/{total_steps}]", end=" ")
                if not self.run_step(step):
                    print("❌ Step failed")
                    return False

            print("\n" + "=" * 50)
            print("✅ Workflow completed successfully!")
            print("\n📌 Next steps:")
            print("   1. Review the changes: git status")
            print(
                "   2. Preview locally: uv run python -m http.server 8323 --directory docs"
            )
            print("   3. If satisfied, commit and push:")
            print("      git add .")
            print("      git commit -m 'Update documentation'")
            print("      git push")

            return True

        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run GitHub Actions workflow locally")
    parser.add_argument(
        "--version",
        default="latest",
        help='Version to build (latest, v0.2.18, etc. or "all" for all versions)',
    )
    args = parser.parse_args()

    # Check for required tools
    if not shutil.which("git"):
        print("❌ git is not installed. Please install git first.")
        sys.exit(1)

    if not shutil.which("node"):
        print("❌ Node.js is not installed. Please install Node.js 20+ first:")
        print("   Visit: https://nodejs.org/")
        sys.exit(1)

    if not shutil.which("npm"):
        print("❌ npm is not installed. Please install Node.js (includes npm) first:")
        print("   Visit: https://nodejs.org/")
        sys.exit(1)

    # Check if workflow file exists
    workflow_file = ".github/workflows/build-and-deploy.yml"
    if not os.path.exists(workflow_file):
        print(f"❌ Workflow file not found: {workflow_file}")
        sys.exit(1)

    # Set version environment variable for workflow
    os.environ["INPUT_VERSION"] = args.version
    print(f"📋 Building version: {args.version}")

    # Run the workflow
    runner = WorkflowRunner(workflow_file)
    success = runner.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
