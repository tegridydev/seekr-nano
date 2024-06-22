import os
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.prompt import Confirm

console = Console()

def get_directory_size(path):
    """Calculate the total size of a directory."""
    total_size = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size

def scan_directories(directories):
    """Scan specified directories and return size information."""
    report = []
    for dir in track(directories, description="Scanning directories..."):
        if os.path.exists(dir):
            size = get_directory_size(dir)
            report.append({"Directory": dir, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

def get_all_drives():
    """Get a list of all available drives."""
    return [f"{chr(drive)}:\\" for drive in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(drive)}:\\")]

def scan_drive(drive):
    """Scan a specific drive and return size information for all directories."""
    report = []
    for root, dirs, _ in track(os.walk(drive), description=f"Scanning drive {drive}..."):
        for d in dirs:
            dir_path = os.path.join(root, d)
            size = get_directory_size(dir_path)
            report.append({"Directory": dir_path, "SizeMB": round(size / (1024 * 1024), 2)})
    return report

def visualize_storage(report):
    """Visualize storage information in a table format."""
    if not report:
        console.print("No data available to visualize.", style="bold red")
        return

    table = Table(title="Top 20 Directories by Size")
    table.add_column("Directory", justify="left", style="cyan", no_wrap=True)
    table.add_column("Size (MB)", justify="right", style="magenta")

    try:
        df = pd.DataFrame(report).sort_values(by="SizeMB", ascending=False).head(20)
        for _, row in df.iterrows():
            table.add_row(row["Directory"], f"{row['SizeMB']:.2f}")
    except KeyError as e:
        console.print(f"Error: {e}. Ensure the report contains 'SizeMB' key.", style="bold red")

    console.print(table)

def generate_storage_report():
    """Generate a comprehensive storage report for all drives."""
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

def find_large_files(path, size_limit_mb=100):
    """Find files larger than the specified size limit."""
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

def analyze_file_types(path):
    """Analyze and report on file types in the given path."""
    file_types = {}

    with console.status("[cyan]Analyzing file types...", spinner="dots"):
        for root, _, files in os.walk(path):
            for file in files:
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                if ext:
                    file_types[ext] = file_types.get(ext, 0) + 1

    table = Table(title="File Type Analysis")
    table.add_column("File Extension", style="cyan")
    table.add_column("Count", style="magenta")

    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        table.add_row(ext, str(count))

    console.print(table)

def disk_usage_overview():
    """Provide an overview of disk usage for all drives."""
    drives = get_all_drives()
    
    table = Table(title="Disk Usage Overview")
    table.add_column("Drive", style="cyan")
    table.add_column("Total Size (GB)", style="magenta")
    table.add_column("Used (GB)", style="yellow")
    table.add_column("Free (GB)", style="green")
    table.add_column("Usage (%)", style="red")

    for drive in drives:
        try:
            total, used, free = shutil.disk_usage(drive)
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            usage_percent = (used / total) * 100

            table.add_row(
                drive,
                f"{total_gb:.2f}",
                f"{used_gb:.2f}",
                f"{free_gb:.2f}",
                f"{usage_percent:.2f}%"
            )
        except Exception as e:
            console.print(f"Error analyzing drive {drive}: {str(e)}", style="bold red")

    console.print(table)

# Additional storage-related functions can be added here as needed