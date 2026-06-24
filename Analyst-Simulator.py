

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import sys
import re
import ctypes
import socket
import getpass
import shutil
import stat
import urllib.request
import zipfile
import io
import queue
import logging
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# --- HIGH DPI AWARENESS FOR CRISP FONTS ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass 

# Destructive tests that require the Safe Mode Guardrail to intercept
DESTRUCTIVE_TECHNIQUES: List[str] = ["T1070", "T1485", "T1486", "T1489", "T1490", "T1491", "T1498", "T1561", "T1495"]

# --- CORE LOGIC: EMULATION ENGINE ---
class EmulationEngine:
    """Handles all file I/O, subprocess execution, and framework management."""
    
    def __init__(self, base_dir: str, logger: logging.Logger):
        self.base_dir = base_dir
        self.invoke_art_path = os.path.join(self.base_dir, "invoke-atomicredteam")
        self.atomics_path = os.path.join(self.base_dir, "atomics")
        self.payloads_path = os.path.join(self.base_dir, "ExternalPayloads")
        self.logger = logger
        self.current_process: Optional[subprocess.Popen] = None

    def check_admin(self) -> bool:
        """Verifies if the current context possesses NT AUTHORITY\SYSTEM or High Integrity."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def is_installed(self) -> bool:
        """Validates the structural integrity of the local framework."""
        return os.path.exists(self.invoke_art_path) and os.path.exists(self.atomics_path)

    def _remove_readonly(self, func: Any, path: str, excinfo: Any) -> None:
        """Callback to force removal of locked or read-only files during purge operations."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def download_framework(self) -> None:
        """Retrieves and provisions the core execution modules from source."""
        self.logger.info("[*] Initiating API module retrieval pipelines...")
        try:
            # 1. Download the Invoke-AtomicRedTeam Execution Engine
            url_invoke = "https://github.com/redcanaryco/invoke-atomicredteam/archive/refs/heads/master.zip"
            req = urllib.request.urlopen(url_invoke)
            with zipfile.ZipFile(io.BytesIO(req.read())) as z:
                z.extractall(self.base_dir)
            
            if os.path.exists(self.invoke_art_path):
                shutil.rmtree(self.invoke_art_path, onerror=self._remove_readonly)
            os.rename(os.path.join(self.base_dir, "invoke-atomicredteam-master"), self.invoke_art_path)
            
            # 2. Download the Atomics folder (Includes the CSV Indexes and YAML files)
            self.logger.info("[*] Mirroring MITRE threat mapping repository definitions...")
            url_atomics = "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"
            req2 = urllib.request.urlopen(url_atomics)
            with zipfile.ZipFile(io.BytesIO(req2.read())) as z2:
                z2.extractall(self.base_dir)
            
            if os.path.exists(self.atomics_path):
                shutil.rmtree(self.atomics_path, onerror=self._remove_readonly)
            
            extracted_art = os.path.join(self.base_dir, "atomic-red-team-master")
            shutil.move(os.path.join(extracted_art, "atomics"), self.base_dir)
            shutil.rmtree(extracted_art, onerror=self._remove_readonly)
            
            self.logger.info("[+] Atomic engine staging initialized flawlessly.")
        except Exception as e:
            self.logger.error(f"[-] Pipeline transmission error: {str(e)}")

    def purge_framework(self) -> None:
        """Destroys the execution framework while preserving forensic logs."""
        self.logger.info("[*] Flushing core execution framework modules...")
        try:
            if os.path.exists(self.invoke_art_path):
                shutil.rmtree(self.invoke_art_path, onerror=self._remove_readonly)
                self.logger.info("[+] Core execution module deleted.")
            if os.path.exists(self.atomics_path):
                shutil.rmtree(self.atomics_path, onerror=self._remove_readonly)
                self.logger.info("[+] Threat matrix definitions unlinked.")
        except Exception as e:
            self.logger.error(f"[-] Encountered locked file descriptor during deletion: {str(e)}")

    def purge_traces(self) -> None:
        """Securely wipes execution traces, logs, and dropped payloads."""
        self.logger.info("[*] Sweeping away dropped file execution traces...")
        try:
            if os.path.exists(self.payloads_path):
                shutil.rmtree(self.payloads_path, onerror=self._remove_readonly)
                self.logger.info("[+] Dropped external testing binaries purged.")
            
            count = 0
            for file in os.listdir(self.base_dir):
                if file.endswith((".csv", ".html")) or file.startswith("Report_"):
                    try:
                        os.remove(os.path.join(self.base_dir, file))
                        self.logger.info(f"[+] Cleaned artifact file trace: {file}")
                        count += 1
                    except Exception:
                        pass
            self.logger.info(f"[+] Trace wipe completed cleanly. Removed {count} context files.")
        except Exception as e:
            self.logger.error(f"[-] Execution trace cleaner exception encountered: {str(e)}")

    def kill_process(self) -> None:
        """Forcefully terminates the active subprocess tree."""
        if self.current_process and self.current_process.poll() is None:
            self.logger.warning("[!] FORCE STOP INITIATED. Hunting down background process tree...")
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.current_process.pid)], capture_output=True)
                self.logger.info("[+] Execution forcefully terminated by operator.")
            except Exception as e:
                self.logger.error(f"[-] Failed to kill process tree: {str(e)}")

    def execute_powershell(self, script: str) -> Tuple[int, str]:
        """Dispatches commands to a hidden PowerShell instance and yields output."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        command = ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", script]
        captured_output: List[str] = []
        
        try:
            self.current_process = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if self.current_process.stdout:
                for line in self.current_process.stdout:
                    clean_line = line.strip()
                    captured_output.append(clean_line)
                    self.logger.info(clean_line)
                    
            self.current_process.wait()
            status_code = self.current_process.returncode
            end_msg = f"[+] Processing Block Exit Hook Terminated (Status Code: {status_code})"
            self.logger.info("-" * 70)
            self.logger.info(end_msg)
            
            return status_code, "\n".join(captured_output)
            
        except Exception as e:
            self.logger.error(f"[-] Runtime interception error: {str(e)}")
            return 1, str(e)
        finally:
            self.current_process = None


# --- GUI: VIEW LAYER ---
class QueueHandler(logging.Handler):
    """Custom logging handler that routes logs to a Tkinter queue for safe UI updates."""
    def __init__(self, log_queue: queue.Queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record: logging.LogRecord) -> None:
        self.log_queue.put(self.format(record))


class AtomicEnterpriseGUI:
    """Presentation layer and UI event controller."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Analyst Simulator")
        self.root.geometry("1150x750") # Compact mode default
        
        # --- ADD THESE LINES TO SET THE WINDOW ICON ---
        try:
            # Using the raw string (r"") for your exact absolute path
            icon_path = r"C:\Users\bhara\Downloads\security.ico"
            self.root.iconbitmap(icon_path)
        except Exception as e:
            self.logger.warning(f"Could not load icon: {e}")
        # ----------------------------------------------

        # FIX 1: Teardown protocol to prevent zombie processes on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.base_dir = self.get_application_path()
        self.log_queue: queue.Queue = queue.Queue()
        self.setup_logging()
        
        self.engine = EmulationEngine(self.base_dir, self.logger)
        
        self.is_executing = False
        self.console_maximized = False
        self.master_catalog: Dict[str, Dict[str, str]] = {}
        self.audit_log: List[Dict[str, Any]] = []

        if not self.show_disclaimer():
            self.root.destroy()
            sys.exit(0)

        self.apply_dark_theme()
        self.build_ui()
        self.configure_terminal_tags()
        
        self.load_catalog()
        self.logger.info(f"[*] Portable Working Directory: {self.base_dir}")
        self.logger.info(f"[*] Privilege Level: {'ADMINISTRATOR' if self.engine.check_admin() else 'Standard User (Some tests may fail)'}")
        self.check_installation_status()
        
        self.process_log_queue()

    def on_closing(self) -> None:
        """Safely shuts down background subprocesses before terminating the GUI loop."""
        if self.is_executing:
            warning_msg = "A simulation is currently running.\n\nExiting now will forcefully kill the background PowerShell processes. Are you sure you want to exit?"
            if messagebox.askokcancel("Active Operation Warning", warning_msg, icon="warning"):
                self.engine.kill_process()
                self.root.destroy()
                os._exit(0) # Stronger than sys.exit, guarantees thread annihilation
        else:
            self.root.destroy()
            os._exit(0)

    def setup_logging(self) -> None:
        """Initializes standard library logging for forensic retention and UI streaming."""
        self.logger = logging.getLogger("AtomicEnterprise")
        self.logger.setLevel(logging.DEBUG)
        
        # UI Queue Handler
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(queue_handler)
        
        # File Handler (Forensic Audit Trail)
        file_handler = logging.FileHandler(os.path.join(self.base_dir, "atomic_execution.log"))
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(file_handler)

    def get_application_path(self) -> str:
        if getattr(sys, 'frozen', False): return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def show_disclaimer(self) -> bool:
        disclaimer_text = (
            "LEGAL DISCLAIMER & TERMS OF USE\n\n"
            "1. This application acts as an automation interface for security testing tools.\n"
            "2. You are strictly prohibited from executing simulations on systems you do not own.\n"
            "3. The developers assume absolutely no liability for system downtime or data loss.\n\n"
            "REQUIREMENTS TO RUN:\n"
            "• Latest Python\n"
            "• Windows 10/11 Endpoint.\n"
            "• Active Internet Connection.\n"
            "• Administrator Privileges (Recommended).\n"
            "• Antivirus/EDR Exclusions applied to this folder.\n\n"
            "Do you confirm you have explicit authorization to run these tests?"
        )
        return messagebox.askyesno("Security Authorization Notice", disclaimer_text, icon="warning")

    def apply_dark_theme(self) -> None:
        app_bg = "#0d1117"  
        panel_bg = "#161b22"
        text_fg = "#c9d1d9"
        accent_blue = "#58a6ff"
        
        self.root.configure(bg=app_bg)
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('.', background=app_bg, foreground=text_fg, font=('Segoe UI', 10))
        style.configure('TLabelframe', background=panel_bg, foreground=accent_blue, font=('Segoe UI', 11, 'bold'), bordercolor="#30363d")
        style.configure('TLabelframe.Label', background=panel_bg, foreground=accent_blue)
        style.configure('Treeview', background="#0d1117", foreground=text_fg, fieldbackground="#0d1117", borderwidth=0, font=('Segoe UI', 10), rowheight=25)
        style.configure('Treeview.Heading', background="#21262d", foreground="white", font=('Segoe UI', 10, 'bold'), borderwidth=1)
        style.map('Treeview', background=[('selected', '#1f6feb')], foreground=[('selected', 'white')])
        
        style.configure('TRadiobutton', background=panel_bg, foreground=text_fg, font=('Segoe UI', 10))
        style.map('TRadiobutton', background=[('active', panel_bg)])
        style.configure('TCheckbutton', background=panel_bg, foreground="#3fb950", font=('Segoe UI', 10, 'bold'))
        style.map('TCheckbutton', background=[('active', panel_bg)])
        style.configure('TButton', font=('Segoe UI', 10, 'bold'))

    def configure_terminal_tags(self) -> None:
        self.console.tag_config('error', foreground='#ff3333', font=("Consolas", 10, "bold"))
        self.console.tag_config('success', foreground='#00ff00', font=("Consolas", 10, "bold"))
        self.console.tag_config('warning', foreground='#ffcc00', font=("Consolas", 10, "italic"))
        self.console.tag_config('info', foreground='#e6e6e6')
        self.console.tag_config('highlight', foreground='#00e5ff', font=("Consolas", 10, "bold"))

    def build_ui(self) -> None:
        # Top-Level Splitting (Reduced sashwidth and changed to FLAT for a seamless look)
        self.main_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, bg="#30363d", bd=0, sashwidth=3, sashrelief=tk.FLAT, cursor="sb_v_double_arrow")
        self.main_pane.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.upper_wrapper = ttk.Frame(self.main_pane, cursor="arrow")
        self.lower_wrapper = ttk.Frame(self.main_pane, cursor="arrow")

        self.main_pane.add(self.upper_wrapper, minsize=200, stretch="always")
        self.main_pane.add(self.lower_wrapper, minsize=100, stretch="always")

        # Horizontal Splitting
        horizontal_pane = tk.PanedWindow(self.upper_wrapper, orient=tk.HORIZONTAL, bg="#30363d", bd=0, sashwidth=3, sashrelief=tk.FLAT, cursor="sb_h_double_arrow")
        horizontal_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(horizontal_pane, padding=2, cursor="arrow")
        right_frame = ttk.Frame(horizontal_pane, padding=2, cursor="arrow")
        
        horizontal_pane.add(left_frame, minsize=250, stretch="always")
        horizontal_pane.add(right_frame, minsize=400, stretch="always")

        # --- LEFT PANEL: DYNAMIC TACTIC CATALOG ---
        cat_frame = ttk.LabelFrame(left_frame, text=" MITRE ATT&CK Catalog ")
        cat_frame.pack(fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(cat_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_catalog)
        tk.Entry(search_frame, textvariable=self.search_var, bg="#0d1117", fg="white", insertbackground="white", relief=tk.FLAT, cursor="xterm").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        tree_container = ttk.Frame(cat_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_container, columns=("ID", "Name", "Tactic"), show="headings", selectmode="browse")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Name", text="Technique Name")
        self.tree.heading("Tactic", text="MITRE Tactic")
        
        self.tree.column("ID", width=90, minwidth=80, anchor="center")
        self.tree.column("Name", width=250, minwidth=250) 
        self.tree.column("Tactic", width=180, minwidth=150) 
        
        self.tree.bind('<<TreeviewSelect>>', self.update_live_command)

        v_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)

        # --- RIGHT PANEL: SCROLLABLE CONTROLS ---
        self.right_canvas = tk.Canvas(right_frame, bg="#161b22", highlightthickness=0, cursor="arrow")
        right_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.right_canvas.yview)
        
        self.scrollable_right = ttk.Frame(self.right_canvas, cursor="arrow")
        self.scrollable_window = self.right_canvas.create_window((0, 0), window=self.scrollable_right, anchor="nw")

        self.scrollable_right.bind("<Configure>", lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")))
        self.right_canvas.bind("<Configure>", lambda e: self.right_canvas.itemconfig(self.scrollable_window, width=e.width))
        self.right_canvas.configure(yscrollcommand=right_scrollbar.set)

        self.right_canvas.pack(side="left", fill="both", expand=True)
        right_scrollbar.pack(side="right", fill="y")
        
        # FIX 2: Bind global mouse wheel intelligently without destroying Treeview scrolls
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel, add="+")

        # Management Controls
        setup_frame = ttk.Frame(self.scrollable_right)
        setup_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(setup_frame, text="Emulation Engine Management", font=('Segoe UI', 12, 'bold'), foreground="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        self.setup_btn = tk.Button(setup_frame, text="⬇ Download Framework", command=self.dispatch_setup, bg="#238636", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        self.setup_btn.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        self.artifacts_btn = tk.Button(setup_frame, text="📦 Show Artifact Logs", command=self.show_artifacts, bg="#8957e5", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        self.artifacts_btn.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        self.delete_framework_btn = tk.Button(setup_frame, text="❌ Delete Framework Core", command=self.dispatch_delete_framework, bg="#da3633", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        self.delete_framework_btn.grid(row=2, column=0, padx=2, pady=2, sticky="ew")

        self.delete_traces_btn = tk.Button(setup_frame, text="🧹 Clear Logs & Traces", command=self.dispatch_clear_traces, bg="#b62324", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4, cursor="hand2")
        self.delete_traces_btn.grid(row=2, column=1, padx=2, pady=2, sticky="ew")

        setup_frame.columnconfigure(0, weight=1)
        setup_frame.columnconfigure(1, weight=1)

        # Execution Configuration
        opt_frame = ttk.LabelFrame(self.scrollable_right, text=" Execution Strategy Properties ")
        opt_frame.pack(fill=tk.X, pady=(0, 10))

        self.action_var = tk.StringVar(value="-Confirm:$false")
        self.action_var.trace("w", lambda name, index, mode: self.update_live_command())
        
        options = [
            ("1. Show Details", "-ShowDetails"),
            ("2. Check Prerequisites", "-CheckPrereqs"),
            ("3. Get Prerequisites", "-GetPrereqs"),
            ("4. Run Attack Simulation", "-Confirm:$false"),
            ("5. Cleanup Target State", "-Cleanup")
        ]

        for i, (text, val) in enumerate(options):
            ttk.Radiobutton(opt_frame, text=text, variable=self.action_var, value=val, cursor="hand2").grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)

        ttk.Separator(opt_frame, orient="horizontal").grid(row=3, column=0, columnspan=2, sticky="ew", pady=10, padx=5)

        test_sel_frame = ttk.Frame(opt_frame)
        test_sel_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Label(test_sel_frame, text="Select Specific Test:").pack(side=tk.LEFT)
        
        self.test_selector = ttk.Combobox(test_sel_frame, state="readonly", width=70)
        self.test_selector.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        self.test_selector.set("All Tests")
        self.test_selector.bind("<<ComboboxSelected>>", self.update_live_command)

        self.safe_mode_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_frame, text="Safe Mode (Block High-Risk Environment Impacts)", variable=self.safe_mode_var, bg="#161b22", fg="#3fb950", selectcolor="#0d1117", font=("Segoe UI", 9, "bold"), activebackground="#161b22", activeforeground="#3fb950", cursor="hand2").grid(row=5, column=0, columnspan=2, sticky="w", padx=10)

        custom_frame = ttk.Frame(opt_frame)
        custom_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 10))
        ttk.Label(custom_frame, text="Live Command Override (Edit this PowerShell directly before Launch):", foreground="#58a6ff").pack(anchor="w")
        
        self.cmd_box = tk.Text(custom_frame, height=3, bg="#0d1117", fg="#c9d1d9", insertbackground="white", relief=tk.FLAT, font=("Consolas", 10), wrap=tk.WORD, cursor="xterm")
        self.cmd_box.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(opt_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        
        self.exec_btn = tk.Button(btn_frame, text="▶ Dispatch Action Matrix", command=self.dispatch_action, bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15, cursor="hand2")
        self.exec_btn.pack(side=tk.LEFT, padx=5)

        self.read_src_btn = tk.Button(btn_frame, text="📖 Read Source Code", command=self.view_source, bg="#0e639c", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15, cursor="hand2")
        self.read_src_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="🛑 Force Stop", command=self.engine.kill_process, bg="#da3633", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15, state="disabled", cursor="hand2")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = tk.Button(btn_frame, text="📑 Export Audit HTML Summary", command=self.export_html_report, bg="#238636", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15, cursor="hand2")
        self.export_btn.pack(side=tk.LEFT, padx=5)

        # Terminal Assembly
        console_frame = ttk.LabelFrame(self.lower_wrapper, text=" Execution Stream Output ", padding=4)
        console_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        terminal_ctrl_frame = ttk.Frame(console_frame)
        terminal_ctrl_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.max_btn = tk.Button(terminal_ctrl_frame, text="⛶ Maximize Terminal", command=self.toggle_console, bg="#1f6feb", fg="white", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, padx=8, cursor="hand2")
        self.max_btn.pack(side=tk.RIGHT)

        self.console = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, state='disabled', bg="#0d1117", fg="#c9d1d9", font=("Consolas", 10), relief=tk.FLAT, cursor="arrow")
        self.console.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.status_bar = ttk.Label(self.root, text=self.get_status_text("System Ready"), background="#1f6feb", foreground="white", padding=(5, 2))
        self.status_bar.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)

    def _on_global_mousewheel(self, event: Any) -> None:
        """Smart scroll delegator: Only scrolls the right canvas if the mouse is physically over it or its children."""
        try:
            # winfo_containing gets the exact widget under the cursor
            hovered_widget = event.widget.winfo_containing(event.x_root, event.y_root)
            if hovered_widget and str(hovered_widget).startswith(str(self.right_canvas)):
                self.right_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except Exception:
            pass

    # --- DYNAMIC CSV PARSER (PULLS FROM INDEXES FOLDER) ---
    def _parse_indexes_csv(self) -> Dict[str, Dict[str, str]]:
        """Silently parses the Red Canary index.csv file to extract ALL techniques and their mappings."""
        mapping = {}
        csv_path = os.path.join(self.engine.atomics_path, "Indexes", "Indexes-CSV", "index.csv")
        alt_csv_path = os.path.join(self.engine.atomics_path, "Indexes", "index.csv")
        target_path = csv_path if os.path.exists(csv_path) else alt_csv_path

        if os.path.exists(target_path):
            try:
                with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    
                    idx_t_id, idx_name, idx_tactic = -1, -1, -1
                    for i, h in enumerate(headers):
                        h_lower = h.lower()
                        if "technique #" in h_lower or "technique id" in h_lower or h_lower == "technique":
                            idx_t_id = i
                        elif "technique name" in h_lower or (h_lower == "name" and idx_name == -1):
                            idx_name = i
                        elif "tactic" in h_lower:
                            idx_tactic = i
                            
                    if idx_t_id != -1:
                        for row in reader:
                            if len(row) > idx_t_id:
                                t_id = row[idx_t_id].strip()
                                if t_id and t_id not in mapping:
                                    name = row[idx_name].strip() if idx_name != -1 and len(row) > idx_name else "Unknown Technique"
                                    tactic = row[idx_tactic].strip() if idx_tactic != -1 and len(row) > idx_tactic else "Unknown Tactic"
                                    mapping[t_id] = {"name": name, "tactic": tactic}
            except Exception as e:
                self.logger.error(f"[-] Catalog Parser Error: {e}")
        return mapping

    def load_catalog(self) -> None:
        self.master_catalog.clear()
        if os.path.exists(self.engine.atomics_path):
            index_mapping = self._parse_indexes_csv()
            for item in os.listdir(self.engine.atomics_path):
                if re.match(r"^T\d{4}(\.\d{3})?$", item):
                    if item in index_mapping:
                        name = index_mapping[item]["name"]
                        tactic = index_mapping[item]["tactic"]
                    else:
                        name = "Custom / Local Technique"
                        tactic = "Unknown Tactic"
                    self.master_catalog[item] = {"name": name, "tactic": tactic}
        self.populate_treeview()

    def populate_treeview(self, search_query: str = "") -> None:
        self.tree.delete(*self.tree.get_children())
        if not self.master_catalog:
            self.tree.insert("", "end", values=("---", "Framework missing. Click 'Download Framework' to populate.", "---"))
            return
        query = search_query.lower()
        for t_id, data in sorted(self.master_catalog.items()):
            if query in t_id.lower() or query in data["name"].lower() or query in data["tactic"].lower():
                self.tree.insert("", "end", values=(t_id, data["name"], data["tactic"]))

    def filter_catalog(self, *args: Any) -> None:
        self.populate_treeview(self.search_var.get())

    # --- SOURCE VIEWER ---
    def view_source(self) -> None:
        """Opens a read-only popup window to display the raw YAML intelligence for the selected attack."""
        selected = self.tree.focus()
        if not selected or self.tree.item(selected, "values")[0] == "---":
            messagebox.showwarning("Target Missing", "Select a technique from the catalog to view its source code.")
            return
            
        t_id = self.tree.item(selected, "values")[0]
        yaml_path = os.path.join(self.engine.atomics_path, t_id, f"{t_id}.yaml")
        
        if os.path.exists(yaml_path):
            source_win = tk.Toplevel(self.root)
            source_win.title(f"Intelligence Source: {t_id} (Read-Only)")
            source_win.geometry("900x600")
            source_win.configure(bg="#0d1117")
            
            ttk.Label(source_win, text=f"Raw Adversarial Logic: {t_id}", font=('Segoe UI', 12, 'bold'), foreground="#58a6ff", background="#0d1117").pack(pady=10)
            
            txt = scrolledtext.ScrolledText(source_win, bg="#0d1117", fg="#c9d1d9", font=("Consolas", 10), relief=tk.FLAT)
            txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    txt.insert(tk.END, f.read())
            except Exception as e:
                txt.insert(tk.END, f"Error reading source file: {str(e)}")
                
            txt.config(state='disabled')
        else:
            messagebox.showerror("Error", "The YAML source file for this technique could not be found.")

    # --- UI UPDATERS & RENDERERS ---
    def toggle_console(self) -> None:
        if not self.console_maximized:
            self.main_pane.forget(self.upper_wrapper)
            self.max_btn.config(text="🗗 Restore View", bg="#da3633")
            self.console_maximized = True
        else:
            self.main_pane.add(self.upper_wrapper, before=self.lower_wrapper, minsize=200, stretch="always")
            self.max_btn.config(text="⛶ Maximize Terminal", bg="#1f6feb")
            self.console_maximized = False

    def process_log_queue(self) -> None:
        while not self.log_queue.empty():
            try:
                message = self.log_queue.get_nowait()
                self._render_log(message)
            except queue.Empty:
                break
        self.root.after(100, self.process_log_queue)

    def _render_log(self, message: str) -> None:
        self.console.config(state='normal')
        lower_msg = message.lower()
        tag = 'info'
        
        # FIX 4: Corrected typo "[*}" to "[!]" so warnings highlight properly
        if any(x in lower_msg for x in ["error", "exception", "fail", "not recognized", "cannot find", "denied", "invalid"]): tag = 'error'
        elif any(x in lower_msg for x in ["[+] ", "success", "completed", "verified", "done executing"]): tag = 'success'
        elif any(x in lower_msg for x in ["[!] ", "[*] ", "warning", "caution", "flagged"]): tag = 'warning'
        elif ">> " in message or "tag:" in lower_msg or "verbose:" in lower_msg: tag = 'highlight'
            
        self.console.insert(tk.END, message + "\n", tag)
        self.console.see(tk.END)
        self.console.config(state='disabled')

    def get_status_text(self, state: str) -> str:
        return f" Status: {state}  |  Endpoint: {socket.gethostname()}  |  Operator: {getpass.getuser()}  |  Clock: {datetime.now().strftime('%H:%M:%S')}"

    def update_status(self, state: str) -> None:
        self.status_bar.config(text=self.get_status_text(state))

    def check_installation_status(self) -> None:
        if self.engine.is_installed():
            self.logger.info("[+] Dependencies active on machine asset. System runs locally.")
            self.delete_framework_btn.config(state="normal")
            self.delete_traces_btn.config(state="normal")
            self.artifacts_btn.config(state="normal")
        else:
            self.logger.warning("[*] Structural Framework files not detected. Execution requires 'Download Framework'.")
            self.delete_framework_btn.config(state="disabled")
            self.delete_traces_btn.config(state="disabled")
            self.artifacts_btn.config(state="disabled")

    def set_gui_state(self, executing: bool) -> None:
        self.is_executing = executing
        state = "disabled" if executing else "normal"
        
        self.exec_btn.config(state=state)
        self.setup_btn.config(state=state)
        self.stop_btn.config(state="normal" if executing else "disabled")
        
        if not executing and self.engine.is_installed():
            self.delete_framework_btn.config(state="normal")
            self.delete_traces_btn.config(state="normal")
        else:
            self.delete_framework_btn.config(state="disabled")
            self.delete_traces_btn.config(state="disabled")
            
        self.update_status("Processing Instruction Blocks..." if executing else "System Ready")

    def update_live_command(self, event: Any = None) -> None:
        selected = self.tree.focus()
        if not selected or self.tree.item(selected, "values")[0] == "---":
            self.cmd_box.delete("1.0", tk.END)
            self.test_selector['values'] = ["All Tests"]
            self.test_selector.set("All Tests")
            return

        technique_id = self.tree.item(selected, "values")[0]
        action = self.action_var.get()
        
        if event and event.widget == self.tree:
            tests = ["All Tests"]
            yaml_path = os.path.join(self.engine.atomics_path, technique_id, f"{technique_id}.yaml")
            
            if os.path.exists(yaml_path):
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        in_tests_block = False
                        test_idx = 1
                        for line in f:
                            if line.startswith('atomic_tests:'):
                                in_tests_block = True
                            elif in_tests_block and line.strip().startswith('- name:'):
                                t_name = line.split('name:', 1)[1].strip().strip('\'"')
                                tests.append(f"Test {test_idx}: {t_name}")
                                test_idx += 1
                except Exception:
                    pass
                    
            self.test_selector['values'] = tests
            self.test_selector.set("All Tests")

        test_num_arg = ""
        selected_test = self.test_selector.get()
        if selected_test and selected_test != "All Tests":
            try:
                t_num = selected_test.split(":")[0].replace("Test", "").strip()
                test_num_arg = f" -TestNumbers {t_num}"
            except Exception:
                pass

        generated_cmd = f"Invoke-AtomicTest '{technique_id}'{test_num_arg} {action} -PathToAtomicsFolder '{self.engine.atomics_path}' -Verbose"
        self.cmd_box.delete("1.0", tk.END)
        self.cmd_box.insert("1.0", generated_cmd)

    # --- ASYNC DISPATCHERS ---
    def dispatch_setup(self) -> None:
        if self.is_executing: return
        self.set_gui_state(True)
        def _task():
            self.engine.download_framework()
            self.root.after(0, self.check_installation_status)
            self.root.after(0, self.load_catalog)
            self.root.after(0, self.set_gui_state, False)
        threading.Thread(target=_task, daemon=True).start()

    def dispatch_delete_framework(self) -> None:
        if self.is_executing: return
        msg = ("Are you sure you want to delete the Core Simulation Framework?\n\n"
               "This will remove the modules and threat matrices. Logs remain safe.")
        if not messagebox.askyesno("Confirm Framework Deletion", msg, icon="warning"): return
        
        self.set_gui_state(True)
        def _task():
            self.engine.purge_framework()
            self.root.after(0, self.check_installation_status)
            self.root.after(0, self.load_catalog)
            self.root.after(0, lambda: self.cmd_box.delete("1.0", tk.END))
            self.root.after(0, lambda: self.test_selector.config(values=["All Tests"]))
            self.root.after(0, lambda: self.test_selector.set("All Tests"))
            self.root.after(0, self.set_gui_state, False)
        threading.Thread(target=_task, daemon=True).start()

    def dispatch_clear_traces(self) -> None:
        if self.is_executing: return
        msg = ("Are you sure you want to clear all simulation logs and dropped assets?")
        if not messagebox.askyesno("Confirm Clean Sweep", msg, icon="question"): return
        
        self.set_gui_state(True)
        def _task():
            self.engine.purge_traces()
            self.root.after(0, self.set_gui_state, False)
        threading.Thread(target=_task, daemon=True).start()

    def dispatch_action(self) -> None:
        if self.is_executing: return
        selected = self.tree.focus()
        if not selected or self.tree.item(selected, "values")[0] == "---":
            messagebox.showwarning("Target Missing", "Select an execution matrix rule from the mapping catalog.")
            return

        user_edited_command = self.cmd_box.get("1.0", tk.END).strip()
        if not user_edited_command:
            messagebox.showwarning("Command Empty", "The command terminal cannot be empty.")
            return

        technique_id = self.tree.item(selected, "values")[0]
        technique_name = self.tree.item(selected, "values")[1]
        action = self.action_var.get()
        psd1_path = os.path.join(self.engine.invoke_art_path, "Invoke-AtomicRedTeam.psd1")

        if not self.engine.is_installed():
            self.logger.error("[-] Framework missing. Execute download pipelines first.")
            return

        if self.safe_mode_var.get() and action in ["-Confirm:$false", "-GetPrereqs"]:
            for d_tech in DESTRUCTIVE_TECHNIQUES:
                if technique_id.startswith(d_tech):
                    if action == "-GetPrereqs":
                        msg = (f"🛑 SAFE MODE ALERT: MALICIOUS PAYLOADS 🛑\n\n"
                               f"Technique {technique_id} is recognized as highly destructive.\n\n"
                               f"Downloading its prerequisites will pull actual malware binaries "
                               f"(e.g., Ransomware simulators or wipers) to your hard drive.\n\n"
                               f"Are you sure you want to download these artifacts?")
                    else:
                        msg = (f"🛑 SYSTEM POLICY ALERT 🛑\n\n"
                               f"Strategy {technique_id} is flagged as High-Risk.\n\n"
                               f"Are you authorized to dispatch this operation inside this infrastructure?")
                    
                    if not messagebox.askyesno("Destructive Filter Active", msg, icon='warning'):
                        self.logger.warning(f"[!] Matrix {technique_id} intercepted by Safe Mode.")
                        return
                    break

        self.logger.info(f"[*] Dispatching Execution Payload...")
        attack_script = f"Import-Module '{psd1_path}' -Force; {user_edited_command}"
        
        self.set_gui_state(True)
        def _task():
            status, output = self.engine.execute_powershell(attack_script)
            
            # FIX 3: Accurately map the selected action rather than a hardcoded string
            action_label = {
                "-ShowDetails": "Viewed Test Details",
                "-CheckPrereqs": "Checked System Prerequisites",
                "-GetPrereqs": "Downloaded Remote Payloads",
                "-Confirm:$false": "Executed Live Emulation",
                "-Cleanup": "Initiated Environment Cleanup"
            }.get(action, "Executed Command")

            self.audit_log.append({
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "technique": technique_id,
                "name": technique_name,
                "action": action_label, 
                "output": output,
                "exit_code": status
            })
            self.root.after(0, self.set_gui_state, False)
        threading.Thread(target=_task, daemon=True).start()

    # --- FORENSICS & REPORTING ---
    def show_artifacts(self) -> None:
        artifact_win = tk.Toplevel(self.root)
        artifact_win.title("Downloaded Artifacts & Traces")
        artifact_win.geometry("850x500")
        artifact_win.configure(bg="#0d1117")
        
        ttk.Label(artifact_win, text="Local Artifacts & Downloaded Payloads", font=('Segoe UI', 12, 'bold'), foreground="#58a6ff", background="#0d1117").pack(pady=10)
        
        tree = ttk.Treeview(artifact_win, columns=("File", "Size", "Type", "Time"), show="headings", selectmode="none")
        tree.heading("File", text="Artifact Path")
        tree.heading("Size", text="Size (KB)")
        tree.heading("Type", text="Category")
        tree.heading("Time", text="Last Modified")
        
        tree.column("File", width=380)
        tree.column("Size", width=70, anchor="e")
        tree.column("Type", width=150, anchor="center")
        tree.column("Time", width=150, anchor="center")
        
        scrollbar = ttk.Scrollbar(artifact_win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        paths_to_scan = {
            "Framework Core": self.engine.invoke_art_path,
            "Attack Matrices": self.engine.atomics_path,
            "Target Payloads": self.engine.payloads_path
        }
        
        total_size_kb = 0
        artifact_list: List[Tuple[str, float, str, float]] = []
        
        for category, path in paths_to_scan.items():
            if os.path.exists(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        try:
                            size = os.path.getsize(filepath) / 1024
                            mtime = os.path.getmtime(filepath)
                            total_size_kb += size
                            rel_path = os.path.relpath(filepath, self.base_dir)
                            artifact_list.append((rel_path, size, category, mtime))
                        except Exception: pass
        
        for file in os.listdir(self.base_dir):
            if file.endswith((".csv", ".log", ".html")):
                filepath = os.path.join(self.base_dir, file)
                try:
                    size = os.path.getsize(filepath) / 1024
                    mtime = os.path.getmtime(filepath)
                    total_size_kb += size
                    artifact_list.append((file, size, "Execution Trace Log", mtime))
                except Exception: pass

        artifact_list.sort(key=lambda x: x[3], reverse=True)

        for rel_path, size, category, mtime in artifact_list:
            time_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            tree.insert("", "end", values=(rel_path, f"{size:.1f}", category, time_str))

        status_txt = f"Total Tracked Files: {len(artifact_list)}  |  Total Disk Footprint: {(total_size_kb/1024):.2f} MB"
        ttk.Label(artifact_win, text=status_txt, font=('Segoe UI', 10, 'italic'), foreground="#c9d1d9", background="#0d1117").pack(side="bottom", pady=10)

    def export_html_report(self) -> None:
        if not self.audit_log:
            messagebox.showinfo("Buffer Empty", "Execute testing simulations to construct logging summaries.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html", filetypes=[("HTML Document", "*.html")],
            title="Save  Team Audit Report", initialfile=f"Report_{datetime.now().strftime('%Y%m%d')}.html"
        )
        if not file_path: return

        html_content = f"""
        <!DOCTYPE html>
        <html><head><title>Emulation Report</title>
        <style>body {{font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0d1117; color: #c9d1d9; margin: 40px;}}
        h1 {{color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px;}}
        .summary {{background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 30px;}}
        .test-card {{background: #161b22; border-left: 5px solid #1f6feb; margin-bottom: 20px; padding: 20px; border-radius: 4px; border: 1px solid #30363d;}}
        .meta {{font-size: 0.9em; color: #8b949e; margin-bottom: 15px;}}
        pre {{background: #0d1117; color: #00ff00; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: Consolas, monospace; font-size: 0.9em; border: 1px solid #30363d;}}
        </style></head><body>
        <h1>Atomic Red Team - Emulation Audit Report</h1>
        <div class="summary"><p><strong>Generated On:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Tests Executed:</strong> {len(self.audit_log)}</p></div>
        """
        for test in self.audit_log:
            html_content += f"""
            <div class="test-card"><h3 style="color:#58a6ff; margin-top:0;">{test['technique']} - {test['name']}</h3>
            <div class="meta"><strong>Action:</strong> {test['action']} &nbsp;|&nbsp; <strong>Time:</strong> {test['timestamp']} &nbsp;|&nbsp; <strong>Exit Code:</strong> {test['exit_code']}</div>
            <pre>{test['output']}</pre></div>"""
        html_content += "</body></html>"

        try:
            with open(file_path, "w", encoding="utf-8") as f: f.write(html_content)
            self.logger.info(f"[+] Log archive successfully exported to: {file_path}")
        except Exception as e: 
            messagebox.showerror("Export Fault", f"Data write error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AtomicEnterpriseGUI(root)
    root.mainloop()
    