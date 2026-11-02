"""Health check for ObsStack components."""
import os
import sys
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.performance.optimizer import PerformanceOptimizer

console = Console()

def health_command():
    """Check health of ObsStack components."""
    console.print("\n🏥 [bold]ObsStack Health Check[/bold]\n")
    
    # System requirements
    console.print("[cyan]📊 System Requirements[/cyan]")
    _check_system_requirements()
    console.print()
    
    # Service health
    console.print("[cyan]🔍 Service Health[/cyan]")
    _check_services_health()
    console.print()
    
    # Overall status
    _show_overall_status()

def _check_system_requirements():
    """Check system requirements."""
    optimizer = PerformanceOptimizer()
    meets_req, warnings = optimizer.check_system_requirements()
    
    table = Table(show_header=False, box=None)
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="white")
    
    # Memory
    memory_gb = optimizer.system_memory / (1024 ** 3)
    memory_status = "✅" if memory_gb >= 4 else "⚠️"
    table.add_row("Memory", f"{memory_status} {memory_gb:.1f}GB")
    
    # CPU
    cpu_status = "✅" if optimizer.cpu_count >= 2 else "⚠️"
    table.add_row("CPU Cores", f"{cpu_status} {optimizer.cpu_count}")
    
    # Disk
    import psutil
    disk = psutil.disk_usage('/')
    free_gb = disk.free / (1024 ** 3)
    disk_status = "✅" if free_gb >= 10 else "⚠️"
    table.add_row("Free Disk", f"{disk_status} {free_gb:.1f}GB")
    
    console.print(table)
    
    if warnings:
        console.print()
        for warning in warnings:
            console.print(f"  [yellow]⚠️  {warning}[/yellow]")

def _check_services_health():
    """Check health of all services."""
    services = [
        ("Prometheus", "http://localhost:9090/-/healthy", "metrics"),
        ("Grafana", "http://localhost:3001/api/health", "dashboards"),
        ("Loki", "http://localhost:3100/ready", "logs"),
        ("Tempo", "http://localhost:3200/ready", "traces"),
        ("OTEL Collector", "http://localhost:13133/", "telemetry"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan", width=20)
    table.add_column("Status", style="white", width=15)
    table.add_column("Response Time", style="yellow", width=15)
    table.add_column("Purpose", style="dim")
    
    all_healthy = True
    
    for name, url, purpose in services:
        try:
            import time
            start = time.time()
            response = requests.get(url, timeout=5)
            duration = (time.time() - start) * 1000
            
            if response.status_code == 200:
                status = "[green]✅ Healthy[/green]"
                response_time = f"{duration:.0f}ms"
            else:
                status = "[yellow]⚠️  Degraded[/yellow]"
                response_time = f"{duration:.0f}ms"
                all_healthy = False
        except requests.exceptions.ConnectionError:
            status = "[red]❌ Down[/red]"
            response_time = "N/A"
            all_healthy = False
        except requests.exceptions.Timeout:
            status = "[yellow]⚠️  Timeout[/yellow]"
            response_time = ">5000ms"
            all_healthy = False
        except Exception as e:
            status = f"[red]❌ Error[/red]"
            response_time = "N/A"
            all_healthy = False
        
        table.add_row(name, status, response_time, purpose)
    
    console.print(table)
    return all_healthy

def _show_overall_status():
    """Show overall system status."""
    # Check if services are running
    import subprocess
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=obs-stack", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        running_services = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        expected_services = 7  # Total ObsStack services
        
        if running_services == expected_services:
            status_color = "green"
            status_icon = "✅"
            status_text = "All systems operational"
        elif running_services > 0:
            status_color = "yellow"
            status_icon = "⚠️"
            status_text = f"Partially operational ({running_services}/{expected_services} services)"
        else:
            status_color = "red"
            status_icon = "❌"
            status_text = "ObsStack is not running"
        
        console.print(Panel(
            f"[bold {status_color}]{status_icon} {status_text}[/bold {status_color}]",
            title="Overall Status",
            border_style=status_color
        ))
        
        if running_services < expected_services and running_services > 0:
            console.print("\n💡 [yellow]Some services are down. Try:[/yellow] [cyan]obs-stack up[/cyan]")
        elif running_services == 0:
            console.print("\n💡 [yellow]Start ObsStack with:[/yellow] [cyan]obs-stack up[/cyan]")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]Could not determine status: {e}[/red]\n")