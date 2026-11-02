"""Stop ObsStack observability backend."""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.docker.network_manager import NetworkManager

console = Console()

def down_command(volumes: bool = False, remove_network: bool = False):
    """
    Stop ObsStack observability backend.
    
    Args:
        volumes: Remove volumes (WARNING: deletes all data)
        remove_network: Remove obs-stack network
    """
    console.print("\n🛑 [bold]Stopping ObsStack...[/bold]\n")
    
    # Check if backend exists
    backend_dir = Path.cwd() / "backend"
    if not backend_dir.exists():
        console.print("[yellow]⚠️  Backend not found[/yellow]")
        
        # Try to clean up network anyway
        if remove_network:
            _cleanup_network()
        
        console.print()
        return
    
    compose_file = backend_dir / "docker-compose.yml"
    if not compose_file.exists():
        console.print(f"[yellow]⚠️  {compose_file} not found[/yellow]\n")
        return
    
    # Confirm if removing volumes
    if volumes:
        if not Confirm.ask(
            "[bold red]⚠️  This will DELETE ALL monitoring data. Continue?[/bold red]"
        ):
            console.print("\n[yellow]Cancelled.[/yellow]\n")
            return
    
    try:
        # Stop services
        console.print("📦 [cyan]Stopping services...[/cyan]\n")
        
        cmd = ["docker-compose", "-f", str(compose_file), "down"]
        
        if volumes:
            cmd.append("-v")
            console.print("[yellow]⚠️  Removing volumes...[/yellow]")
        
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print(f"[bold red]✗ Error:[/bold red] {result.stderr}\n")
            sys.exit(1)
        
        console.print(result.stdout)
        
        # Remove network if requested
        if remove_network:
            _cleanup_network()
        
        console.print("\n[bold green]✅ ObsStack stopped successfully[/bold green]\n")
        
    except FileNotFoundError:
        console.print("\n[bold red]✗ docker-compose not found![/bold red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)

def _cleanup_network():
    """Clean up obs-stack network."""
    console.print("\n🌐 [cyan]Removing network...[/cyan]")
    network_manager = NetworkManager()
    
    # List connected containers first
    connected = network_manager.list_connected_containers()
    if connected:
        console.print(f"   [yellow]⚠️  {len(connected)} container(s) still connected:[/yellow]")
        for container in connected:
            console.print(f"      • {container}")
        
        if not Confirm.ask("   [yellow]Disconnect and remove network?[/yellow]"):
            return
    
    if network_manager.delete_network():
        console.print("   [green]✓[/green] Network removed")
    else:
        console.print("   [yellow]⚠️  Could not remove network[/yellow]")