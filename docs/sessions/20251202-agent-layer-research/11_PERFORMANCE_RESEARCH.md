# Performance Research: Agent Layer Phase 4

## Executive Summary

This document presents comprehensive performance research for scaling Agent Layer to 200+ concurrent agents. Based on analysis of the existing codebase, Python asyncio best practices, and industry benchmarks, we identify critical optimization opportunities across five research streams: Memory Management (H1), File Descriptor Management (H2), CPU & Scheduling (H3), Infrastructure Options (H4), and Benchmarking Framework (H5).

**Critical Findings:**
- Current architecture has good foundation but needs optimization for 200+ agent scale
- Memory overhead per asyncio task: ~1KB (manageable for 200 agents)
- File descriptor exhaustion is primary risk area (subprocess management)
- Agent routing caching provides good performance baseline
- Infrastructure containerization essential for isolation

---

## H1: Memory Analysis & Optimization (4h)

### 1.1 Current Memory Usage Patterns

#### Existing Agent Executor Architecture

From `/router/router_core/orchestration/agent_executor.py`:
```python
class AgentExecutor:
    def __init__(self, routing_interface, tool_registry,
                 cache_ttl_seconds=300, enable_caching=True):
        self._routing_cache: dict[str, tuple[RoutingDecision, float]] = {}
        # Each cached decision: ~1-2KB (small overhead)
```

**Memory per Agent Iteration:**
- AgentState: ~200 bytes (agent_id, iteration, context)
- RoutingDecision: ~500 bytes (model, provider, parameters)
- IterationResult: ~1KB (includes execution result)
- Cache entry: ~1-2KB per unique state

#### Industry Benchmarks (2024)

Per [How Much Memory Do You Need to Run 1 Million Concurrent Tasks?](https://hez2010.github.io/async-runtimes-benchmarks-2024/):
- Python asyncio: ~1KB per task overhead
- For 200 agents: ~200KB base overhead (negligible)
- Real memory usage dominated by agent state, not asyncio overhead

### 1.2 Memory Leak Detection Strategy

#### Common Leak Patterns in Agent Systems

1. **Circular References in Agent State**
```python
# Current risk area in agent_executor.py:
self._routing_cache[cache_key] = (decision, time.time())
# Cache grows unbounded if not managed
```

2. **Subprocess Pipe Accumulation**
```python
# From mcp_lifecycle_manager.py:
process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# Each Popen creates 2 pipes (4 file descriptors)
# Not closing pipes = memory + FD leak
```

3. **HTTP Connection Pooling**
- Agent automation and MCP discovery create HTTP clients
- Without proper cleanup: connection pool exhaustion

#### Detection Tooling

**1. Memory Profiling**
```python
# Add to server_control.py
import tracemalloc
import psutil

class MemoryProfiler:
    def __init__(self):
        tracemalloc.start()
        self.snapshots = []

    def take_snapshot(self, label: str):
        snapshot = tracemalloc.take_snapshot()
        self.snapshots.append((label, snapshot))

        # Get current process memory
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            'label': label,
            'rss_mb': mem_info.rss / 1024 / 1024,
            'vms_mb': mem_info.vms / 1024 / 1024,
            'tracemalloc_mb': sum(s.size for s in snapshot.statistics('lineno')) / 1024 / 1024
        }

    def compare_snapshots(self, label1: str, label2: str):
        snap1 = next(s for l, s in self.snapshots if l == label1)
        snap2 = next(s for l, s in self.snapshots if l == label2)

        top_stats = snap2.compare_to(snap1, 'lineno')
        return [
            f"{stat.traceback}: +{stat.size_diff / 1024:.1f} KB"
            for stat in top_stats[:10]
        ]
```

**2. Reference Counting**
```python
import gc
import sys

def find_circular_refs(obj_type):
    """Find circular references for object type."""
    gc.collect()
    objs = [obj for obj in gc.get_objects() if isinstance(obj, obj_type)]

    circular = []
    for obj in objs:
        referrers = gc.get_referrers(obj)
        if any(obj in gc.get_referents(r) for r in referrers):
            circular.append(obj)

    return circular
```

### 1.3 Memory Optimization Playbook

#### Strategy 1: Connection Pooling

**Problem:** Creating new HTTP clients per agent request
```python
# Current pattern in agent_automation.py (implicit):
async def process_user_input(self, user_input: str):
    # Potentially creates new HTTP connections per call
    intent = await self.intent_recognizer.recognize(user_input)
```

**Solution:** Shared connection pool
```python
from aiohttp import ClientSession, TCPConnector

class AgentConnectionPool:
    def __init__(self, max_connections: int = 100):
        self.connector = TCPConnector(limit=max_connections, limit_per_host=10)
        self.session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        if self.session is None or self.session.closed:
            self.session = ClientSession(connector=self.connector)
        return self.session

    async def cleanup(self):
        if self.session:
            await self.session.close()
```

#### Strategy 2: Cache Size Limiting

**Problem:** Unbounded routing cache in AgentExecutor
```python
# Current: cache grows indefinitely
self._routing_cache[cache_key] = (decision, time.time())
```

**Solution:** LRU cache with TTL
```python
from cachetools import TTLCache

class AgentExecutor:
    def __init__(self, routing_interface, tool_registry,
                 cache_ttl_seconds=300, max_cache_size=10000):
        # LRU cache with TTL and size limit
        self._routing_cache = TTLCache(maxsize=max_cache_size, ttl=cache_ttl_seconds)
```

#### Strategy 3: Agent State Recycling

**Problem:** Creating new AgentState objects per iteration
```python
# Each state creation allocates new memory
state = AgentState(agent_id="agent-1", iteration=1, ...)
```

**Solution:** State object pool
```python
from queue import Queue

class AgentStatePool:
    def __init__(self, pool_size: int = 200):
        self.pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self.pool.put(AgentState.__new__(AgentState))

    def acquire(self, agent_id: str, iteration: int, ...) -> AgentState:
        try:
            state = self.pool.get_nowait()
            # Reset state fields
            state.agent_id = agent_id
            state.iteration = iteration
            state.history = []
            state.metadata = {}
            return state
        except:
            # Pool exhausted, create new
            return AgentState(agent_id, iteration, ...)

    def release(self, state: AgentState):
        try:
            self.pool.put_nowait(state)
        except:
            pass  # Pool full, let GC handle it
```

#### Strategy 4: Garbage Collection Tuning

**Problem:** Default GC settings not optimized for agent workload
```python
import gc

# Current: default GC thresholds
# (700, 10, 10) - triggers GC too frequently for long-running agents
```

**Solution:** Tune GC for agent lifecycle
```python
def configure_gc_for_agents():
    """Configure GC for long-running agent workload."""
    # Increase thresholds to reduce GC overhead
    # (10000, 20, 20) - less frequent GC, better for steady-state
    gc.set_threshold(10000, 20, 20)

    # Enable debug mode for leak detection (dev only)
    if __debug__:
        gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS)
```

### 1.4 Memory Profiling Guide

#### Profiling Workflow

**1. Baseline Measurement**
```bash
# Start with memory profiling
python -m memory_profiler server.py

# Or use tracemalloc
python -X tracemalloc=25 server.py
```

**2. Per-Agent Profiling**
```python
@profile  # memory_profiler decorator
async def execute_agent_iteration(state: AgentState):
    # Profile this critical path
    result = await agent_executor.execute_iteration(state)
    return result
```

**3. Continuous Monitoring**
```python
class MemoryMonitor:
    def __init__(self, threshold_mb: float = 500):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process()

    async def monitor_loop(self):
        while True:
            mem_mb = self.process.memory_info().rss / 1024 / 1024
            if mem_mb > self.threshold_mb:
                logger.warning(f"Memory usage high: {mem_mb:.1f} MB")
                # Trigger GC
                gc.collect()
            await asyncio.sleep(10)
```

### 1.5 Memory Optimization Deliverables

**Playbook Structure:**
1. Connection pool pattern for HTTP clients
2. LRU cache with size limits for routing decisions
3. Object pooling for frequently allocated structures
4. GC tuning for long-running agent workloads
5. Memory profiling integration points

**Target Metrics:**
- <500MB total memory for 200 concurrent agents
- <2MB per agent average
- <100ms GC pause time
- Zero memory leaks over 24h operation

---

## H2: File Descriptor Management (3h)

### 2.1 File Descriptor Exhaustion Analysis

#### Root Causes Identified

**1. Subprocess Pipe Leaks**

From `mcp_lifecycle_manager.py`:
```python
process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
# Creates 2 pipes (4 FDs total)
# If not closed: FDs accumulate
```

Per [Python subprocess running out of file descriptors](https://stackoverflow.com/questions/6669996/python-subprocess-running-out-of-file-descriptors):
- Each `subprocess.Popen` with `PIPE` creates 2 pipes
- Pipes remain open until process is garbage collected
- With 200 agents, potentially 400+ FDs from pipes alone

**2. HTTP Connection Accumulation**

From agent automation patterns:
```python
# Implicit HTTP connections in discovery/automation
async def discover_tools(self, intent: Intent) -> List[str]:
    # May create new HTTP connections
    tools = await fetch_tools_from_registry()
```

**3. File Handle Inheritance**

Per [PEP 446 – Make newly created file descriptors non-inheritable](https://peps.python.org/pep-0446/):
- Child processes inherit parent FDs by default
- Can cause FD exhaustion in parent process
- Requires explicit close-on-exec handling

#### System Limits Analysis

**macOS (Darwin 25.0.0):**
```bash
# Soft limit
ulimit -n  # typically 256 or 1024

# Hard limit
ulimit -Hn  # typically 10240

# Per-process limit
sysctl kern.maxfilesperproc  # typically 10240

# System-wide limit
sysctl kern.maxfiles  # typically 12288
```

**For 200 agents:**
- Minimum FDs needed: 200 * 3 (stdin/stdout/stderr) = 600
- With pipes: 200 * 5 = 1000 FDs
- With HTTP connections: 200 * 2 = 400 FDs
- Total minimum: ~2000 FDs
- **Must increase ulimit to at least 4096**

### 2.2 FD Leak Detection Strategy

#### Detection Tools

**1. FD Count Monitoring**
```python
import os
import psutil

class FileDescriptorMonitor:
    def __init__(self, threshold: int = 1000):
        self.threshold = threshold
        self.process = psutil.Process()

    def get_fd_count(self) -> int:
        """Get current file descriptor count."""
        try:
            # Unix-based systems
            return self.process.num_fds()
        except AttributeError:
            # macOS workaround
            return len(os.listdir(f'/proc/{self.process.pid}/fd'))

    def get_fd_details(self) -> List[Dict]:
        """Get detailed FD information."""
        fds = []
        for fd in self.process.open_files():
            fds.append({
                'path': fd.path,
                'fd': fd.fd,
                'mode': fd.mode
            })

        for conn in self.process.connections():
            fds.append({
                'type': 'socket',
                'fd': conn.fd,
                'status': conn.status,
                'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
            })

        return fds

    async def monitor_loop(self):
        """Continuous FD monitoring."""
        while True:
            fd_count = self.get_fd_count()
            if fd_count > self.threshold:
                logger.warning(f"FD count high: {fd_count}")
                details = self.get_fd_details()
                logger.warning(f"FD details: {details[:10]}")  # Log first 10
            await asyncio.sleep(5)
```

**2. Subprocess Tracking**
```python
class SubprocessTracker:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    def register(self, name: str, process: subprocess.Popen):
        """Register subprocess for tracking."""
        self.active_processes[name] = process
        logger.debug(f"Registered subprocess: {name} (PID {process.pid})")

    def cleanup(self, name: str) -> bool:
        """Clean up subprocess and pipes."""
        if name not in self.active_processes:
            return False

        process = self.active_processes[name]
        try:
            # Close pipes explicitly
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
            if process.stdin:
                process.stdin.close()

            # Terminate process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            del self.active_processes[name]
            logger.debug(f"Cleaned up subprocess: {name}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up subprocess {name}: {e}")
            return False

    def cleanup_all(self):
        """Clean up all tracked subprocesses."""
        for name in list(self.active_processes.keys()):
            self.cleanup(name)
```

### 2.3 Connection Pooling Strategy

#### HTTP Connection Pool

**Problem:** Each agent creating new HTTP connections
```python
# Current implicit pattern
async def make_request(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
# Session created and destroyed per request
```

**Solution:** Shared session with connection limits
```python
from aiohttp import ClientSession, TCPConnector, ClientTimeout

class ConnectionPoolManager:
    def __init__(self, max_connections: int = 100,
                 per_host_limit: int = 10,
                 timeout_seconds: int = 30):
        self.connector = TCPConnector(
            limit=max_connections,
            limit_per_host=per_host_limit,
            ttl_dns_cache=300,  # 5 min DNS cache
            enable_cleanup_closed=True
        )
        self.timeout = ClientTimeout(total=timeout_seconds)
        self._session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        """Get or create shared session."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(
                connector=self.connector,
                timeout=self.timeout
            )
        return self._session

    async def cleanup(self):
        """Clean up session and connections."""
        if self._session and not self._session.closed:
            await self._session.close()
            # Wait for connections to close
            await asyncio.sleep(0.25)
```

#### Database Connection Pool

**Problem:** Opening new DB connections per agent
```python
# Potential pattern in adapters
async def query_db(query: str):
    conn = await asyncpg.connect(dsn)
    result = await conn.fetch(query)
    await conn.close()
    return result
```

**Solution:** Connection pool with limits
```python
import asyncpg

class DatabasePool:
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 50):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=30,
            max_queries=50000,  # Recycle after 50k queries
            max_inactive_connection_lifetime=300  # 5 min idle timeout
        )

    async def execute(self, query: str, *args):
        """Execute query using pool."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def cleanup(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
```

### 2.4 Lazy Initialization Pattern

#### Problem: Eager Subprocess Creation

From `mcp_lifecycle_manager.py`:
```python
async def start_mcp(self, name: str, command: List[str]) -> bool:
    # Immediately creates subprocess
    process = subprocess.Popen(command, ...)
    self.processes[name] = process_info
```

#### Solution: On-Demand Subprocess Spawning

```python
class LazySubprocessManager:
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.processes: Dict[str, subprocess.Popen] = {}
        self.idle_processes: asyncio.Queue = asyncio.Queue()

    async def get_or_create_process(self, name: str, command: List[str]) -> subprocess.Popen:
        """Get existing process or create new one."""
        # Check if process already exists
        if name in self.processes and self.processes[name].poll() is None:
            return self.processes[name]

        # Acquire semaphore to limit concurrent processes
        await self.semaphore.acquire()

        try:
            # Create new process
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            self.processes[name] = process
            return process
        finally:
            # Release semaphore after process startup
            asyncio.create_task(self._release_after_delay())

    async def _release_after_delay(self):
        """Release semaphore after small delay."""
        await asyncio.sleep(0.1)
        self.semaphore.release()

    async def cleanup_idle(self, idle_timeout: int = 300):
        """Clean up idle processes."""
        current_time = time.time()
        for name, process in list(self.processes.items()):
            if process.poll() is not None:
                # Process already terminated
                self._cleanup_process(name, process)
            # Add idle tracking logic here

    def _cleanup_process(self, name: str, process: subprocess.Popen):
        """Clean up process and close pipes."""
        try:
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
            if process.stdin:
                process.stdin.close()
            del self.processes[name]
        except Exception as e:
            logger.error(f"Error cleaning up process {name}: {e}")
```

### 2.5 Resource Cleanup Patterns

#### Context Manager for Subprocess Lifecycle

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_subprocess(command: List[str]):
    """Context manager for subprocess with guaranteed cleanup."""
    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        yield process
    finally:
        if process:
            # Close pipes
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
            if process.stdin:
                process.stdin.close()

            # Terminate process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

# Usage
async def run_agent_with_subprocess():
    async with managed_subprocess(['python', 'agent.py']) as process:
        # Work with process
        stdout, stderr = process.communicate()
    # Pipes and process automatically cleaned up
```

#### Graceful Shutdown Handler

```python
import signal

class GracefulShutdown:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.cleanup_handlers: List[Callable] = []

    def register_cleanup(self, handler: Callable):
        """Register cleanup handler."""
        self.cleanup_handlers.append(handler)

    def setup_signals(self):
        """Set up signal handlers."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Execute graceful shutdown."""
        self.shutdown_event.set()

        # Run cleanup handlers
        for handler in self.cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in cleanup handler: {e}")

        logger.info("Graceful shutdown complete")

# Global instance
shutdown_manager = GracefulShutdown()

# Usage
shutdown_manager.register_cleanup(connection_pool.cleanup)
shutdown_manager.register_cleanup(subprocess_tracker.cleanup_all)
shutdown_manager.setup_signals()
```

### 2.6 FD Management Deliverables

**Strategy Document Structure:**
1. FD monitoring and alerting system
2. Connection pooling patterns (HTTP, DB, subprocess)
3. Lazy initialization for on-demand resource allocation
4. Context managers for guaranteed cleanup
5. Graceful shutdown with resource release

**Target Metrics:**
- <1000 FDs for 200 concurrent agents
- Zero FD leaks over 24h operation
- <50ms overhead for connection pool access
- 100% subprocess cleanup success rate

---

## H3: CPU & Scheduling Optimization (4h)

### 3.1 CPU Profiling Techniques

#### Current Execution Patterns

From `agent_executor.py`:
```python
async def execute_iteration(self, state: AgentState) -> IterationResult:
    # Routing overhead
    routing_decision = await self._route_iteration(state)

    # Execution overhead
    execution_result = await self._execute_action(state, routing_decision)
```

**Hot Paths Identified:**
1. Routing decision logic (cache lookups, consensus voting)
2. Tool execution (subprocess spawning, HTTP calls)
3. State serialization/deserialization
4. Metric collection and logging

#### Profiling Tools

**1. cProfile for CPU Profiling**
```python
import cProfile
import pstats
import io

def profile_agent_execution():
    """Profile agent execution with cProfile."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Run agent workload
    asyncio.run(execute_200_agents())

    profiler.disable()

    # Print stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(50)  # Top 50 functions
    print(s.getvalue())
```

**2. py-spy for Live Profiling**
```bash
# Install py-spy
pip install py-spy

# Profile running process
py-spy record -o profile.svg -- python server.py

# Top view (live)
py-spy top --pid <process_id>
```

**3. Async-Specific Profiling**
```python
import asyncio
import time

class AsyncProfiler:
    def __init__(self):
        self.timings = {}

    async def profile_task(self, name: str, coro):
        """Profile async task execution."""
        start = time.perf_counter()
        try:
            result = await coro
            duration = time.perf_counter() - start

            if name not in self.timings:
                self.timings[name] = []
            self.timings[name].append(duration)

            return result
        except Exception as e:
            duration = time.perf_counter() - start
            logger.error(f"Task {name} failed after {duration:.3f}s: {e}")
            raise

    def get_stats(self) -> Dict[str, Dict]:
        """Get timing statistics."""
        stats = {}
        for name, timings in self.timings.items():
            stats[name] = {
                'count': len(timings),
                'mean': sum(timings) / len(timings),
                'min': min(timings),
                'max': max(timings),
                'p50': sorted(timings)[len(timings) // 2],
                'p95': sorted(timings)[int(len(timings) * 0.95)],
                'p99': sorted(timings)[int(len(timings) * 0.99)]
            }
        return stats
```

### 3.2 Bottleneck Identification

#### CPU-Intensive Operations

**1. JSON Serialization**
```python
# Current pattern in agent state
def to_dict(self) -> dict[str, Any]:
    return {
        "agent_id": self.agent_id,
        "context": self.context,  # Large dict
        "history": self.history    # Growing list
    }

# Optimization: Use orjson for faster serialization
import orjson

def to_json_fast(self) -> bytes:
    return orjson.dumps({
        "agent_id": self.agent_id,
        "context": self.context,
        "history": self.history
    })
```

**2. Cache Key Generation**
```python
# Current: JSON serialization for cache key
def _generate_cache_key(self, state: AgentState) -> str:
    key_parts = [
        state.agent_id,
        str(state.action_type.value),
        state.task,
        json.dumps(state.context, sort_keys=True, default=str),
    ]
    return "|".join(key_parts)

# Optimization: Hash-based key
import hashlib

def _generate_cache_key_fast(self, state: AgentState) -> str:
    # Faster: hash context instead of serializing
    context_hash = hashlib.blake2s(
        str(state.context).encode(),
        digest_size=16
    ).hexdigest()

    return f"{state.agent_id}|{state.action_type.value}|{context_hash}"
```

**3. Routing Decision Overhead**
```python
# Current: Sequential routing
async def route_iteration(self, state: AgentState) -> RoutingDecision:
    # Check cache
    # Call routing interface
    # Update cache
    pass

# Optimization: Parallel cache check + prefetch
async def route_iteration_optimized(self, state: AgentState) -> RoutingDecision:
    # Parallel cache check and model prefetch
    cache_task = asyncio.create_task(self._check_cache(state))
    prefetch_task = asyncio.create_task(self._prefetch_model(state))

    cached_result = await cache_task
    if cached_result:
        prefetch_task.cancel()
        return cached_result

    await prefetch_task
    return await self._route_with_prefetch(state)
```

### 3.3 Async/Await Optimization

#### Event Loop Tuning

**Problem:** Default event loop not optimized for high concurrency
```python
# Current: default asyncio event loop
asyncio.run(main())
```

**Solution:** uvloop for better performance
```python
import uvloop

def run_with_uvloop():
    """Run with high-performance uvloop."""
    # Install uvloop as default
    uvloop.install()

    # Run event loop
    asyncio.run(main())

# Benchmark shows 2-4x throughput improvement over default loop
```

#### Task Scheduling Optimization

**Problem:** Too many concurrent tasks overwhelming event loop
```python
# Current: spawn all 200 agents at once
tasks = [execute_agent(i) for i in range(200)]
results = await asyncio.gather(*tasks)
```

**Solution:** Semaphore-based concurrency limiting
```python
class AgentScheduler:
    def __init__(self, max_concurrent: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_agents = 0
        self.completed_agents = 0

    async def execute_agent_limited(self, agent_id: str):
        """Execute agent with concurrency limit."""
        async with self.semaphore:
            self.active_agents += 1
            try:
                result = await execute_agent(agent_id)
                self.completed_agents += 1
                return result
            finally:
                self.active_agents -= 1

    async def execute_all(self, agent_ids: List[str]):
        """Execute all agents with controlled concurrency."""
        tasks = [
            self.execute_agent_limited(agent_id)
            for agent_id in agent_ids
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

#### Avoiding Blocking Operations

**Problem:** Blocking operations in async context
```python
# Bad: blocking file I/O in async function
async def load_config():
    with open('config.json') as f:
        return json.load(f)  # Blocks event loop!
```

**Solution:** Offload to thread pool
```python
import concurrent.futures

class IOExecutor:
    def __init__(self, max_workers: int = 10):
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="io-worker"
        )

    async def read_file(self, path: str) -> str:
        """Read file without blocking event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._read_file_sync,
            path
        )

    def _read_file_sync(self, path: str) -> str:
        with open(path) as f:
            return f.read()

    def shutdown(self):
        self.executor.shutdown(wait=True)
```

### 3.4 Multi-Processing vs Threading

#### Analysis

For **200 concurrent agents**:

**Asyncio (Current):**
- ✅ Low memory overhead (~200KB for 200 agents)
- ✅ Efficient for I/O-bound workloads (HTTP, DB, subprocess)
- ✅ Simple shared state management
- ❌ Limited by GIL for CPU-intensive work
- **Recommendation: PRIMARY APPROACH**

**Threading:**
- ❌ Higher overhead (~8MB per thread * 200 = 1.6GB)
- ❌ Still limited by GIL
- ❌ Complex synchronization
- **Recommendation: AVOID for agent execution**
- **Use case: Offload blocking I/O only (via executor)**

**Multi-Processing:**
- ✅ True parallelism for CPU-intensive work
- ✅ Bypasses GIL
- ❌ Very high overhead (~50MB per process * 200 = 10GB)
- ❌ Complex IPC and state sharing
- ❌ Slower startup time
- **Recommendation: HYBRID for CPU-heavy subtasks only**

#### Hybrid Pattern

```python
from multiprocessing import Pool

class HybridExecutor:
    def __init__(self, process_pool_size: int = 4):
        # Small process pool for CPU-intensive work
        self.process_pool = Pool(processes=process_pool_size)

        # Thread pool for blocking I/O
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=10
        )

    async def execute_cpu_intensive(self, func, *args):
        """Offload CPU-intensive work to process pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # Use default executor
            self.process_pool.apply,
            func,
            args
        )

    async def execute_blocking_io(self, func, *args):
        """Offload blocking I/O to thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool,
            func,
            *args
        )

    def cleanup(self):
        self.process_pool.close()
        self.process_pool.join()
        self.thread_pool.shutdown(wait=True)

# Usage
executor = HybridExecutor()

# CPU-intensive: use process pool
result = await executor.execute_cpu_intensive(
    compute_embeddings,
    large_dataset
)

# Blocking I/O: use thread pool
config = await executor.execute_blocking_io(
    json.load,
    open('config.json')
)
```

### 3.5 CPU Affinity Strategies

#### Linux-Specific Optimizations

**Problem:** OS scheduler moves tasks between cores, causing cache misses

**Solution:** Pin critical agents to specific CPU cores
```python
import os

def set_cpu_affinity(core_ids: List[int]):
    """Set CPU affinity for current process (Linux only)."""
    if hasattr(os, 'sched_setaffinity'):
        os.sched_setaffinity(0, core_ids)
        logger.info(f"Set CPU affinity to cores: {core_ids}")

def configure_agent_affinity():
    """Configure CPU affinity for agent system."""
    # Get available cores
    num_cores = os.cpu_count()

    # Reserve cores for agent execution
    # Example: 8-core system
    # - Cores 0-1: System, networking
    # - Cores 2-7: Agent execution
    agent_cores = list(range(2, num_cores))

    set_cpu_affinity(agent_cores)
```

#### macOS Considerations

**Note:** macOS does not support `sched_setaffinity`
- Use process priority instead:
```python
import os

def set_process_priority():
    """Set process priority (macOS compatible)."""
    # Lower nice value = higher priority
    os.nice(-10)  # Requires elevated privileges
```

### 3.6 CPU Optimization Deliverables

**Optimization Guide Structure:**
1. Profiling toolkit (cProfile, py-spy, async profiler)
2. Hot path optimizations (JSON, hashing, routing)
3. Event loop tuning (uvloop, semaphores)
4. Hybrid execution (async + thread pool + process pool)
5. CPU affinity configuration (Linux)

**Target Metrics:**
- <10ms routing decision latency (cached)
- <100ms routing decision latency (uncached)
- <5% CPU usage per agent (I/O-bound workload)
- 50-agent concurrency per core

---

## H4: Infrastructure Options (4h)

### 4.1 Docker Containerization

#### Current Deployment Model

**Monolithic Process:**
- All 200 agents in single Python process
- ✅ Simple deployment
- ✅ Low overhead
- ❌ No isolation between agents
- ❌ One agent crash = all agents affected
- ❌ Difficult resource limiting per agent

#### Container Architecture

**Option 1: Agent per Container**
```dockerfile
# Dockerfile for single agent
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent_executor.py .
COPY tools/ ./tools/
COPY infrastructure/ ./infrastructure/

# Set resource limits
ENV AGENT_ID=${AGENT_ID}
ENV MEMORY_LIMIT=100M
ENV CPU_LIMIT=0.5

# Run agent
CMD ["python", "agent_executor.py", "--agent-id", "${AGENT_ID}"]
```

**Docker Compose for 200 agents:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-template:
    image: agent-executor:latest
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 100M
        reservations:
          cpus: '0.25'
          memory: 50M
    restart: on-failure
    networks:
      - agent-network

  # Generate 200 agent services
  # (Use script to generate or Docker Swarm for scaling)

networks:
  agent-network:
    driver: bridge
```

**Pros:**
- ✅ Strong isolation between agents
- ✅ Individual resource limiting
- ✅ Fault tolerance (one agent crash ≠ all agents)
- ✅ Easy scaling (add/remove containers)

**Cons:**
- ❌ High overhead (200 containers * ~50MB = 10GB)
- ❌ Complex orchestration
- ❌ Network latency for inter-agent communication

**Recommendation:** Use for production with <50 agents or high-value agents requiring isolation

**Option 2: Agent Pool per Container**
```dockerfile
# Dockerfile for agent pool (20 agents per container)
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Agent pool configuration
ENV AGENTS_PER_POOL=20
ENV POOL_ID=${POOL_ID}

# Run agent pool
CMD ["python", "agent_pool.py", "--pool-id", "${POOL_ID}", "--agents", "${AGENTS_PER_POOL}"]
```

**Agent Pool Implementation:**
```python
class AgentPool:
    def __init__(self, pool_id: str, num_agents: int):
        self.pool_id = pool_id
        self.num_agents = num_agents
        self.agents = []

    async def start(self):
        """Start all agents in pool."""
        for i in range(self.num_agents):
            agent_id = f"{self.pool_id}-agent-{i}"
            agent = AgentExecutor(
                routing_interface=routing,
                tool_registry=tools
            )
            self.agents.append((agent_id, agent))

    async def execute_all(self):
        """Execute all agents concurrently."""
        tasks = [
            agent.execute_iteration(
                AgentState(agent_id=agent_id, ...)
            )
            for agent_id, agent in self.agents
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

**Pros:**
- ✅ Moderate isolation (20 agents per container)
- ✅ Lower overhead (10 containers * 200MB = 2GB)
- ✅ Easier orchestration
- ✅ Lower network latency

**Cons:**
- ❌ Agent group failure (20 agents affected per crash)
- ❌ Less granular resource control

**Recommendation:** PRIMARY APPROACH for 200-agent deployment

### 4.2 Kubernetes Orchestration

#### Kubernetes Manifest

**Deployment for Agent Pools:**
```yaml
# agent-pool-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-pool
  labels:
    app: smartcp
    component: agent-pool
spec:
  replicas: 10  # 10 pools * 20 agents = 200 agents
  selector:
    matchLabels:
      app: smartcp
      component: agent-pool
  template:
    metadata:
      labels:
        app: smartcp
        component: agent-pool
    spec:
      containers:
      - name: agent-pool
        image: smartcp/agent-pool:latest
        resources:
          requests:
            memory: "200Mi"
            cpu: "500m"
          limits:
            memory: "500Mi"
            cpu: "1000m"
        env:
        - name: AGENTS_PER_POOL
          value: "20"
        - name: POOL_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: ROUTING_ENDPOINT
          value: "http://routing-service:8000"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

**Service for Agent Communication:**
```yaml
# agent-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: agent-pool-service
spec:
  selector:
    app: smartcp
    component: agent-pool
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

**Horizontal Pod Autoscaler:**
```yaml
# agent-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-pool-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-pool
  minReplicas: 5
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Pros:**
- ✅ Automatic scaling based on load
- ✅ Self-healing (automatic restart on failure)
- ✅ Load balancing across pools
- ✅ Rolling updates with zero downtime
- ✅ Resource quotas and limits

**Cons:**
- ❌ Complex setup and operations
- ❌ Requires Kubernetes expertise
- ❌ Additional infrastructure cost

**Recommendation:** Use for production at scale (>100 agents) with team Kubernetes expertise

### 4.3 Lightweight VMs (Firecracker)

#### Firecracker microVM Architecture

[AWS Firecracker](https://firecracker-microvm.github.io/):
- Lightweight virtualization (boot in <125ms)
- Minimal memory overhead (~5MB per microVM)
- Strong isolation (KVM-based)

**Use Case for SmartCP:**
```python
# firecracker_manager.py
import json
import subprocess

class FirecrackerManager:
    def __init__(self, socket_path: str = "/tmp/firecracker.socket"):
        self.socket_path = socket_path

    def create_microvm(self, vm_id: str, memory_mb: int = 128, vcpus: int = 1):
        """Create Firecracker microVM for agent."""
        config = {
            "boot-source": {
                "kernel_image_path": "/path/to/vmlinux",
                "boot_args": "console=ttyS0 reboot=k panic=1"
            },
            "drives": [{
                "drive_id": "rootfs",
                "path_on_host": f"/path/to/agent-{vm_id}.ext4",
                "is_root_device": True,
                "is_read_only": False
            }],
            "machine-config": {
                "vcpu_count": vcpus,
                "mem_size_mib": memory_mb
            },
            "network-interfaces": [{
                "iface_id": "eth0",
                "guest_mac": f"AA:FC:00:00:00:{vm_id:02d}",
                "host_dev_name": f"tap{vm_id}"
            }]
        }

        # Write config
        with open(f"/tmp/vm-{vm_id}-config.json", "w") as f:
            json.dump(config, f)

        # Start Firecracker
        subprocess.Popen([
            "firecracker",
            "--api-sock", self.socket_path,
            "--config-file", f"/tmp/vm-{vm_id}-config.json"
        ])
```

**Pros:**
- ✅ Strong isolation (VM-level)
- ✅ Fast startup (<125ms)
- ✅ Low overhead (~5MB per microVM)
- ✅ Secure multi-tenancy

**Cons:**
- ❌ Linux-only (KVM required)
- ❌ Complex setup
- ❌ Limited ecosystem compared to Docker
- ❌ Requires kernel expertise for optimization

**Recommendation:** Future consideration for high-security multi-tenant deployments

### 4.4 Cloud Platform Comparison

#### AWS

**ECS Fargate:**
```yaml
# task-definition.json
{
  "family": "agent-pool",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "agent-pool",
    "image": "smartcp/agent-pool:latest",
    "memory": 1024,
    "cpu": 512,
    "essential": true,
    "environment": [
      {"name": "AGENTS_PER_POOL", "value": "20"}
    ]
  }]
}
```

**Pros:**
- ✅ Serverless container execution
- ✅ No cluster management
- ✅ Pay-per-use billing

**Cons:**
- ❌ Higher cost than EC2
- ❌ Cold start latency

**Cost Estimate (200 agents):**
- 10 Fargate tasks (20 agents each)
- 0.5 vCPU + 1GB memory per task
- ~$0.04/hour per task
- Total: ~$300/month

#### GCP

**Cloud Run:**
```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: agent-pool
spec:
  template:
    spec:
      containerConcurrency: 20  # 20 agents per instance
      containers:
      - image: gcr.io/project/agent-pool:latest
        resources:
          limits:
            memory: 1Gi
            cpu: 1000m
```

**Pros:**
- ✅ Auto-scaling to zero
- ✅ Simple deployment
- ✅ Request-based pricing

**Cons:**
- ❌ Stateless model (not ideal for long-running agents)
- ❌ 15-minute request timeout

**Cost Estimate:**
- Similar to Fargate (~$300/month)

#### Azure

**Container Instances:**
```yaml
# container-group.yaml
apiVersion: '2019-12-01'
location: eastus
name: agent-pool
properties:
  containers:
  - name: agent-pool
    properties:
      image: smartcp/agent-pool:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 1
```

**Pros:**
- ✅ Fast deployment
- ✅ Per-second billing

**Cons:**
- ❌ Less mature than AWS/GCP container services

**Cost Estimate:**
- Similar pricing (~$300/month)

### 4.5 Cost Analysis

#### On-Premise Deployment

**Hardware Requirements:**
- CPU: 16 cores (Intel Xeon or AMD EPYC)
- Memory: 32GB RAM
- Storage: 500GB SSD
- Network: 1Gbps

**Cost:**
- Initial: $3,000-5,000 (server)
- Ongoing: $50-100/month (power, cooling)
- **Total Year 1:** ~$4,200

#### Cloud Deployment

**AWS EC2 (c6i.4xlarge):**
- 16 vCPUs, 32GB RAM
- On-Demand: ~$0.68/hour = $490/month
- Reserved (1-year): ~$0.41/hour = $295/month
- **Total Year 1:** ~$3,540 (reserved)

**Cloud Fargate/Run:**
- 10 tasks * $0.04/hour = $0.40/hour
- **Total:** ~$300/month = $3,600/year

#### Recommendation Matrix

| Scale | Environment | Recommendation |
|-------|-------------|----------------|
| <50 agents | Development | Docker Compose on single host |
| 50-100 agents | Production (low) | EC2 + Docker Compose or ECS |
| 100-200 agents | Production (med) | Kubernetes (EKS/GKE/AKS) |
| 200+ agents | Production (high) | Kubernetes + HPA + spot instances |

### 4.6 Infrastructure Deliverables

**Recommendations Document:**
1. Agent Pool Architecture (20 agents per container)
2. Docker containerization (Dockerfile, compose)
3. Kubernetes manifests (deployment, service, HPA)
4. Cloud platform comparison (AWS, GCP, Azure)
5. Cost analysis and recommendations

**Implementation Priority:**
1. **Phase 1 (Week 1-2):** Docker containerization with agent pools
2. **Phase 2 (Week 3-4):** Local Kubernetes deployment (minikube/kind)
3. **Phase 3 (Month 2):** Cloud deployment (EKS or GKE)
4. **Phase 4 (Month 3):** Auto-scaling and monitoring

**Target Infrastructure:**
- 10 agent pool containers (20 agents each)
- <2GB total memory
- <4 cores total CPU
- <$300/month cloud cost
- 99.9% uptime SLA

---

## H5: Benchmarking Framework (2h)

### 5.1 Performance Metrics Definition

#### Core Metrics

**1. Throughput Metrics**
```python
@dataclass
class ThroughputMetrics:
    """Throughput measurements."""
    agents_per_second: float
    iterations_per_second: float
    requests_per_second: float
    total_agents: int
    total_iterations: int
    duration_seconds: float
```

**2. Latency Metrics**
```python
@dataclass
class LatencyMetrics:
    """Latency measurements (milliseconds)."""
    routing_p50: float
    routing_p95: float
    routing_p99: float
    execution_p50: float
    execution_p95: float
    execution_p99: float
    end_to_end_p50: float
    end_to_end_p95: float
    end_to_end_p99: float
```

**3. Resource Metrics**
```python
@dataclass
class ResourceMetrics:
    """Resource utilization measurements."""
    memory_mb: float
    memory_peak_mb: float
    cpu_percent: float
    cpu_peak_percent: float
    file_descriptors: int
    file_descriptors_peak: int
    thread_count: int
    asyncio_tasks: int
```

**4. Reliability Metrics**
```python
@dataclass
class ReliabilityMetrics:
    """Reliability measurements."""
    success_rate: float  # 0.0 to 1.0
    error_rate: float
    timeout_rate: float
    retry_count: int
    cache_hit_rate: float
```

### 5.2 Load Testing Harness

#### Load Test Configuration

```python
@dataclass
class LoadTestConfig:
    """Load test configuration."""
    num_agents: int = 200
    duration_seconds: int = 300  # 5 minutes
    ramp_up_seconds: int = 30
    workload_type: str = "constant"  # constant, ramp, spike, stress
    target_rps: float = 100.0  # requests per second

    # Agent behavior
    think_time_ms: int = 100
    actions_per_agent: int = 10

    # Thresholds
    max_latency_ms: float = 1000
    max_error_rate: float = 0.01  # 1%
    max_memory_mb: float = 2000
```

#### Load Generator

```python
class LoadGenerator:
    """Generate load for agent system."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.executor = None
        self.metrics_collector = MetricsCollector()

    async def run_constant_load(self):
        """Run constant load test."""
        # Ramp up
        agents = await self._ramp_up()

        # Sustain load
        start_time = time.time()
        while time.time() - start_time < self.config.duration_seconds:
            tasks = [
                self._execute_agent_iteration(agent_id)
                for agent_id in agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Record metrics
            for result in results:
                if isinstance(result, Exception):
                    self.metrics_collector.record_error()
                else:
                    self.metrics_collector.record_success(result)

            # Think time
            await asyncio.sleep(self.config.think_time_ms / 1000)

        # Ramp down
        await self._ramp_down()

        return self.metrics_collector.get_summary()

    async def run_ramp_load(self):
        """Run ramping load test."""
        start_agents = 10
        increment = (self.config.num_agents - start_agents) / 10

        for i in range(10):
            num_agents = int(start_agents + i * increment)
            logger.info(f"Ramping to {num_agents} agents")

            # Run with current load level
            await self._run_load_level(num_agents, duration=30)

        return self.metrics_collector.get_summary()

    async def run_spike_load(self):
        """Run spike load test."""
        # Baseline
        await self._run_load_level(50, duration=60)

        # Spike
        logger.info("Executing spike")
        await self._run_load_level(self.config.num_agents, duration=30)

        # Recovery
        await self._run_load_level(50, duration=60)

        return self.metrics_collector.get_summary()

    async def _execute_agent_iteration(self, agent_id: str) -> IterationResult:
        """Execute single agent iteration."""
        state = AgentState(
            agent_id=agent_id,
            iteration=self.metrics_collector.get_iteration(agent_id),
            action_type=ActionType.THINK,
            task="benchmark_task",
            context={"benchmark": True}
        )

        start_time = time.perf_counter()
        try:
            result = await self.executor.execute_iteration(state)
            latency_ms = (time.perf_counter() - start_time) * 1000
            result.total_latency_ms = latency_ms
            return result
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Agent {agent_id} failed after {latency_ms:.1f}ms: {e}")
            raise

    async def _ramp_up(self) -> List[str]:
        """Ramp up agents gradually."""
        agents = []
        increment = self.config.num_agents / 10

        for i in range(10):
            batch_size = int(increment)
            batch = [f"agent-{len(agents) + j}" for j in range(batch_size)]
            agents.extend(batch)

            logger.info(f"Ramped up to {len(agents)} agents")
            await asyncio.sleep(self.config.ramp_up_seconds / 10)

        return agents

    async def _ramp_down(self):
        """Ramp down gracefully."""
        logger.info("Ramping down")
        await asyncio.sleep(self.config.ramp_up_seconds)
```

### 5.3 Metrics Collection

#### Metrics Collector

```python
class MetricsCollector:
    """Collect and aggregate metrics during load test."""

    def __init__(self):
        self.latencies: List[float] = []
        self.routing_latencies: List[float] = []
        self.execution_latencies: List[float] = []
        self.successes = 0
        self.errors = 0
        self.timeouts = 0
        self.start_time = time.time()
        self.agent_iterations: Dict[str, int] = {}

        # Resource tracking
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self.fd_samples: List[int] = []

        # Start resource monitoring
        asyncio.create_task(self._monitor_resources())

    def record_success(self, result: IterationResult):
        """Record successful iteration."""
        self.successes += 1
        self.latencies.append(result.total_latency_ms)
        self.routing_latencies.append(result.routing_decision.routing_latency_ms)
        self.execution_latencies.append(result.execution_latency_ms)

        # Track agent iteration count
        if result.agent_id not in self.agent_iterations:
            self.agent_iterations[result.agent_id] = 0
        self.agent_iterations[result.agent_id] += 1

    def record_error(self):
        """Record error."""
        self.errors += 1

    def record_timeout(self):
        """Record timeout."""
        self.timeouts += 1

    async def _monitor_resources(self):
        """Monitor resource usage."""
        process = psutil.Process()

        while True:
            try:
                # Memory
                mem_mb = process.memory_info().rss / 1024 / 1024
                self.memory_samples.append(mem_mb)

                # CPU
                cpu_pct = process.cpu_percent(interval=0.1)
                self.cpu_samples.append(cpu_pct)

                # File descriptors
                try:
                    fd_count = process.num_fds()
                    self.fd_samples.append(fd_count)
                except:
                    pass

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                break

    def get_iteration(self, agent_id: str) -> int:
        """Get current iteration for agent."""
        return self.agent_iterations.get(agent_id, 0) + 1

    def get_summary(self) -> Dict:
        """Get metrics summary."""
        duration = time.time() - self.start_time
        total_requests = self.successes + self.errors + self.timeouts

        return {
            'throughput': {
                'agents_per_second': len(self.agent_iterations) / duration,
                'iterations_per_second': self.successes / duration,
                'total_iterations': self.successes,
                'duration_seconds': duration
            },
            'latency': {
                'routing_p50': self._percentile(self.routing_latencies, 50),
                'routing_p95': self._percentile(self.routing_latencies, 95),
                'routing_p99': self._percentile(self.routing_latencies, 99),
                'execution_p50': self._percentile(self.execution_latencies, 50),
                'execution_p95': self._percentile(self.execution_latencies, 95),
                'execution_p99': self._percentile(self.execution_latencies, 99),
                'end_to_end_p50': self._percentile(self.latencies, 50),
                'end_to_end_p95': self._percentile(self.latencies, 95),
                'end_to_end_p99': self._percentile(self.latencies, 99)
            },
            'resources': {
                'memory_mb': self._average(self.memory_samples),
                'memory_peak_mb': max(self.memory_samples) if self.memory_samples else 0,
                'cpu_percent': self._average(self.cpu_samples),
                'cpu_peak_percent': max(self.cpu_samples) if self.cpu_samples else 0,
                'file_descriptors': self._average(self.fd_samples),
                'file_descriptors_peak': max(self.fd_samples) if self.fd_samples else 0
            },
            'reliability': {
                'success_rate': self.successes / total_requests if total_requests > 0 else 0,
                'error_rate': self.errors / total_requests if total_requests > 0 else 0,
                'timeout_rate': self.timeouts / total_requests if total_requests > 0 else 0
            }
        }

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _average(self, values: List[float]) -> float:
        """Calculate average."""
        return sum(values) / len(values) if values else 0.0
```

### 5.4 Regression Detection

#### Baseline Storage

```python
class PerformanceBaseline:
    """Store and compare performance baselines."""

    def __init__(self, baseline_file: str = "performance_baseline.json"):
        self.baseline_file = baseline_file
        self.baselines: Dict[str, Dict] = self._load_baselines()

    def _load_baselines(self) -> Dict:
        """Load baselines from file."""
        try:
            with open(self.baseline_file) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_baseline(self, name: str, metrics: Dict):
        """Save baseline metrics."""
        self.baselines[name] = {
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }

        with open(self.baseline_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)

        logger.info(f"Saved baseline: {name}")

    def compare(self, name: str, current_metrics: Dict) -> Dict:
        """Compare current metrics to baseline."""
        if name not in self.baselines:
            logger.warning(f"No baseline found for: {name}")
            return {}

        baseline = self.baselines[name]['metrics']

        comparisons = {}

        # Compare throughput
        throughput_diff = (
            (current_metrics['throughput']['iterations_per_second'] -
             baseline['throughput']['iterations_per_second']) /
            baseline['throughput']['iterations_per_second'] * 100
        )
        comparisons['throughput_change_pct'] = throughput_diff

        # Compare latency
        latency_diff = (
            (current_metrics['latency']['end_to_end_p95'] -
             baseline['latency']['end_to_end_p95']) /
            baseline['latency']['end_to_end_p95'] * 100
        )
        comparisons['latency_p95_change_pct'] = latency_diff

        # Compare memory
        memory_diff = (
            (current_metrics['resources']['memory_peak_mb'] -
             baseline['resources']['memory_peak_mb']) /
            baseline['resources']['memory_peak_mb'] * 100
        )
        comparisons['memory_change_pct'] = memory_diff

        # Detect regressions
        regressions = []
        if throughput_diff < -10:
            regressions.append(f"Throughput decreased by {abs(throughput_diff):.1f}%")
        if latency_diff > 20:
            regressions.append(f"Latency increased by {latency_diff:.1f}%")
        if memory_diff > 20:
            regressions.append(f"Memory usage increased by {memory_diff:.1f}%")

        comparisons['regressions'] = regressions
        comparisons['baseline_timestamp'] = self.baselines[name]['timestamp']

        return comparisons
```

### 5.5 Continuous Monitoring

#### Monitoring Integration

```python
class ContinuousMonitor:
    """Continuous performance monitoring."""

    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self.metrics_history: List[Dict] = []
        self.alert_thresholds = {
            'memory_mb': 1500,
            'cpu_percent': 80,
            'error_rate': 0.05,  # 5%
            'latency_p95_ms': 1000
        }

    async def monitor_loop(self, executor: AgentExecutor):
        """Continuous monitoring loop."""
        while True:
            try:
                # Collect metrics
                metrics = await self._collect_metrics(executor)
                self.metrics_history.append(metrics)

                # Check thresholds
                alerts = self._check_thresholds(metrics)
                if alerts:
                    await self._send_alerts(alerts)

                # Persist metrics
                await self._persist_metrics(metrics)

                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.interval_seconds)

    async def _collect_metrics(self, executor: AgentExecutor) -> Dict:
        """Collect current metrics."""
        process = psutil.Process()

        executor_metrics = executor.get_metrics()

        return {
            'timestamp': datetime.now().isoformat(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(interval=0.1),
            'cache_hit_rate': executor_metrics['cache_hit_rate'],
            'total_iterations': executor_metrics['total_iterations']
        }

    def _check_thresholds(self, metrics: Dict) -> List[str]:
        """Check if any thresholds exceeded."""
        alerts = []

        for key, threshold in self.alert_thresholds.items():
            if key in metrics and metrics[key] > threshold:
                alerts.append(f"{key} exceeded threshold: {metrics[key]} > {threshold}")

        return alerts

    async def _send_alerts(self, alerts: List[str]):
        """Send alerts."""
        for alert in alerts:
            logger.warning(f"ALERT: {alert}")
            # Could integrate with PagerDuty, Slack, etc.

    async def _persist_metrics(self, metrics: Dict):
        """Persist metrics to time-series database."""
        # Could integrate with Prometheus, InfluxDB, etc.
        pass
```

### 5.6 Benchmarking Deliverables

**Framework Structure:**
1. Metrics definitions (throughput, latency, resources, reliability)
2. Load testing harness (constant, ramp, spike, stress)
3. Metrics collection and aggregation
4. Baseline storage and comparison
5. Regression detection
6. Continuous monitoring integration

**Usage Example:**
```python
async def run_benchmark():
    # Configure load test
    config = LoadTestConfig(
        num_agents=200,
        duration_seconds=300,
        workload_type="constant"
    )

    # Create load generator
    generator = LoadGenerator(config)

    # Run load test
    logger.info("Starting load test")
    results = await generator.run_constant_load()

    # Compare to baseline
    baseline = PerformanceBaseline()
    comparison = baseline.compare("v1.0.0", results)

    if comparison.get('regressions'):
        logger.error(f"Performance regressions detected: {comparison['regressions']}")
    else:
        logger.info("No performance regressions")
        # Save as new baseline
        baseline.save_baseline("v1.1.0", results)

    return results, comparison

# Run benchmark
results, comparison = asyncio.run(run_benchmark())
print(json.dumps(results, indent=2))
print(json.dumps(comparison, indent=2))
```

**Target Benchmarks (200 agents):**
- Throughput: >100 iterations/second
- Latency P95: <500ms (cached), <1000ms (uncached)
- Memory: <2GB total
- CPU: <70% sustained
- Error rate: <1%
- Cache hit rate: >80%

---

## References & Sources

### Memory Optimization
- [Yes, Python Scales: Lessons from Handling Millions of API Calls a Day](https://medium.com/@thiagosalvatore/yes-python-scales-lessons-from-handling-millions-of-api-calls-a-day-f6b38a9b3484)
- [How Much Memory Do You Need in 2024 to Run 1 Million Concurrent Tasks?](https://hez2010.github.io/async-runtimes-benchmarks-2024/)
- [Optimize I/O Applications with Async Python Techniques](https://www.clariontech.com/blog/adopting-async/python-for-i-o-applications)
- [Python asyncio sleep is big memory usage - Stack Overflow](https://stackoverflow.com/questions/75949130/python-asyncio-sleep-is-big-memory-usage)

### File Descriptor Management
- [Detect file handle leaks in python? - Stack Overflow](https://stackoverflow.com/questions/561988/detect-file-handle-leaks-in-python)
- [PEP 446 – Make newly created file descriptors non-inheritable](https://peps.python.org/pep-0446/)
- [Python subprocess running out of file descriptors - Stack Overflow](https://stackoverflow.com/questions/6669996/python-subprocess-running-out-of-file-descriptors)
- [PEP 433 – Easier suppression of file descriptor inheritance](https://peps.python.org/pep-0433/)

### Agent Orchestration & Benchmarking
- [Top 5 Open-Source Agentic Frameworks](https://research.aimultiple.com/agentic-frameworks/)
- [AI Agent Orchestration Frameworks: Which One Works Best for You? – n8n Blog](https://blog.n8n.io/ai-agent-orchestration-frameworks/)
- [GitHub - AgentOps-AI/agentops: Python SDK for AI agent monitoring](https://github.com/AgentOps-AI/agentops)
- [Top 10+ Agentic Orchestration Frameworks & Tools](https://research.aimultiple.com/agentic-orchestration/)

### General Performance
- [Scaling asyncio on Free-Threaded Python | Labs](https://labs.quansight.org/blog/scaling-asyncio-on-free-threaded-python)
- [Optimizing Python for Concurrency: A Deep Dive into Asyncio, Threads, and Multiprocessing](https://medium.com/@sohail_saifi/optimizing-python-for-concurrency-a-deep-dive-into-asyncio-threads-and-multiprocessing-2bbde8459304)

---

## Next Steps

### Immediate Actions (Week 1)

1. **Implement Memory Profiling**
   - Add `tracemalloc` integration to server_control.py
   - Create MemoryMonitor class
   - Add memory alerts

2. **Implement FD Monitoring**
   - Add FileDescriptorMonitor to server lifecycle
   - Create SubprocessTracker for pipe management
   - Add FD alerts

3. **Create Benchmarking Harness**
   - Implement LoadGenerator
   - Implement MetricsCollector
   - Run baseline benchmark (50 agents)

### Short-Term (Week 2-4)

4. **Optimize Hot Paths**
   - Replace JSON with orjson for serialization
   - Implement hash-based cache keys
   - Add connection pooling

5. **Infrastructure Prototype**
   - Create Dockerfile for agent pools
   - Create docker-compose.yml
   - Test with 10 agent pools (200 agents)

### Medium-Term (Month 2-3)

6. **Production Deployment**
   - Kubernetes manifests
   - Cloud deployment (EKS or GKE)
   - Auto-scaling setup

7. **Continuous Monitoring**
   - Prometheus integration
   - Grafana dashboards
   - Alert rules

---

## Conclusion

This research provides a comprehensive foundation for scaling Agent Layer to 200+ concurrent agents. Key findings:

1. **Memory:** Python asyncio provides excellent memory efficiency (~1KB/task). Focus on connection pooling and cache size limiting.

2. **File Descriptors:** Primary risk area. Requires explicit subprocess cleanup, connection pooling, and FD monitoring.

3. **CPU:** Asyncio + uvloop optimal for I/O-bound agent workload. Use thread pool for blocking I/O, avoid multiprocessing overhead.

4. **Infrastructure:** Agent pool architecture (20 agents/container) provides best balance of isolation, overhead, and cost.

5. **Benchmarking:** Comprehensive framework enables regression detection and continuous optimization.

**Estimated Timeline:**
- Week 1-2: Profiling and monitoring
- Week 3-4: Optimization implementation
- Month 2: Infrastructure containerization
- Month 3: Production deployment

**Success Criteria:**
- 200 concurrent agents running smoothly
- <2GB total memory
- <1000 file descriptors
- >100 iterations/second throughput
- <500ms P95 latency
- 99.9% uptime

This research enables confident scaling of Agent Layer to production requirements.
