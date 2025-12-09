#!/usr/bin/env python3
"""Infrastructure manager and CLI orchestration."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any, Dict, List, Optional

from pheno.infra.tunneling import (
    AsyncTunnelManager,
    TunnelConfig,
    TunnelInfo,
    TunnelProtocol,
    TunnelStatus,
    TunnelType,
)

from smartcp.infra_common_constants import LOGGER, ROOT
from smartcp.infra_common_types import InfraState, ProjectSettings
from smartcp.infra_common_utils import (
    build_state,
    find_port,
    kill_processes_on_port,
)


class InfraManager:
    """Manages infrastructure provisioning and service lifecycle."""

    def __init__(self, state: InfraState) -> None:
        self.state = state
        self._tunnel_manager = AsyncTunnelManager()
        self._tunnel_info: Optional[TunnelInfo] = None
        self._port: Optional[int] = None
        self._service_process: Optional[subprocess.Popen[str]] = None
        from smartcp.infra_common_utils import ResourceSupervisor

        self._resources = ResourceSupervisor(state.managed_resources)

    async def ensure_resources(self) -> Dict[str, bool]:
        """Ensure all managed resources are started.

        Returns:
            Dictionary mapping resource names to success status.
        """
        return await asyncio.to_thread(self._resources.start_all)

    async def ensure_tunnel(self) -> None:
        """Ensure tunnel is configured and created."""
        spec = self.state.service
        if spec.kill_existing and spec.preferred_port:
            kill_processes_on_port(spec.preferred_port)
        self._port = find_port(spec.preferred_port)
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
        """Provision all resources and tunnels.

        Returns:
            Status dictionary.
        """
        await self.ensure_resources()
        await self.ensure_tunnel()
        self._persist()
        return self.status()

    def start_service(self) -> None:
        """Start the service process."""
        spec = self.state.service
        if self._service_process or not spec.command:
            return
        env = os.environ.copy()
        env.update(spec.env)
        LOGGER.info("Starting %s via command: %s", self.state.display_name, spec.command)
        self._service_process = subprocess.Popen(
            spec.command, cwd=str(spec.working_dir), env=env
        )
        self._persist()

    async def stop_service(self) -> None:
        """Stop the service process."""
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
        """Tear down all resources and services."""
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
        """Get current infrastructure status.

        Returns:
            Status dictionary.
        """
        tunnel_status = (
            self._tunnel_info.status.value
            if self._tunnel_info
            else TunnelStatus.CLOSED.value
        )
        return {
            "service": self.state.name,
            "display_name": self.state.display_name,
            "port": self._port,
            "tunnel_status": tunnel_status,
            "tunnel_url": self._tunnel_info.public_url if self._tunnel_info else None,
            "process_running": bool(
                self._service_process and self._service_process.poll() is None
            ),
            "resources": self._resources.resource_status(),
        }

    def _persist(self) -> None:
        """Persist status to state file."""
        self.state.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state.state_file.write_text(json.dumps(self.status(), indent=2))


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Arguments to parse or None for sys.argv.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Project infrastructure orchestrator."
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="start",
        choices=["start", "stop", "status", "resources", "sync"],
        help="Action to perform (default: start).",
    )
    parser.add_argument(
        "--no-service", action="store_true", help="Skip starting the service process."
    )
    parser.add_argument(
        "--print-status",
        action="store_true",
        help="Print status after command execution.",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local pheno-sdk build (for sync command).",
    )
    return parser.parse_args(argv)


def run_cli(settings: ProjectSettings, argv: Optional[List[str]] = None) -> int:
    """Run the CLI orchestrator.

    Args:
        settings: Project settings.
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Exit code.
    """
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

            LOGGER.info("Configured local pheno-sdk environment")
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
