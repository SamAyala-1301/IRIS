"""Instrument all containers command."""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import docker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.instrumentor.orchestrator import InstrumentationOrchestrator

console = Console()

def instrument_all_command():
    """Instrument all running containers."""
    console.print("\n🔧 [bold cyan]Instrumenting all running containers...[/bold cyan]\n")
    
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list()
        
        if not containers:
            console.print("[yellow]No running containers found.[/yellow]")
            return
        
        console.print(f"Found [cyan]{len(containers)}[/cyan] running containers\n")
        
        orchestrator = InstrumentationOrchestrator()
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Instrumenting...", total=len(containers))
            
            for container in containers:
                progress.update(task, description=f"Instrumenting {container.name[:20]}...")
                
                try:
                    result = orchestrator.instrument_container(container.id)
                    results.append(result)
                except Exception as e:
                    console.print(f"[red]Error instrumenting {container.name}: {e}[/red]")
                
                progress.advance(task)
        
        # Display results table
        table = Table(title="\n🎯 Instrumentation Results", show_header=True, header_style="bold magenta")
        table.add_column("Container", style="cyan", no_wrap=True)
        table.add_column("Framework", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Endpoints", style="yellow")
        
        for result in results:
            status_color = "green" if result.is_successful() else "red"
            status_icon = "✅" if result.is_successful() else "❌"
            
            endpoints = result.get_endpoints()
            endpoint_str = ", ".join(endpoints.keys()) if endpoints else "N/A"
            
            table.add_row(
                result.container_name[:30],
                result.framework,
                f"[{status_color}]{status_icon} {result.status.value}[/{status_color}]",
                endpoint_str
            )
        
        console.print(table)
        
        # Summary
        console.print(f"\n📊 [bold]Summary:[/bold]")
        successful = sum(1 for r in results if r.is_successful())
        console.print(f"  • Total containers: {len(results)}")
        console.print(f"  • Successfully instrumented: [green]{successful}[/green]")
        console.print(f"  • Failed: [red]{len(results) - successful}[/red]")
        
        console.print("\n💡 [bold]Next Steps:[/bold]")
        console.print("  1. Restart instrumented containers")
        console.print("  2. Run: [cyan]obs-stack status[/cyan] to verify")
        console.print("  3. Start observability stack\n")
        
    except docker.errors.DockerException as e:
        console.print(f"[bold red]✗ Docker error:[/bold red] {e}")
        sys.exit(1)