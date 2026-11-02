"""Instrument command - add observability to a container."""
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.instrumentor.orchestrator import InstrumentationOrchestrator

console = Console()

def instrument_command(container: str):
    """
    Instrument a container with OpenTelemetry.
    
    Args:
        container: Container ID or name
    """
    console.print(f"\n🔧 [bold]Instrumenting container:[/bold] [cyan]{container}[/cyan]\n")
    
    try:
        orchestrator = InstrumentationOrchestrator()
        
        # Instrument
        with console.status("[bold green]Instrumenting..."):
            result = orchestrator.instrument_container(container)
        
        # Display result
        if result.is_successful():
            console.print(Panel(
                f"[bold green]✅ Successfully Instrumented[/bold green]\n\n"
                f"Framework: [cyan]{result.framework}[/cyan]\n"
                f"Status: [green]{result.status.value}[/green]",
                title="🎉 Success",
                border_style="green"
            ))
            
            # Show modifications
            if result.modifications:
                console.print("\n📝 [bold]Changes Made:[/bold]\n")
                for mod in result.modifications:
                    if mod.startswith("⚠️"):
                        console.print(f"  [yellow]{mod}[/yellow]")
                    else:
                        console.print(f"  [green]✓[/green] {mod}")
            
            # Show endpoints
            endpoints = result.get_endpoints()
            if endpoints:
                console.print("\n🔗 [bold]Monitoring Endpoints:[/bold]\n")
                table = Table(show_header=False, box=None)
                table.add_column("Type", style="cyan")
                table.add_column("Endpoint", style="white")
                
                for endpoint_type, url in endpoints.items():
                    table.add_row(endpoint_type.title(), url)
                
                console.print(table)
            
            # Next steps
            console.print("\n💡 [bold]Next Steps:[/bold]")
            console.print("  1. Restart the container: [cyan]docker restart " + container + "[/cyan]")
            console.print("  2. Verify instrumentation: [cyan]obs-stack status " + container + "[/cyan]")
            console.print("  3. Start observability stack (if not running)")
            
        else:
            console.print(Panel(
                f"[bold red]✗ Instrumentation Failed[/bold red]\n\n"
                f"Framework: [cyan]{result.framework}[/cyan]\n"
                f"Error: [red]{result.error_message}[/red]",
                title="❌ Failed",
                border_style="red"
            ))
            
            if result.modifications:
                console.print("\n⚠️  [yellow]Partial changes were made:[/yellow]")
                for mod in result.modifications:
                    console.print(f"  • {mod}")
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Error:[/bold red] {e}\n")
        sys.exit(1)