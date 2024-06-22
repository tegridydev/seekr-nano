import os
import pandas as pd
import psutil
import subprocess
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Confirm

console = Console()

def get_directory_size(path):
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def scan_directories(directories):
    report = []
    for dir in track(directories, description="Scanning directories..."):
        if os.path.exists(dir):
            size = get_directory_size(dir)
            report.append({"Directory": dir, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

def get_all_drives():
    return [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:\\")]

def scan_drive(drive):
    report = []
    for root, dirs, _ in track(os.walk(drive), description=f"Scanning drive {drive}..."):
        for d in dirs:
            dir_path = os.path.join(root, d)
            size = get_directory_size(dir_path)
            report.append({"Directory": dir_path, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

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

def generate_storage_report():
    all_drives = get_all_drives()
    full_report = []

    for drive in all_drives:
        if Confirm.ask(f"Do you want to scan drive {drive}?"):
            full_report.extend(scan_drive(drive))

    if not full_report:
        console.print("No data to generate report.", style="bold red")
        return

    report_path = os.path.join(os.path.expanduser("~"), "storage_report.csv")
    pd.DataFrame(full_report).to_csv(report_path, index=False)
    console.print(f"Storage report generated at {report_path}", style="bold green")

    visualize_storage(full_report)

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

def optimize_performance():
    console.print("Starting system optimization...", style="bold yellow")

    optimization_steps = {
        "Close unnecessary applications": ["taskkill", "/F", "/IM", "application_name.exe"],
        "Clean up temporary files": ["cleanmgr", "/sagerun:1"],
        "Uninstall unused programs": ["appwiz.cpl"],
        "Defragment your disk (if using HDD)": ["dfrgui"],
        "Enable Storage Sense for automatic cleanup": ["start", "ms-settings:storagesense"],
        "Perform malware scan": ["start", "ms-settings:windowsdefender"],
        "Update system and drivers": ["start", "ms-settings:windowsupdate"],
        "Adjust visual effects for better performance": ["sysdm.cpl"],
        "Disable unnecessary startup programs": ["taskmgr"],
        "Check for disk errors": ["chkdsk", "/f", "C:"],
        "Enable Fast Startup": ["powercfg", "/hibernate", "on"],
        "Optimize SSD (if applicable)": ["defrag", "/C", "/O"]
    }

    for step, command in optimization_steps.items():
        console.print(f"- {step}")
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            console.print(f"  Error: {e}", style="bold red")
        except FileNotFoundError:
            console.print(f"  Command not found: {' '.join(command)}", style="bold yellow")

    console.print("System optimization completed.", style="bold green")

def analyze_running_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            proc.cpu_percent(interval=1)
            processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    
    table = Table(title="Top 10 CPU-Consuming Processes")
    table.add_column("PID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("CPU %", style="green")
    table.add_column("Memory %", style="yellow")

    for proc in processes[:10]:
        table.add_row(
            str(proc['pid']),
            proc['name'],
            f"{proc['cpu_percent']:.2f}%",
            f"{proc['memory_percent']:.2f}%"
        )

    console.print(table)

def find_large_files(path, size_limit_mb=100):
    large_files = []

    with console.status("[cyan]Scanning for large files...", spinner="dots"):
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    if file_size > size_limit_mb:
                        large_files.append((file_path, file_size))
                except OSError:
                    pass

    table = Table(title=f"Large Files (>{size_limit_mb} MB)")
    table.add_column("File Path", style="cyan")
    table.add_column("Size (MB)", style="magenta")

    for file_path, file_size in sorted(large_files, key=lambda x: x[1], reverse=True):
        table.add_row(file_path, f"{file_size:.2f}")

    console.print(table)

# Additional functions can be added here as needed