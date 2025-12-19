# Same logger as other but improved...sorta
import logging
from pathlib import Path
import os
import sys
import threading

def get_logger(name: str = "app_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        log_dir = Path.home() / "NonomiBeat" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / "NonomiBeat.log")

        fh = logging.FileHandler(log_path, mode="a")
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(formatter)

        logger.addHandler(fh)
    return logger

default_logger = get_logger()

class CStdoutCapturer:
    def __init__(self):
        self.pipe_out, self.pipe_in = os.pipe()
        self.thread = threading.Thread(target=self._drain_pipe, daemon=True)
        self.original_stdout_fd = sys.stdout.fileno()
        self.saved_stdout_fd = os.dup(self.original_stdout_fd)

    def start(self):
        """Start pipleline"""
        os.dup2(self.pipe_in, self.original_stdout_fd)
        self.thread.start()

    def _drain_pipe(self):
        while True:
            data = os.read(self.pipe_out, 1024)
            if not data:
                break
            os.write(self.saved_stdout_fd, b"PD_C_CORE: " + data)

    def stop(self):
        """Stop and cleanup"""
        os.dup2(self.saved_stdout_fd, self.original_stdout_fd)
        os.close(self.pipe_in)
        os.close(self.pipe_out)

    @staticmethod
    def pd_print_callback(message):
        """Callback for PureData print statements"""
        msg = message.strip()
        if not msg.replace('.','').isdigit():
            print(f"[PD MSG] {msg}")