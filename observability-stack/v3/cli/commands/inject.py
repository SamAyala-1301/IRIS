"""Inject observability into existing docker-compose services."""
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.docker.sidecar_injector import SidecarInjector
from core.docker.compose_generator import ComposeGenerator

console = Console()

def inject_command(service: str = None, compose_file: str = "docker-compose.yml"):
    """
    Inject observability into docker-compose services.
    
    Args:
        service: Specific service name to inject into (optional)
        compose_file: Path to docker-compose.yml
    """
    console.print("\n💉 [bold]Injecting observability...[/bold]\n")
    
    compose_path = Path.cwd() / compose_file
    
    if not compose_path.exists():
        console.print(f"[bold red]✗ {compose_file} not found![/bold red]\n")
        sys.exit(1)
    
    try:
        injector = SidecarInjector()
        generator = ComposeGenerator()
        
        # Load compose file
        compose = generator.load_existing_compose(str(compose_path))
        services = list(compose.get('services', {}).keys())
        
        if not services:
            console.print("[yellow]⚠️  No services found in compose file[/yellow]\n")
            return
        
        # If specific service provided
        if service:
            if service not in services:
                console.print(f"[bold red]✗ Service '{service}' not found![/bold red]")
                console.print(f"Available: {', '.join(services)}\n")
                sys.exit(1)
            
            services_to_inject = [service]
        else:
            # Show available services
            console.print(f"[cyan]Found {len(services)} services:[/cyan]")
            for svc in services:
                console.print(f"  • {svc}")
            console.print()
            
            if not Confirm.ask(f"[yellow]Inject into all {len(services)} services?[/yellow]"):
                console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
            
            services_to_inject = services
        
        # Inject into each service
        console.print()
        results = {}
        for svc in services_to_inject:
            console.print(f"💉 Injecting {svc}...")
            success = injector.inject_into_compose_service(svc, str(compose_path))
            results[svc] = success
        
        # Show results
        console.print()
        table = Table(title="Injection Results", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        
        for svc, success in results.items():
            if success:
                table.add_row(svc, "[green]✅ Injected[/green]")
            else:
                table.add_row(svc, "[red]❌ Failed[/red]")
        
        console.print(table)
        
        # Next steps
        successful = sum(1 for v in results.values() if v)
        if successful > 0:
            console.print(f"\n[bold green]✅ Injected {successful}/{len(results)} services[/bold green]\n")
            console.print("[white]Next steps:[/white]")
            console.print("  1. Review changes: [cyan]git diff docker-compose.yml[/cyan]")
            console.print("  2. Restart services: [cyan]docker-compose up -d[/cyan]")
            console.print("  3. Start observability: [cyan]obs-stack up[/cyan]\n")
        else:
            console.print("\n[bold red]✗ Injection failed for all services[/bold red]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)

def inject_into_running_command(container: str = None):
    """Inject observability into running containers."""
    console.print("\n💉 [bold]Injecting into running containers...[/bold]\n")
    
    try:
        injector = SidecarInjector()
        
        if container:
            # Single container
            from core.detector.framework_detector import FrameworkDetector
            detector = FrameworkDetector()
            
            console.print(f"🔍 Detecting {container}...")
            detection = detector.detect(container)
            
            console.print(f"   Framework: [cyan]{detection.framework.value}[/cyan]")
            console.print()
            
            console.print(f"💉 Injecting...")
            success = injector.inject_into_container(container, detection.framework.value)
            
            if success:
                console.print(f"\n[bold green]✅ Injected successfully[/bold green]\n")
                console.print("[white]Container is now connected to obs-stack network[/white]")
                console.print("Restart container to apply instrumentation.\n")
            else:
                console.print(f"\n[bold red]✗ Injection failed[/bold red]\n")
        else:
            # All containers
            import docker
            docker_client = docker.from_env()
            containers = docker_client.containers.list()
            
            if not containers:
                console.print("[yellow]No running containers found[/yellow]\n")
                return
            
            console.print(f"Found {len(containers)} running containers\n")
            
            if not Confirm.ask(f"[yellow]Inject into all {len(containers)} containers?[/yellow]"):
                console.print("\n[yellow]Cancelled.[/yellow]\n")
                return
            
            container_ids = [c.id for c in containers]
            results = injector.batch_inject(container_ids)
            
            # Show results
            table = Table(title="Injection Results", show_header=True)
            table.add_column("Container", style="cyan")
            table.add_column("Status", style="white")
            
            for cid, success in results.items():
                container_obj = docker_client.containers.get(cid)
                if success:
                    table.add_row(container_obj.name, "[green]✅ Injected[/green]")
                else:
                    table.add_row(container_obj.name, "[red]❌ Failed[/red]")
            
            console.print()
            console.print(table)
            console.print()
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)