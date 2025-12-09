#!/usr/bin/env python3
"""Common infrastructure utilities."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore

from smartcp.infra_common_constants import LOGGER, _DOCKER_AVAILABLE
from smartcp.infra_common_types import InfraState, ProjectSettings, ServiceSpec


def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration from file.

    Args:
        path: Path to YAML configuration file.

    Returns:
        Configuration dictionary or empty dict if not found/invalid.
    """
    if not path.exists():
        LOGGER.debug("Config file %s not found; using defaults.", path)
        return {}
    if yaml is None:
        LOGGER.warning("PyYAML not installed; ignoring %s.", path)
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
            if not isinstance(data, dict):
                raise TypeError("Top-level YAML node must be a mapping.")
            return data
    except Exception as exc:
        LOGGER.warning("Failed to parse %s (%s); falling back to defaults.", path, exc)
        return {}


def expand_env(values: Dict[str, str]) -> Dict[str, str]:
    """Expand environment variables in dictionary values.

    Args:
        values: Dictionary with potentially templated values.

    Returns:
        Dictionary with expanded values.
    """
    expanded: Dict[str, str] = {}
    for key, value in values.items():
        expanded[key] = os.path.expandvars(str(value))
    return expanded


def find_port(preferred: Optional[int]) -> int:
    """Find an available port.

    Tries preferred port first, then any available port (0).

    Args:
        preferred: Preferred port number or None.

    Returns:
        Available port number.
    """
    candidates = ([preferred] if preferred else []) + [0]
    last_error: Optional[OSError] = None
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("127.0.0.1", port))
                sock.listen(1)
                return sock.getsockname()[1]
        except OSError as exc:
            last_error = exc
            continue
    fallback = preferred or 8080
    if last_error:
        LOGGER.debug("Port bind fallback to %s after error: %s", fallback, last_error)
    return fallback


def kill_processes_on_port(port: int) -> None:
    """Kill processes bound to a port.

    Args:
        port: Port number to free.
    """
    if port <= 0:
        return
    if psutil:
        killed = 0
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                for conn in proc.connections(kind="inet"):
                    if conn.laddr and conn.laddr.port == port:
                        LOGGER.info(
                            "Terminating process %s (%s) using port %s",
                            proc.pid,
                            proc.name(),
                            port,
                        )
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            proc.kill()
                        killed += 1
        if killed:
            LOGGER.info("Killed %s process(es) on port %s", killed, port)
        return

    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        LOGGER.warning(
            "psutil and lsof unavailable; cannot free port %s automatically.", port
        )
        return
    for pid in filter(None, result.stdout.strip().splitlines()):
        subprocess.run(["kill", "-9", pid], check=False)
        LOGGER.info("Killed process %s on port %s", pid, port)


def docker_available() -> bool:
    """Check if Docker CLI is available.

    Returns:
        True if docker command is in PATH, False otherwise.
    """
    import smartcp.infra_common_constants as constants

    if constants._DOCKER_AVAILABLE is None:
        docker_path = shutil.which("docker")
        constants._DOCKER_AVAILABLE = docker_path is not None
        if not constants._DOCKER_AVAILABLE:
            LOGGER.warning(
                "Docker CLI not available; managed resources will remain stopped."
            )
    return bool(constants._DOCKER_AVAILABLE)


class ResourceSupervisor:
    """Supervisor for Docker-based managed resources."""

    def __init__(self, resources: Dict[str, Dict[str, Any]]) -> None:
        self.resources_config = resources
        self.containers = {
            name: cfg.get("container_name", f"{name}-container")
            for name, cfg in resources.items()
        }

    def _run(self, args: Iterable[str]) -> subprocess.CompletedProcess[str]:
        """Run docker command.

        Args:
            args: Docker command arguments.

        Returns:
            Completed process result.
        """
        return subprocess.run(["docker", *args], capture_output=True, text=True)

    def _run_container(self, name: str, extra_args: List[str]) -> bool:
        """Run a Docker container.

        Args:
            name: Resource name.
            extra_args: Additional docker run arguments.

        Returns:
            True if container started successfully, False otherwise.
        """
        if not docker_available():
            return False
        container = self.containers[name]
        self._run(["stop", container])
        self._run(["rm", "-f", container])
        result = self._run(["run", "-d", "--rm", "--name", container, *extra_args])
        if result.returncode != 0:
            LOGGER.error("Failed to start resource %s: %s", name, result.stderr.strip())
            return False
        return True

    def _start_postgres(self, name: str, cfg: Dict[str, Any]) -> bool:
        """Start a PostgreSQL container.

        Args:
            name: Resource name.
            cfg: Configuration dict.

        Returns:
            True if started successfully, False otherwise.
        """
        if not docker_available():
            return False
        port = int(cfg.get("port", 5433))
        database = cfg.get("database", "app")
        user = cfg.get("user", "postgres")
        password = cfg.get("password", "postgres")
        version = cfg.get("version", "16-alpine")
        data_dir = Path(cfg.get("data_dir", "./data/postgres")).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        return self._run_container(
            name,
            [
                "-p",
                f"{port}:5432",
                "-e",
                f"POSTGRES_DB={database}",
                "-e",
                f"POSTGRES_USER={user}",
                "-e",
                f"POSTGRES_PASSWORD={password}",
                "-v",
                f"{data_dir}:/var/lib/postgresql/data",
                f"postgres:{version}",
            ],
        )

    def _start_nats(self, name: str, cfg: Dict[str, Any]) -> bool:
        """Start a NATS container.

        Args:
            name: Resource name.
            cfg: Configuration dict.

        Returns:
            True if started successfully, False otherwise.
        """
        if not docker_available():
            return False
        port = int(cfg.get("port", 4222))
        monitor_port = int(cfg.get("monitor_port", 8222))
        enable_js = bool(cfg.get("enable_jetstream", True))
        version = cfg.get("version", "2.10-alpine")
        data_dir = Path(cfg.get("data_dir", "./data/nats")).expanduser().resolve()
        data_dir.mkdir(parents=True, exist_ok=True)
        args = [
            "-p",
            f"{port}:4222",
            "-p",
            f"{monitor_port}:8222",
            "-v",
            f"{data_dir}:/data",
            f"nats:{version}",
            "-m",
            "8222",
        ]
        if enable_js:
            args.append("-js")
        return self._run_container(name, args)

    def start_all(self) -> Dict[str, bool]:
        """Start all managed resources.

        Returns:
            Dictionary mapping resource names to success status.
        """
        results: Dict[str, bool] = {}
        for name, cfg in self.resources_config.items():
            resource_type = (cfg.get("type") or name).lower()
            if resource_type in {"postgres", "postgresql"}:
                results[name] = self._start_postgres(name, cfg)
            elif resource_type == "nats":
                results[name] = self._start_nats(name, cfg)
            else:
                LOGGER.warning("Unsupported resource type '%s'; skipping.", resource_type)
                results[name] = False
        return results

    def stop_all(self) -> None:
        """Stop all managed resources."""
        if not docker_available():
            return
        for container in self.containers.values():
            with suppress(Exception):
                self._run(["stop", container])
                self._run(["rm", "-f", container])

    def resource_status(self) -> Dict[str, str]:
        """Get status of all managed resources.

        Returns:
            Dictionary mapping resource names to status strings.
        """
        if not docker_available():
            return {
                name: "unmanaged (docker unavailable)"
                for name in self.resources_config
            }
        return {
            name: self._run(
                ["ps", "-a", "-f", f"name={container}", "--format", "{{.Status}}"]
            ).stdout.strip()
            or "stopped"
            for name, container in self.containers.items()
        }


def build_state(settings: ProjectSettings) -> InfraState:
    """Build infrastructure state from settings and config.

    Args:
        settings: Project settings.

    Returns:
        Infrastructure state object.
    """
    config = load_yaml_config(settings.config_path)

    service_cfg = config.get("service", {})
    env_cfg = service_cfg.get("env", {})
    env = settings.default_env.copy()
    env.update(expand_env({k: str(v) for k, v in env_cfg.items()}))

    command = service_cfg.get("command", settings.default_command)
    if isinstance(command, str):
        command = [command]
    command = [str(part) for part in command] or settings.default_command

    working_dir = service_cfg.get("working_dir", ".")
    working_dir_path = (settings.project_root / working_dir).resolve()

    port_cfg = config.get("port", service_cfg.get("port", {}))
    preferred_port = int(port_cfg.get("preferred", settings.default_port))
    kill_existing = bool(port_cfg.get("kill_existing", settings.default_kill_existing))

    tunnel_cfg = config.get("tunnel", service_cfg.get("tunnel", {}))
    enable_tunnel = bool(tunnel_cfg.get("enabled", settings.default_enable_tunnel))
    tunnel_domain = str(tunnel_cfg.get("domain", settings.default_domain))
    subdomain = tunnel_cfg.get("subdomain")
    if subdomain:
        tunnel_domain = f"{subdomain}.{tunnel_domain}"

    display_name = service_cfg.get("display_name", settings.display_name)

    resources_cfg = config.get("resources", {})
    managed_resources = resources_cfg.get("managed", {})
    if isinstance(managed_resources, list):
        managed_resources = {
            item["name"]: item
            for item in managed_resources
            if isinstance(item, dict) and "name" in item
        }
    if not isinstance(managed_resources, dict):
        managed_resources = {}

    service = ServiceSpec(
        command=command,
        working_dir=working_dir_path,
        env=env,
        preferred_port=preferred_port,
        kill_existing=kill_existing,
        enable_tunnel=enable_tunnel,
        tunnel_domain=tunnel_domain,
    )

    return InfraState(
        name=settings.name,
        display_name=display_name,
        service=service,
        managed_resources=managed_resources,
        state_file=settings.state_file,
    )
