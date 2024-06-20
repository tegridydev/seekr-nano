import os
import pandas as pd
import psutil
import subprocess
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Prompt, Confirm

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

# calculate ~ directory ~ size
def get_directory_size(path):
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

# scan ~ directories
def scan_directories(directories):
    report = []
    for dir in track(directories, description="Scanning directories..."):
        if os.path.exists(dir):
            size = get_directory_size(dir)
            report.append({"Directory": dir, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

# get ~ all ~ drives
def get_all_drives():
    return [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:\\")]

# scan ~ drive
def scan_drive(drive):
    report = []
    for root, dirs, _ in track(os.walk(drive), description=f"Scanning drive {drive}..."):
        for d in dirs:
            dir_path = os.path.join(root, d)
            size = get_directory_size(dir_path)
            report.append({"Directory": dir_path, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

# visualize ~ storage
def visualize_storage(report):
    if not report:
        console.print("No data available to visualize.", style="bold red")
        return

    table = Table(title="Top 20 Directories by Size")
    table.add_column("Directory", justify="left", style="cyan", no_wrap=True)
    table.add_column("Size (MB)", justify="right", style="magenta")

    try:
        df = pd.DataFrame(report).sort_values(by="SizeMB", ascending=False).head(20)
        for _, row in df.iterrows():
            table.add_row(row["Directory"], str(row["SizeMB"]))
    except KeyError as e:
        console.print(f"Error: {e}. Ensure the report contains 'SizeMB' key.", style="bold red")

    console.print(table)

# generate ~ storage ~ report
def generate_storage_report():
    all_drives = get_all_drives()
    full_report = []

    for drive in all_drives:
        if Confirm.ask(f"Do you want to scan drive {drive}?"):
            full_report.extend(scan_drive(drive))

    if not full_report:
        console.print("No data to generate report.", style="bold red")
        return

    report_path = "M:\\storage_report.csv"
    pd.DataFrame(full_report).to_csv(report_path, index=False)
    console.print(f"Storage report generated at {report_path}", style="bold green")

    visualize_storage(full_report)

# show ~ performance ~ metrics
def show_performance_metrics():
    metrics = {
        "CPU Usage (%)": f"{psutil.cpu_percent(interval=1)}%",
        "Memory Usage (%)": f"{psutil.virtual_memory().percent}%",
        "Total Memory (GB)": f"{psutil.virtual_memory().total / (1024**3):.2f}",
        "Available Memory (GB)": f"{psutil.virtual_memory().available / (1024**3):.2f}",
        "Used Memory (GB)": f"{psutil.virtual_memory().used / (1024**3):.2f}",
        "Disk Usage (%)": f"{psutil.disk_usage('/').percent}%",
        "Total Disk Space (GB)": f"{psutil.disk_usage('/').total / (1024**3):.2f}",
        "Used Disk Space (GB)": f"{psutil.disk_usage('/').used / (1024**3):.2f}",
        "Free Disk Space (GB)": f"{psutil.disk_usage('/').free / (1024**3):.2f}"
    }

    table = Table(title="PC Performance Metrics")
    table.add_column("Metric", justify="left", style="cyan", no_wrap=True)
    table.add_column("Value", justify="right", style="magenta")

    for metric, value in metrics.items():
        table.add_row(metric, value)

    console.print(table)

# optimize ~ system ~ performance
def optimize_performance():
    console.print("Starting system optimization...", style="bold yellow")

    optimization_steps = {
        "- Close unnecessary applications.": ["taskkill /F /IM application_name.exe"],
        "- Clean up temporary files.": ["cleanmgr", "/sagerun:1"],
        "- Uninstall unused programs.": ["appwiz.cpl"],
        "- Defragment your disk (if using HDD).": ["dfrgui"],
        "- Enable Storage Sense for automatic cleanup.": ["start ms-settings:storagesense"],
        "- Configure ReadyBoost (if applicable).": ["Insert a USB flash drive and configure ReadyBoost through its properties in File Explorer."],
        "- Perform malware scan.": ["start ms-settings:windowsdefender"],
        "- Update system and drivers.": ["start ms-settings:windowsupdate"],
        "- Adjust visual effects for better performance.": ["sysdm.cpl"],
        "- Disable unnecessary startup programs.": ["taskmgr"],
        "- Check for disk errors.": ["chkdsk /f C:"],
        "- Enable Fast Startup.": ["powercfg /hibernate on", "powercfg -h off", "powercfg -h on"],
        "- Clear browser cache.": ["Open your browser settings and clear cache, cookies, and browsing history."],
        "- Optimize SSD (if applicable).": ["defrag /C /O"]
    }

    for step, command in optimization_steps.items():
        console.print(step)
        if isinstance(command, list):
            for cmd in command:
                if cmd.startswith("Open"):
                    console.print(cmd)
                else:
                    subprocess.run(cmd.split())
        else:
            console.print(command)

    console.print("System optimization completed.", style="bold green")

# display ~ mainmenu
def main_menu():
    console.print(LOGO, style="bold blue")
    while True:
        console.print("Storage and Performance Analysis Tool", style="bold cyan")
        console.print("[1] Scan ~ specific directories")
        console.print("[2] Scan ~ all drives")
        console.print("[3] Generate ~ storage report")
        console.print("[4] Show ~ performance metrics")
        console.print("[5] Optimize ~ performance")
        console.print("[6] exit ~ (っ◔◡◔)っ")
        
        choice = Prompt.ask("Choose an option", choices=["1", "2", "3", "4", "5", "6"], default="6")
        
        if choice == "1":
            directories = Prompt.ask("Enter directories to scan (comma-separated)", default="C:\\").split(',')
            report = scan_directories([d.strip() for d in directories])
            visualize_storage(report)
        elif choice == "2":
            for drive in get_all_drives():
                if Confirm.ask(f"Do you want to scan drive {drive}?"):
                    visualize_storage(scan_drive(drive))
        elif choice == "3":
            generate_storage_report()
        elif choice == "4":
            show_performance_metrics()
        elif choice == "5":
            optimize_performance()
        elif choice == "6":
            console.print("Exiting the tool. Goodbye!", style="bold red")
            break

if __name__ == "__main__":
    main_menu()
