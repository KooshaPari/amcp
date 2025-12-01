"""
Bash Executor for SmartCP

Provides:
- Bash command execution
- Command validation
- Job management
- Output streaming
- Error handling
"""

import asyncio
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BashJob:
    """Bash job representation."""
    job_id: str
    command: str
    status: JobStatus = JobStatus.PENDING
    output: str = ""
    error: str = ""
    exit_code: Optional[int] = None
    process: Optional[asyncio.subprocess.Process] = None


class CommandValidator:
    """Validates bash commands for safety."""
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'dd\s+if=',      # dd if=
        r'mkfs',          # mkfs
        r':\(\)\{:\|:\&\};:',  # fork bomb
    ]
    
    # Allowed commands
    ALLOWED_COMMANDS = {
        'ls', 'cat', 'grep', 'find', 'echo', 'pwd', 'cd', 'mkdir',
        'touch', 'cp', 'mv', 'rm', 'chmod', 'chown', 'tar', 'zip',
        'unzip', 'curl', 'wget', 'git', 'python', 'node', 'npm',
        'pip', 'docker', 'kubectl', 'aws', 'gcloud', 'az'
    }
    
    @classmethod
    def validate(cls, command: str) -> tuple[bool, Optional[str]]:
        """Validate command safety."""
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Extract first command
        first_cmd = command.split()[0] if command.split() else ""
        
        # Check if command is allowed
        if first_cmd not in cls.ALLOWED_COMMANDS:
            return False, f"Command not allowed: {first_cmd}"
        
        return True, None


class BashExecutor:
    """Bash command executor with job management."""
    
    def __init__(self, timeout: int = 300, max_jobs: int = 100):
        self.timeout = timeout
        self.max_jobs = max_jobs
        self.jobs: Dict[str, BashJob] = {}
        self.job_counter = 0
    
    async def execute(self, command: str, validate: bool = True) -> BashJob:
        """Execute bash command."""
        # Validate command
        if validate:
            is_valid, error = CommandValidator.validate(command)
            if not is_valid:
                logger.warning(f"Command validation failed: {error}")
                job = BashJob(
                    job_id=self._generate_job_id(),
                    command=command,
                    status=JobStatus.FAILED,
                    error=error or "Command validation failed"
                )
                self.jobs[job.job_id] = job
                return job
        
        # Create job
        job = BashJob(
            job_id=self._generate_job_id(),
            command=command,
            status=JobStatus.PENDING
        )
        self.jobs[job.job_id] = job
        
        # Execute asynchronously
        asyncio.create_task(self._execute_async(job))
        
        return job
    
    async def _execute_async(self, job: BashJob) -> None:
        """Execute command asynchronously."""
        try:
            job.status = JobStatus.RUNNING
            logger.info(f"Executing job {job.job_id}: {job.command}")
            
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                job.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            job.process = process
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                job.output = stdout.decode('utf-8', errors='replace')
                job.error = stderr.decode('utf-8', errors='replace')
                job.exit_code = process.returncode
                job.status = JobStatus.COMPLETED if process.returncode == 0 else JobStatus.FAILED
                
                logger.info(f"Job {job.job_id} completed with exit code {process.returncode}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Job {job.job_id} timed out after {self.timeout}s")
                process.kill()
                job.status = JobStatus.FAILED
                job.error = f"Command timed out after {self.timeout} seconds"
                job.exit_code = -1
        
        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.exit_code = -1
    
    async def get_job(self, job_id: str) -> Optional[BashJob]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel running job."""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        if job.status == JobStatus.RUNNING and job.process:
            job.process.kill()
            job.status = JobStatus.CANCELLED
            logger.info(f"Job {job_id} cancelled")
            return True
        
        return False
    
    async def list_jobs(self) -> List[BashJob]:
        """List all jobs."""
        return list(self.jobs.values())
    
    async def cleanup_old_jobs(self, max_age_seconds: int = 3600) -> int:
        """Clean up old completed jobs."""
        import time
        current_time = time.time()
        removed = 0
        
        for job_id, job in list(self.jobs.items()):
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                # Remove old jobs (simplified - would need timestamp tracking)
                if removed < len(self.jobs) - self.max_jobs:
                    del self.jobs[job_id]
                    removed += 1
        
        logger.info(f"Cleaned up {removed} old jobs")
        return removed
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        self.job_counter += 1
        return f"job_{self.job_counter:06d}"


# Global executor instance
_executor: Optional[BashExecutor] = None


def get_bash_executor() -> BashExecutor:
    """Get or create global bash executor."""
    global _executor
    if _executor is None:
        _executor = BashExecutor()
    return _executor


async def execute_bash(command: str, validate: bool = True) -> Dict[str, Any]:
    """Execute bash command and return result."""
    executor = get_bash_executor()
    job = await executor.execute(command, validate=validate)
    
    # Wait for completion
    while job.status == JobStatus.RUNNING:
        await asyncio.sleep(0.1)
    
    return {
        "job_id": job.job_id,
        "command": job.command,
        "status": job.status.value,
        "output": job.output,
        "error": job.error,
        "exit_code": job.exit_code
    }

