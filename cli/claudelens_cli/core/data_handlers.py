"""Handlers for various Claude data types."""
import json
from pathlib import Path
from typing import Any

import aiofiles


class TodoHandler:
    """Handles Claude todo list files."""

    async def read_todo_file(self, file_path: Path) -> dict[str, Any]:
        """Read and parse a todo file."""
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            todos = json.loads(content)

            # Extract session ID from filename
            # Format: [session-uuid]-agent-[session-uuid].json
            filename = file_path.name
            session_id = filename.split("-agent-")[0]

            return {
                "sessionId": session_id,
                "filename": filename,
                "todos": todos,
                "todoCount": len(todos),
            }


class ConfigHandler:
    """Handles Claude configuration files."""

    async def read_config(self, claude_dir: Path) -> dict[str, Any]:
        """Read Claude configuration files."""
        config = {}

        # Read config.json
        config_path = claude_dir / "config.json"
        if config_path.exists():
            async with aiofiles.open(config_path, "r", encoding="utf-8") as f:
                config["config"] = json.loads(await f.read())

        # Read settings.json
        settings_path = claude_dir / "settings.json"
        if settings_path.exists():
            async with aiofiles.open(settings_path, "r", encoding="utf-8") as f:
                config["settings"] = json.loads(await f.read())

        return config


class ProjectScanner:
    """Scans for Claude projects and sessions."""

    def find_projects(self, claude_dir: Path) -> list[dict[str, Any]]:
        """Find all projects in Claude directory."""
        projects_dir = claude_dir / "projects"
        if not projects_dir.exists():
            return []

        projects = []
        for project_dir in projects_dir.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith("."):
                # Convert directory name back to path
                # Format: -Users-username-path-to-project
                path_parts = project_dir.name.split("-")
                if path_parts[0] == "":  # Leading dash
                    path_parts[0] = "/"
                project_path = "/".join(path_parts).replace("//", "/")

                # Count sessions
                jsonl_files = list(project_dir.glob("*.jsonl"))

                projects.append(
                    {
                        "name": project_dir.name,
                        "path": project_path,
                        "directory": str(project_dir),
                        "sessionCount": len(jsonl_files),
                        "sessions": [f.stem for f in jsonl_files],
                    }
                )

        return projects
