"""Initialize ObsStack in a project."""
import os
import sys
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.docker.network_manager import NetworkManager
from core.docker.compose_generator import ComposeGenerator

console = Console()

def init_command(force: bool = False):
    """
    Initialize ObsStack in current directory.
    
    Creates:
    - backend/ directory with observability stack
    - obs-stack.yml for integration
    - .obsstack/ for configuration
    """
    console.print("\n🚀 [bold]Initializing ObsStack V3...[/bold]\n")
    
    current_dir = Path.cwd()
    backend_dir = current_dir / "backend"
    obsstack_dir = current_dir / ".obsstack"
    
    # Check if already initialized
    if backend_dir.exists() and not force:
        if not Confirm.ask(f"[yellow]backend/ directory already exists. Overwrite?[/yellow]"):
            console.print("\n[yellow]Initialization cancelled.[/yellow]\n")
            return
    
    try:
        # 1. Copy backend directory
        console.print("📦 [cyan]Installing observability backend...[/cyan]")
        _copy_backend_files(backend_dir, force)
        console.print("   [green]✓[/green] Backend files installed")
        
        # 2. Create .obsstack directory
        console.print("\n⚙️  [cyan]Creating configuration directory...[/cyan]")
        obsstack_dir.mkdir(exist_ok=True)
        _create_config_file(obsstack_dir / "config.yml")
        console.print("   [green]✓[/green] Configuration created")
        
        # 3. Create Docker network
        console.print("\n🌐 [cyan]Setting up Docker network...[/cyan]")
        network_manager = NetworkManager()
        network_manager.create_network()
        
        # 4. Check for existing docker-compose.yml
        compose_file = current_dir / "docker-compose.yml"
        if compose_file.exists():
            console.print("\n📄 [cyan]Found existing docker-compose.yml[/cyan]")
            
            if Confirm.ask("   [yellow]Generate integration file (obs-stack.yml)?[/yellow]"):
                _generate_integration_file(current_dir)
        else:
            console.print("\n[yellow]ℹ️  No docker-compose.yml found[/yellow]")
            console.print("   Create one or use: [cyan]obs-stack inject[/cyan] later")
        
        # 5. Success message
        console.print(Panel(
            "[bold green]✅ ObsStack initialized successfully![/bold green]\n\n"
            "[white]Next steps:[/white]\n"
            "  1. Start observability stack: [cyan]obs-stack up[/cyan]\n"
            "  2. Instrument your apps: [cyan]obs-stack instrument <container>[/cyan]\n"
            "  3. View dashboards: [cyan]http://localhost:3001[/cyan] (admin/obsstack)",
            title="🎉 Success",
            border_style="green"
        ))
        
        console.print()
        
    except Exception as e:
        console.print(f"\n[bold red]✗ Initialization failed:[/bold red] {e}\n")
        sys.exit(1)

def _copy_backend_files(backend_dir: Path, force: bool):
    """Copy backend files from package to project."""
    # Get package backend directory
    package_dir = Path(__file__).parent.parent.parent / "backend"
    
    if not package_dir.exists():
        # If backend not in package, create from templates
        _create_backend_structure(backend_dir)
    else:
        # Copy from package
        if backend_dir.exists() and force:
            shutil.rmtree(backend_dir)
        shutil.copytree(package_dir, backend_dir)

def _create_backend_structure(backend_dir: Path):
    """Create backend directory structure if not exists."""
    backend_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (backend_dir / "prometheus").mkdir(exist_ok=True)
    (backend_dir / "grafana").mkdir(exist_ok=True)
    (backend_dir / "otel-collector").mkdir(exist_ok=True)
    (backend_dir / "loki").mkdir(exist_ok=True)
    (backend_dir / "tempo").mkdir(exist_ok=True)
    (backend_dir / "promtail").mkdir(exist_ok=True)
    (backend_dir / "alertmanager").mkdir(exist_ok=True)
    
    # Note: Actual config files should be copied from the artifacts we created
    console.print("   [yellow]⚠️  Backend configs need to be created manually[/yellow]")
    console.print("   [yellow]   Use the configs from v3/backend/ directory[/yellow]")

def _create_config_file(config_path: Path):
    """Create ObsStack configuration file."""
    config = """# ObsStack V3 Configuration

version: "3.0.0"

# Backend settings
backend:
  network: "obs-stack-network"
  prometheus_port: 9090
  grafana_port: 3001
  otel_collector_port: 4317

# Instrumentation settings
instrumentation:
  auto_detect: true
  auto_instrument: false
  frameworks:
    - flask
    - django
    - fastapi
    - express

# Monitoring settings
monitoring:
  metrics_interval: 15s
  log_level: info
  retention:
    metrics: 15d
    logs: 7d
    traces: 24h
"""
    
    with open(config_path, 'w') as f:
        f.write(config)

def _generate_integration_file(project_dir: Path):
    """Generate obs-stack.yml integration file."""
    import yaml
    
    # Read existing compose
    with open(project_dir / "docker-compose.yml", 'r') as f:
        compose = yaml.safe_load(f)
    
    # Get service names
    services = list(compose.get('services', {}).keys())
    
    console.print(f"   Found {len(services)} services: {', '.join(services)}")
    
    # Generate integration
    generator = ComposeGenerator()
    integration = generator.generate_integration_compose(services)
    
    # Save
    output_file = project_dir / "obs-stack.yml"
    generator.save_compose_file(integration, str(output_file))
    
    console.print(f"   [green]✓[/green] Generated {output_file.name}")
    console.print(f"\n   [cyan]Start with:[/cyan] docker-compose -f docker-compose.yml -f obs-stack.yml up")