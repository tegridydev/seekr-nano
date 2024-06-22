import psutil
import platform
import GPUtil
import time
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

def get_system_info():
    """Retrieve and display detailed system information."""
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Architecture": platform.machine(),
        "Processor": platform.processor(),
        "Total RAM": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        "Python Version": platform.python_version(),
    }

    table = Table(title="System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in info.items():
        table.add_row(key, str(value))

    console.print(table)

def analyze_cpu():
    """Analyze and display CPU information."""
    cpu_info = {
        "Physical cores": psutil.cpu_count(logical=False),
        "Total cores": psutil.cpu_count(logical=True),
        "Max Frequency": f"{psutil.cpu_freq().max:.2f}Mhz",
        "Current Frequency": f"{psutil.cpu_freq().current:.2f}Mhz",
        "CPU Usage Per Core": "",
    }
    
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        cpu_info[f"Core {i}"] = f"{percentage}%"

    cpu_info["Total CPU Usage"] = f"{psutil.cpu_percent()}%"

    table = Table(title="CPU Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in cpu_info.items():
        table.add_row(key, str(value))

    console.print(table)

def analyze_memory():
    """Analyze and display memory usage information."""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    memory_info = {
        "Total": f"{memory.total / (1024**3):.2f} GB",
        "Available": f"{memory.available / (1024**3):.2f} GB",
        "Used": f"{memory.used / (1024**3):.2f} GB",
        "Percentage": f"{memory.percent}%",
        "Swap Total": f"{swap.total / (1024**3):.2f} GB",
        "Swap Free": f"{swap.free / (1024**3):.2f} GB",
        "Swap Used": f"{swap.used / (1024**3):.2f} GB",
        "Swap Percentage": f"{swap.percent}%",
    }

    table = Table(title="Memory Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in memory_info.items():
        table.add_row(key, str(value))

    console.print(table)

def analyze_gpu():
    """Analyze and display GPU information if available."""
    try:
        gpus = GPUtil.getGPUs()
        if not gpus:
            console.print("[yellow]No GPU detected.[/yellow]")
            return

        table = Table(title="GPU Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        gpu = gpus[0]  # Assuming single GPU system
        gpu_info = {
            "Name": gpu.name,
            "Load": f"{gpu.load*100:.2f}%",
            "Free Memory": f"{gpu.memoryFree}MB",
            "Used Memory": f"{gpu.memoryUsed}MB",
            "Total Memory": f"{gpu.memoryTotal}MB",
            "Temperature": f"{gpu.temperature}°C",
        }

        for key, value in gpu_info.items():
            table.add_row(key, str(value))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error analyzing GPU: {str(e)}[/red]")

def generate_resource_usage_graph(duration=60, interval=1):
    """Generate a graph of CPU and memory usage over time."""
    cpu_percentages = []
    mem_percentages = []
    timestamps = []

    start_time = time.time()
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Collecting resource usage data...", total=duration)
        
        while time.time() - start_time < duration:
            cpu_percentages.append(psutil.cpu_percent())
            mem_percentages.append(psutil.virtual_memory().percent)
            timestamps.append(time.time() - start_time)
            progress.update(task, advance=interval)
            time.sleep(interval)

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, cpu_percentages, label='CPU Usage')
    plt.plot(timestamps, mem_percentages, label='Memory Usage')
    plt.title('Resource Usage Over Time')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Usage (%)')
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    console.print("[green]Resource usage graph generated.[/green]")
    console.print(f"[cyan]Graph data (base64):[/cyan] {img_base64}")

def analyze_disk_io():
    """Analyze and display disk I/O statistics."""
    io_counters = psutil.disk_io_counters()

    disk_io_info = {
        "Read count": io_counters.read_count,
        "Write count": io_counters.write_count,
        "Read bytes": f"{io_counters.read_bytes / (1024**3):.2f} GB",
        "Write bytes": f"{io_counters.write_bytes / (1024**3):.2f} GB",
        "Read time": f"{io_counters.read_time} ms",
        "Write time": f"{io_counters.write_time} ms",
    }

    table = Table(title="Disk I/O Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in disk_io_info.items():
        table.add_row(key, str(value))

    console.print(table)

def analyze_battery():
    """Analyze and display battery information if available."""
    if not hasattr(psutil, "sensors_battery"):
        console.print("[yellow]Battery information not available on this system.[/yellow]")
        return

    battery = psutil.sensors_battery()
    if battery is None:
        console.print("[yellow]No battery detected.[/yellow]")
        return

    battery_info = {
        "Percentage": f"{battery.percent}%",
        "Power plugged": "Yes" if battery.power_plugged else "No",
        "Time left": str(time.strftime("%H:%M:%S", time.gmtime(battery.secsleft))) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "N/A",
    }

    table = Table(title="Battery Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in battery_info.items():
        table.add_row(key, str(value))

    console.print(table)

def analyze_network_usage():
    """Analyze and display network usage statistics."""
    net_io = psutil.net_io_counters()

    net_info = {
        "Bytes sent": f"{net_io.bytes_sent / (1024**3):.2f} GB",
        "Bytes received": f"{net_io.bytes_recv / (1024**3):.2f} GB",
        "Packets sent": net_io.packets_sent,
        "Packets received": net_io.packets_recv,
        "Error in": net_io.errin,
        "Error out": net_io.errout,
        "Drop in": net_io.dropin,
        "Drop out": net_io.dropout,
    }

    table = Table(title="Network Usage Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in net_info.items():
        table.add_row(key, str(value))

    console.print(table)

# Additional performance-related functions can be added here as needed