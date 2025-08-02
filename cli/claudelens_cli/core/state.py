"""State management for sync operations."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class ProjectState(BaseModel):
    """State for a single project."""

    last_sync: datetime
    last_file: str | None = None
    last_line: int | None = None
    synced_sessions: set[str] = Field(default_factory=set)  # Session UUIDs
    synced_messages: set[str] = Field(default_factory=set)  # Message UUIDs
    message_count: int = 0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat(), set: lambda v: list(v)}


class DatabaseState(BaseModel):
    """State for SQLite database sync."""

    last_sync: datetime
    last_message_timestamp: datetime | None = None
    synced_message_count: int = 0

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class SyncState(BaseModel):
    """Overall sync state."""

    version: str = "1.0.0"
    last_sync: datetime | None = None
    projects: dict[str, ProjectState] = Field(default_factory=dict)
    database_state: DatabaseState | None = None
    synced_todos: set[str] = Field(default_factory=set)  # Todo file names
    synced_snapshots: set[str] = Field(default_factory=set)  # Shell snapshot files

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            set: lambda v: list(v),
        }


class StateManager:
    """Manages sync state."""

    def __init__(self, state_dir: Path | None = None):
        self.state_dir = state_dir or (Path.home() / ".claudelens")
        self.state_file = self.state_dir / "sync_state.json"
        self.state = self._load_state()

    def _load_state(self) -> SyncState:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                # Convert ISO strings back to datetime
                if data.get("last_sync"):
                    data["last_sync"] = datetime.fromisoformat(data["last_sync"])
                for project_data in data.get("projects", {}).values():
                    project_data["last_sync"] = datetime.fromisoformat(
                        project_data["last_sync"]
                    )
                    project_data["synced_sessions"] = set(
                        project_data.get("synced_sessions", [])
                    )
                    project_data["synced_messages"] = set(
                        project_data.get("synced_messages", [])
                    )
                if db_state := data.get("database_state"):
                    db_state["last_sync"] = datetime.fromisoformat(
                        db_state["last_sync"]
                    )
                    if db_state.get("last_message_timestamp"):
                        db_state["last_message_timestamp"] = datetime.fromisoformat(
                            db_state["last_message_timestamp"]
                        )
                data["synced_todos"] = set(data.get("synced_todos", []))
                data["synced_snapshots"] = set(data.get("synced_snapshots", []))
                return SyncState(**data)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load state: {e}[/yellow]")
        return SyncState()

    def save(self) -> None:
        """Save state to file."""
        self.state_dir.mkdir(exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.state.model_dump(mode="json"), f, indent=2)

    def get_project_state(self, project_path: str) -> ProjectState | None:
        """Get state for a specific project."""
        return self.state.projects.get(project_path)

    def update_project_state(
        self,
        project_path: str,
        last_file: str | None = None,
        last_line: int | None = None,
        new_sessions: set[str] | None = None,
        new_messages: set[str] | None = None,
    ) -> None:
        """Update state for a project."""
        if project_path not in self.state.projects:
            self.state.projects[project_path] = ProjectState(
                last_sync=datetime.utcnow()
            )

        project_state = self.state.projects[project_path]
        project_state.last_sync = datetime.utcnow()

        if last_file is not None:
            project_state.last_file = last_file
        if last_line is not None:
            project_state.last_line = last_line
        if new_sessions:
            project_state.synced_sessions.update(new_sessions)
        if new_messages:
            project_state.synced_messages.update(new_messages)
            project_state.message_count = len(project_state.synced_messages)

        self.state.last_sync = datetime.utcnow()
        self.save()

    def is_message_synced(self, project_path: str, message_id: str) -> bool:
        """Check if a message has already been synced."""
        project_state = self.get_project_state(project_path)
        if project_state:
            return message_id in project_state.synced_messages
        return False

    def is_session_synced(self, project_path: str, session_id: str) -> bool:
        """Check if a session has already been synced."""
        project_state = self.get_project_state(project_path)
        if project_state:
            return session_id in project_state.synced_sessions
        return False

    def clear_project(self, project_path: str) -> None:
        """Clear state for a project."""
        if project_path in self.state.projects:
            del self.state.projects[project_path]
            self.save()

    def update_database_state(
        self, last_message_timestamp: datetime | None = None, new_message_count: int = 0
    ) -> None:
        """Update state for database sync."""
        if not self.state.database_state:
            self.state.database_state = DatabaseState(last_sync=datetime.utcnow())

        self.state.database_state.last_sync = datetime.utcnow()
        if last_message_timestamp:
            self.state.database_state.last_message_timestamp = last_message_timestamp
        self.state.database_state.synced_message_count += new_message_count

        self.state.last_sync = datetime.utcnow()
        self.save()

    def add_synced_todo(self, todo_file: str) -> None:
        """Mark a todo file as synced."""
        self.state.synced_todos.add(todo_file)
        self.state.last_sync = datetime.utcnow()
        self.save()

    def is_todo_synced(self, todo_file: str) -> bool:
        """Check if a todo file has been synced."""
        return todo_file in self.state.synced_todos

    @staticmethod
    def hash_message(message: dict) -> str:
        """Generate a hash for a message."""
        # Create a deterministic string representation
        content = json.dumps(message, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode()).hexdigest()
