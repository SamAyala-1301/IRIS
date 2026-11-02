"""Main CLI entry point - ENHANCED."""
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.detector.framework_detector import FrameworkDetector
from core.detector.framework_db import get_all_frameworks
from cli.commands.detect_all import detect_all_command
from cli.commands.validate import validate_command
from cli.commands.instrument import instrument_command
from cli.commands.instrument_all import instrument_all_command
from cli.commands.status import status_command
from cli.commands.init import init_command
from cli.commands.up import up_command
from cli.commands.down import down_command
from cli.commands.inject import inject_command, inject_into_running_command
from cli.commands.logs import logs_command
from cli.commands.ps import ps_command
from cli.commands.dashboard import dashboard_command
from cli.commands.health import health_command

console = Console()

@click.group()
@click.version_option(version="3.0.0-alpha", prog_name="obs-stack")
def cli():
    """
    🚀 ObsStack V3 - Instant Observability for Any App
    
    Auto-detect frameworks and add monitoring with zero code changes.
    """
    pass

@cli.command()
def version():
    """Show version information."""
    console.print("\n[bold blue]ObsStack v3.0.0-alpha[/bold blue]")
    console.print("Auto-detection and instrumentation system")
    console.print("\n[dim]Status: MS2 In Progress - Docker Integration 🚀[/dim]\n")

@cli.command()
@click.argument('container')
def detect(container):
    """
    Detect framework in a specific container.
    
    CONTAINER: Container ID or name
    
    Example: obs-stack detect flask-app
    
    Tip: To scan all containers, use: obs-stack detect-all
    """
    console.print(f"\n🔍 Detecting framework in: [cyan]{container}[/cyan]\n")
    
    try:
        detector = FrameworkDetector()
        result = detector.detect(container)
        
        # Create results table
        table = Table(title="Detection Results", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Container ID", result.container_id[:12])
        table.add_row("Container Name", result.container_name)
        table.add_row("Framework", result.framework.value)
        table.add_row("Language", result.language.value)
        if result.version:
            table.add_row("Version", result.version)
        table.add_row("Confidence", f"{result.confidence:.2%}")
        
        console.print(table)
        
        # Confidence indicator
        if result.is_confident():
            console.print(f"\n[bold green]✓[/bold green] High confidence detection")
        else:
            console.print(f"\n[bold yellow]⚠[/bold yellow] Low confidence - run 'obs-stack validate {container}' for details")
        
    except ValueError as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        console.print(f"\n[yellow]💡 Tip:[/yellow] To scan all containers, use: [cyan]obs-stack detect-all[/cyan]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Unexpected error:[/bold red] {e}")
        sys.exit(1)

@cli.command(name='detect-all')
def detect_all():
    """Scan and detect frameworks in all running containers."""
    detect_all_command()

@cli.command()
@click.argument('container')
def validate(container):
    """
    Validate detection with detailed breakdown.
    
    CONTAINER: Container ID or name
    
    Shows which detectors contributed to the result.
    """
    validate_command(container)

@cli.command(name='list-frameworks')
def list_frameworks():
    """List all supported frameworks."""
    frameworks = get_all_frameworks()
    
    console.print("\n📚 [bold]Supported Frameworks:[/bold]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Framework", style="cyan", width=15)
    table.add_column("Language", style="blue", width=10)
    table.add_column("Description", style="white")
    
    for sig in frameworks:
        table.add_row(
            sig.display_name,
            sig.language.value,
            sig.description
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(frameworks)} frameworks[/dim]\n")

@cli.command()
def list_indicators():
    """Show all detection indicators."""
    detector = FrameworkDetector()
    indicators = detector.get_indicators()
    
    console.print("\n[bold]🔍 Detection Indicators:[/bold]\n")
    
    for category, data in indicators.items():
        console.print(f"[cyan]{category.replace('_', ' ').title()}:[/cyan]")
        rprint(f"  {data}\n")

@cli.command()
@click.argument('container')
def instrument(container):
    """
    Instrument a container with OpenTelemetry.
    
    CONTAINER: Container ID or name
    
    Adds observability to detected framework automatically.
    """
    instrument_command(container)

@cli.command(name='instrument-all')
def instrument_all():
    """Instrument all running containers."""
    instrument_all_command()

@cli.command()
@click.argument('container', required=False)
def status(container):
    """
    Check instrumentation status.
    
    CONTAINER: Optional container ID or name. If omitted, checks all.
    
    Example: obs-stack status flask-app
    """
    status_command(container)

# MS2 Commands - Docker Integration
@cli.command()
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init(force):
    """
    Initialize ObsStack in current directory.
    
    Creates backend infrastructure and configuration.
    """
    init_command(force)

@cli.command()
@click.option('--build', is_flag=True, help='Rebuild images')
@click.option('--no-detach', is_flag=True, help='Run in foreground')
def up(build, no_detach):
    """
    Start ObsStack observability backend.
    
    Starts Prometheus, Grafana, Loki, Tempo, and OTEL Collector.
    """
    up_command(detach=not no_detach, build=build)

@cli.command()
@click.option('--volumes', is_flag=True, help='Remove data volumes (WARNING: deletes all data)')
@click.option('--network', is_flag=True, help='Remove obs-stack network')
def down(volumes, network):
    """
    Stop ObsStack observability backend.
    
    Use --volumes to also delete all monitoring data.
    """
    down_command(volumes=volumes, remove_network=network)

@cli.command()
@click.option('--service', '-s', help='Specific service to inject into')
@click.option('--file', '-f', default='docker-compose.yml', help='Compose file path')
def inject(service, file):
    """
    Inject observability into docker-compose services.
    
    Modifies docker-compose.yml to add obs-stack integration.
    """
    inject_command(service=service, compose_file=file)

@cli.command(name='inject-running')
@click.argument('container', required=False)
def inject_running(container):
    """
    Inject observability into running containers.
    
    Connects containers to obs-stack network.
    """
    inject_into_running_command(container)

@cli.command()
@click.option('--service', '-s', help='Specific service')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--tail', '-n', default=100, help='Number of lines to show')
def logs(service, follow, tail):
    """
    View logs from ObsStack services.
    
    Example: obs-stack logs -f grafana
    """
    logs_command(service=service, follow=follow, tail=tail)

@cli.command()
def ps():
    """
    Show all ObsStack containers.
    
    Displays status, ports, and uptime for all services.
    """
    ps_command()

if __name__ == '__main__':
    cli()