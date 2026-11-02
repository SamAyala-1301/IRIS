"""Validate detection for a container."""
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.detector.framework_detector import FrameworkDetector
from core.detector.framework_db import get_framework_signature

console = Console()

def validate_command(container: str):
    """
    Validate detection and show detailed breakdown.
    
    Args:
        container: Container ID or name
    """
    console.print(f"\n🔬 [bold]Validating detection for:[/bold] [cyan]{container}[/cyan]\n")
    
    try:
        detector = FrameworkDetector()
        result = detector.detect(container)
        
        # Show detection result
        console.print(Panel(
            f"[bold green]{result.framework.value}[/bold green] ({result.language.value})\n"
            f"Confidence: [{'green' if result.is_confident() else 'yellow'}]{result.confidence:.1%}[/]",
            title="🎯 Detection Result",
            border_style="green" if result.is_confident() else "yellow"
        ))
        
        # Show detailed hints from each detector
        console.print("\n📋 [bold]Detection Breakdown:[/bold]\n")
        
        metadata = result.metadata
        
        # Create breakdown table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Detector", style="cyan", width=20)
        table.add_column("Findings", style="white")
        table.add_column("Contribution", style="magenta", justify="right")
        
        # Calculate contributions
        total_hints = sum(
            len([v for v in hints.values() if isinstance(v, (int, float))])
            for hints in metadata.values()
        )
        
        for detector_name, hints in metadata.items():
            if hints:
                findings = [f"{k.value if hasattr(k, 'value') else k}: {v:.2f}" 
                           for k, v in hints.items() if isinstance(v, (int, float))]
                
                if findings:
                    contribution = (len(findings) / total_hints * 100) if total_hints > 0 else 0
                    table.add_row(
                        detector_name.replace('_hints', '').title(),
                        "\n".join(findings[:3]),  # Show top 3
                        f"{contribution:.0f}%"
                    )
        
        console.print(table)
        
        # Show framework signature if detected
        if result.framework != result.framework.UNKNOWN:
            console.print("\n📖 [bold]Framework Information:[/bold]\n")
            signature = get_framework_signature(result.framework)
            
            if signature:
                info_table = Table(show_header=False, box=None)
                info_table.add_column("Property", style="cyan", width=20)
                info_table.add_column("Value", style="white")
                
                info_table.add_row("Name", signature.display_name)
                info_table.add_row("Language", signature.language.value)
                info_table.add_row("Description", signature.description)
                if result.version:
                    info_table.add_row("Detected Version", result.version)
                info_table.add_row("Common Ports", ", ".join(map(str, signature.common_ports)))
                
                console.print(info_table)
        
        # Confidence assessment
        console.print("\n✅ [bold]Assessment:[/bold]\n")
        if result.is_confident(0.8):
            console.print("  [bold green]✓[/bold green] Very high confidence - detection is reliable")
        elif result.is_confident(0.6):
            console.print("  [bold yellow]⚠[/bold yellow] Moderate confidence - likely correct but verify")
        else:
            console.print("  [bold red]✗[/bold red] Low confidence - manual verification recommended")
        
    except ValueError as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Unexpected error:[/bold red] {e}")
        sys.exit(1)
