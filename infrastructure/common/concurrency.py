"""
Filesystem & Concurrency Management for SmartCP

Provides:
- Atomic file operations
- File locking
- Change monitoring
- Concurrent access control
"""

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class FileOperation(Enum):
    """File operations."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    RENAME = "rename"
    COPY = "copy"


@dataclass
class FileChange:
    """File change event."""
    path: str
    operation: FileOperation
    timestamp: datetime
    size: Optional[int] = None


class FileLock:
    """File lock for concurrent access control."""
    
    def __init__(self, file_path: str, timeout: int = 30):
        self.file_path = file_path
        self.lock_file = f"{file_path}.lock"
        self.timeout = timeout
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire file lock."""
        try:
            async with self.lock:
                # Create lock file
                Path(self.lock_file).touch()
                logger.debug(f"Lock acquired: {self.file_path}")
                return True
        except Exception as e:
            logger.error(f"Error acquiring lock: {e}")
            return False
    
    async def release(self) -> bool:
        """Release file lock."""
        try:
            async with self.lock:
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
                logger.debug(f"Lock released: {self.file_path}")
                return True
        except Exception as e:
            logger.error(f"Error releasing lock: {e}")
            return False
    
    async def is_locked(self) -> bool:
        """Check if file is locked."""
        return os.path.exists(self.lock_file)


class AtomicFileOperations:
    """Atomic file operations."""
    
    def __init__(self):
        self.locks: Dict[str, FileLock] = {}
    
    def _get_lock(self, file_path: str) -> FileLock:
        """Get or create lock for file."""
        if file_path not in self.locks:
            self.locks[file_path] = FileLock(file_path)
        return self.locks[file_path]
    
    async def atomic_write(self, file_path: str, content: str) -> bool:
        """Atomically write to file."""
        lock = self._get_lock(file_path)
        
        try:
            await lock.acquire()
            
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(file_path)) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            # Atomic rename
            os.replace(tmp_path, file_path)
            logger.info(f"Atomic write completed: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error in atomic write: {e}")
            return False
        
        finally:
            await lock.release()
    
    async def atomic_read(self, file_path: str) -> Optional[str]:
        """Atomically read from file."""
        lock = self._get_lock(file_path)
        
        try:
            await lock.acquire()
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            logger.debug(f"Atomic read completed: {file_path}")
            return content
        
        except Exception as e:
            logger.error(f"Error in atomic read: {e}")
            return None
        
        finally:
            await lock.release()
    
    async def atomic_delete(self, file_path: str) -> bool:
        """Atomically delete file."""
        lock = self._get_lock(file_path)
        
        try:
            await lock.acquire()
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Atomic delete completed: {file_path}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error in atomic delete: {e}")
            return False
        
        finally:
            await lock.release()
    
    async def atomic_copy(self, src: str, dst: str) -> bool:
        """Atomically copy file."""
        src_lock = self._get_lock(src)
        dst_lock = self._get_lock(dst)
        
        try:
            await src_lock.acquire()
            await dst_lock.acquire()
            
            # Copy to temporary file
            with tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(dst)) as tmp:
                tmp_path = tmp.name
            
            shutil.copy2(src, tmp_path)
            os.replace(tmp_path, dst)
            
            logger.info(f"Atomic copy completed: {src} -> {dst}")
            return True
        
        except Exception as e:
            logger.error(f"Error in atomic copy: {e}")
            return False
        
        finally:
            await src_lock.release()
            await dst_lock.release()


class FileChangeMonitor:
    """Monitor file changes."""
    
    def __init__(self):
        self.watchers: Dict[str, Callable] = {}
        self.changes: List[FileChange] = []
        self.lock = asyncio.Lock()
    
    async def watch(self, file_path: str, callback: Callable) -> None:
        """Watch file for changes."""
        self.watchers[file_path] = callback
        logger.info(f"Watching file: {file_path}")
        
        last_mtime = 0
        
        while file_path in self.watchers:
            try:
                if os.path.exists(file_path):
                    mtime = os.path.getmtime(file_path)
                    if mtime > last_mtime:
                        size = os.path.getsize(file_path)
                        change = FileChange(
                            path=file_path,
                            operation=FileOperation.WRITE,
                            timestamp=datetime.now(),
                            size=size
                        )
                        
                        async with self.lock:
                            self.changes.append(change)
                        
                        await callback(change)
                        last_mtime = mtime
            
            except Exception as e:
                logger.error(f"Error watching file: {e}")
            
            await asyncio.sleep(1)
    
    async def unwatch(self, file_path: str) -> None:
        """Stop watching file."""
        if file_path in self.watchers:
            del self.watchers[file_path]
            logger.info(f"Stopped watching file: {file_path}")
    
    async def get_changes(self, file_path: Optional[str] = None) -> List[FileChange]:
        """Get file changes."""
        async with self.lock:
            if file_path:
                return [c for c in self.changes if c.path == file_path]
            return self.changes.copy()


class FilesystemConcurrency:
    """Unified filesystem concurrency management."""
    
    def __init__(self):
        self.atomic_ops = AtomicFileOperations()
        self.monitor = FileChangeMonitor()
    
    async def write(self, file_path: str, content: str) -> bool:
        """Write file atomically."""
        return await self.atomic_ops.atomic_write(file_path, content)
    
    async def read(self, file_path: str) -> Optional[str]:
        """Read file atomically."""
        return await self.atomic_ops.atomic_read(file_path)
    
    async def delete(self, file_path: str) -> bool:
        """Delete file atomically."""
        return await self.atomic_ops.atomic_delete(file_path)
    
    async def copy(self, src: str, dst: str) -> bool:
        """Copy file atomically."""
        return await self.atomic_ops.atomic_copy(src, dst)
    
    async def watch(self, file_path: str, callback: Callable) -> None:
        """Watch file for changes."""
        await self.monitor.watch(file_path, callback)
    
    async def unwatch(self, file_path: str) -> None:
        """Stop watching file."""
        await self.monitor.unwatch(file_path)


# Global instance
_filesystem_concurrency: Optional[FilesystemConcurrency] = None


def get_filesystem_concurrency() -> FilesystemConcurrency:
    """Get or create global filesystem concurrency manager."""
    global _filesystem_concurrency
    if _filesystem_concurrency is None:
        _filesystem_concurrency = FilesystemConcurrency()
    return _filesystem_concurrency

