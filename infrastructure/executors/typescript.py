"""
TypeScript Executor for SmartCP

Provides:
- TypeScript code execution
- Node.js integration
- Package management
- Async execution
"""

import asyncio
import logging
import tempfile
import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class TypeScriptExecutionStatus(Enum):
    """TypeScript execution status."""
    PENDING = "pending"
    TRANSPILING = "transpiling"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TypeScriptExecutionResult:
    """TypeScript execution result."""
    status: TypeScriptExecutionStatus
    output: str = ""
    error: str = ""
    exit_code: Optional[int] = None
    execution_time: float = 0.0


class TypeScriptExecutor:
    """TypeScript code executor."""
    
    def __init__(self, timeout: int = 300, node_path: str = "node", npx_path: str = "npx"):
        self.timeout = timeout
        self.node_path = node_path
        self.npx_path = npx_path
        self.executions: Dict[str, TypeScriptExecutionResult] = {}
        self.execution_counter = 0
    
    async def execute(self, code: str, filename: str = "main.ts") -> TypeScriptExecutionResult:
        """Execute TypeScript code."""
        import time
        start_time = time.time()
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write TypeScript file
                ts_file = os.path.join(tmpdir, filename)
                with open(ts_file, 'w') as f:
                    f.write(code)
                
                # Create package.json
                package_json = os.path.join(tmpdir, "package.json")
                with open(package_json, 'w') as f:
                    json.dump({
                        "name": "smartcp-ts",
                        "version": "1.0.0",
                        "type": "module"
                    }, f)
                
                # Execute using ts-node or tsx
                result = await self._execute_typescript(tmpdir, filename)
                result.execution_time = time.time() - start_time
                
                return result
        
        except Exception as e:
            logger.error(f"Error executing TypeScript code: {e}")
            return TypeScriptExecutionResult(
                status=TypeScriptExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time
            )
    
    async def _execute_typescript(self, tmpdir: str, filename: str) -> TypeScriptExecutionResult:
        """Execute TypeScript file."""
        try:
            # Try using tsx (faster)
            result = await self._run_command(
                [self.npx_path, "tsx", filename],
                cwd=tmpdir
            )
            
            if result.exit_code == 0:
                return result
            
            # Fallback to ts-node
            result = await self._run_command(
                [self.npx_path, "ts-node", filename],
                cwd=tmpdir
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error executing TypeScript: {e}")
            return TypeScriptExecutionResult(
                status=TypeScriptExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )
    
    async def _run_command(self, cmd: list, cwd: str = None) -> TypeScriptExecutionResult:
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
                
                return TypeScriptExecutionResult(
                    status=TypeScriptExecutionStatus.COMPLETED if process.returncode == 0 else TypeScriptExecutionStatus.FAILED,
                    output=output,
                    error=error,
                    exit_code=process.returncode
                )
            
            except asyncio.TimeoutError:
                process.kill()
                return TypeScriptExecutionResult(
                    status=TypeScriptExecutionStatus.FAILED,
                    error=f"Command timed out after {self.timeout}s",
                    exit_code=-1
                )
        
        except Exception as e:
            logger.error(f"Error running command: {e}")
            return TypeScriptExecutionResult(
                status=TypeScriptExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )
    
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        filename: str = "main.ts"
    ) -> TypeScriptExecutionResult:
        """Execute TypeScript code with dependencies."""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create package.json with dependencies
                package_json = os.path.join(tmpdir, "package.json")
                with open(package_json, 'w') as f:
                    json.dump({
                        "name": "smartcp-ts",
                        "version": "1.0.0",
                        "type": "module",
                        "dependencies": dependencies
                    }, f)
                
                # Write TypeScript file
                ts_file = os.path.join(tmpdir, filename)
                with open(ts_file, 'w') as f:
                    f.write(code)
                
                # Install dependencies
                await self._run_command(
                    [self.npx_path, "npm", "install"],
                    cwd=tmpdir
                )
                
                # Execute
                return await self._execute_typescript(tmpdir, filename)
        
        except Exception as e:
            logger.error(f"Error executing TypeScript with dependencies: {e}")
            return TypeScriptExecutionResult(
                status=TypeScriptExecutionStatus.FAILED,
                error=str(e),
                exit_code=-1
            )


# Global executor instance
_ts_executor: Optional[TypeScriptExecutor] = None


def get_typescript_executor() -> TypeScriptExecutor:
    """Get or create global TypeScript executor."""
    global _ts_executor
    if _ts_executor is None:
        _ts_executor = TypeScriptExecutor()
    return _ts_executor


async def execute_typescript(code: str, filename: str = "main.ts") -> Dict[str, Any]:
    """Execute TypeScript code and return result."""
    executor = get_typescript_executor()
    result = await executor.execute(code, filename)
    
    return {
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time
    }


async def execute_typescript_with_deps(
    code: str,
    dependencies: Dict[str, str],
    filename: str = "main.ts"
) -> Dict[str, Any]:
    """Execute TypeScript code with dependencies."""
    executor = get_typescript_executor()
    result = await executor.execute_with_dependencies(code, dependencies, filename)
    
    return {
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "exit_code": result.exit_code,
        "execution_time": result.execution_time
    }

