import os
import sys
import platform
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from rich.prompt import Prompt, Confirm
from rich.table import Table
from configparser import ConfigParser

# Initialize Rich console
console = Console()

# Set up logging
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
log = logging.getLogger("rich")

def get_seekr_version():
    return "1.0.0"  # Update this when you release new versions

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def check_dependencies():
    required_packages = ['rich', 'psutil', 'scapy', 'requests', 'pandas', 'matplotlib', 'speedtest-cli']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        console.print(f"[bold red]Missing required packages: {', '.join(missing_packages)}[/bold red]")
        console.print("Please install them using: pip install " + ' '.join(missing_packages))
        return False
    return True

def load_config(config_file='seekr_config.ini'):
    config = ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config['DEFAULT'] = {
            'LogLevel': 'INFO',
            'OutputFormat': 'table',
            'MaxThreads': '100'
        }
        with open(config_file, 'w') as f:
            config.write(f)
    return config

def save_config(config, config_file='seekr_config.ini'):
    with open(config_file, 'w') as f:
        config.write(f)

def get_system_info():
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Architecture": platform.machine(),
        "Processor": platform.processor(),
        "Python Version": sys.version,
        "SEEKR Version": get_seekr_version()
    }
    return info

def display_system_info():
    info = get_system_info()
    table = Table(title="System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in info.items():
        table.add_row(key, str(value))

    console.print(table)

def confirm_action(message):
    return Confirm.ask(message)

def get_user_input(message, choices=None):
    if choices:
        return Prompt.ask(message, choices=choices)
    return Prompt.ask(message)

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def safe_divide(a, b):
    return a / b if b != 0 else 0

def create_progress_bar(description, total):
    return Progress().add_task(description, total=total)

# Add more utility functions as needed