"""Status command - check instrumentation status."""
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.instrumentor.orchestrator import InstrumentationOrchestrator
from core.detector.framework_detector import FrameworkDetector

console = Console()

def status_command(container: str = None):
    """
    Check instrumentation status of containers.
    
    Args:
        container: Optional container ID or name. If not provided, checks all.
    """
    if container:
        _check_single_container(container)
    else:
        _check_all_containers()

def _check_single_container(container: str):
    """Check status of a single container."""
    console.print(f"\n📊 [bold]Checking status:[/bold] [cyan]{container}[/cyan]\n")
    
    try:
        orchestrator = InstrumentationOrchestrator()
        detector = FrameworkDetector()
        
        # Detect framework
        detection = detector.detect(container)
        
        # Check instrumentation
        is_instrumented = orchestrator.verify_instrumentation(container)
        
        # Display status
        status_color = "green" if is_instrumented else "yellow"
        status_text = "✅ Instrumented" if is_instrumented else "⚠️  Not Instrumented"
        
        console.print(Panel(
            f"Framework: [cyan]{detection.framework.value}[/cyan]\n"
            f"Language: [blue]{detection.language.value}[/blue]\n"
            f"Status: [{status_color}]{status_text}[/{status_color}]",
            title="Container Status",
            border_style=status_color
        ))
        
        if not is_instrumented:
            console.print("\n💡 [bold]To instrument this container:[/bold]")
            console.print(f"  [cyan]obs-stack instrument {container}[/cyan]\n")
        else:
            console.print("\n✅ [green]Container is instrumented and ready![/green]\n")
        
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)

def _check_all_containers():
    """Check status of all containers."""
    console.print("\n📊 [bold]Checking all containers...[/bold]\n")
    
    try:
        import docker
        docker_client = docker.from_env()
        containers = docker_client.containers.list()
        
        if not containers:
            console.print("[yellow]No running containers found.[/yellow]\n")
            return
        
        orchestrator = InstrumentationOrchestrator()
        detector = FrameworkDetector()
        
        # Build status table
        table = Table(title="Container Instrumentation Status", show_header=True, header_style="bold magenta")
        table.add_column("Container", style="cyan", width=25)
        table.add_column("Framework", style="blue", width=15)
        table.add_column("Status", style="white", width=20)
        
        for container in containers:
            try:
                detection = detector.detect(container.id)
                is_instrumented = orchestrator.verify_instrumentation(container.id)
                
                if is_instrumented:
                    status = "[green]✅ Instrumented[/green]"
                else:
                    status = "[yellow]⚠️  Not Instrumented[/yellow]"
                
                table.add_row(
                    container.name[:25],
                    detection.framework.value,
                    status
                )
            except Exception:
                table.add_row(
                    container.name[:25],
                    "error",
                    "[red]✗ Check failed[/red]"
                )
        
        console.print(table)
        console.print()
        
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)