"""Start ObsStack observability backend."""
import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.docker.network_manager import NetworkManager

console = Console()

def up_command(detach: bool = True, build: bool = False):
    """
    Start ObsStack observability backend.
    
    Args:
        detach: Run in background
        build: Rebuild images before starting
    """
    console.print("\n🚀 [bold]Starting ObsStack observability backend...[/bold]\n")
    
    # Check if backend exists
    backend_dir = Path.cwd() / "backend"
    if not backend_dir.exists():
        console.print("[bold red]✗ Backend not found![/bold red]")
        console.print("\n[yellow]Run first:[/yellow] [cyan]obs-stack init[/cyan]\n")
        sys.exit(1)
    
    compose_file = backend_dir / "docker-compose.yml"
    if not compose_file.exists():
        console.print(f"[bold red]✗ {compose_file} not found![/bold red]\n")
        sys.exit(1)
    
    try:
        # 1. Create network
        console.print("🌐 [cyan]Setting up network...[/cyan]")
        network_manager = NetworkManager()
        network_manager.create_network()
        
        # 2. Start services
        console.print("\n📦 [cyan]Starting services...[/cyan]\n")
        
        cmd = ["docker-compose", "-f", str(compose_file)]
        
        if build:
            cmd.extend(["up", "--build"])
        else:
            cmd.append("up")
        
        if detach:
            cmd.append("-d")
        
        result = subprocess.run(
            cmd,
            cwd=backend_dir,
            capture_output=False,
            text=True
        )
        
        if result.returncode != 0:
            console.print("\n[bold red]✗ Failed to start services[/bold red]\n")
            sys.exit(1)
        
        # 3. Wait a bit for services to start
        import time
        console.print("\n⏳ [cyan]Waiting for services to start...[/cyan]")
        time.sleep(5)
        
        # 4. Check service status
        console.print()
        _check_services(backend_dir)
        
        # 5. Success message
        console.print(Panel(
            "[bold green]✅ ObsStack is running![/bold green]\n\n"
            "[white]Access:[/white]\n"
            "  📊 Grafana:    [cyan]http://localhost:3001[/cyan] (admin/obsstack)\n"
            "  📈 Prometheus: [cyan]http://localhost:9090[/cyan]\n"
            "  📝 Loki:       [cyan]http://localhost:3100[/cyan]\n"
            "  🔍 Tempo:      [cyan]http://localhost:3200[/cyan]\n\n"
            "[white]Next:[/white]\n"
            "  • Instrument apps: [cyan]obs-stack instrument <container>[/cyan]\n"
            "  • View logs: [cyan]obs-stack logs[/cyan]\n"
            "  • Stop: [cyan]obs-stack down[/cyan]",
            title="🎉 Success",
            border_style="green"
        ))
        console.print()
        
    except FileNotFoundError:
        console.print("\n[bold red]✗ docker-compose not found![/bold red]")
        console.print("Install: [cyan]https://docs.docker.com/compose/install/[/cyan]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)

def _check_services(backend_dir: Path):
    """Check status of backend services."""
    try:
        # Use docker ps directly instead of docker-compose ps
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=obs-stack", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print("[yellow]⚠️  Could not check service status[/yellow]")
            return
        
        lines = result.stdout.strip().split('\n')
        if not lines or lines[0] == '':
            console.print("[yellow]⚠️  No services found[/yellow]")
            return
        
        # Create status table
        table = Table(title="Service Status", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan", width=20)
        table.add_column("Status", style="white", width=15)
        table.add_column("Ports", style="yellow")
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0].replace("obs-stack-", "")
                status_text = parts[1]
                ports = parts[2] if len(parts) > 2 else "N/A"
                
                # Parse status
                is_up = "Up" in status_text
                status_color = "green" if is_up else "red"
                status_icon = "✅" if is_up else "❌"
                
                # Clean up ports display
                if ports and ports != "N/A":
                    # Extract just the external ports
                    port_list = []
                    for port_mapping in ports.split(','):
                        if '->' in port_mapping:
                            external = port_mapping.split('->')[0].strip()
                            port_list.append(external)
                    ports = ', '.join(port_list) if port_list else "N/A"
                
                table.add_row(
                    name,
                    f"[{status_color}]{status_icon} {'Running' if is_up else 'Down'}[/{status_color}]",
                    ports
                )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[yellow]⚠️  Could not check service status: {e}[/yellow]")