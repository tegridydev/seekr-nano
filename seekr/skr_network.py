import socket
import ssl
import asyncio
import ipaddress
import psutil
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from scapy.all import ARP, Ether, srp
from concurrent.futures import ThreadPoolExecutor, as_completed
import speedtest

console = Console()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        console.print(f"[bold red]Error getting local IP: {e}[/bold red]")
        return None

def get_network_interface(local_ip):
    if not local_ip:
        return None
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address == local_ip:
                return interface
    return None

def get_network_range(local_ip):
    if not local_ip:
        return None
    try:
        return str(ipaddress.ip_network(f"{local_ip}/24", strict=False))
    except ValueError as e:
        console.print(f"[bold red]Error getting network range: {e}[/bold red]")
        return None

async def async_scan_network(target_ip):
    loop = asyncio.get_running_loop()
    arp = ARP(pdst=target_ip)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp

    def send_packet():
        return srp(packet, timeout=3, verbose=0)[0]

    with console.status("[bold cyan]Sending ARP requests to discover devices...[/bold cyan]"):
        result = await loop.run_in_executor(None, send_packet)
    
    devices = [{'ip': received.psrc, 'mac': received.hwsrc} for sent, received in result]

    if not devices:
        console.print("[bold yellow]No devices found. Check your network settings and try again.[/bold yellow]")
    return devices

def display_devices(devices):
    table = Table(title="Available Devices")
    table.add_column("Index", justify="right", style="cyan", no_wrap=True)
    table.add_column("IP Address", style="magenta")
    table.add_column("MAC Address", style="green")

    for index, device in enumerate(devices):
        table.add_row(str(index + 1), device['ip'], device['mac'])

    console.print(table)

def scan_port(target, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((target, port))
    sock.close()
    return port if result == 0 else None

def check_open_ports(target, port_range=(1, 1000)):
    open_ports = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_port = {executor.submit(scan_port, target, port): port for port in range(port_range[0], port_range[1] + 1)}
        with Progress() as progress:
            task = progress.add_task(f"[cyan]Scanning {target}", total=port_range[1] - port_range[0] + 1)
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    result = future.result()
                    if result:
                        open_ports.append(result)
                    progress.update(task, advance=1, description=f"[cyan]Scanning {target} - Port {port}")
                except Exception as e:
                    console.print(f"[bold red]An error occurred while scanning port {port}: {str(e)}[/bold red]")
    return open_ports

def get_service_name(port):
    try:
        return socket.getservbyport(port)
    except OSError:
        return "Unknown"

def get_ssl_info(ip, port):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((ip, port), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=ip) as secure_sock:
                cert = secure_sock.getpeercert()
                return {
                    "Issuer": dict(x[0] for x in cert['issuer']),
                    "Subject": dict(x[0] for x in cert['subject']),
                    "Version": cert['version'],
                    "Serial Number": cert['serialNumber'],
                }
    except Exception as e:
        return f"SSL Error: {str(e)}"

def get_http_info(ip, port):
    try:
        url = f"http://{ip}:{port}"
        response = requests.get(url, timeout=3)
        return {
            "Status Code": response.status_code,
            "Server": response.headers.get('Server', 'Unknown'),
            "Content-Type": response.headers.get('Content-Type', 'Unknown'),
        }
    except requests.RequestException as e:
        return f"HTTP Error: {str(e)}"

def analyze_port(ip, port):
    service_name = get_service_name(port)
    result = {
        "Port": port,
        "Service": service_name,
        "SSL Info": None,
        "HTTP Info": None,
    }

    if service_name in ['https', 'ssl']:
        result["SSL Info"] = get_ssl_info(ip, port)

    if service_name in ['http', 'https']:
        result["HTTP Info"] = get_http_info(ip, port)

    return result

def closer_look(ip, open_ports):
    console.print(f"\n[bold cyan]Performing a closer look at open ports on {ip}...[/bold cyan]")
    results = []

    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing ports...", total=len(open_ports))
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_port = {executor.submit(analyze_port, ip, port): port for port in open_ports}
            for future in as_completed(future_to_port):
                port = future_to_port[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    console.print(f"[bold red]An error occurred while analyzing port {port}: {str(e)}[/bold red]")
                progress.update(task, advance=1)

    display_analysis_results(results)

def display_analysis_results(results):
    table = Table(title="Port Analysis Results")
    table.add_column("Port", style="cyan")
    table.add_column("Service", style="magenta")
    table.add_column("SSL Info", style="green")
    table.add_column("HTTP Info", style="yellow")

    for result in results:
        ssl_info = str(result["SSL Info"]) if result["SSL Info"] else "N/A"
        http_info = str(result["HTTP Info"]) if result["HTTP Info"] else "N/A"
        table.add_row(
            str(result["Port"]),
            result["Service"],
            ssl_info,
            http_info
        )

    console.print(table)

async def scan_single_device(target):
    console.print(f"\n[bold cyan]Scanning {target}...[/bold cyan]")
    open_ports = check_open_ports(target)

    if open_ports:
        console.print(f"\n[bold green]Open ports on {target}:[/bold green] {sorted(open_ports)}")
        closer_look(target, open_ports)
    else:
        console.print("\n[bold yellow]No open ports found.[/bold yellow]")

async def scan_all_devices(devices):
    for device in devices:
        await scan_single_device(device['ip'])

def network_speed_test():
    console.print("[cyan]Performing network speed test...[/cyan]")
    st = speedtest.Speedtest()
    
    with Progress() as progress:
        download_task = progress.add_task("[green]Testing download speed...", total=100)
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        progress.update(download_task, completed=100)

        upload_task = progress.add_task("[yellow]Testing upload speed...", total=100)
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        progress.update(upload_task, completed=100)

    ping = st.results.ping

    table = Table(title="Network Speed Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Download Speed", f"{download_speed:.2f} Mbps")
    table.add_row("Upload Speed", f"{upload_speed:.2f} Mbps")
    table.add_row("Ping", f"{ping:.2f} ms")

    console.print(table)

def analyze_network_connections():
    connections = psutil.net_connections()
    
    table = Table(title="Current Network Connections")
    table.add_column("Local Address", style="cyan")
    table.add_column("Local Port", style="magenta")
    table.add_column("Remote Address", style="green")
    table.add_column("Remote Port", style="yellow")
    table.add_column("Status", style="blue")

    for conn in connections:
        if conn.laddr and conn.raddr:
            table.add_row(
                conn.laddr.ip,
                str(conn.laddr.port),
                conn.raddr.ip,
                str(conn.raddr.port),
                conn.status
            )

    console.print(table)

# Additional network-related functions can be added here as needed