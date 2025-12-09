"""
Core scope inference detection engine.

Analyzes chat logs, tool calls, file system operations to automatically infer
scope levels from black-box agent interactions.
"""

import re
from typing import Optional, Dict, List, Any, Set
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
import logging

from ..scope_levels import ScopeLevel
from .types import InferenceSignal, ToolCallAnalysis, ChatAnalysis
from . import patterns

logger = logging.getLogger(__name__)


class ScopeInferenceEngine:
    """
    Comprehensive inference engine that tracks EVERYTHING.

    Analyzes:
    - Chat messages (OpenAI completion requests/responses)
    - Tool calls (file operations, shell commands, etc.)
    - Directory traversal patterns
    - File access patterns
    - Time-based patterns (working hours, session breaks)
    - Graph relations (entities, relationships)

    Infers:
    - SESSION: Conversation continuity, breaks indicate new session
    - PHASE: plan → docwrite → implementation → testing patterns
    - PROJECT: File paths, git repos, project names
    - WORKSPACE: Team mentions, shared directories
    - ORGANIZATION: Company names, domain patterns
    - ITERATION: Loop patterns, retry attempts
    """

    def __init__(self):
        # Historical data
        self.chat_history: List[ChatAnalysis] = []
        self.tool_call_history: List[ToolCallAnalysis] = []

        # Current state tracking
        self.current_session_id: Optional[str] = None
        self.current_project_id: Optional[str] = None
        self.current_phase: Optional[str] = None
        self.current_cwd: Optional[str] = None
        self.current_workspace: Optional[str] = None

        # Counters for confidence scoring
        self.project_mentions = Counter()
        self.directory_visits = Counter()
        self.file_access_patterns = Counter()
        self.phase_indicators = Counter()

        # Graph relations (Neo4j will store this)
        self.entity_graph: Dict[str, Set[str]] = defaultdict(set)

        # Session detection
        self.last_activity: Optional[datetime] = None
        self.session_break_threshold = 30 * 60  # 30 minutes

    async def analyze_chat_message(
        self,
        user_message: str,
        assistant_message: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[InferenceSignal]:
        """
        Analyze a chat exchange and extract inference signals.

        For black-box agents (ReAct, etc.), we only see:
        - messages[].content (user and assistant)
        - tool_calls[] if present
        - timestamps

        From this we infer EVERYTHING.
        """
        signals: List[InferenceSignal] = []
        now = datetime.now()

        # 1. SESSION DETECTION
        session_signal = await self._detect_session_boundary(now)
        if session_signal:
            signals.append(session_signal)

        # 2. PROJECT DETECTION from message content
        project_signals = self._detect_project_from_text(
            user_message + " " + assistant_message
        )
        signals.extend(project_signals)

        # 3. PHASE DETECTION from message intent
        phase_signal = self._detect_phase_from_text(user_message)
        if phase_signal:
            signals.append(phase_signal)

        # 4. WORKSPACE/ORGANIZATION DETECTION
        entity_signals = self._detect_entities_from_text(
            user_message + " " + assistant_message
        )
        signals.extend(entity_signals)

        # 5. DIRECTORY CHANGES from chat
        dir_signals = self._detect_directory_changes(
            user_message + " " + assistant_message
        )
        signals.extend(dir_signals)

        # Store for historical analysis
        analysis = ChatAnalysis(
            user_message=user_message,
            assistant_message=assistant_message,
            timestamp=now,
            intent=phase_signal.value if phase_signal else None,
            project_mentions=[s.value for s in project_signals],
            directory_changes=[s.value for s in dir_signals],
        )
        self.chat_history.append(analysis)
        self.last_activity = now

        return signals

    async def analyze_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[InferenceSignal]:
        """
        Analyze a tool call to extract scope signals.

        Critical for tracking:
        - File operations (read_file, write_file, list_directory)
        - Shell commands (execute_bash, run_command)
        - Directory changes (cd commands, path arguments)
        - Git operations (clone, commit, push)
        """
        signals: List[InferenceSignal] = []
        now = datetime.now()

        # Track current working directory
        cwd_before = self.current_cwd
        cwd_after = self._extract_cwd_from_tool_call(tool_name, arguments, result)
        if cwd_after:
            self.current_cwd = cwd_after

            # Infer project from directory change
            project_signal = self._infer_project_from_path(cwd_after)
            if project_signal:
                signals.append(project_signal)

        # Extract file access patterns
        files_accessed = self._extract_files_from_tool_call(
            tool_name, arguments, result
        )
        for file_path in files_accessed:
            self.file_access_patterns[file_path] += 1

            # Infer project from file path
            project_signal = self._infer_project_from_path(file_path)
            if project_signal:
                signals.append(project_signal)

        # Detect phase transitions from tool patterns
        phase_signal = self._detect_phase_from_tool(tool_name, arguments)
        if phase_signal:
            signals.append(phase_signal)

        # Store analysis
        analysis = ToolCallAnalysis(
            tool_name=tool_name,
            arguments=arguments,
            timestamp=now,
            cwd_before=cwd_before,
            cwd_after=cwd_after,
            files_accessed=files_accessed,
        )
        self.tool_call_history.append(analysis)
        self.last_activity = now

        return signals

    def _detect_session_boundary(self, now: datetime) -> Optional[InferenceSignal]:
        """Detect if we've crossed into a new session based on inactivity."""
        if self.last_activity is None:
            # First interaction = new session
            session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}"
            self.current_session_id = session_id
            return InferenceSignal(
                scope_level=ScopeLevel.SESSION,
                key="session_id",
                value=session_id,
                confidence=1.0,
                evidence="First interaction (new session)",
            )

        # Check for session break (30+ minutes of inactivity)
        elapsed = (now - self.last_activity).total_seconds()
        if elapsed > self.session_break_threshold:
            session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}"
            self.current_session_id = session_id
            return InferenceSignal(
                scope_level=ScopeLevel.SESSION,
                key="session_id",
                value=session_id,
                confidence=0.9,
                evidence=f"Session break detected ({elapsed/60:.1f} min inactivity)",
            )

        return None

    def _detect_project_from_text(self, text: str) -> List[InferenceSignal]:
        """Extract project references from text."""
        signals = []

        project_names = patterns.extract_project_mentions(text)
        for project_name in project_names:
            self.project_mentions[project_name] += 1

            # Higher confidence if mentioned multiple times
            count = self.project_mentions[project_name]
            confidence = min(0.5 + (count * 0.1), 0.95)

            signals.append(InferenceSignal(
                scope_level=ScopeLevel.PROJECT,
                key="project_id",
                value=self._normalize_id(project_name),
                confidence=confidence,
                evidence=f"Project mention: '{project_name}' (count: {count})",
            ))

        return signals

    def _detect_phase_from_text(self, text: str) -> Optional[InferenceSignal]:
        """Detect current phase from message content."""
        phase_scores = patterns.score_phase_from_text(text)

        if not phase_scores:
            return None

        # Get highest scoring phase
        best_phase = max(phase_scores.items(), key=lambda x: x[1])
        phase_name, score = best_phase

        # Update current phase if different
        if self.current_phase != phase_name:
            self.current_phase = phase_name
            phase_id = f"phase_{phase_name}_{datetime.now().strftime('%H%M%S')}"

            return InferenceSignal(
                scope_level=ScopeLevel.PHASE,
                key="phase_id",
                value=phase_id,
                confidence=min(0.6 + (score * 0.1), 0.95),
                evidence=f"Phase transition detected: {phase_name} (score: {score})",
            )

        return None

    def _detect_entities_from_text(self, text: str) -> List[InferenceSignal]:
        """Detect workspace and organization from text."""
        signals = []

        # Workspace detection
        workspaces = patterns.extract_workspace_mentions(text)
        for workspace_name in workspaces:
            signals.append(InferenceSignal(
                scope_level=ScopeLevel.WORKSPACE,
                key="workspace_id",
                value=self._normalize_id(workspace_name),
                confidence=0.7,
                evidence=f"Workspace mention: '{workspace_name}'",
            ))

        # Organization detection
        organizations = patterns.extract_organization_mentions(text)
        for org_name in organizations:
            signals.append(InferenceSignal(
                scope_level=ScopeLevel.ORGANIZATION,
                key="organization_id",
                value=self._normalize_id(org_name),
                confidence=0.8,
                evidence=f"Organization mention: '{org_name}'",
            ))

        return signals

    def _detect_directory_changes(self, text: str) -> List[InferenceSignal]:
        """Detect directory changes from chat (cd commands, path mentions)."""
        signals = []

        directories = patterns.extract_directory_changes(text)
        for directory in directories:
            self.directory_visits[directory] += 1

            # Update current directory
            self.current_cwd = directory

            # Infer project from directory
            project_signal = self._infer_project_from_path(directory)
            if project_signal:
                signals.append(project_signal)

            signals.append(InferenceSignal(
                scope_level=ScopeLevel.SESSION,
                key="cwd",
                value=directory,
                confidence=0.9,
                evidence=f"Directory change: {directory}",
            ))

        return signals

    def _extract_cwd_from_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract current working directory from tool call."""

        # Bash/shell commands
        if tool_name in ("execute_bash", "run_command", "run_shell"):
            command = arguments.get("command", "")

            # Extract cd command
            cd_match = re.search(r"cd\s+([/~][\w/.-]+)", command)
            if cd_match:
                return cd_match.group(1)

            # Check if command changed directory
            if result and "cwd" in result:
                return result["cwd"]

        # File operations with path arguments
        if tool_name in ("read_file", "write_file", "edit_file"):
            file_path = arguments.get("file_path") or arguments.get("path")
            if file_path:
                return str(Path(file_path).parent)

        # Git operations
        if tool_name in ("git_clone", "git_init"):
            repo_path = arguments.get("path") or arguments.get("directory")
            if repo_path:
                return repo_path

        return None

    def _extract_files_from_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Extract file paths from tool call."""
        files = []

        # Direct file operations
        if tool_name in ("read_file", "write_file", "edit_file"):
            file_path = arguments.get("file_path") or arguments.get("path")
            if file_path:
                files.append(file_path)

        # Glob patterns
        if tool_name in ("glob", "find_files"):
            if result and "files" in result:
                files.extend(result["files"])

        # Grep/search results
        if tool_name in ("grep", "search_files"):
            if result and "matches" in result:
                for match in result["matches"]:
                    if "file" in match:
                        files.append(match["file"])

        # List directory
        if tool_name in ("list_directory", "ls"):
            if result and "files" in result:
                base_dir = arguments.get("path", self.current_cwd or ".")
                files.extend([f"{base_dir}/{f}" for f in result["files"]])

        return files

    def _infer_project_from_path(self, path: str) -> Optional[InferenceSignal]:
        """Infer project from file/directory path."""
        project_name = patterns.infer_project_from_path(path)

        if not project_name:
            return None

        # Increase weight for path-based inference
        self.project_mentions[project_name] += 2

        count = self.project_mentions[project_name]
        confidence = min(0.6 + (count * 0.05), 0.95)

        return InferenceSignal(
            scope_level=ScopeLevel.PROJECT,
            key="project_id",
            value=project_name,
            confidence=confidence,
            evidence=f"Project inferred from path: {path}",
        )

    def _detect_phase_from_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Optional[InferenceSignal]:
        """Detect phase from tool usage patterns."""

        # Testing phase
        if tool_name in ("run_tests", "pytest", "run_coverage"):
            return self._create_phase_signal("testing", 0.9, "Test execution tool")

        # Implementation phase
        if tool_name in ("write_file", "edit_file", "create_file"):
            # Check if writing tests
            file_path = arguments.get("file_path", "")
            if "test" in file_path.lower():
                return self._create_phase_signal("testing", 0.85, "Writing test file")
            else:
                return self._create_phase_signal(
                    "implementation", 0.8, "Writing code"
                )

        # Documentation phase
        if tool_name in ("write_file", "edit_file"):
            file_path = arguments.get("file_path", "")
            if any(
                ext in file_path.lower()
                for ext in [".md", ".rst", ".txt", "readme"]
            ):
                return self._create_phase_signal(
                    "documentation", 0.85, "Writing docs"
                )

        # Planning phase (reading many files)
        if tool_name in ("read_file", "grep", "glob"):
            # If we've read many files recently, likely planning
            recent_reads = sum(
                1 for tc in self.tool_call_history[-10:]
                if tc.tool_name in ("read_file", "grep", "glob")
            )
            if recent_reads >= 5:
                return self._create_phase_signal(
                    "planning", 0.7, "Multiple file reads"
                )

        # Debugging phase
        if tool_name in ("execute_bash", "run_command"):
            command = arguments.get("command", "")
            if any(
                word in command.lower()
                for word in ["debug", "error", "log", "trace"]
            ):
                return self._create_phase_signal("debugging", 0.8, "Debug command")

        return None

    def _create_phase_signal(
        self,
        phase_name: str,
        confidence: float,
        evidence: str
    ) -> InferenceSignal:
        """Create a phase transition signal."""
        phase_id = f"phase_{phase_name}_{datetime.now().strftime('%H%M%S')}"

        # Update phase counter
        self.phase_indicators[phase_name] += 1

        return InferenceSignal(
            scope_level=ScopeLevel.PHASE,
            key="phase_id",
            value=phase_id,
            confidence=confidence,
            evidence=evidence,
        )

    def _normalize_id(self, name: str) -> str:
        """Normalize name to valid ID."""
        return name.lower().replace(" ", "_").replace("-", "_")

    async def get_current_scope_state(self) -> Dict[ScopeLevel, str]:
        """Get current inferred scope state."""
        state = {}

        if self.current_session_id:
            state[ScopeLevel.SESSION] = self.current_session_id

        if self.current_phase:
            state[ScopeLevel.PHASE] = self.current_phase

        if self.current_project_id:
            state[ScopeLevel.PROJECT] = self.current_project_id

        if self.current_workspace:
            state[ScopeLevel.WORKSPACE] = self.current_workspace

        return state

    async def analyze_historical_patterns(self) -> Dict[str, Any]:
        """
        Analyze historical data to improve inference.

        Returns insights like:
        - Most common project (high confidence)
        - Typical phase progression
        - Working directory patterns
        - Time-of-day patterns
        """
        insights = {
            "most_common_project": None,
            "phase_progression": [],
            "directory_hotspots": [],
            "file_access_patterns": [],
        }

        # Most common project
        if self.project_mentions:
            project, count = self.project_mentions.most_common(1)[0]
            insights["most_common_project"] = {
                "name": project,
                "count": count,
                "confidence": min(count / 10.0, 0.95),
            }

        # Phase progression
        if len(self.chat_history) >= 5:
            recent_phases = [
                chat.intent
                for chat in self.chat_history[-20:]
                if chat.intent
            ]
            insights["phase_progression"] = recent_phases

        # Directory hotspots
        if self.directory_visits:
            top_dirs = self.directory_visits.most_common(5)
            insights["directory_hotspots"] = [
                {"path": path, "visits": count}
                for path, count in top_dirs
            ]

        # File access patterns
        if self.file_access_patterns:
            top_files = self.file_access_patterns.most_common(10)
            insights["file_access_patterns"] = [
                {"file": file, "accesses": count}
                for file, count in top_files
            ]

        return insights

    async def build_neo4j_relations(self) -> List[Dict[str, Any]]:
        """
        Build graph relations for Neo4j storage.

        Creates edges like:
        - (Session)-[:CONTAINS]->(Phase)
        - (Phase)-[:WORKS_ON]->(Project)
        - (Project)-[:HAS_FILE]->(File)
        - (File)-[:ACCESSED_BY]->(ToolCall)
        - (ToolCall)-[:PART_OF]->(PromptChain)
        """
        relations = []

        # Build session → project relations
        for chat in self.chat_history:
            for project_name in chat.project_mentions:
                relations.append({
                    "type": "SESSION_WORKS_ON_PROJECT",
                    "from": self.current_session_id,
                    "to": self._normalize_id(project_name),
                    "timestamp": chat.timestamp.isoformat(),
                    "confidence": 0.8,
                })

        # Build phase → file relations
        for tool_call in self.tool_call_history:
            for file_path in tool_call.files_accessed:
                relations.append({
                    "type": "PHASE_ACCESSES_FILE",
                    "from": self.current_phase,
                    "to": file_path,
                    "tool": tool_call.tool_name,
                    "timestamp": tool_call.timestamp.isoformat(),
                })

        return relations
