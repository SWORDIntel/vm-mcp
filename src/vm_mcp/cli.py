from __future__ import annotations

import argparse
import asyncio
import json

from .service import VMService
from .proxmox import ProxmoxLifecycle, ProxmoxSnapshot
from .xen import XenLifecycle


def main() -> int:
    parser = argparse.ArgumentParser(prog="vmctl")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("exec")
    state_parser = sub.add_parser("state")
    metrics_parser = sub.add_parser("metrics")
    snap_parser = sub.add_parser("snapshot")
    snap_parser.add_argument("--vmid", required=True)
    snap_parser.add_argument("--action", choices=["list", "create"], required=True)
    snap_parser.add_argument("--name")
    state_parser.add_argument("--vmid", required=True)
    state_parser.add_argument("--action", choices=["status", "start", "stop", "reboot"], required=True)
    state_parser.add_argument("--provider", choices=["proxmox", "xen"], default="proxmox")
    run_parser.add_argument("--vmid", required=True)
    run_parser.add_argument("--cmd", required=True)
    run_parser.add_argument("--danger-mode", action="store_true")
    run_parser.add_argument("--actor", default="operator")
    run_parser.add_argument("--audit-tag")

    args = parser.parse_args()
    service = VMService.build()
    xen = XenLifecycle(runner=service.runner)
    proxmox = ProxmoxLifecycle(runner=service.runner)
    snapshot = ProxmoxSnapshot(runner=service.runner)

    if args.command == "exec":
        result = asyncio.run(
            service.exec(
                vmid=args.vmid,
                cmd=args.cmd,
                actor=args.actor,
                danger_mode=args.danger_mode,
                audit_tag=args.audit_tag,
            )
        )
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1


    if args.command == "state":
        adapter = proxmox if args.provider == "proxmox" else xen
        action = getattr(adapter, args.action)
        result = asyncio.run(action(args.vmid))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "metrics":
        print(json.dumps(service.metrics_snapshot(), sort_keys=True))
        return 0

    if args.command == "snapshot":
        if args.action == "create" and not args.name:
            raise SystemExit("--name is required for snapshot create")
        action = getattr(snapshot, args.action)
        kwargs = {"vmid": args.vmid}
        if args.name:
            kwargs["name"] = args.name
        result = asyncio.run(action(**kwargs))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
