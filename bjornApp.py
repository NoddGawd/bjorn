import threading
import signal
import logging
import time
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from init_shared import shared_data
from display import Display, handle_exit_display
from comment import Commentaireia
from webapp import web_thread, handle_exit_web
from orchestrator import Orchestrator
from logger import Logger

logger = Logger(name="Bjorn.py", level=logging.DEBUG)

class BjornApp:
    def __init__(self, root, shared_data):
        self.root = root
        self.shared_data = shared_data
        self.commentaire_ia = Commentaireia()
        self.orchestrator_thread = None
        self.orchestrator = None
        self.root.protocol("WM_DELETE_WINDOW", self.handle_exit)
        
        self.create_widgets()
        self.run()

    def create_widgets(self):
        self.start_button = tk.Button(self.root, text="Start Orchestrator", command=self.start_orchestrator)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(self.root, text="Stop Orchestrator", command=self.stop_orchestrator)
        self.stop_button.pack(pady=10)

    def run(self):
        if hasattr(self.shared_data, 'startup_delay') and self.shared_data.startup_delay > 0:
            logger.info(f"Waiting for startup delay: {self.shared_data.startup_delay} seconds")
            time.sleep(self.shared_data.startup_delay)

        while not self.shared_data.should_exit:
            if not self.shared_data.manual_mode:
                self.check_and_start_orchestrator()
            self.root.update_idletasks()
            self.root.update()
            time.sleep(1)

    def check_and_start_orchestrator(self):
        if self.is_wifi_connected():
            self.wifi_connected = True
            if self.orchestrator_thread is None or not self.orchestrator_thread.is_alive():
                self.start_orchestrator()
        else:
            self.wifi_connected = False
            logger.info("Waiting for Wi-Fi connection to start Orchestrator...")

    def start_orchestrator(self):
        if self.is_wifi_connected():
            if self.orchestrator_thread is None or not self.orchestrator_thread.is_alive():
                logger.info("Starting Orchestrator thread...")
                self.shared_data.orchestrator_should_exit = False
                self.shared_data.manual_mode = False
                self.orchestrator = Orchestrator()
                self.orchestrator_thread = threading.Thread(target=self.orchestrator.run)
                self.orchestrator_thread.start()
                logger.info("Orchestrator thread started, automatic mode activated.")
            else:
                logger.info("Orchestrator thread is already running.")
        else:
            logger.warning("Cannot start Orchestrator: Wi-Fi is not connected.")

    def stop_orchestrator(self):
        self.shared_data.manual_mode = True
        logger.info("Stop button pressed. Manual mode activated & Stopping Orchestrator...")
        if self.orchestrator_thread is not None and self.orchestrator_thread.is_alive():
            logger.info("Stopping Orchestrator thread...")
            self.shared_data.orchestrator_should_exit = True
            self.orchestrator_thread.join()
            logger.info("Orchestrator thread stopped.")
            self.shared_data.bjornorch_status = "IDLE"
            self.shared_data.bjornstatustext2 = ""
            self.shared_data.manual_mode = True
        else:
            logger.info("Orchestrator thread is not running.")

    def is_wifi_connected(self):
        result = subprocess.Popen(['nmcli', '-t', '-f', 'active', 'dev', 'wifi'], stdout=subprocess.PIPE, text=True).communicate()[0]
        self.wifi_connected = 'yes' in result
        return self.wifi_connected

    def handle_exit(self):
        self.shared_data.should_exit = True
        self.shared_data.orchestrator_should_exit = True
        self.shared_data.display_should_exit = True
        self.shared_data.webapp_should_exit = True
        if self.orchestrator_thread is not None and self.orchestrator_thread.is_alive():
            self.orchestrator_thread.join()
        self.root.destroy()
        logger.info("Application exited cleanly.")
        sys.exit(0)

if __name__ == "__main__":
    shared_data.load_config()
    root = tk.Tk()
    root.title("Bjorn Application")
    app = BjornApp(root, shared_data)
    root.mainloop()
