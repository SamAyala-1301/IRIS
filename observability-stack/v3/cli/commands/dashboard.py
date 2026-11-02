"""Generate dashboards for instrumented services."""
import os
import sys
from pathlib import Path
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.grafana.dashboard_generator import DashboardGenerator
from core.detector.framework_detector import FrameworkDetector

console = Console()

def dashboard_command(container: str = None, all_containers: bool = False):
    """
    Generate Grafana dashboards for services.
    
    Args:
        container: Specific container
        all_containers: Generate for all containers
    """
    console.print("\n📊 [bold]Generating Grafana dashboards...[/bold]\n")
    
    backend_dir = Path.cwd() / "backend"
    if not backend_dir.exists():
        console.print("[bold red]✗ Backend not initialized![/bold red]")
        console.print("Run: [cyan]obs-stack init[/cyan]\n")
        sys.exit(1)
    
    dashboard_dir = backend_dir / "grafana" / "dashboards"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        generator = DashboardGenerator()
        detector = FrameworkDetector()
        
        if container:
            _generate_single_dashboard(container, generator, detector, dashboard_dir)
        elif all_containers:
            _generate_all_dashboards(generator, detector, dashboard_dir)
        else:
            console.print("[yellow]Specify --container or --all[/yellow]\n")
            sys.exit(1)
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)

def _generate_single_dashboard(container: str, generator, detector, output_dir: Path):
    """Generate dashboard for a single container."""
    console.print(f"🔍 Detecting {container}...")
    
    try:
        detection = detector.detect(container)
        framework = detection.framework.value
        
        if framework == "unknown":
            console.print(f"[yellow]⚠️  Could not detect framework for {container}[/yellow]")
            framework = "generic"
        
        console.print(f"   Framework: [cyan]{framework}[/cyan]\n")
        
        console.print(f"📊 Generating dashboard...")
        dashboard = generator.generate_dashboard(framework, container)
        
        output_file = output_dir / f"{container}-dashboard.json"
        generator.save_dashboard(dashboard, str(output_file))
        
        console.print(f"[green]✅ Dashboard created:[/green] {output_file.name}")
        console.print(f"\n💡 [bold]Next steps:[/bold]")
        console.print(f"  1. Restart Grafana: [cyan]docker restart obs-stack-grafana[/cyan]")
        console.print(f"  2. View dashboard: [cyan]http://localhost:3001[/cyan]\n")
        
    except Exception as e:
        console.print(f"[red]✗ Failed: {e}[/red]\n")

def _generate_all_dashboards(generator, detector, output_dir: Path):
    """Generate dashboards for all containers."""
    import docker
    
    docker_client = docker.from_env()
    containers = docker_client.containers.list()
    
    if not containers:
        console.print("[yellow]No running containers found[/yellow]\n")
        return
    
    console.print(f"Found [cyan]{len(containers)}[/cyan] containers\n")
    
    generated = 0
    for container in containers:
        try:
            console.print(f"📊 Processing {container.name}...")
            detection = detector.detect(container.id)
            framework = detection.framework.value
            
            if framework == "unknown":
                console.print(f"   [dim]Skipping (unknown framework)[/dim]")
                continue
            
            dashboard = generator.generate_dashboard(framework, container.name)
            output_file = output_dir / f"{container.name}-dashboard.json"
            generator.save_dashboard(dashboard, str(output_file))
            
            console.print(f"   [green]✓ Created {output_file.name}[/green]")
            generated += 1
            
        except Exception as e:
            console.print(f"   [red]✗ Failed: {e}[/red]")
    
    console.print(f"\n[bold green]✅ Generated {generated} dashboards[/bold green]")
    
    if generated > 0:
        console.print(f"\n💡 [bold]Restart Grafana to load dashboards:[/bold]")
        console.print(f"   [cyan]docker restart obs-stack-grafana[/cyan]\n")