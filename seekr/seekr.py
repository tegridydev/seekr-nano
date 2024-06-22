import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm
from skr_tools import (
    scan_directories, get_all_drives, scan_drive, visualize_storage,
    generate_storage_report, show_performance_metrics, optimize_performance
)
from skr_network import (
    get_local_ip, get_network_interface, get_network_range, async_scan_network,
    display_devices, scan_single_device, scan_all_devices
)

console = Console()

LOGO = r"""
_____/\\\\\\\\\\\____/\\\\\\\\\\\\\\\__/\\\\\\\\\\\\\\\__/\\\________/\\\____/\\\\\\\\\_____        
 ___/\\\/////////\\\_\/\\\///////////__\/\\\///////////__\/\\\_____/\\\//___/\\\///////\\\___       
  __\//\\\______\///__\/\\\_____________\/\\\_____________\/\\\__/\\\//_____\/\\\_____\/\\\___      
   ___\////\\\_________\/\\\\\\\\\\\_____\/\\\\\\\\\\\_____\/\\\\\\//\\\_____\/\\\\\\\\\\\/____     
    ______\////\\\______\/\\\///////______\/\\\///////______\/\\\//_\//\\\____\/\\\//////\\\____    
     _________\////\\\___\/\\\_____________\/\\\_____________\/\\\____\//\\\___\/\\\____\//\\\___   
      __/\\\______\//\\\__\/\\\_____________\/\\\_____________\/\\\_____\//\\\__\/\\\_____\//\\\__  
       _\///\\\\\\\\\\\/___\/\\\\\\\\\\\\\\\_\/\\\\\\\\\\\\\\\_\/\\\______\//\\\_\/\\\______\//\\\_ 
        ___\///////////_____\///////////////__\///////////////__\///________\///__\///________\///__
"""

async def storage_menu():
    while True:
        console.print("\n[bold cyan]Storage Analysis Menu:[/bold cyan]")
        console.print("1. Scan specific directories")
        console.print("2. Scan all drives")
        console.print("3. Generate storage report")
        console.print("4. Return to main menu")

        storage_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="4")

        if storage_choice == '1':
            directories = Prompt.ask("Enter directories to scan (comma-separated)", default="C:\\").split(',')
            report = scan_directories([d.strip() for d in directories])
            visualize_storage(report)
        elif storage_choice == '2':
            for drive in get_all_drives():
                if Confirm.ask(f"Do you want to scan drive {drive}?"):
                    visualize_storage(scan_drive(drive))
        elif storage_choice == '3':
            generate_storage_report()
        elif storage_choice == '4':
            break

async def performance_menu():
    while True:
        console.print("\n[bold cyan]Performance Analysis Menu:[/bold cyan]")
        console.print("1. Show performance metrics")
        console.print("2. Optimize system performance")
        console.print("3. Return to main menu")

        performance_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3"], default="3")

        if performance_choice == '1':
            show_performance_metrics()
        elif performance_choice == '2':
            optimize_performance()
        elif performance_choice == '3':
            break

async def network_menu():
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
        console.print("\n[bold cyan]Network Menu:[/bold cyan]")
        console.print("1. Display discovered devices")
        console.print("2. Scan a single device")
        console.print("3. Scan all devices")
        console.print("4. Rescan network")
        console.print("5. Return to main menu")

        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"], default="5")

        if choice == '1':
            display_devices(devices)
        elif choice == '2':
            display_devices(devices)
            device_choice = Prompt.ask("Enter the number of the device to scan (or 'b' to go back)")
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
            break

async def main_menu():
    while True:
        console.print(LOGO, style="bold blue")
        console.print("\n[bold cyan]Main Menu:[/bold cyan]")
        console.print("1. Storage Analysis")
        console.print("2. Performance Analysis")
        console.print("3. Network Analysis")
        console.print("4. Exit")

        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="4")

        if choice == '1':
            await storage_menu()
        elif choice == '2':
            await performance_menu()
        elif choice == '3':
            await network_menu()
        elif choice == '4':
            console.print("[bold cyan]Exiting SEEKR. Goodbye![/bold cyan]")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Program interrupted. Exiting...[/bold cyan]")