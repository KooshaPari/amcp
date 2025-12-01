"""
Comprehensive scope inference engine.

Analyzes chat logs, tool calls, file system operations, and graph relations
to automatically infer ALL scope levels (session, project, phase, workspace, etc.)
from black-box agent interactions like ReAct agents sending OpenAI completion requests.

This is the CORE of making SmartCP work with any agent framework without
explicit instrumentation.
"""

import re
import asyncio
from typing import Optional, Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
import logging

from dsl_scope.scope_levels import ScopeLevel
from dsl_scope.project_inference import InferredContext

logger = logging.getLogger(__name__)


@dataclass
class InferenceSignal:
    """Single inference signal with confidence score."""
    scope_level: ScopeLevel
    key: str  # session_id, project_id, etc.
    value: str  # actual ID or name
    confidence: float  # 0.0-1.0
    evidence: str  # What caused this inference
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolCallAnalysis:
    """Analysis of a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    timestamp: datetime
    cwd_before: Optional[str] = None
    cwd_after: Optional[str] = None
    files_accessed: List[str] = field(default_factory=list)
    project_signals: List[str] = field(default_factory=list)
    phase_signals: List[str] = field(default_factory=list)


@dataclass
class ChatAnalysis:
    """Analysis of chat messages."""
    user_message: str
    assistant_message: str
    timestamp: datetime
    intent: Optional[str] = None  # planning, implementation, debugging, etc.
    project_mentions: List[str] = field(default_factory=list)
    directory_changes: List[str] = field(default_factory=list)
    files_mentioned: List[str] = field(default_factory=list)


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

        # Phase transition patterns
        self.phase_patterns = {
            "planning": [
                r"let'?s? plan",
                r"how should we",
                r"strategy for",
                r"approach to",
                r"design pattern",
                r"architecture",
                r"requirements",
                r"spec(?:ification)?",
            ],
            "documentation": [
                r"write (?:a |the )?(?:doc|readme|guide)",
                r"document(?:ation)?",
                r"add comments?",
                r"explain (?:how|what|why)",
                r"create (?:a |the )?guide",
            ],
            "implementation": [
                r"implement",
                r"write (?:the )?code",
                r"add (?:a |the )?function",
                r"create (?:a |the )?class",
                r"fix (?:the )?bug",
                r"refactor",
            ],
            "testing": [
                r"test(?:s|ing)?",
                r"run tests?",
                r"pytest",
                r"coverage",
                r"verify",
                r"validate",
            ],
            "debugging": [
                r"debug",
                r"error",
                r"bug",
                r"issue",
                r"problem",
                r"fix",
                r"broken",
            ],
        }

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
        project_signals = self._detect_project_from_text(user_message + " " + assistant_message)
        signals.extend(project_signals)

        # 3. PHASE DETECTION from message intent
        phase_signal = self._detect_phase_from_text(user_message)
        if phase_signal:
            signals.append(phase_signal)

        # 4. WORKSPACE/ORGANIZATION DETECTION
        entity_signals = self._detect_entities_from_text(user_message + " " + assistant_message)
        signals.extend(entity_signals)

        # 5. DIRECTORY CHANGES from chat
        dir_signals = self._detect_directory_changes(user_message + " " + assistant_message)
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
        files_accessed = self._extract_files_from_tool_call(tool_name, arguments, result)
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

        # Pattern 1: Explicit project mentions
        patterns = [
            r"(?:working on|building|developing)\s+(?:the\s+)?([A-Z][a-z]+(?:[A-Z][a-z]+)*)",
            r"project\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
            r"in\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+project",
            r"(?:github|gitlab)\.com/[\w-]+/([\w-]+)",  # Git URLs
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                project_name = match.group(1)
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
        text_lower = text.lower()

        # Score each phase
        phase_scores = {}
        for phase, patterns in self.phase_patterns.items():
            score = sum(
                1 for pattern in patterns
                if re.search(pattern, text_lower, re.IGNORECASE)
            )
            if score > 0:
                phase_scores[phase] = score

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

        # Workspace patterns
        workspace_patterns = [
            r"(?:in|under)\s+(?:the\s+)?([A-Z][a-z]+)\s+workspace",
            r"workspace\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
            r"(?:team|group)\s+workspace:\s+([A-Za-z0-9_-]+)",
        ]

        for pattern in workspace_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                workspace_name = match.group(1)
                signals.append(InferenceSignal(
                    scope_level=ScopeLevel.WORKSPACE,
                    key="workspace_id",
                    value=self._normalize_id(workspace_name),
                    confidence=0.7,
                    evidence=f"Workspace mention: '{workspace_name}'",
                ))

        # Organization patterns
        org_patterns = [
            r"(?:at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Inc|Corp|LLC|Ltd)",
            r"organization:\s+([A-Za-z0-9_-]+)",
            r"(?:company|org)\s+(?:called|named)\s+([A-Za-z0-9_-]+)",
        ]

        for pattern in org_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                org_name = match.group(1)
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

        # Pattern 1: Explicit cd commands
        cd_patterns = [
            r"cd\s+([/~][\w/.-]+)",
            r"change directory to\s+([/~][\w/.-]+)",
            r"go to\s+([/~][\w/.-]+)",
        ]

        for pattern in cd_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                directory = match.group(1)
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
            pattern = arguments.get("pattern")
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

        # Pattern 1: /path/to/project_name/src/...
        match = re.search(r"/([a-z_][a-z0-9_-]*)/(?:src|lib|tests?|docs?)/", path)
        if match:
            project_name = match.group(1)
            self.project_mentions[project_name] += 2  # Higher weight for paths

            count = self.project_mentions[project_name]
            confidence = min(0.6 + (count * 0.05), 0.95)

            return InferenceSignal(
                scope_level=ScopeLevel.PROJECT,
                key="project_id",
                value=project_name,
                confidence=confidence,
                evidence=f"Project inferred from path: {path}",
            )

        # Pattern 2: ~/project_name/
        match = re.search(r"~/([a-z_][a-z0-9_-]+)/", path)
        if match:
            project_name = match.group(1)
            self.project_mentions[project_name] += 1

            return InferenceSignal(
                scope_level=ScopeLevel.PROJECT,
                key="project_id",
                value=project_name,
                confidence=0.7,
                evidence=f"Project inferred from home path: {path}",
            )

        return None

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
                return self._create_phase_signal("implementation", 0.8, "Writing code")

        # Documentation phase
        if tool_name in ("write_file", "edit_file"):
            file_path = arguments.get("file_path", "")
            if any(ext in file_path.lower() for ext in [".md", ".rst", ".txt", "readme"]):
                return self._create_phase_signal("documentation", 0.85, "Writing docs")

        # Planning phase (reading many files)
        if tool_name in ("read_file", "grep", "glob"):
            # If we've read many files recently, likely planning
            recent_reads = sum(
                1 for tc in self.tool_call_history[-10:]
                if tc.tool_name in ("read_file", "grep", "glob")
            )
            if recent_reads >= 5:
                return self._create_phase_signal("planning", 0.7, "Multiple file reads")

        # Debugging phase
        if tool_name in ("execute_bash", "run_command"):
            command = arguments.get("command", "")
            if any(word in command.lower() for word in ["debug", "error", "log", "trace"]):
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


class ComprehensiveScopeInferenceEngine:
    """
    MAXIMUM KNOWLEDGE DENSITY inference system.

    Integrates:
    - Chat log analysis
    - Tool call tracking
    - File system monitoring
    - Neo4j graph relations
    - Historical patterns
    - Time-series analysis
    - Embeddings for semantic similarity
    """

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        redis_url: str,
    ):
        self.scope_engine = ScopeInferenceEngine()

        # Will connect to Neo4j for graph storage
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password

        # Will connect to Redis for real-time state
        self.redis_url = redis_url

        # Confidence thresholds for auto-activation
        self.confidence_thresholds = {
            ScopeLevel.SESSION: 0.8,
            ScopeLevel.PHASE: 0.7,
            ScopeLevel.PROJECT: 0.6,
            ScopeLevel.WORKSPACE: 0.7,
            ScopeLevel.ORGANIZATION: 0.8,
            ScopeLevel.ITERATION: 0.5,
        }

    async def process_openai_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[InferenceSignal]:
        """
        Process an OpenAI completion request from a black-box ReAct agent.

        Extract ALL possible inference signals from:
        - message history
        - tool calls in messages
        - metadata timestamps
        - conversation patterns
        """
        signals = []

        # Extract latest user and assistant messages
        user_msg = ""
        assistant_msg = ""
        tool_calls_data = []

        for msg in reversed(messages):
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user" and not user_msg:
                user_msg = content
            elif role == "assistant" and not assistant_msg:
                assistant_msg = content

                # Extract tool calls if present
                if "tool_calls" in msg:
                    tool_calls_data.extend(msg["tool_calls"])

        # 1. Analyze chat messages
        chat_signals = await self.scope_engine.analyze_chat_message(
            user_msg, assistant_msg, metadata
        )
        signals.extend(chat_signals)

        # 2. Analyze tool calls
        for tool_call in tool_calls_data:
            func = tool_call.get("function", {})
            tool_name = func.get("name", "")
            args_str = func.get("arguments", "{}")

            try:
                import json
                arguments = json.loads(args_str) if isinstance(args_str, str) else args_str
            except:
                arguments = {}

            tool_signals = await self.scope_engine.analyze_tool_call(
                tool_name, arguments
            )
            signals.extend(tool_signals)

        return signals

    async def auto_activate_scopes(
        self,
        signals: List[InferenceSignal],
        dsl_system
    ) -> Dict[ScopeLevel, str]:
        """
        Automatically activate scope contexts based on inference signals.

        Returns activated scopes.
        """
        activated = {}

        # Group signals by scope level
        by_scope: Dict[ScopeLevel, List[InferenceSignal]] = defaultdict(list)
        for signal in signals:
            by_scope[signal.scope_level].append(signal)

        # For each scope, pick highest confidence signal
        for scope_level, scope_signals in by_scope.items():
            if not scope_signals:
                continue

            # Get highest confidence signal
            best_signal = max(scope_signals, key=lambda s: s.confidence)

            # Check if confidence exceeds threshold
            threshold = self.confidence_thresholds.get(scope_level, 0.7)
            if best_signal.confidence < threshold:
                logger.debug(
                    f"Skipping {scope_level.value}: confidence {best_signal.confidence} < {threshold}"
                )
                continue

            # Activate scope
            logger.info(
                f"Auto-activating {scope_level.value}: {best_signal.value} "
                f"(confidence: {best_signal.confidence:.2f}, evidence: {best_signal.evidence})"
            )

            # Set context in DSL system
            if scope_level == ScopeLevel.SESSION:
                await dsl_system.context_manager.set_session_context(best_signal.value)
            elif scope_level == ScopeLevel.PHASE:
                phase_type = best_signal.value.split("_")[1] if "_" in best_signal.value else "unknown"
                await dsl_system.context_manager.set_phase_context(
                    best_signal.value, phase_type
                )
            elif scope_level == ScopeLevel.PROJECT:
                # Extract project name if present
                project_name = next(
                    (s.evidence.split("'")[1] for s in scope_signals if "'" in s.evidence),
                    None
                )
                await dsl_system.context_manager.set_project_context(
                    best_signal.value, project_name
                )
            elif scope_level == ScopeLevel.WORKSPACE:
                await dsl_system.context_manager.set_workspace_context(best_signal.value)
            elif scope_level == ScopeLevel.ORGANIZATION:
                await dsl_system.context_manager.set_organization_context(best_signal.value)

            activated[scope_level] = best_signal.value

        return activated

    async def store_to_neo4j(self, signals: List[InferenceSignal]) -> None:
        """
        Store inference signals and relations to Neo4j.

        Creates dense similarity network:
        - Nodes: Sessions, Projects, Files, ToolCalls, Messages
        - Edges: Relations with confidence scores
        - Properties: Timestamps, evidence, metadata
        """
        # TODO: Implement Neo4j storage
        # Will use py2neo or neo4j-driver
        pass

    async def get_historical_context(
        self,
        scope_level: ScopeLevel,
        lookback_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Query historical patterns from Neo4j.

        For a given scope level, return:
        - Most likely values based on past behavior
        - Confidence scores
        - Related entities
        - Temporal patterns
        """
        # TODO: Query Neo4j for patterns
        insights = await self.scope_engine.analyze_historical_patterns()
        return insights


# Global singleton
_inference_engine: Optional[ComprehensiveScopeInferenceEngine] = None


def get_comprehensive_inference_engine(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> ComprehensiveScopeInferenceEngine:
    """Get or create global comprehensive inference engine."""
    global _inference_engine

    if _inference_engine is None:
        # Load from environment
        import os
        uri = neo4j_uri or os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = neo4j_user or os.getenv("NEO4J_USERNAME", "neo4j")
        password = neo4j_password or os.getenv("NEO4J_PASSWORD", "")
        redis = redis_url or os.getenv("UPSTASH_REDIS_REST_URL", "redis://localhost:6379")

        _inference_engine = ComprehensiveScopeInferenceEngine(
            neo4j_uri=uri,
            neo4j_user=user,
            neo4j_password=password,
            redis_url=redis,
        )

    return _inference_engine
