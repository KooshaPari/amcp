"""
Multi-Language Executor for SmartCP

Unified interface for executing code in multiple languages:
- Python
- Go
- TypeScript
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    GO = "go"
    TYPESCRIPT = "typescript"


class LanguageExecutor(ABC):
    """Abstract base class for language executors."""
    
    @abstractmethod
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute code in the language."""
        pass
    
    @abstractmethod
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute code with dependencies."""
        pass


class PythonExecutorAdapter(LanguageExecutor):
    """Adapter for Python executor."""
    
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Python code."""
        from bash_executor import execute_bash
        
        # Write code to temp file and execute
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            
            try:
                result = await execute_bash(f"python {f.name}")
                return result
            finally:
                os.unlink(f.name)
    
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute Python code with dependencies."""
        from bash_executor import execute_bash
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create requirements.txt
            req_file = os.path.join(tmpdir, "requirements.txt")
            with open(req_file, 'w') as f:
                for dep, version in dependencies.items():
                    f.write(f"{dep}=={version}\n")
            
            # Create Python file
            py_file = os.path.join(tmpdir, "main.py")
            with open(py_file, 'w') as f:
                f.write(code)
            
            # Install and run
            await execute_bash(f"pip install -r {req_file}")
            result = await execute_bash(f"python {py_file}")
            return result


class GoExecutorAdapter(LanguageExecutor):
    """Adapter for Go executor."""
    
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute Go code."""
        from go_executor import execute_go
        return await execute_go(code, kwargs.get('module_name', 'main'))
    
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute Go code with dependencies."""
        from go_executor import execute_go_with_deps
        return await execute_go_with_deps(
            code,
            dependencies,
            kwargs.get('module_name', 'main')
        )


class TypeScriptExecutorAdapter(LanguageExecutor):
    """Adapter for TypeScript executor."""
    
    async def execute(self, code: str, **kwargs) -> Dict[str, Any]:
        """Execute TypeScript code."""
        from typescript_executor import execute_typescript
        return await execute_typescript(code, kwargs.get('filename', 'main.ts'))
    
    async def execute_with_dependencies(
        self,
        code: str,
        dependencies: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute TypeScript code with dependencies."""
        from typescript_executor import execute_typescript_with_deps
        return await execute_typescript_with_deps(
            code,
            dependencies,
            kwargs.get('filename', 'main.ts')
        )


class MultiLanguageExecutor:
    """Unified multi-language executor."""
    
    def __init__(self):
        self.executors: Dict[Language, LanguageExecutor] = {
            Language.PYTHON: PythonExecutorAdapter(),
            Language.GO: GoExecutorAdapter(),
            Language.TYPESCRIPT: TypeScriptExecutorAdapter(),
        }
    
    async def execute(
        self,
        language: Language,
        code: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute code in specified language."""
        if language not in self.executors:
            return {
                "status": "failed",
                "error": f"Unsupported language: {language.value}",
                "exit_code": -1
            }
        
        executor = self.executors[language]
        return await executor.execute(code, **kwargs)
    
    async def execute_with_dependencies(
        self,
        language: Language,
        code: str,
        dependencies: Dict[str, str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute code with dependencies."""
        if language not in self.executors:
            return {
                "status": "failed",
                "error": f"Unsupported language: {language.value}",
                "exit_code": -1
            }
        
        executor = self.executors[language]
        return await executor.execute_with_dependencies(code, dependencies, **kwargs)
    
    def register_executor(self, language: Language, executor: LanguageExecutor) -> None:
        """Register custom executor for language."""
        self.executors[language] = executor
        logger.info(f"Registered executor for {language.value}")


# Global instance
_multi_executor: Optional[MultiLanguageExecutor] = None


def get_multi_language_executor() -> MultiLanguageExecutor:
    """Get or create global multi-language executor."""
    global _multi_executor
    if _multi_executor is None:
        _multi_executor = MultiLanguageExecutor()
    return _multi_executor


async def execute_code(
    language: str,
    code: str,
    **kwargs
) -> Dict[str, Any]:
    """Execute code in specified language."""
    try:
        lang = Language(language)
        executor = get_multi_language_executor()
        return await executor.execute(lang, code, **kwargs)
    except ValueError:
        return {
            "status": "failed",
            "error": f"Unknown language: {language}",
            "exit_code": -1
        }


async def execute_code_with_deps(
    language: str,
    code: str,
    dependencies: Dict[str, str],
    **kwargs
) -> Dict[str, Any]:
    """Execute code with dependencies."""
    try:
        lang = Language(language)
        executor = get_multi_language_executor()
        return await executor.execute_with_dependencies(lang, code, dependencies, **kwargs)
    except ValueError:
        return {
            "status": "failed",
            "error": f"Unknown language: {language}",
            "exit_code": -1
        }

