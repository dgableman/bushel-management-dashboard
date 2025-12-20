"""
Main entry point for Bushel Management Reports application.
"""
import tkinter as tk
from gui.main_window import ReportsWindow


def main():
    """Launch the reports GUI application."""
    root = tk.Tk()
    app = ReportsWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()


