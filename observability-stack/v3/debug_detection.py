#!/usr/bin/env python3
"""Debug detection for flask-test container."""

import docker
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.detector.scanners.port_scanner import PortScanner
from core.detector.scanners.process_scanner import ProcessScanner
from core.detector.scanners.http_prober import HTTPProber
from core.detector.analyzers.env_analyzer import EnvAnalyzer
from core.detector.analyzers.file_analyzer import FileAnalyzer
from core.detector.analyzers.package_analyzer import PackageAnalyzer

def debug_container(container_name):
    """Debug detection for a specific container."""
    client = docker.from_env()
    
    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound:
        print(f"❌ Container '{container_name}' not found")
        return
    
    print(f"🔍 Debugging detection for: {container_name}")
    print("=" * 60)
    
    # 1. Port Scanner
    print("\n1️⃣ PORT SCANNER:")
    scanner = PortScanner()
    result = scanner.scan(container)
    print(f"   Result: {result}")
    
    # Show port info
    ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
    print(f"   Exposed ports: {list(ports.keys())}")
    
    # 2. Process Scanner
    print("\n2️⃣ PROCESS SCANNER:")
    scanner = ProcessScanner()
    result = scanner.scan(container)
    print(f"   Result: {result}")
    
    # Show actual processes
    try:
        exec_result = container.exec_run("ps aux")
        if exec_result.exit_code == 0:
            processes = exec_result.output.decode('utf-8')
            print("   Running processes:")
            for line in processes.split('\n')[:5]:  # Show first 5
                print(f"     {line}")
    except:
        print("   ⚠️ Could not list processes")
    
    # 3. HTTP Prober
    print("\n3️⃣ HTTP PROBER:")
    prober = HTTPProber()
    result = prober.probe(container)
    print(f"   Result: {result}")
    
    # Show container IP
    networks = container.attrs['NetworkSettings']['Networks']
    for network_name, network_data in networks.items():
        print(f"   Network: {network_name}, IP: {network_data.get('IPAddress')}")
    
    # 4. Environment Analyzer
    print("\n4️⃣ ENVIRONMENT ANALYZER:")
    analyzer = EnvAnalyzer()
    result = analyzer.analyze(container)
    print(f"   Result: {result}")
    
    # Show env vars
    env_vars = container.attrs.get('Config', {}).get('Env', [])
    print("   Environment variables:")
    for var in env_vars[:10]:  # Show first 10
        print(f"     {var}")
    
    # 5. File Analyzer
    print("\n5️⃣ FILE ANALYZER:")
    analyzer = FileAnalyzer()
    result = analyzer.analyze(container)
    print(f"   Result: {result}")
    
    # Check for specific files
    print("   Checking files:")
    for filename in ['requirements.txt', 'app.py', 'Pipfile']:
        try:
            exec_result = container.exec_run(f"test -f {filename}")
            exists = "✓" if exec_result.exit_code == 0 else "✗"
            print(f"     {exists} {filename}")
        except:
            print(f"     ? {filename}")
    
    # 6. Package Analyzer
    print("\n6️⃣ PACKAGE ANALYZER:")
    analyzer = PackageAnalyzer()
    result = analyzer.analyze(container)
    print(f"   Result: {result}")
    
    # Show requirements.txt content
    try:
        exec_result = container.exec_run("cat requirements.txt")
        if exec_result.exit_code == 0:
            content = exec_result.output.decode('utf-8')
            print("   requirements.txt content:")
            print(f"     {content.strip()}")
    except:
        print("   ⚠️ Could not read requirements.txt")
    
    print("\n" + "=" * 60)
    print("✅ Debug complete")

if __name__ == '__main__':
    container = sys.argv[1] if len(sys.argv) > 1 else 'flask-test'
    debug_container(container)