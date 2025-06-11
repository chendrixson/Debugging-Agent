"""Process utilities for cross-platform process management."""

import os
import sys
import psutil
import subprocess
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

# Handle imports for both package and direct execution
try:
    from src.utils.exceptions import ProcessError, LaunchError
except ImportError:
    from utils.exceptions import ProcessError, LaunchError


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    name: str
    exe_path: Optional[str]
    cmdline: List[str]
    status: str
    cpu_percent: float
    memory_percent: float


class ProcessManager:
    """Cross-platform process management utilities."""
    
    @staticmethod
    def list_processes() -> List[ProcessInfo]:
        """List all running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'status']):
            try:
                proc_info = ProcessInfo(
                    pid=proc.info['pid'],
                    name=proc.info['name'] or "Unknown",
                    exe_path=proc.info['exe'],
                    cmdline=proc.info['cmdline'] or [],
                    status=proc.info['status'],
                    cpu_percent=proc.cpu_percent(),
                    memory_percent=proc.memory_percent()
                )
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process disappeared or access denied, skip it
                continue
        return processes
    
    @staticmethod
    def get_process_by_pid(pid: int) -> Optional[ProcessInfo]:
        """Get process information by PID."""
        try:
            proc = psutil.Process(pid)
            return ProcessInfo(
                pid=proc.pid,
                name=proc.name(),
                exe_path=proc.exe(),
                cmdline=proc.cmdline(),
                status=proc.status(),
                cpu_percent=proc.cpu_percent(),
                memory_percent=proc.memory_percent()
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    @staticmethod
    def find_processes_by_name(name: str) -> List[ProcessInfo]:
        """Find processes by name (partial match)."""
        processes = []
        for proc_info in ProcessManager.list_processes():
            if name.lower() in proc_info.name.lower():
                processes.append(proc_info)
        return processes
    
    @staticmethod
    def launch_process(
        executable: str, 
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> subprocess.Popen:
        """Launch a new process."""
        if not os.path.exists(executable):
            raise LaunchError(f"Executable not found: {executable}")
        
        cmd = [executable]
        if args:
            cmd.extend(args)
        
        try:
            # On Windows, we want to create the process in a way that allows debugging
            if sys.platform == "win32":
                # CREATE_NEW_CONSOLE = 0x00000010
                creationflags = 0x00000010
                process = subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    env=env,
                    creationflags=creationflags,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    cwd=working_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            return process
            
        except Exception as e:
            raise LaunchError(f"Failed to launch process {executable}: {e}")
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if a process is still running."""
        try:
            return psutil.pid_exists(pid)
        except Exception:
            return False
    
    @staticmethod
    def kill_process(pid: int, force: bool = False) -> bool:
        """Kill a process by PID."""
        try:
            proc = psutil.Process(pid)
            if force:
                proc.kill()
            else:
                proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False 