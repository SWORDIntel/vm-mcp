import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from vm_mcp.proxmox import ProxmoxFileOps
from vm_mcp.models import CommandResult

@pytest.mark.asyncio
async def test_proxmox_file_put_missing_local():
    runner = MagicMock()
    ops = ProxmoxFileOps(runner=runner)
    
    result = await ops.put("100", "nonexistent.txt", "/tmp/remote.txt")
    assert result.ok is False
    assert "Local file not found" in result.stderr
    runner.run.assert_not_called()

@pytest.mark.asyncio
async def test_proxmox_file_put_success():
    runner = MagicMock()
    # Mock runner.run to be an AsyncMock that returns a CommandResult
    runner.run = AsyncMock(return_value=CommandResult(
        ok=True, code=0, stdout="", stderr="", duration_ms=10, vmid="100", cmd="qm guest file write ..."
    ))
    
    ops = ProxmoxFileOps(runner=runner)
    
    # We need a real file to exist for the check
    with patch("pathlib.Path.exists", return_value=True):
        result = await ops.put("100", "local.txt", "/tmp/remote.txt")
        assert result.ok is True
        runner.run.assert_called_once()
        call_args = runner.run.call_args[1]
        assert "qm guest file write 100 /tmp/remote.txt local.txt" in call_args["cmd"]

@pytest.mark.asyncio
async def test_proxmox_file_get_success():
    runner = MagicMock()
    runner.run = AsyncMock(return_value=CommandResult(
        ok=True, code=0, stdout="file content", stderr="", duration_ms=10, vmid="100", cmd="qm guest file read ..."
    ))
    
    ops = ProxmoxFileOps(runner=runner)
    result = await ops.get("100", "/tmp/remote.txt")
    
    assert result.ok is True
    assert result.stdout == "file content"
    runner.run.assert_called_once()
    call_args = runner.run.call_args[1]
    assert "qm guest file read 100 /tmp/remote.txt" in call_args["cmd"]
