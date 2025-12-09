"""
Go Executor for SmartCP

Provides:
- Go code execution
- Go module management
- Async execution
- Error handling
"""

import asyncio
import logging
import tempfile
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class GoExecutionStatus(Enum):
    """Go execution status."""
    PENDING = "pending"
    COMPILING = "compiling"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GoExecutionResult:
    """Go execution result."""
    status: GoExecutionStatus
    output: str = ""
    error: str = ""
    exit_code: Optional[int] = None
    execution_time: float = 0.0


class GoExecutor:
    """Go code executor."""
    
    def __init__(self, timeout: int = 300, go_path: str = "go"):
        self.timeout = timeout
        self.go_path = go_path
        self.executions: Dict[str, GoExecutionResult] = {}
        self.execution_counter = 0
    
    async def execute(self, code: str, module_name: str = "main") -> GoExecutionResult:
        """Execute Go code."""
        import time
        start_time = time.time()
        
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write Go file
                go_file = os.path.join(tmpdir, f"{module_name}.go")
                with open(go_file, 'w') as f:
                    f.write(code)
                
                # Compile and run
                result = await self._compile_and_run(tmpdir, module_name)
                result.execution_time = time.time() - start_time
                
                return result
        
        except Exception as e:
            logger.error(f"Error executing Go code: {e}")
            return GoExecutionResult(
                status=GoExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time
            )
    
    async def _compile_and_run(self, tmpdir: str, module_name: str) -> GoExecutionResult:
        """Compile and run Go code."""
        try:
            # Compile
            compile_result = await self._run_command(
                [self.go_path, "build", "-o", f"{module_name}", f"{module_name}.go"],
                cwd=tmpdir
            )
            
            if compile_result.exit_code != 0:
                return GoExecutionResult(
                    status=GoExecutionStatus.FAILED,
                    error=compile_result.error,
                    exit_code=compile_result.exit_code
                )
            
            # Run
            run_result = await self._run_command(
                [os.path.join(tmpdir, module_name)],
                cwd=tmpdir
            )
            
            return run_result
        
        except Exception as e:
            logger.error(f"Error compiling/running Go code: {e}")
            return GoExecutionResult(
                status=GoExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )
    
    async def _run_command(self, cmd: list, cwd: str = None) -> GoExecutionResult:
        """Run command and capture output."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                output = stdout.decode('utf-8', errors='replace')
                error = stderr.decode('utf-8', errors='replace')
                
                return GoExecutionResult(
                    status=GoExecutionStatus.COMPLETED if process.returncode == 0 else GoExecutionStatus.FAILED,
                    output=output,
                    error=error,
                    exit_code=process.returncode
                )
            
            except asyncio.TimeoutError:
                process.kill()
                return GoExecutionResult(
                    status=GoExecutionStatus.FAILED,
                    error=f"Command timed out after {self.timeout}s",
                    exit_code=-1
                )
        
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return GoExecutionResult(
                status=GoExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )
    
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        module_name: str = "main"
    ) -> GoExecutionResult:
        """Execute Go code with dependencies."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create go.mod
                go_mod = os.path.join(tmpdir, "go.mod")
                with open(go_mod, 'w') as f:
                    f.write(f"module {module_name}\n\ngo 1.21\n\nrequire (\n")
                    for dep, version in dependencies.items():
                        f.write(f"    {dep} {version}\n")
                    f.write(")\n")
                
                # Write Go file
                go_file = os.path.join(tmpdir, f"{module_name}.go")
                with open(go_file, 'w') as f:
                    f.write(code)
                
                # Download dependencies
                await self._run_command(
                    [self.go_path, "mod", "download"],
                    cwd=tmpdir
                )
                
                # Compile and run
                return await self._compile_and_run(tmpdir, module_name)
        
        except Exception as e:
            logger.error(f"Error executing Go code with dependencies: {e}")
            return GoExecutionResult(
                status=GoExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )


# Global executor instance
_go_executor: Optional[GoExecutor] = None


def get_go_executor() -> GoExecutor:
    """Get or create global Go executor."""
    global _go_executor
    if _go_executor is None:
        _go_executor = GoExecutor()
    return _go_executor


async def execute_go(code: str, module_name: str = "main") -> Dict[str, Any]:
    """Execute Go code and return result."""
    executor = get_go_executor()
    result = await executor.execute(code, module_name)
    
    return {
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time
    }


async def execute_go_with_deps(
    code: str,
    dependencies: Dict[str, str],
    module_name: str = "main"
) -> Dict[str, Any]:
    """Execute Go code with dependencies."""
    executor = get_go_executor()
    result = await executor.execute_with_dependencies(code, dependencies, module_name)
    
    return {
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time
    }

