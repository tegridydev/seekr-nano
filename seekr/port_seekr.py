import asyncio
import socket
import psutil
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from scapy.all import ARP, Ether, srp
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

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

async def scan_single_device(target):
    console.print(f"\n[bold cyan]Scanning {target}...[/bold cyan]")
    open_ports = check_open_ports(target)

    if open_ports:
        console.print(f"\n[bold green]Open ports on {target}:[/bold green] {sorted(open_ports)}")
    else:
        console.print("\n[bold yellow]No open ports found.[/bold yellow]")

async def scan_all_devices(devices):
    for device in devices:
        await scan_single_device(device['ip'])

async def main_menu():
    local_ip = get_local_ip()
    if not local_ip:
        return

    network_interface = get_network_interface(local_ip)
    network_range = get_network_range(local_ip)

    console.print(f"[bold cyan]Local IP Address: {local_ip}[/bold cyan]")
    console.print(f"[bold cyan]Network Interface: {network_interface}[/bold cyan]")
    console.print(f"[bold cyan]Network Range: {network_range}[/bold cyan]")

    if not network_range:
        return

    devices = await async_scan_network(network_range)

    if not devices:
        return

    while True:
        console.print("\n[bold cyan]Main Menu:[/bold cyan]")
        console.print("1. Display discovered devices")
        console.print("2. Scan a single device")
        console.print("3. Scan all devices")
        console.print("4. Rescan network")
        console.print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            display_devices(devices)
        elif choice == '2':
            display_devices(devices)
            device_choice = input("Enter the number of the device to scan (or 'b' to go back): ")
            if device_choice.lower() == 'b':
                continue
            try:
                device_index = int(device_choice) - 1
                if 0 <= device_index < len(devices):
                    await scan_single_device(devices[device_index]['ip'])
                else:
                    console.print("[bold red]Invalid device number.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter a number or 'b'.[/bold red]")
        elif choice == '3':
            await scan_all_devices(devices)
        elif choice == '4':
            devices = await async_scan_network(network_range)
            if devices:
                display_devices(devices)
            else:
                console.print("[bold yellow]No devices found after rescan.[/bold yellow]")
        elif choice == '5':
            console.print("[bold cyan]Exiting...[/bold cyan]")
            break
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Program interrupted. Exiting...[/bold cyan]")
