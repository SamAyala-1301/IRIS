"""Detect all running containers."""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import docker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.detector.framework_detector import FrameworkDetector

console = Console()

def detect_all_command():
    """Detect frameworks in all running containers."""
    console.print("\n🔍 [bold cyan]Scanning all running containers...[/bold cyan]\n")
    
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list()
        
        if not containers:
            console.print("[yellow]No running containers found.[/yellow]")
            return
        
        console.print(f"Found [cyan]{len(containers)}[/cyan] running containers\n")
        
        detector = FrameworkDetector()
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Detecting...", total=len(containers))
            
            for container in containers:
                progress.update(task, description=f"Scanning {container.name[:20]}...")
                
                try:
                    result = detector.detect(container.id)
                    results.append(result)
                except Exception as e:
                    console.print(f"[red]Error detecting {container.name}: {e}[/red]")
                
                progress.advance(task)
        
        # Display results table
        table = Table(title="\n🎯 Detection Results", show_header=True, header_style="bold magenta")
        table.add_column("Container", style="cyan", no_wrap=True)
        table.add_column("Framework", style="green")
        table.add_column("Language", style="blue")
        table.add_column("Version", style="yellow")
        table.add_column("Confidence", style="magenta", justify="right")
        
        for result in results:
            confidence_color = "green" if result.is_confident() else "yellow"
            
            table.add_row(
                result.container_name[:30],
                result.framework.value,
                result.language.value,
                result.version or "N/A",
                f"[{confidence_color}]{result.confidence:.0%}[/{confidence_color}]"
            )
        
        console.print(table)
        
        # Summary statistics
        console.print(f"\n📊 [bold]Summary:[/bold]")
        console.print(f"  • Total containers scanned: {len(results)}")
        confident = sum(1 for r in results if r.is_confident())
        console.print(f"  • High confidence detections: {confident}")
        console.print(f"  • Low confidence detections: {len(results) - confident}")
        
    except docker.errors.DockerException as e:
        console.print(f"[bold red]✗ Docker error:[/bold red] {e}")
        console.print("\n💡 [yellow]Tip:[/yellow] Make sure Docker daemon is running")
        sys.exit(1)