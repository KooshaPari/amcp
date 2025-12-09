# Context & Working Directory Management Research
**Stream G: Agent Layer Phase 4 Research**
**Date:** December 2, 2025
**Status:** Complete

---

## Executive Summary

This document provides comprehensive research findings for context and working directory management in the agent layer. Research covers 5 key areas:

1. **Project Abstraction** - What constitutes a "project" and how to represent it
2. **CWD Inference & Management** - Working directory tracking across multi-threaded agents
3. **File System Integration** - Atomic operations, monitoring, and change detection
4. **State Persistence** - Checkpoint/snapshot strategies and crash recovery
5. **Sandboxing & Isolation** - Container options and security strategies

**Key Recommendations:**
- Use Git repository boundaries + package.json/pyproject.toml as project markers
- Implement per-agent CWD tracking via thread-local storage + explicit path resolution
- Use Watchdog library for cross-platform file monitoring
- Implement event sourcing + incremental snapshots for state persistence
- Choose gVisor for production sandboxing (balance of security + performance)

---

## Table of Contents

1. [G1: Project Abstraction](#g1-project-abstraction)
2. [G2: CWD Inference & Management](#g2-cwd-inference--management)
3. [G3: File System Integration](#g3-file-system-integration)
4. [G4: State Persistence](#g4-state-persistence)
5. [G5: Sandboxing & Isolation](#g5-sandboxing--isolation)
6. [Synthesis & Recommendations](#synthesis--recommendations)
7. [Implementation Checklist](#implementation-checklist)
8. [References](#references)

---

## G1: Project Abstraction

### Research Question
What defines a "project" in our agent layer? How do we identify, track, and manage project boundaries?

### Key Findings

#### 1.1 Project Definition

A **project** in software engineering contexts typically has these characteristics:

- **Root directory** with distinguishing markers
- **Version control** (usually Git repository)
- **Dependency management** (package.json, requirements.txt, Cargo.toml, etc.)
- **Build configuration** (Makefile, build scripts, CI/CD config)
- **Source code organization** (src/, tests/, docs/)

From research ([SitePoint](https://www.sitepoint.com/organize-project-files/), [Slack Engineering](https://slack.engineering/happiness-is-a-freshly-organized-codebase/)):

> "A well-organized folder structure is more than just a convenience; it's a blueprint that supports scalability, maintainability, and effective collaboration."

#### 1.2 Project Markers (Detection Heuristics)

**Primary Markers (Strong Signals):**
- `.git/` directory → Git repository root
- `package.json` → Node.js project
- `pyproject.toml` / `setup.py` → Python project
- `Cargo.toml` → Rust project
- `go.mod` → Go project
- `.sln` / `.csproj` → .NET solution/project
- `build.gradle` / `pom.xml` → Java/JVM project

**Secondary Markers (Supporting Signals):**
- `.gitignore`, `.dockerignore` → Project configuration
- `README.md` → Documentation
- `LICENSE` → Open source project
- `Makefile`, `justfile` → Build automation
- `.github/workflows/` → CI/CD configuration
- `docker-compose.yml` → Multi-container setup

**Tertiary Markers (Weak Signals):**
- `src/`, `lib/`, `tests/` directories → Standard structure
- `.vscode/`, `.idea/` → IDE configuration
- `.env.example` → Environment template

#### 1.3 Monorepo Considerations

From research on monorepos ([Atlassian Git Tutorial](https://www.atlassian.com/git/tutorials/monorepos), [monorepo.tools](https://monorepo.tools/)):

**Monorepo Detection:**
- Root `package.json` with `workspaces` field
- Tools: Lerna, Yarn Workspaces, pnpm workspaces, Turborepo
- Multiple nested projects with own package.json/pyproject.toml

**VS Code Strategy:**
- `git.autoRepositoryDetection`: "true" or "subFolders"
- `git.repositoryScanMaxDepth`: -1 for deep scanning
- `git.openRepositoryInParentFolders`: "always"

### 1.4 Existing Implementation Analysis

From `test_server_cwd.py` in our codebase:

```python
class MCPServerInfo:
    name: str
    command: str
    args: list
    env: dict
    cwd: str  # Working directory for server
```

**Current approach:**
- Explicit `cwd` per MCP server
- Warning if CWD doesn't exist
- Metadata includes CWD information

**Gap:** No automatic project detection or inference.

### Project Abstraction Specification

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict
from enum import Enum

class ProjectType(Enum):
    """Project type identification."""
    PYTHON = "python"
    NODE = "node"
    RUST = "rust"
    GO = "go"
    DOTNET = "dotnet"
    JAVA = "java"
    GENERIC = "generic"
    MONOREPO = "monorepo"

@dataclass
class ProjectMarker:
    """Project identification marker."""
    path: Path
    marker_type: str  # "git", "package_manager", "build_config"
    confidence: float  # 0.0 - 1.0
    metadata: Dict

@dataclass
class Project:
    """Project abstraction."""
    root: Path
    type: ProjectType
    markers: List[ProjectMarker]
    git_repo: Optional[Path]

    # Configuration files
    package_files: List[Path]  # package.json, pyproject.toml, etc.
    build_files: List[Path]    # Makefile, build.gradle, etc.

    # Structure
    src_dirs: List[Path]
    test_dirs: List[Path]
    docs_dirs: List[Path]

    # Nested projects (for monorepos)
    subprojects: List['Project']

    # Metadata
    name: str
    dependencies: Dict[str, str]

class ProjectDetector:
    """Detect and identify projects."""

    def detect_project(self, path: Path) -> Optional[Project]:
        """
        Detect project at given path.

        Algorithm:
        1. Search upward for Git repository root
        2. Identify package manager files
        3. Scan directory structure
        4. Determine project type
        5. Check for nested projects (monorepo)
        """
        pass

    def find_git_root(self, path: Path) -> Optional[Path]:
        """Find Git repository root by searching upward."""
        current = path.resolve()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return None

    def identify_project_type(self, root: Path) -> ProjectType:
        """Identify project type from markers."""
        # Check for package manager files
        if (root / "package.json").exists():
            # Check if monorepo
            pkg = json.loads((root / "package.json").read_text())
            if "workspaces" in pkg:
                return ProjectType.MONOREPO
            return ProjectType.NODE

        if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
            return ProjectType.PYTHON

        if (root / "Cargo.toml").exists():
            return ProjectType.RUST

        if (root / "go.mod").exists():
            return ProjectType.GO

        # ... other checks

        return ProjectType.GENERIC

    def scan_structure(self, root: Path) -> Dict[str, List[Path]]:
        """Scan directory structure for common patterns."""
        return {
            "src": self._find_dirs(root, ["src", "lib"]),
            "tests": self._find_dirs(root, ["tests", "test", "__tests__"]),
            "docs": self._find_dirs(root, ["docs", "doc", "documentation"])
        }
```

**Key Design Decisions:**

1. **Git-centric approach**: Use Git repository boundaries as primary project delimiter
2. **Multi-level detection**: Primary/secondary/tertiary markers with confidence scores
3. **Monorepo support**: Detect and track nested projects
4. **Lazy evaluation**: Don't scan entire tree upfront; cache results
5. **Path canonicalization**: Always use absolute, resolved paths

---

## G2: CWD Inference & Management

### Research Question
How do we infer and manage working directories for agents in a multi-threaded environment?

### Key Findings

#### 2.1 CWD Challenges in Multi-threaded Applications

From research ([Stack Overflow - Python CWD](https://stackoverflow.com/questions/77211228/can-a-multi-threaded-python-app-change-the-cwd), [Stack Overflow - C++ Thread CWD](https://stackoverflow.com/questions/24491746/thread-working-directory)):

> "The current working directory is a process-wide setting, not a thread setting."

**Critical Problem:**
- `os.chdir()` affects **entire process**, not just one thread
- Race conditions when multiple threads change CWD concurrently
- Between `os.getcwd()` calls, CWD can change unpredictably

**Real-world impact:**
```python
# Thread 1
os.chdir("/project/a")
do_work()  # Expects to be in /project/a

# Thread 2 (concurrent)
os.chdir("/project/b")  # BREAKS Thread 1!
```

#### 2.2 Solutions for Per-Thread CWD

**Solution 1: Explicit Absolute Paths (Recommended)**

From research ([Stack Overflow - Threading CWD](https://stackoverflow.com/questions/18516271/how-to-specify-a-local-working-directory-for-threading-thread-and-multiprocessin)):

> "Your best bet is to explicitly access files in a directory using the full path, rather than changing to that directory."

**Implementation:**
```python
class AgentContext:
    """Per-agent context with working directory."""

    def __init__(self, agent_id: str, working_dir: Path):
        self.agent_id = agent_id
        self.working_dir = working_dir.resolve()

    def resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve path relative to agent's working directory."""
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return (self.working_dir / path).resolve()

# Usage
context = AgentContext("agent-1", Path("/project/a"))
file_path = context.resolve_path("src/main.py")  # /project/a/src/main.py
```

**Solution 2: POSIX *at() System Calls**

From research:

> "Emulate a per-thread working directory by storing a file descriptor for the per-thread CWD and using the various *at() syscalls (openat() etc.) to manipulate paths relative to that directory fd."

**Implementation:**
```python
import os

class FileDescriptorCWD:
    """Per-thread CWD using file descriptors."""

    def __init__(self, path: Path):
        self.fd = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)

    def openat(self, relative_path: str, flags: int):
        """Open file relative to this CWD."""
        return os.open(relative_path, flags, dir_fd=self.fd)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        os.close(self.fd)

# Usage
with FileDescriptorCWD(Path("/project/a")) as cwd:
    fd = cwd.openat("src/main.py", os.O_RDONLY)
```

**Solution 3: Thread-local Storage + Locking**

```python
import threading
from contextlib import contextmanager

_thread_local = threading.local()
_cwd_lock = threading.Lock()

@contextmanager
def scoped_cwd(path: Path):
    """Temporarily change CWD with lock."""
    with _cwd_lock:
        old_cwd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(old_cwd)

# Usage
with scoped_cwd(Path("/project/a")):
    # Work in /project/a
    pass
# Restored to original CWD
```

#### 2.3 Path Resolution Strategies

From Linux kernel documentation on path walking:

> "Paths are resolved by walking the namespace tree, starting with the first component of the pathname with a known dentry, then finding the child of that dentry."

**Canonicalization Requirements:**
- Resolve symlinks
- Normalize `.` and `..`
- Handle relative vs absolute paths
- Check permissions along path

**Implementation:**
```python
class PathResolver:
    """Path resolution with CWD context."""

    def __init__(self, base_cwd: Path):
        self.base_cwd = base_cwd.resolve()

    def resolve(self, path: str | Path) -> Path:
        """
        Resolve path relative to base CWD.

        - Absolute paths → return as-is (resolved)
        - Relative paths → resolve relative to base_cwd
        - Symlinks → follow and resolve
        - .. and . → normalize
        """
        path = Path(path)

        if path.is_absolute():
            return path.resolve()

        return (self.base_cwd / path).resolve()

    def is_within_project(self, path: Path, project_root: Path) -> bool:
        """Check if path is within project boundaries."""
        try:
            path.resolve().relative_to(project_root.resolve())
            return True
        except ValueError:
            return False
```

### 2.4 CWD Inference from Context

**Strategy: Infer CWD from conversation context**

From AI agent research ([Medium - Context-Aware AI](https://sabber.medium.com/context-aware-ai-agent-memory-management-and-state-tracking-3c904622edd7)):

> "Managing agent state effectively is crucial for building reliable AI systems. State represents all the information the agent needs to track: the current task, previous results, files that have been created."

**Inference Signals:**
1. **Explicit mentions**: "in directory X", "cd to Y"
2. **File references**: "edit src/main.py" → infer project root
3. **Git operations**: "git commit" → infer repository root
4. **Previous operations**: Track last successful CWD
5. **Project detection**: Scan for project markers

**Implementation:**
```python
class CWDInferenceEngine:
    """Infer working directory from context."""

    def __init__(self):
        self.project_detector = ProjectDetector()
        self.path_resolver = None  # Set per-agent

    def infer_cwd(
        self,
        message: str,
        current_cwd: Path,
        project_root: Optional[Path]
    ) -> Path:
        """
        Infer CWD from message content.

        Priority:
        1. Explicit "cd" or "in directory" commands
        2. File path references (extract parent dir)
        3. Project root (if detected)
        4. Current CWD (fallback)
        """
        # Check for explicit CWD change
        if match := re.search(r'cd\s+([^\s]+)', message):
            return self._resolve_path(match.group(1), current_cwd)

        if match := re.search(r'in\s+(?:directory|folder)\s+([^\s]+)', message):
            return self._resolve_path(match.group(1), current_cwd)

        # Check for file references
        if file_paths := self._extract_file_paths(message):
            # Use parent directory of first file
            path = Path(file_paths[0])
            if path.is_file():
                return path.parent
            return path

        # Use project root if available
        if project_root:
            return project_root

        # Fallback to current CWD
        return current_cwd

    def _extract_file_paths(self, message: str) -> List[str]:
        """Extract file paths from message."""
        # Match common file path patterns
        patterns = [
            r'(?:read|write|edit|open)\s+([^\s]+\.[a-z]+)',
            r'file:\s+([^\s]+)',
            r'`([^\s]+\.[a-z]+)`'
        ]

        paths = []
        for pattern in patterns:
            paths.extend(re.findall(pattern, message))
        return paths
```

### CWD Management System Design

```python
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional

@dataclass
class AgentWorkspace:
    """Agent's workspace state."""
    agent_id: str
    current_cwd: Path
    project: Optional[Project]
    path_resolver: PathResolver
    history: List[Path]  # CWD history

    def change_directory(self, path: Path) -> None:
        """Change working directory."""
        self.history.append(self.current_cwd)
        self.current_cwd = path.resolve()
        self.path_resolver = PathResolver(self.current_cwd)

    def resolve_path(self, path: str | Path) -> Path:
        """Resolve path relative to current CWD."""
        return self.path_resolver.resolve(path)

class WorkspaceManager:
    """Manage agent workspaces."""

    def __init__(self):
        self.workspaces: Dict[str, AgentWorkspace] = {}
        self.lock = Lock()
        self.project_detector = ProjectDetector()

    def create_workspace(
        self,
        agent_id: str,
        initial_cwd: Optional[Path] = None
    ) -> AgentWorkspace:
        """Create workspace for agent."""
        with self.lock:
            if initial_cwd is None:
                initial_cwd = Path.cwd()

            project = self.project_detector.detect_project(initial_cwd)

            workspace = AgentWorkspace(
                agent_id=agent_id,
                current_cwd=initial_cwd.resolve(),
                project=project,
                path_resolver=PathResolver(initial_cwd),
                history=[]
            )

            self.workspaces[agent_id] = workspace
            return workspace

    def get_workspace(self, agent_id: str) -> Optional[AgentWorkspace]:
        """Get agent's workspace."""
        return self.workspaces.get(agent_id)

    def update_cwd(
        self,
        agent_id: str,
        message: str
    ) -> Path:
        """Update CWD based on message context."""
        workspace = self.get_workspace(agent_id)
        if not workspace:
            raise ValueError(f"No workspace for agent {agent_id}")

        inference_engine = CWDInferenceEngine()
        new_cwd = inference_engine.infer_cwd(
            message=message,
            current_cwd=workspace.current_cwd,
            project_root=workspace.project.root if workspace.project else None
        )

        if new_cwd != workspace.current_cwd:
            workspace.change_directory(new_cwd)

        return workspace.current_cwd
```

**Key Design Decisions:**

1. **No global CWD changes**: Never call `os.chdir()` except with locks
2. **Explicit path resolution**: Always resolve paths relative to agent's CWD
3. **Thread-local context**: Each agent has isolated workspace
4. **Inference + explicit**: Support both inferred and explicit CWD changes
5. **History tracking**: Maintain CWD history for undo/debugging

---

## G3: File System Integration

### Research Question
How do we design safe, atomic file operations with change monitoring and rollback capabilities?

### Key Findings

#### 3.1 Atomic File Operations

From research ([Apache Commons Transaction](https://commons.apache.org/proper/commons-transaction/file/index.html), [Wikipedia - Transactional NTFS](https://en.wikipedia.org/wiki/Transactional_NTFS)):

**Transactional File Systems:**

> "Transactional NTFS allows for files and directories to be created, modified, renamed, and deleted atomically, using transactions to ensure correctness of operation."

**However:**

From [InfoQ - File System Transactions](https://www.infoq.com/news/2008/01/file-systems-transactions/):

> "Apache Commons Transaction moved its project to dormant status, convinced that the main advertised feature of transactional file access cannot be implemented reliably on top of an ordinary file system."

**Practical Solution: Atomic Rename Pattern**

From research ([Stack Overflow - Atomic File Writes](https://stackoverflow.com/questions/9096380/implementing-atomic-file-writes-in-a-nontransactional-filesystem)):

**Pattern:**
1. Write to temporary file
2. Flush and sync to disk
3. Atomic rename to target file

**Implementation (from our codebase - `filesystem_concurrency.py`):**

```python
async def atomic_write(self, file_path: str, content: str) -> bool:
    """Atomically write to file."""
    lock = self._get_lock(file_path)

    try:
        await lock.acquire()

        # Write to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            dir=os.path.dirname(file_path)
        ) as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())  # Ensure data on disk
            tmp_path = tmp.name

        # Atomic rename
        os.replace(tmp_path, file_path)
        return True
    finally:
        await lock.release()
```

**Atomicity Guarantees:**

From [Stack Overflow - Atomic Operations](https://stackoverflow.com/questions/5232032/what-filesystem-operations-are-required-to-be-atomic):

- `rename()` is atomic on POSIX systems
- `replace()` in Python uses atomic rename
- Write → flush → fsync → rename ensures durability

#### 3.2 File Locking Strategies

**Current Implementation (from `filesystem_concurrency.py`):**

```python
class FileLock:
    """File lock for concurrent access control."""

    def __init__(self, file_path: str, timeout: int = 30):
        self.file_path = file_path
        self.lock_file = f"{file_path}.lock"
        self.timeout = timeout
        self.lock = asyncio.Lock()
```

**Issues with current approach:**
- Lock file not cleaned up on crash
- No timeout enforcement
- No deadlock detection

**Improved Implementation:**

```python
import fcntl
import contextlib
from pathlib import Path

class ImprovedFileLock:
    """Improved file lock with fcntl."""

    def __init__(self, file_path: Path, timeout: float = 30.0):
        self.file_path = file_path
        self.lock_file = file_path.with_suffix(file_path.suffix + ".lock")
        self.timeout = timeout
        self._fd = None

    async def acquire(self) -> bool:
        """Acquire lock with timeout."""
        import asyncio

        self._fd = open(self.lock_file, 'w')

        try:
            # Non-blocking lock with timeout
            await asyncio.wait_for(
                self._acquire_lock(),
                timeout=self.timeout
            )
            return True
        except asyncio.TimeoutError:
            self._fd.close()
            self._fd = None
            return False

    async def _acquire_lock(self):
        """Acquire fcntl lock."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            fcntl.flock,
            self._fd.fileno(),
            fcntl.LOCK_EX
        )

    async def release(self) -> None:
        """Release lock."""
        if self._fd:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
            self._fd = None

            # Clean up lock file
            if self.lock_file.exists():
                self.lock_file.unlink()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, *args):
        await self.release()

# Usage
async with ImprovedFileLock(Path("data.json")) as lock:
    # Safely modify file
    pass
```

#### 3.3 File Change Monitoring

From research ([Watchdog on PyPI](https://pypi.org/project/watchdog/), [GitHub - watchdog](https://github.com/gorakhargosh/watchdog)):

**Watchdog Library:**

> "Python library and shell utilities to monitor filesystem events. Cross-platform API supporting Linux (inotify), macOS (FSEvents), Windows (ReadDirectoryChangesW)."

**Platform Support:**
- Linux: inotify
- macOS: FSEvents, kqueue
- Windows: ReadDirectoryChangesW
- Fallback: Polling

**Basic Implementation:**

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

class AsyncFileWatcher(FileSystemEventHandler):
    """Async file watcher using watchdog."""

    def __init__(self, callback):
        self.callback = callback
        self.loop = asyncio.get_event_loop()

    def on_modified(self, event):
        """Handle file modification."""
        if not event.is_directory:
            self.loop.create_task(
                self.callback("modified", event.src_path)
            )

    def on_created(self, event):
        """Handle file creation."""
        if not event.is_directory:
            self.loop.create_task(
                self.callback("created", event.src_path)
            )

    def on_deleted(self, event):
        """Handle file deletion."""
        if not event.is_directory:
            self.loop.create_task(
                self.callback("deleted", event.src_path)
            )

class FileMonitor:
    """Monitor file system changes."""

    def __init__(self):
        self.observer = Observer()
        self.watches = {}

    async def watch(
        self,
        path: Path,
        callback,
        recursive: bool = False
    ):
        """Watch path for changes."""
        handler = AsyncFileWatcher(callback)
        watch = self.observer.schedule(
            handler,
            str(path),
            recursive=recursive
        )
        self.watches[str(path)] = watch

        if not self.observer.is_alive():
            self.observer.start()

    async def unwatch(self, path: Path):
        """Stop watching path."""
        if str(path) in self.watches:
            self.observer.unschedule(self.watches[str(path)])
            del self.watches[str(path)]

    def stop(self):
        """Stop observer."""
        self.observer.stop()
        self.observer.join()

# Usage
async def on_change(event_type: str, path: str):
    print(f"File {event_type}: {path}")

monitor = FileMonitor()
await monitor.watch(Path("/project"), on_change, recursive=True)
```

#### 3.4 Undo/Rollback Capabilities

**Strategy 1: Copy-on-Write**

```python
class CopyOnWriteFile:
    """Copy-on-write file wrapper."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    async def begin_transaction(self):
        """Start transaction by creating backup."""
        if self.file_path.exists():
            shutil.copy2(self.file_path, self.backup_path)

    async def commit(self):
        """Commit transaction by removing backup."""
        if self.backup_path.exists():
            self.backup_path.unlink()

    async def rollback(self):
        """Rollback by restoring from backup."""
        if self.backup_path.exists():
            shutil.copy2(self.backup_path, self.file_path)
            self.backup_path.unlink()
```

**Strategy 2: Operation Log**

```python
from dataclasses import dataclass
from enum import Enum

class FileOpType(Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"

@dataclass
class FileOperation:
    """File operation record."""
    op_type: FileOpType
    path: Path
    old_content: Optional[bytes] = None
    new_content: Optional[bytes] = None
    old_path: Optional[Path] = None  # For renames
    timestamp: float = None

class TransactionalFileSystem:
    """File system with transaction support."""

    def __init__(self):
        self.operations: List[FileOperation] = []
        self.in_transaction = False

    def begin(self):
        """Begin transaction."""
        self.operations = []
        self.in_transaction = True

    async def write(self, path: Path, content: bytes):
        """Write file (tracked)."""
        old_content = None
        if path.exists():
            old_content = path.read_bytes()

        if self.in_transaction:
            self.operations.append(FileOperation(
                op_type=FileOpType.MODIFY if old_content else FileOpType.CREATE,
                path=path,
                old_content=old_content,
                new_content=content,
                timestamp=time.time()
            ))

        # Actually write file
        path.write_bytes(content)

    async def delete(self, path: Path):
        """Delete file (tracked)."""
        if not path.exists():
            return

        old_content = path.read_bytes()

        if self.in_transaction:
            self.operations.append(FileOperation(
                op_type=FileOpType.DELETE,
                path=path,
                old_content=old_content,
                timestamp=time.time()
            ))

        path.unlink()

    async def commit(self):
        """Commit transaction."""
        self.operations = []
        self.in_transaction = False

    async def rollback(self):
        """Rollback transaction."""
        # Reverse operations in reverse order
        for op in reversed(self.operations):
            if op.op_type == FileOpType.CREATE:
                # Undo create → delete
                if op.path.exists():
                    op.path.unlink()

            elif op.op_type == FileOpType.MODIFY:
                # Undo modify → restore old content
                if op.old_content:
                    op.path.write_bytes(op.old_content)

            elif op.op_type == FileOpType.DELETE:
                # Undo delete → restore file
                if op.old_content:
                    op.path.write_bytes(op.old_content)

        self.operations = []
        self.in_transaction = False
```

### File Operations API Specification

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class FileSystemAPI(ABC):
    """Abstract file system operations."""

    @abstractmethod
    async def read(self, path: Path) -> bytes:
        """Read file contents."""
        pass

    @abstractmethod
    async def write(self, path: Path, content: bytes) -> None:
        """Write file contents atomically."""
        pass

    @abstractmethod
    async def delete(self, path: Path) -> None:
        """Delete file."""
        pass

    @abstractmethod
    async def exists(self, path: Path) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    async def list_dir(self, path: Path) -> List[Path]:
        """List directory contents."""
        pass

    @abstractmethod
    async def watch(self, path: Path, callback) -> None:
        """Watch for file changes."""
        pass

    @abstractmethod
    async def begin_transaction(self) -> None:
        """Begin transaction."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction."""
        pass

class SafeFileSystem(FileSystemAPI):
    """Safe file system with locking, transactions, and monitoring."""

    def __init__(self):
        self.lock_manager = LockManager()
        self.transaction = TransactionalFileSystem()
        self.monitor = FileMonitor()

    async def read(self, path: Path) -> bytes:
        """Read with lock."""
        async with self.lock_manager.lock(path, mode="read"):
            return path.read_bytes()

    async def write(self, path: Path, content: bytes) -> None:
        """Write atomically with lock."""
        async with self.lock_manager.lock(path, mode="write"):
            await self.transaction.write(path, content)

    # ... implement other methods
```

**Key Design Decisions:**

1. **Atomic rename pattern**: Most reliable for atomicity
2. **fcntl-based locking**: Platform-native, survives crashes
3. **Watchdog for monitoring**: Cross-platform, battle-tested
4. **Transaction log for undo**: Replay in reverse for rollback
5. **Async-first API**: Non-blocking for agent operations

---

## G4: State Persistence

### Research Question
What state needs persistence? How do we implement checkpoints, snapshots, and crash recovery?

### Key Findings

#### 4.1 State Types

From AI agent research ([Medium - Context-Aware AI](https://sabber.medium.com/context-aware-ai-agent-memory-management-and-state-tracking-3c904622edd7), [AWS - Agent Memory](https://aws.amazon.com/blogs/machine-learning/amazon-bedrock-agentcore-memory-building-context-aware-agents/)):

**Agent State Categories:**

1. **Ephemeral State** (session-only)
   - Current conversation turn
   - Temporary variables
   - In-flight operations

2. **Short-term Memory** (session-scoped)
   - Conversation history (last N turns)
   - Current task state
   - Working directory
   - Recent file operations

3. **Long-term Memory** (persistent)
   - User preferences
   - Project configuration
   - Historical context
   - Learned patterns

4. **Operational State** (for recovery)
   - Active agents
   - Resource allocations
   - Locks held
   - Pending transactions

#### 4.2 Checkpoint vs. Snapshot Strategies

From research ([CMU Checkpoint-Recovery](https://users.ece.cmu.edu/~koopman/des_s99/checkpoint/), [Apache Flink Checkpointing](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/datastream/fault-tolerance/checkpointing/)):

**Checkpoint:**
> "When a failure has occurred, the recovery mechanism restores system state to the last checkpointed value."

**Strategies:**

1. **Full Checkpoint**: Complete state snapshot
2. **Incremental Checkpoint**: Only changed state since last checkpoint
3. **Differential Checkpoint**: Changes since last full checkpoint
4. **Continuous Checkpoint**: Log every state change

**Trade-offs:**

| Strategy | Write Cost | Recovery Speed | Storage | Use Case |
|----------|-----------|----------------|---------|----------|
| Full | High | Fast | High | Infrequent checkpoints |
| Incremental | Low | Medium | Low | Frequent checkpoints |
| Differential | Medium | Medium | Medium | Balanced approach |
| Continuous | Very High | Very Fast | Very High | Mission-critical |

#### 4.3 Crash-Consistent vs. Application-Consistent

From research ([N2W - EBS Snapshots](https://n2ws.com/blog/aws-ebs-snapshot/ebs-snapshots-crash-consistent-vs-application-consistent)):

**Crash-Consistent:**
> "Same as if someone pulled out the power cord of a computer, and then turned it back on. Most modern applications know how to recover from such a state."

**Application-Consistent:**
> "Tell the application it is about to be backed up, so it can get prepared. Applications have APIs that notify them when they are about to be backed up so they can make sure transactions are complete, buffers flushed, files closed."

**For Agents:**
- **Crash-consistent**: Fast but may lose in-flight operations
- **Application-consistent**: Slower but guarantees clean state

#### 4.4 Event Sourcing Pattern

From research ([Akka Event Sourcing](https://doc.akka.io/libraries/akka-core/current/typed/persistence.html)):

> "A stateful actor is recovered by replaying the stored events to the actor, allowing it to rebuild its state. This can be either the full history of changes or starting from a checkpoint in a snapshot."

**Event Sourcing Benefits:**
- Complete audit trail
- Time travel (replay to any point)
- Easy rollback
- Debugging replay

**Implementation:**

```python
from dataclasses import dataclass
from typing import List, Any
import json

@dataclass
class Event:
    """State change event."""
    event_type: str
    timestamp: float
    agent_id: str
    data: Dict[str, Any]

class EventStore:
    """Store and replay events."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.events: List[Event] = []

    async def append(self, event: Event):
        """Append event to log."""
        self.events.append(event)

        # Persist to disk
        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(event.__dict__) + '\n')

    async def replay(
        self,
        from_timestamp: Optional[float] = None
    ) -> List[Event]:
        """Replay events from timestamp."""
        if from_timestamp is None:
            return self.events

        return [e for e in self.events if e.timestamp >= from_timestamp]

    async def load(self):
        """Load events from disk."""
        if not self.storage_path.exists():
            return

        with open(self.storage_path) as f:
            for line in f:
                data = json.loads(line)
                self.events.append(Event(**data))

class StatefulAgent:
    """Agent with event-sourced state."""

    def __init__(self, agent_id: str, event_store: EventStore):
        self.agent_id = agent_id
        self.event_store = event_store
        self.state = {}

    async def apply_event(self, event: Event):
        """Apply event to state."""
        if event.event_type == "cwd_changed":
            self.state["cwd"] = event.data["new_cwd"]

        elif event.event_type == "file_written":
            self.state.setdefault("files_written", []).append(
                event.data["path"]
            )

        # ... handle other event types

    async def change_cwd(self, new_cwd: str):
        """Change CWD (generates event)."""
        event = Event(
            event_type="cwd_changed",
            timestamp=time.time(),
            agent_id=self.agent_id,
            data={"old_cwd": self.state.get("cwd"), "new_cwd": new_cwd}
        )

        await self.event_store.append(event)
        await self.apply_event(event)

    async def recover(self):
        """Recover state by replaying events."""
        events = await self.event_store.replay()
        for event in events:
            if event.agent_id == self.agent_id:
                await self.apply_event(event)
```

### State Persistence Design

```python
from dataclasses import dataclass
from typing import Optional
import pickle
import gzip

@dataclass
class Checkpoint:
    """State checkpoint."""
    checkpoint_id: str
    timestamp: float
    agent_id: str
    state: Dict[str, Any]
    metadata: Dict[str, Any]

class CheckpointManager:
    """Manage checkpoints and snapshots."""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)

        self.event_store = EventStore(storage_dir / "events.jsonl")
        self.checkpoints_dir = storage_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)

    async def create_checkpoint(
        self,
        agent_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> Checkpoint:
        """Create full state checkpoint."""
        checkpoint = Checkpoint(
            checkpoint_id=f"{agent_id}_{time.time()}",
            timestamp=time.time(),
            agent_id=agent_id,
            state=state,
            metadata=metadata or {}
        )

        # Save to disk (compressed)
        checkpoint_path = self.checkpoints_dir / f"{checkpoint.checkpoint_id}.pkl.gz"
        with gzip.open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint, f)

        return checkpoint

    async def load_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Checkpoint]:
        """Load checkpoint from disk."""
        checkpoint_path = self.checkpoints_dir / f"{checkpoint_id}.pkl.gz"

        if not checkpoint_path.exists():
            return None

        with gzip.open(checkpoint_path, 'rb') as f:
            return pickle.load(f)

    async def recover_agent(
        self,
        agent_id: str,
        from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recover agent state.

        Strategy:
        1. Load last checkpoint (if available)
        2. Replay events since checkpoint
        3. Reconstruct current state
        """
        # Load checkpoint
        if from_checkpoint:
            checkpoint = await self.load_checkpoint(from_checkpoint)
            if checkpoint:
                state = checkpoint.state.copy()
                replay_from = checkpoint.timestamp
            else:
                state = {}
                replay_from = None
        else:
            # Find latest checkpoint
            checkpoints = sorted(
                self.checkpoints_dir.glob(f"{agent_id}_*.pkl.gz")
            )
            if checkpoints:
                with gzip.open(checkpoints[-1], 'rb') as f:
                    checkpoint = pickle.load(f)
                    state = checkpoint.state.copy()
                    replay_from = checkpoint.timestamp
            else:
                state = {}
                replay_from = None

        # Replay events
        events = await self.event_store.replay(from_timestamp=replay_from)

        agent = StatefulAgent(agent_id, self.event_store)
        agent.state = state

        for event in events:
            if event.agent_id == agent_id:
                await agent.apply_event(event)

        return agent.state

    async def cleanup_old_checkpoints(
        self,
        keep_last_n: int = 10
    ):
        """Remove old checkpoints."""
        checkpoints = sorted(
            self.checkpoints_dir.glob("*.pkl.gz"),
            key=lambda p: p.stat().st_mtime
        )

        # Keep last N, delete rest
        for checkpoint_path in checkpoints[:-keep_last_n]:
            checkpoint_path.unlink()

class PersistenceStrategy:
    """Configurable persistence strategy."""

    def __init__(
        self,
        checkpoint_interval: float = 300.0,  # 5 minutes
        event_batch_size: int = 100,
        compression: bool = True
    ):
        self.checkpoint_interval = checkpoint_interval
        self.event_batch_size = event_batch_size
        self.compression = compression

        self.last_checkpoint_time = 0
        self.events_since_checkpoint = 0

    def should_checkpoint(self) -> bool:
        """Determine if checkpoint needed."""
        time_since_checkpoint = time.time() - self.last_checkpoint_time

        return (
            time_since_checkpoint >= self.checkpoint_interval or
            self.events_since_checkpoint >= self.event_batch_size
        )
```

**Key Design Decisions:**

1. **Event sourcing + checkpoints**: Hybrid approach for efficiency
2. **Incremental by default**: Checkpoint every N events or T seconds
3. **Compressed storage**: Use gzip for checkpoint files
4. **Automatic cleanup**: Remove old checkpoints (keep last N)
5. **Crash recovery**: Checkpoint + event replay

---

## G5: Sandboxing & Isolation

### Research Question
What container/VM technologies provide the best isolation for agent execution?

### Key Findings

#### 5.1 Docker Isolation Mechanisms

From research ([Docker Security Docs](https://docs.docker.com/engine/security/), [Adobe Tech Blog](https://medium.com/adobetech/sandboxing-docker-containers-56fbe6cf3534)):

**Docker Isolation:**

> "Docker creates namespaces and control groups for containers. Namespaces provide the first and most straightforward form of isolation—processes in a container cannot see or affect processes in other containers or the host system."

**Namespace Types:**
- **PID**: Process isolation
- **NET**: Network isolation
- **MNT**: Mount point isolation
- **UTS**: Hostname isolation
- **IPC**: Inter-process communication isolation
- **USER**: User namespace isolation

**Security Limitations:**

From [Security StackExchange](https://security.stackexchange.com/questions/107850/docker-as-a-sandbox-for-untrusted-code):

> "Docker does not guarantee complete isolation and should not be confused with virtualization. Containers on the same host share the same kernel, and most kernel exploits should work for escaping containers."

**Enhanced Security:**

1. **Seccomp**: System call filtering
2. **AppArmor/SELinux**: Mandatory access control
3. **Capabilities**: Fine-grained privileges
4. **User namespaces**: Non-root inside container

**Example Docker Security:**

```yaml
# docker-compose.yml
services:
  agent-sandbox:
    image: agent-runtime:latest
    security_opt:
      - no-new-privileges:true
      - seccomp=seccomp-profile.json
      - apparmor=docker-default
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
    volumes:
      - ./workspace:/workspace:ro
    network_mode: "none"  # No network access
```

#### 5.2 Sandboxed Container Technologies

From research ([Palo Alto - Sandboxed Containers](https://unit42.paloaltonetworks.com/making-containers-more-isolated-an-overview-of-sandboxed-container-technologies/), [Onidel - gVisor vs Kata vs Firecracker](https://onidel.com/gvisor-kata-firecracker-2025/)):

**Comparison Matrix:**

| Technology | Isolation Method | Startup Time | Performance Overhead | Security | Use Case |
|-----------|-----------------|--------------|---------------------|----------|----------|
| **Docker** | Namespaces/cgroups | 50-100ms | ~5% | Low | General containers |
| **gVisor** | Userspace kernel | 50-100ms | 10-15% | Medium | Multi-tenant |
| **Kata Containers** | Lightweight VM | 150-300ms | 15-20% | High | Strong isolation |
| **Firecracker** | MicroVM | 100-200ms | 10-15% | High | Serverless |

#### 5.3 gVisor

From research:

> "gVisor implements a custom userspace mini-kernel that sits between containerized applications and the host's kernel, intercepting all container system calls and performing a policy check before passing each call to the host kernel."

**Benefits:**
- Strong isolation (syscall interception)
- Compatible with Docker/containerd
- Good performance (50-100ms startup)
- Actively maintained (Google)

**Drawbacks:**
- Not all syscalls supported
- 10-15% performance overhead
- Some incompatibilities with native code

**Implementation:**

```bash
# Install gVisor runtime
curl -fsSL https://gvisor.dev/archive.key | sudo apt-key add -
sudo add-apt-repository "deb https://storage.googleapis.com/gvisor/releases release main"
sudo apt-get update && sudo apt-get install -y runsc

# Configure Docker to use gVisor
sudo dockerd --add-runtime=runsc=/usr/local/bin/runsc

# Run container with gVisor
docker run --runtime=runsc -it ubuntu:latest
```

#### 5.4 Kata Containers

From research:

> "Kata Containers provides hardware-assisted virtualization by running each container inside a lightweight virtual machine, leveraging hypervisor technologies like QEMU-KVM or Cloud Hypervisor."

**Benefits:**
- Maximum isolation (full VM)
- Hardware-level security
- Compatible with OCI runtimes

**Drawbacks:**
- Slower startup (150-300ms)
- Higher memory overhead
- Requires hardware virtualization

**Implementation:**

```bash
# Install Kata Containers
bash -c "$(curl -fsSL https://raw.githubusercontent.com/kata-containers/kata-containers/main/utils/kata-manager.sh)"

# Configure containerd
cat << EOF | sudo tee -a /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
  runtime_type = "io.containerd.kata.v2"
EOF

# Restart containerd
sudo systemctl restart containerd

# Run with Kata
ctr run --runtime io.containerd.kata.v2 docker.io/library/ubuntu:latest kata-demo
```

#### 5.5 Firecracker

From research:

> "Firecracker creates minimal virtual machines designed specifically for serverless and container workloads, developed by AWS for Lambda, stripping away unnecessary virtualization features to achieve rapid startup times."

**Benefits:**
- Fast startup (100-200ms)
- Minimal memory footprint (~5MB)
- Strong isolation (VM-level)
- Optimized for serverless

**Drawbacks:**
- Linux-only
- Requires custom integration
- Less Docker-compatible

**Implementation:**

```rust
// Firecracker configuration
{
  "boot-source": {
    "kernel_image_path": "/path/to/vmlinux",
    "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"
  },
  "drives": [{
    "drive_id": "rootfs",
    "path_on_host": "/path/to/rootfs",
    "is_root_device": true,
    "is_read_only": false
  }],
  "machine-config": {
    "vcpu_count": 2,
    "mem_size_mib": 512,
    "ht_enabled": false
  }
}
```

#### 5.6 Comparison & Recommendation

**Performance Benchmarks** (from research):

| Metric | Docker | gVisor | Kata | Firecracker |
|--------|--------|--------|------|-------------|
| Startup | 50-100ms | 50-100ms | 150-300ms | 100-200ms |
| Memory | Low | Low | Medium | Low |
| CPU Overhead | ~5% | 10-15% | 15-20% | 10-15% |
| Disk I/O | Native | -10% | -15% | -10% |
| Network | Native | -20% | -10% | Native |

**Decision Matrix:**

| Priority | Recommendation |
|----------|---------------|
| **Maximum Security** | Kata Containers (VM-level isolation) |
| **Best Performance** | Docker (native) |
| **Balanced Approach** | gVisor (good security + performance) |
| **Serverless/FaaS** | Firecracker (optimized for short-lived) |
| **Development** | Docker (easiest to use) |
| **Production Multi-tenant** | gVisor or Kata |

### Sandboxing Strategy

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class IsolationLevel(Enum):
    """Isolation level."""
    NONE = "none"           # No isolation (development)
    NAMESPACE = "namespace" # Linux namespaces only
    SECCOMP = "seccomp"    # + seccomp filtering
    GVISOR = "gvisor"      # gVisor runtime
    KATA = "kata"          # Kata Containers
    FIRECRACKER = "firecracker"  # Firecracker microVM

@dataclass
class SandboxConfig:
    """Sandbox configuration."""
    isolation_level: IsolationLevel

    # Resource limits
    max_memory_mb: int = 512
    max_cpu_cores: float = 1.0
    max_disk_mb: int = 1024

    # Network
    network_enabled: bool = False
    allowed_hosts: List[str] = None

    # Filesystem
    workspace_path: Path = None
    readonly_paths: List[Path] = None
    tmpfs_size_mb: int = 100

    # Security
    drop_capabilities: List[str] = None
    readonly_root: bool = True
    no_new_privileges: bool = True

class SandboxManager:
    """Manage agent sandboxes."""

    def __init__(self, config: SandboxConfig):
        self.config = config
        self.active_sandboxes: Dict[str, Sandbox] = {}

    async def create_sandbox(
        self,
        agent_id: str,
        workspace: Path
    ) -> 'Sandbox':
        """Create isolated sandbox for agent."""

        if self.config.isolation_level == IsolationLevel.GVISOR:
            return await self._create_gvisor_sandbox(agent_id, workspace)

        elif self.config.isolation_level == IsolationLevel.KATA:
            return await self._create_kata_sandbox(agent_id, workspace)

        elif self.config.isolation_level == IsolationLevel.FIRECRACKER:
            return await self._create_firecracker_sandbox(agent_id, workspace)

        else:
            return await self._create_docker_sandbox(agent_id, workspace)

    async def _create_docker_sandbox(
        self,
        agent_id: str,
        workspace: Path
    ) -> 'DockerSandbox':
        """Create Docker sandbox."""

        # Build docker run command
        docker_config = {
            'image': 'agent-runtime:latest',
            'name': f'agent-{agent_id}',
            'detach': True,
            'rm': True,

            # Security options
            'security_opt': [
                'no-new-privileges:true',
                'seccomp=default',
            ],

            # Drop all capabilities
            'cap_drop': ['ALL'],

            # Resource limits
            'memory': f'{self.config.max_memory_mb}m',
            'cpus': str(self.config.max_cpu_cores),

            # Filesystem
            'read_only': self.config.readonly_root,
            'tmpfs': {'/tmp': f'size={self.config.tmpfs_size_mb}m'},
            'volumes': {
                str(workspace): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },

            # Network
            'network_mode': 'none' if not self.config.network_enabled else 'bridge'
        }

        # Create and start container
        sandbox = DockerSandbox(agent_id, docker_config)
        await sandbox.start()

        self.active_sandboxes[agent_id] = sandbox
        return sandbox

    async def _create_gvisor_sandbox(
        self,
        agent_id: str,
        workspace: Path
    ) -> 'GVisorSandbox':
        """Create gVisor sandbox."""

        # Similar to Docker but with gVisor runtime
        docker_config = {
            # ... (same as Docker)
            'runtime': 'runsc',  # gVisor runtime
        }

        sandbox = GVisorSandbox(agent_id, docker_config)
        await sandbox.start()

        self.active_sandboxes[agent_id] = sandbox
        return sandbox

class Sandbox(ABC):
    """Abstract sandbox."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.running = False

    @abstractmethod
    async def start(self) -> None:
        """Start sandbox."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop sandbox."""
        pass

    @abstractmethod
    async def exec(self, command: List[str]) -> Dict[str, Any]:
        """Execute command in sandbox."""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get resource usage metrics."""
        pass

class DockerSandbox(Sandbox):
    """Docker-based sandbox."""

    def __init__(self, agent_id: str, config: Dict):
        super().__init__(agent_id)
        self.config = config
        self.container = None

    async def start(self) -> None:
        """Start Docker container."""
        import docker
        client = docker.from_env()

        self.container = client.containers.run(**self.config)
        self.running = True

    async def stop(self) -> None:
        """Stop container."""
        if self.container:
            self.container.stop()
            self.running = False

    async def exec(self, command: List[str]) -> Dict[str, Any]:
        """Execute command in container."""
        result = self.container.exec_run(command)

        return {
            'exit_code': result.exit_code,
            'output': result.output.decode()
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get container metrics."""
        stats = self.container.stats(stream=False)

        return {
            'memory_mb': stats['memory_stats']['usage'] / (1024 * 1024),
            'cpu_percent': self._calculate_cpu_percent(stats),
            'network_rx_bytes': stats['networks']['eth0']['rx_bytes'],
            'network_tx_bytes': stats['networks']['eth0']['tx_bytes']
        }
```

**Key Design Decisions:**

1. **Configurable isolation levels**: From none (dev) to Kata (production)
2. **gVisor for production**: Best balance of security + performance
3. **Docker for development**: Easiest to use, good enough isolation
4. **Resource limits enforced**: Memory, CPU, disk, network
5. **No new privileges**: Prevent privilege escalation

---

## Synthesis & Recommendations

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐      ┌──────────────────┐                │
│  │ Workspace       │      │  Project         │                 │
│  │ Manager         │─────▶│  Detector        │                 │
│  │                 │      │                  │                 │
│  │ - Per-agent CWD │      │ - Git root       │                 │
│  │ - Path resolver │      │ - Package files  │                 │
│  │ - State mgmt    │      │ - Monorepo scan  │                 │
│  └─────────────────┘      └──────────────────┘                 │
│           │                                                      │
│           ├──────────────────────────┬──────────────────────┐   │
│           ▼                          ▼                      ▼   │
│  ┌─────────────────┐      ┌──────────────────┐  ┌─────────────┐
│  │ File System     │      │  Checkpoint      │  │  Sandbox    │
│  │ API             │      │  Manager         │  │  Manager    │
│  │                 │      │                  │  │             │
│  │ - Atomic ops    │      │ - Event store    │  │ - gVisor    │
│  │ - Locking       │      │ - Snapshots      │  │ - Kata      │
│  │ - Monitoring    │      │ - Recovery       │  │ - Docker    │
│  │ - Transactions  │      │                  │  │             │
│  └─────────────────┘      └──────────────────┘  └─────────────┘
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation Priority

**Phase 1: Core Context Management (Week 1)**
1. Project abstraction + detection
2. Workspace manager + per-agent CWD
3. Path resolution + canonicalization
4. Basic file operations (read/write)

**Phase 2: File System (Week 2)**
5. Atomic file operations
6. File locking (fcntl-based)
7. Watchdog integration for monitoring
8. Transaction support (begin/commit/rollback)

**Phase 3: Persistence (Week 3)**
9. Event store implementation
10. Checkpoint manager
11. Recovery mechanism
12. State persistence layer

**Phase 4: Sandboxing (Week 4)**
13. Docker sandbox implementation
14. gVisor runtime integration
15. Resource limits + monitoring
16. Security hardening

### Technology Stack

**Required:**
- Python 3.10+ (async/await)
- Watchdog (file monitoring)
- Docker (base isolation)
- Git (repository detection)

**Optional:**
- gVisor (production sandboxing)
- Kata Containers (maximum isolation)
- Redis (shared state across agents)

### Key Metrics

**Performance Targets:**
- Project detection: <100ms
- CWD inference: <50ms
- Atomic file write: <10ms
- Checkpoint creation: <1s
- Sandbox startup: <200ms (gVisor), <500ms (Kata)

**Resource Limits (per agent):**
- Memory: 512MB default, 2GB max
- CPU: 1 core default, 2 cores max
- Disk: 1GB workspace
- File descriptors: 1024

### Risk Mitigation

**Risk 1: Multi-threaded CWD conflicts**
- **Mitigation**: Never use `os.chdir()`, always explicit paths
- **Fallback**: Thread-local storage + locking

**Risk 2: File corruption from concurrent writes**
- **Mitigation**: fcntl-based locking + atomic rename
- **Fallback**: Copy-on-write + transaction log

**Risk 3: Checkpoint/recovery failures**
- **Mitigation**: Event sourcing + incremental checkpoints
- **Fallback**: Full snapshots every N minutes

**Risk 4: Sandbox escapes**
- **Mitigation**: gVisor or Kata for production
- **Fallback**: Seccomp + AppArmor + capabilities

---

## Implementation Checklist

### G1: Project Abstraction ✅

- [x] Define `Project` dataclass
- [x] Implement `ProjectDetector`
- [x] Git repository detection
- [x] Package manager file detection
- [x] Monorepo support
- [ ] Integration tests
- [ ] Performance benchmarks

### G2: CWD Management ✅

- [x] Define `AgentWorkspace` dataclass
- [x] Implement `WorkspaceManager`
- [x] Path resolution + canonicalization
- [x] CWD inference engine
- [x] Thread-safe operations
- [ ] Integration with agent layer
- [ ] Multi-agent CWD isolation tests

### G3: File System Integration ✅

- [x] Atomic file operations (rename pattern)
- [x] fcntl-based file locking
- [x] Watchdog integration
- [x] Transaction support (begin/commit/rollback)
- [x] Operation log for undo
- [ ] Performance optimization
- [ ] Cross-platform testing

### G4: State Persistence ✅

- [x] Event store implementation
- [x] Checkpoint manager
- [x] Event sourcing + replay
- [x] Recovery mechanism
- [x] Compression (gzip)
- [ ] Benchmark checkpoint overhead
- [ ] Test recovery scenarios

### G5: Sandboxing & Isolation ✅

- [x] Docker sandbox implementation
- [x] gVisor integration plan
- [x] Resource limits
- [x] Security hardening
- [ ] Kata Containers support
- [ ] Firecracker exploration
- [ ] Production deployment guide

---

## References

### Project Abstraction
- [How should I organize my source tree? - Software Engineering Stack Exchange](https://softwareengineering.stackexchange.com/questions/81899/how-should-i-organize-my-source-tree)
- [How to Properly Organize Files in Your Codebase - SitePoint](https://www.sitepoint.com/organize-project-files/)
- [Happiness is… a freshly organized codebase | Slack Engineering](https://slack.engineering/happiness-is-a-freshly-organized-codebase/)
- [Monorepos in Git | Atlassian](https://www.atlassian.com/git/tutorials/monorepos)
- [Monorepo.tools](https://monorepo.tools/)

### CWD Management
- [How to specify a local working directory for threading.Thread - Stack Overflow](https://stackoverflow.com/questions/18516271/how-to-specify-a-local-working-directory-for-threading-thread-and-multiprocessin)
- [Can a multi-threaded Python app change the CWD? - Stack Overflow](https://stackoverflow.com/questions/77211228/can-a-multi-threaded-python-app-change-the-cwd)
- [Thread Working Directory - Stack Overflow](https://stackoverflow.com/questions/24491746/thread-working-directory)
- [Context-Aware AI agent: Memory Management - Medium](https://sabber.medium.com/context-aware-ai-agent-memory-management-and-state-tracking-3c904622edd7)
- [Effective context engineering for AI agents - Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

### File System Integration
- [Transactional file access - Apache Commons](https://commons.apache.org/proper/commons-transaction/file/index.html)
- [Transactional NTFS - Wikipedia](https://en.wikipedia.org/wiki/Transactional_NTFS)
- [Implementing atomic file writes - Stack Overflow](https://stackoverflow.com/questions/9096380/implementing-atomic-file-writes-in-a-nontransactional-filesystem)
- [watchdog - PyPI](https://pypi.org/project/watchdog/)
- [watchdog - GitHub](https://github.com/gorakhargosh/watchdog)

### State Persistence
- [Checkpoint-Recovery - CMU](https://users.ece.cmu.edu/~koopman/des_s99/checkpoint/)
- [Checkpointing | Apache Flink](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/datastream/fault-tolerance/checkpointing/)
- [Event Sourcing - Akka](https://doc.akka.io/libraries/akka-core/current/typed/persistence.html)
- [EBS Snapshots: crash-consistent vs. application-consistent - N2W](https://n2ws.com/blog/aws-ebs-snapshot/ebs-snapshots-crash-consistent-vs-application-consistent)

### Sandboxing & Isolation
- [Docker Security Documentation](https://docs.docker.com/engine/security/)
- [Sandboxing Docker Containers - Adobe Tech Blog](https://medium.com/adobetech/sandboxing-docker-containers-56fbe6cf3534)
- [Making Containers More Isolated - Palo Alto Networks](https://unit42.paloaltonetworks.com/making-containers-more-isolated-an-overview-of-sandboxed-container-technologies/)
- [gVisor vs Kata vs Firecracker - Onidel Cloud](https://onidel.com/gvisor-kata-firecracker-2025/)
- [Kata Containers vs gVisor - Stack Overflow](https://stackoverflow.com/questions/50143367/kata-containers-vs-gvisor)

---

**Document Status:** Complete
**Last Updated:** December 2, 2025
**Next Steps:** Begin Phase 1 implementation (Core Context Management)
