#!/usr/bin/env python3
"""Shared infrastructure utilities for local entrypoints."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
from contextlib import suppress
from dataclasses import dataclass, field
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


ROOT = Path(__file__).resolve().parent
PHENO_SRC = ROOT / "pheno-sdk" / "src"
if PHENO_SRC.exists():  # pragma: no cover - path setup
    sys.path.insert(0, str(PHENO_SRC))

from pheno.infra.tunneling import (  # noqa: E402 - depends on sys.path mutation
    AsyncTunnelManager,
    TunnelConfig,
    TunnelInfo,
    TunnelProtocol,
    TunnelStatus,
    TunnelType,
)


LOGGER = logging.getLogger("infra-common")


@dataclass(slots=True)
class ServiceSpec:
    command: List[str]
    working_dir: Path
    env: Dict[str, str]
    preferred_port: int
    kill_existing: bool
    enable_tunnel: bool
    tunnel_domain: str


@dataclass(slots=True)
class InfraState:
    name: str
    display_name: str
    service: ServiceSpec
    managed_resources: Dict[str, Dict[str, Any]]
    state_file: Path


@dataclass(slots=True)
class ProjectSettings:
    name: str
    display_name: str
    project_root: Path
    config_path: Path
    state_file: Path
    default_command: List[str]
    default_workdir: Path
    default_env: Dict[str, str] = field(default_factory=dict)
    default_port: int = 8080
    default_domain: str = "localhost"
    default_kill_existing: bool = True
    default_enable_tunnel: bool = True


def load_yaml_config(path: Path) -> Dict[str, Any]:
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


def _expand_env(values: Dict[str, str]) -> Dict[str, str]:
    expanded: Dict[str, str] = {}
    for key, value in values.items():
        expanded[key] = os.path.expandvars(str(value))
    return expanded


def _find_port(preferred: Optional[int]) -> int:
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


def _kill_processes_on_port(port: int) -> None:
    if port <= 0:
        return
    if psutil:
        killed = 0
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            with suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                for conn in proc.connections(kind="inet"):
                    if conn.laddr and conn.laddr.port == port:
                        LOGGER.info("Terminating process %s (%s) using port %s", proc.pid, proc.name(), port)
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
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        LOGGER.warning("psutil and lsof unavailable; cannot free port %s automatically.", port)
        return
    for pid in filter(None, result.stdout.strip().splitlines()):
        subprocess.run(["kill", "-9", pid], check=False)
        LOGGER.info("Killed process %s on port %s", pid, port)


_DOCKER_AVAILABLE: Optional[bool] = None


def docker_available() -> bool:
    global _DOCKER_AVAILABLE
    if _DOCKER_AVAILABLE is None:
        docker_path = shutil.which("docker")
        _DOCKER_AVAILABLE = docker_path is not None
        if not _DOCKER_AVAILABLE:
            LOGGER.warning("Docker CLI not available; managed resources will remain stopped.")
    return bool(_DOCKER_AVAILABLE)


class ResourceSupervisor:
    def __init__(self, resources: Dict[str, Dict[str, Any]]) -> None:
        self.resources_config = resources
        self.containers = {name: cfg.get("container_name", f"{name}-container") for name, cfg in resources.items()}

    def _run(self, args: Iterable[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["docker", *args], capture_output=True, text=True)

    def _run_container(self, name: str, extra_args: List[str]) -> bool:
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
        if not docker_available():
            return
        for container in self.containers.values():
            with suppress(Exception):
                self._run(["stop", container])
                self._run(["rm", "-f", container])

    def resource_status(self) -> Dict[str, str]:
        if not docker_available():
            return {name: "unmanaged (docker unavailable)" for name in self.resources_config}
        return {
            name: self._run(["ps", "-a", "-f", f"name={container}", "--format", "{{.Status}}"]).stdout.strip()
            or "stopped"
            for name, container in self.containers.items()
        }


# --------------------------------------------------------------------------- #
# Infra manager                                                               #
# --------------------------------------------------------------------------- #


def build_state(settings: ProjectSettings) -> InfraState:
    config = load_yaml_config(settings.config_path)

    service_cfg = config.get("service", {})
    env_cfg = service_cfg.get("env", {})
    env = settings.default_env.copy()
    env.update(_expand_env({k: str(v) for k, v in env_cfg.items()}))

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
        managed_resources = {item["name"]: item for item in managed_resources if isinstance(item, dict) and "name" in item}
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


class InfraManager:
    def __init__(self, state: InfraState) -> None:
        self.state = state
        self._tunnel_manager = AsyncTunnelManager()
        self._tunnel_info: Optional[TunnelInfo] = None
        self._port: Optional[int] = None
        self._service_process: Optional[subprocess.Popen[str]] = None
        self._resources = ResourceSupervisor(state.managed_resources)

    async def ensure_resources(self) -> Dict[str, bool]:
        return await asyncio.to_thread(self._resources.start_all)

    async def ensure_tunnel(self) -> None:
        spec = self.state.service
        if spec.kill_existing and spec.preferred_port:
            _kill_processes_on_port(spec.preferred_port)
        self._port = _find_port(spec.preferred_port)
        if spec.enable_tunnel:
            tunnel_config = TunnelConfig(
                name=spec.tunnel_domain,
                tunnel_type=TunnelType.CLOUDFLARE,
                protocol=TunnelProtocol.HTTPS,
                local_host="127.0.0.1",
                local_port=self._port,
                metadata={"service": self.state.name},
            )
            self._tunnel_info = await self._tunnel_manager.create_tunnel(tunnel_config)

    async def provision(self) -> Dict[str, Any]:
        await self.ensure_resources()
        await self.ensure_tunnel()
        self._persist()
        return self.status()

    def start_service(self) -> None:
        spec = self.state.service
        if self._service_process or not spec.command:
            return
        env = os.environ.copy()
        env.update(spec.env)
        LOGGER.info("Starting %s via command: %s", self.state.display_name, spec.command)
        self._service_process = subprocess.Popen(spec.command, cwd=str(spec.working_dir), env=env)
        self._persist()

    async def stop_service(self) -> None:
        if not self._service_process:
            return
        LOGGER.info("Stopping %s service process", self.state.display_name)
        self._service_process.terminate()
        try:
            await asyncio.to_thread(self._service_process.wait, 5)
        except Exception:
            self._service_process.kill()
        self._service_process = None
        self._persist()

    async def teardown(self) -> None:
        await self.stop_service()
        if self._tunnel_info:
            await self._tunnel_manager.destroy_tunnel(self._tunnel_info.tunnel_id)
        self._tunnel_info = None
        self._port = None
        try:
            await asyncio.to_thread(self._resources.stop_all)
        except RuntimeError:
            self._resources.stop_all()
        if self.state.state_file.exists():
            with suppress(OSError):
                self.state.state_file.unlink()

    def status(self) -> Dict[str, Any]:
        tunnel_status = self._tunnel_info.status.value if self._tunnel_info else TunnelStatus.CLOSED.value
        return {
            "service": self.state.name,
            "display_name": self.state.display_name,
            "port": self._port,
            "tunnel_status": tunnel_status,
            "tunnel_url": self._tunnel_info.public_url if self._tunnel_info else None,
            "process_running": bool(self._service_process and self._service_process.poll() is None),
            "resources": self._resources.resource_status(),
        }

    def _persist(self) -> None:
        self.state.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state.state_file.write_text(json.dumps(self.status(), indent=2))


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project infrastructure orchestrator.")
    parser.add_argument(
        "command",
        nargs="?",
        default="start",
        choices=["start", "stop", "status", "resources", "sync"],
        help="Action to perform (default: start).",
    )
    parser.add_argument("--no-service", action="store_true", help="Skip starting the service process.")
    parser.add_argument("--print-status", action="store_true", help="Print status after command execution.")
    parser.add_argument("--local", action="store_true", help="Use local pheno-sdk build (for sync command).")
    return parser.parse_args(argv)


def run_cli(settings: ProjectSettings, argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    state = build_state(settings)
    manager = InfraManager(state)

    async def _start() -> None:
        status = await manager.provision()
        LOGGER.info("Provisioned %s on port %s", status["service"], status["port"])
        if status["tunnel_url"]:
            LOGGER.info("Tunnel URL: %s", status["tunnel_url"])
        if not args.no_service:
            manager.start_service()
            try:
                while True:
                    await asyncio.sleep(3600)
            except (KeyboardInterrupt, asyncio.CancelledError):
                LOGGER.info("Interrupted; tearing down %s.", state.display_name)
            finally:
                await manager.teardown()

    async def _resources() -> None:
        results = await manager.ensure_resources()
        manager._persist()
        for name, ok in results.items():
            LOGGER.info("Resource %s start status: %s", name, "ok" if ok else "failed")

    async def _stop() -> None:
        await manager.teardown()

    async def _status() -> None:
        # ensure state file is read if tunnel/service not running
        if state.state_file.exists():
            content = json.loads(state.state_file.read_text())
            print(json.dumps(content, indent=2))
        else:
            print(json.dumps(manager.status(), indent=2))

    async def _sync() -> None:
        """Sync command to configure local development environment."""
        if args.local:
            # Set up local pheno-sdk environment
            pheno_sdk_src = ROOT / "pheno-sdk" / "src"
            if not pheno_sdk_src.exists():
                LOGGER.error("Local pheno-sdk not found at %s", pheno_sdk_src)
                return
            
            # Create or update .env file
            env_file = ROOT / ".env"
            env_content = []
            
            if env_file.exists():
                # Read existing .env and update PHENO_LOCAL_DEV
                with env_file.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                updated = False
                for line in lines:
                    if line.strip().startswith("PHENO_LOCAL_DEV="):
                        env_content.append("PHENO_LOCAL_DEV=true\n")
                        updated = True
                    else:
                        env_content.append(line)
                
                if not updated:
                    env_content.append("PHENO_LOCAL_DEV=true\n")
            else:
                env_content = ["PHENO_LOCAL_DEV=true\n"]
            
            # Write updated .env file
            with env_file.open("w", encoding="utf-8") as f:
                f.writelines(env_content)
            
            LOGGER.info("✓ Configured local pheno-sdk environment")
            LOGGER.info("  - Set PHENO_LOCAL_DEV=true in .env")
            LOGGER.info("  - Local pheno-sdk path: %s", pheno_sdk_src)
            print("\n✓ Local development environment configured!")
            print("  - PHENO_LOCAL_DEV=true set in .env")
            print(f"  - Local pheno-sdk: {pheno_sdk_src}")
            print("  - Entry points will now automatically use local pheno-sdk")
        else:
            # Show current configuration
            pheno_sdk_src = ROOT / "pheno-sdk" / "src"
            env_file = ROOT / ".env"
            
            print("\nCurrent pheno-sdk configuration:")
            print(f"  - Local pheno-sdk exists: {pheno_sdk_src.exists()}")
            print(f"  - Local path: {pheno_sdk_src}")
            
            if env_file.exists():
                with env_file.open("r", encoding="utf-8") as f:
                    content = f.read()
                if "PHENO_LOCAL_DEV=true" in content:
                    print("  - Environment: Local development (PHENO_LOCAL_DEV=true)")
                elif "PHENO_LOCAL_DEV=false" in content:
                    print("  - Environment: Production (PHENO_LOCAL_DEV=false)")
                else:
                    print("  - Environment: Auto-detect (PHENO_LOCAL_DEV not set)")
            else:
                print("  - Environment: Auto-detect (no .env file)")
            
            print(f"\nTo use local pheno-sdk, run: {sys.argv[0]} sync --local")

    command_map = {
        "start": _start,
        "resources": _resources,
        "stop": _stop,
        "status": _status,
        "sync": _sync,
    }

    asyncio.run(command_map[args.command]())

    if args.print_status and args.command in {"start", "resources", "stop"}:
        print(json.dumps(manager.status(), indent=2))
    return 0
