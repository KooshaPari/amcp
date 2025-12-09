"""Security and sandboxing for code execution.

Provides security checking and safe builtins configuration for sandboxed
Python code execution.
"""

import ast
from typing import Any


class SecurityChecker:
    """Validates code for security before execution."""

    # Forbidden modules that could be dangerous
    FORBIDDEN_MODULES = {
        "os",
        "sys",
        "subprocess",
        "shutil",
        "socket",
        "http",
        "urllib",
        "requests",
        "pathlib",
        "glob",
        "tempfile",
        "pickle",
        "marshal",
        "shelve",
        "importlib",
        "__builtin__",
        "builtins",
        "ctypes",
        "multiprocessing",
        "threading",
        "concurrent",
        "asyncio",
        "signal",
        "pty",
        "tty",
        "termios",
        "fcntl",
        "resource",
        "sysconfig",
    }

    # Forbidden built-in functions
    FORBIDDEN_BUILTINS = {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__import__",
        "breakpoint",
        "help",
        "quit",
        "exit",
        "globals",
        "locals",
        "vars",
        "dir",
        "getattr",
        "setattr",
        "delattr",
        "hasattr",
    }

    # Forbidden AST node types
    FORBIDDEN_NODES = {
        ast.Import,
        ast.ImportFrom,
    }

    def check(self, code: str) -> list[str]:
        """Check code for security violations.

        Args:
            code: Python code to check

        Returns:
            List of security violation messages (empty if safe)
        """
        violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"Syntax error: {e}"]

        for node in ast.walk(tree):
            # Check for forbidden node types
            if type(node) in self.FORBIDDEN_NODES:
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in self.FORBIDDEN_MODULES:
                            violations.append(f"Forbidden import: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split(".")[0] in self.FORBIDDEN_MODULES:
                        violations.append(f"Forbidden import from: {node.module}")

            # Check for forbidden function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_BUILTINS:
                        violations.append(f"Forbidden function: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    # Check for things like os.system()
                    if isinstance(node.func.value, ast.Name):
                        module = node.func.value.id
                        if module in self.FORBIDDEN_MODULES:
                            violations.append(
                                f"Forbidden module access: {module}.{node.func.attr}"
                            )

        return violations


class SafeBuiltins:
    """Provides safe built-in functions for code execution."""

    ALLOWED = {
        # Type conversions
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "frozenset": frozenset,
        "bytes": bytes,
        "bytearray": bytearray,
        # Math operations
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "divmod": divmod,
        # Iteration
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "sorted": sorted,
        "reversed": reversed,
        "len": len,
        "all": all,
        "any": any,
        # String operations
        "chr": chr,
        "ord": ord,
        "hex": hex,
        "oct": oct,
        "bin": bin,
        "format": format,
        "repr": repr,
        "ascii": ascii,
        # Object introspection (safe subset)
        "type": type,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "callable": callable,
        "id": id,
        "hash": hash,
        # Other safe operations
        "print": print,  # Redirected to StringIO
        "iter": iter,
        "next": next,
        "slice": slice,
        "object": object,
        "property": property,
        "staticmethod": staticmethod,
        "classmethod": classmethod,
        "super": super,
        # Exceptions (for try/except)
        "Exception": Exception,
        "BaseException": BaseException,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "AttributeError": AttributeError,
        "RuntimeError": RuntimeError,
        "StopIteration": StopIteration,
        "ZeroDivisionError": ZeroDivisionError,
        "OverflowError": OverflowError,
        # Constants
        "True": True,
        "False": False,
        "None": None,
    }

    @classmethod
    def get_builtins(cls) -> dict[str, Any]:
        """Get safe builtins dictionary."""
        return cls.ALLOWED.copy()
