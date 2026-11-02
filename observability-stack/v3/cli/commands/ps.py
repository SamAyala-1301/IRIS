"""Show running ObsStack containers."""
import subprocess
from rich.console import Console
from rich.table import Table

console = Console()

def ps_command():
    """Show all ObsStack-related containers."""
    console.print("\n🐳 [bold]ObsStack Containers[/bold]\n")
    
    try:
        # Get all obs-stack containers
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=obs-stack", 
             "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.CreatedAt}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print("[red]✗ Failed to get containers[/red]\n")
            return
        
        lines = result.stdout.strip().split('\n')
        if not lines or lines[0] == '':
            console.print("[yellow]No ObsStack containers found[/yellow]")
            console.print("\n💡 Start with: [cyan]obs-stack up[/cyan]\n")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Container", style="cyan", width=25)
        table.add_column("Status", style="white", width=20)
        table.add_column("Ports", style="yellow", width=30)
        table.add_column("Created", style="dim", width=20)
        
        for line in lines:
            if not line.strip():
                continue
            
            parts = line.split('\t')
            if len(parts) >= 3:
                name = parts[0].replace("obs-stack-", "")
                status = parts[1]
                ports = parts[2] if parts[2] else "N/A"
                created = parts[3] if len(parts) > 3 else "N/A"
                
                # Clean up ports
                if ports and ports != "N/A":
                    port_list = []
                    for pm in ports.split(','):
                        if '->' in pm:
                            external = pm.split('->')[0].strip()
                            port_list.append(external)
                    ports = ', '.join(port_list[:3]) if port_list else "N/A"
                    if len(port_list) > 3:
                        ports += f" +{len(port_list)-3} more"
                
                # Color status
                is_up = "Up" in status
                status_color = "green" if is_up else "red"
                status_icon = "✅" if is_up else "❌"
                
                table.add_row(
                    name,
                    f"[{status_color}]{status_icon} {status}[/{status_color}]",
                    ports,
                    created
                )
        
        console.print(table)
        
        # Summary
        running = sum(1 for line in lines if "Up" in line)
        total = len(lines)
        
        console.print(f"\n📊 [bold]{running}/{total}[/bold] containers running")
        
        if running < total:
            console.print("\n💡 [yellow]Some containers are stopped. Restart with:[/yellow] [cyan]obs-stack up[/cyan]")
        
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]\n")