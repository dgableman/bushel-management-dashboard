"""
Main GUI window for Bushel Management Reports.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from sqlalchemy.orm import Session
from database.db_connection import create_db_session
from reports.contract_queries import get_all_contracts


class ReportsWindow:
    """Main window for the reporting application."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Bushel Management Reports")
        self.root.geometry("1000x700")
        
        self.db: Session = None
        self.db_path: Path = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all widgets for the main window."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Bushel Management Reports",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Database selection frame
        db_frame = ttk.LabelFrame(main_frame, text="Database Connection", padding="10")
        db_frame.pack(fill=tk.X, pady=(0, 10))
        
        db_path_frame = ttk.Frame(db_frame)
        db_path_frame.pack(fill=tk.X)
        
        ttk.Label(db_path_frame, text="Database File:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.db_path_var = tk.StringVar()
        db_entry = ttk.Entry(db_path_frame, textvariable=self.db_path_var, width=60)
        db_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            db_path_frame,
            text="Browse...",
            command=self.browse_database
        )
        browse_btn.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(
            db_path_frame,
            text="Connect",
            command=self.connect_database
        )
        connect_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.connection_status_var = tk.StringVar(value="Not connected")
        self.status_label = ttk.Label(
            db_frame,
            textvariable=self.connection_status_var,
            foreground="red"
        )
        self.status_label.pack(pady=(5, 0))
        
        # Reports frame
        reports_frame = ttk.LabelFrame(main_frame, text="Reports", padding="10")
        reports_frame.pack(fill=tk.BOTH, expand=True)
        
        # Buttons frame
        buttons_frame = ttk.Frame(reports_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        contracts_btn = ttk.Button(
            buttons_frame,
            text="All Contracts Report",
            command=self.show_contracts_report,
            state=tk.DISABLED
        )
        contracts_btn.pack(side=tk.LEFT, padx=5)
        
        self.contracts_btn = contracts_btn
        
        # Results frame with scrollable text
        results_frame = ttk.Frame(reports_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable text widget
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text = tk.Text(
            results_frame,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10)
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_text.yview)
    
    def browse_database(self):
        """Browse for database file."""
        filename = filedialog.askopenfilename(
            title="Select Database File",
            filetypes=[("SQLite databases", "*.db"), ("All files", "*.*")]
        )
        if filename:
            self.db_path_var.set(filename)
    
    def connect_database(self):
        """Connect to the database."""
        db_path_str = self.db_path_var.get().strip()
        if not db_path_str:
            messagebox.showerror("Error", "Please select a database file.")
            return
        
        db_path = Path(db_path_str)
        if not db_path.exists():
            messagebox.showerror("Error", f"Database file not found: {db_path}")
            return
        
        try:
            # Close existing connection if any
            if self.db:
                self.db.close()
            
            # Create new connection
            self.db = create_db_session(str(db_path))
            self.db_path = db_path
            
            # Update UI
            self.connection_status_var.set(f"Connected: {db_path.name}")
            self.status_label.config(foreground="green")
            
            # Enable report buttons
            self.contracts_btn.config(state=tk.NORMAL)
            
            messagebox.showinfo("Success", "Database connected successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to connect to database:\n{str(e)}")
            self.connection_status_var.set("Connection failed")
            self.contracts_btn.config(state=tk.DISABLED)
    
    def show_contracts_report(self):
        """Display all contracts in a formatted report."""
        if not self.db:
            messagebox.showerror("Error", "Please connect to a database first.")
            return
        
        try:
            # Get all contracts
            contracts = get_all_contracts(self.db)
            
            if not contracts:
                self.results_text.delete(1.0, tk.END)
                self.results_text.insert(tk.END, "No contracts found in database.\n")
                return
            
            # Clear previous results
            self.results_text.delete(1.0, tk.END)
            
            # Header
            header = "=" * 120 + "\n"
            header += "ALL CONTRACTS REPORT\n"
            header += "=" * 120 + "\n\n"
            header += f"Total Contracts: {len(contracts)}\n\n"
            
            self.results_text.insert(tk.END, header)
            
            # Format each contract
            for i, contract in enumerate(contracts, 1):
                contract_text = f"\n{'=' * 120}\n"
                contract_text += f"Contract #{i}\n"
                contract_text += f"{'=' * 120}\n"
                contract_text += f"Contract Number:     {contract.contract_number or 'N/A'}\n"
                contract_text += f"Commodity:           {contract.commodity or 'N/A'}\n"
                contract_text += f"Bushels:             {contract.bushels or 'N/A':,}\n"
                contract_text += f"Price per Bushel:    ${contract.price or 0:.2f}\n"
                contract_text += f"Basis:               ${contract.basis or 0:.2f}\n"
                contract_text += f"Status:              {contract.status or 'N/A'}\n"
                contract_text += f"Fill Status:         {contract.fill_status or 'N/A'}\n"
                contract_text += f"Source:              {contract.source or 'N/A'}\n"
                contract_text += f"Date Sold:           {contract.date_sold or 'N/A'}\n"
                contract_text += f"Delivery Start:      {contract.delivery_start or 'N/A'}\n"
                contract_text += f"Delivery End:        {contract.delivery_end or 'N/A'}\n"
                contract_text += f"Buyer Name:          {contract.buyer_name or 'N/A'}\n"
                contract_text += f"Buyer Street:        {contract.buyer_street or 'N/A'}\n"
                contract_text += f"Buyer City/State/Zip: {contract.buyer_city_state_zip or 'N/A'}\n"
                contract_text += f"Needs Review:        {'Yes' if contract.needs_review else 'No'}\n"
                contract_text += f"Notes:               {contract.notes or 'N/A'}\n"
                contract_text += f"Created At:          {contract.created_at or 'N/A'}\n"
                contract_text += f"Updated At:          {contract.updated_at or 'N/A'}\n"
                
                self.results_text.insert(tk.END, contract_text)
            
            # Scroll to top
            self.results_text.see(1.0)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """Launch the reports application."""
    root = tk.Tk()
    app = ReportsWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

