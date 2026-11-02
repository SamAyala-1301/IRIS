"""View ObsStack logs."""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def logs_command(service: str = None, follow: bool = False, tail: int = 100):
    """
    View logs from ObsStack services.
    
    Args:
        service: Specific service to view (optional)
        follow: Follow log output
        tail: Number of lines to show
    """
    backend_dir = Path.cwd() / "backend"
    
    if not backend_dir.exists():
        console.print("[bold red]✗ Backend not found![/bold red]")
        console.print("Run: [cyan]obs-stack init[/cyan]\n")
        sys.exit(1)
    
    compose_file = backend_dir / "docker-compose.yml"
    if not compose_file.exists():
        console.print(f"[bold red]✗ {compose_file} not found![/bold red]\n")
        sys.exit(1)
    
    try:
        cmd = ["docker-compose", "-f", str(compose_file), "logs"]
        
        if follow:
            cmd.append("-f")
        
        cmd.extend(["--tail", str(tail)])
        
        if service:
            cmd.append(service)
        
        # Run interactively
        subprocess.run(cmd, cwd=backend_dir)
        
    except FileNotFoundError:
        console.print("\n[bold red]✗ docker-compose not found![/bold red]\n")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Logs stopped[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)