from __future__ import annotations

import argparse
import asyncio
import json

from .service import VMService
from .proxmox import ProxmoxLifecycle, ProxmoxSnapshot, ProxmoxFileOps
from .orchestration import VMServiceManager, VMContainerManager
from .xen import XenLifecycle


def main() -> int:
    parser = argparse.ArgumentParser(prog="vmctl")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("exec")
    state_parser = sub.add_parser("state")
    metrics_parser = sub.add_parser("metrics")
    
    file_parser = sub.add_parser("file")
    file_sub = file_parser.add_subparsers(dest="action", required=True)
    
    put_parser = file_sub.add_parser("put")
    put_parser.add_argument("--vmid", required=True)
    put_parser.add_argument("--local", required=True)
    put_parser.add_argument("--remote", required=True)
    
    get_parser = file_sub.add_parser("get")
    get_parser.add_argument("--vmid", required=True)
    get_parser.add_argument("--remote", required=True)

    service_parser = sub.add_parser("service")
    service_sub = service_parser.add_subparsers(dest="action", required=True)
    
    svc_status_parser = service_sub.add_parser("status")
    svc_status_parser.add_argument("--vmid", required=True)
    svc_status_parser.add_argument("--name", required=True)
    
    svc_enable_parser = service_sub.add_parser("enable")
    svc_enable_parser.add_argument("--vmid", required=True)
    svc_enable_parser.add_argument("--name", required=True)

    docker_parser = sub.add_parser("docker")
    docker_sub = docker_parser.add_subparsers(dest="action", required=True)
    
    docker_ps_parser = docker_sub.add_parser("ps")
    docker_ps_parser.add_argument("--vmid", required=True)

    slo_parser = sub.add_parser("slo")
    slo_sub = slo_parser.add_subparsers(dest="action", required=True)
    slo_check_parser = slo_sub.add_parser("check")
    slo_check_parser.add_argument("--vmid")
    slo_check_parser.add_argument("--services", nargs="+", default=[])
    slo_check_parser.add_argument("--containers", nargs="+", default=[])

    snap_parser = sub.add_parser("snapshot")
    snap_parser.add_argument("--vmid", required=True)
    snap_parser.add_argument("--action", choices=["list", "create", "rollback", "delete"], required=True)
    snap_parser.add_argument("--name")

    config_parser = sub.add_parser("config")
    config_parser.add_argument("--vmid", required=True)
    config_parser.add_argument("--action", choices=["get", "set"], required=True)
    config_parser.add_argument("--params", nargs="+", help="key=value pairs for set")

    state_parser.add_argument("--vmid", required=True)
    state_parser.add_argument("--action", choices=["status", "start", "stop", "reboot"], required=True)
    state_parser.add_argument("--provider", choices=["proxmox", "xen"], default="proxmox")
    run_parser.add_argument("--vmid", required=True)
    run_parser.add_argument("--cmd", required=True)
    run_parser.add_argument("--danger-mode", action="store_true")
    run_parser.add_argument("--actor", default="operator")
    run_parser.add_argument("--audit-tag")

    gexec_parser = sub.add_parser("guest-exec")
    gexec_parser.add_argument("--vmid", required=True)
    gexec_parser.add_argument("--cmd", required=True)
    gexec_parser.add_argument("--cwd")
    gexec_parser.add_argument("--env", nargs="+", help="K=V pairs")
    gexec_parser.add_argument("--timeout", type=int)

    args = parser.parse_args()
    service = VMService.build()
    xen = XenLifecycle(runner=service.runner)
    proxmox = ProxmoxLifecycle(runner=service.runner)
    snapshot = ProxmoxSnapshot(runner=service.runner)
    file_ops = ProxmoxFileOps(runner=service.runner)
    svc_mgr = VMServiceManager(runner=service.runner)
    container_mgr = VMContainerManager(runner=service.runner)
    proxmox_config = ProxmoxConfig(runner=service.runner)
    gexec = ProxmoxGuestExec(runner=service.runner)

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

    if args.command == "guest-exec":
        env_dict = {}
        if args.env:
            for item in args.env:
                if "=" in item:
                    k, v = item.split("=", 1)
                    env_dict[k] = v
        result = asyncio.run(gexec.exec(
            vmid=args.vmid,
            cmd=args.cmd,
            cwd=args.cwd,
            env=env_dict,
            timeout=args.timeout
        ))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1
    
    if args.command == "config":
        if args.action == "get":
            result = asyncio.run(proxmox_config.get(args.vmid))
        else: # set
            params = {}
            if args.params:
                for p in args.params:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        params[k] = v
            result = asyncio.run(proxmox_config.set(args.vmid, params))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "file":
        if args.action == "put":
            result = asyncio.run(file_ops.put(vmid=args.vmid, local_path=args.local, remote_path=args.remote))
        else: # get
            result = asyncio.run(file_ops.get(vmid=args.vmid, remote_path=args.remote))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "service":
        action = getattr(svc_mgr, args.action)
        result = asyncio.run(action(vmid=args.vmid, service=args.name))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "docker":
        action = getattr(container_mgr, args.action)
        result = asyncio.run(action(vmid=args.vmid))
        print(json.dumps(result.to_dict(), sort_keys=True))
        return 0 if result.ok else 1

    if args.command == "slo":
        # Check general metrics SLO
        metrics_res = service.slo.check_metrics()
        
        # Check guest health SLO if vmid is provided
        guest_res = None
        if args.vmid:
            guest_res = asyncio.run(service.slo.check_guest_health(
                vmid=args.vmid, 
                services=args.services, 
                containers=args.containers,
                svc_mgr=svc_mgr,
                container_mgr=container_mgr
            ))
        
        final_ok = metrics_res.ok and (guest_res.ok if guest_res else True)
        output = {
            "ok": final_ok,
            "metrics": {
                "ok": metrics_res.ok,
                "details": metrics_res.details
            }
        }
        if guest_res:
            output["guest"] = {
                "ok": guest_res.ok,
                "details": guest_res.details
            }
        
        print(json.dumps(output, sort_keys=True))
        return 0 if final_ok else 1


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
