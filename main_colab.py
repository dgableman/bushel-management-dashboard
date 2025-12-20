"""
Main entry point for Bushel Management Reports application (Colab version).
This is a non-GUI version that can run in Google Colab.
"""
import sys
from pathlib import Path
from database.db_connection import create_db_session
from reports.contract_queries import get_all_contracts


def show_contracts_report(db, output_file=None):
    """
    Display all contracts in a formatted report.
    
    Args:
        db: SQLAlchemy database session
        output_file: Optional file path to write report to (if None, prints to console)
    """
    try:
        # Get all contracts
        contracts = get_all_contracts(db)
        
        if not contracts:
            report_text = "No contracts found in database.\n"
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report_text)
            else:
                print(report_text)
            return
        
        # Build report text
        report_lines = []
        
        # Header
        report_lines.append("=" * 120)
        report_lines.append("ALL CONTRACTS REPORT")
        report_lines.append("=" * 120)
        report_lines.append("")
        report_lines.append(f"Total Contracts: {len(contracts)}")
        report_lines.append("")
        
        # Format each contract
        for i, contract in enumerate(contracts, 1):
            report_lines.append("")
            report_lines.append("=" * 120)
            report_lines.append(f"Contract #{i}")
            report_lines.append("=" * 120)
            report_lines.append(f"Contract Number:     {contract.contract_number or 'N/A'}")
            report_lines.append(f"Commodity:           {contract.commodity or 'N/A'}")
            report_lines.append(f"Bushels:             {contract.bushels or 'N/A':,}")
            report_lines.append(f"Price per Bushel:    ${contract.price or 0:.2f}")
            report_lines.append(f"Basis:               ${contract.basis or 0:.2f}")
            report_lines.append(f"Status:              {contract.status or 'N/A'}")
            report_lines.append(f"Fill Status:         {contract.fill_status or 'N/A'}")
            report_lines.append(f"Source:              {contract.source or 'N/A'}")
            report_lines.append(f"Date Sold:           {contract.date_sold or 'N/A'}")
            report_lines.append(f"Delivery Start:      {contract.delivery_start or 'N/A'}")
            report_lines.append(f"Delivery End:        {contract.delivery_end or 'N/A'}")
            report_lines.append(f"Buyer Name:          {contract.buyer_name or 'N/A'}")
            report_lines.append(f"Buyer Street:        {contract.buyer_street or 'N/A'}")
            report_lines.append(f"Buyer City/State/Zip: {contract.buyer_city_state_zip or 'N/A'}")
            report_lines.append(f"Needs Review:        {'Yes' if contract.needs_review else 'No'}")
            report_lines.append(f"Notes:               {contract.notes or 'N/A'}")
            report_lines.append(f"Created At:          {contract.created_at or 'N/A'}")
            report_lines.append(f"Updated At:          {contract.updated_at or 'N/A'}")
        
        report_text = "\n".join(report_lines)
        
        # Output report
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"Report written to: {output_file}")
        else:
            print(report_text)
            
    except Exception as e:
        error_msg = f"Failed to generate report:\n{str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        if output_file:
            with open(output_file, 'w') as f:
                f.write(error_msg)
        raise


def main(db_path: str = None, output_file: str = None):
    """
    Main function to run the reports application.
    
    Args:
        db_path: Path to the database file. If None, will try to get from command line args or use default.
        output_file: Optional file path to write report to (if None, prints to console)
    """
    # Get database path from command line argument or use provided
    if db_path is None:
        if len(sys.argv) > 1:
            db_path = sys.argv[1]
        else:
            # Default path (can be overridden)
            db_path = 'data/bushel_management.db'
    
    # Check if database file exists
    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        print(f"Error: Database file not found: {db_path}")
        print(f"\nUsage: python main_colab.py [database_path] [output_file]")
        print(f"Example: python main_colab.py /path/to/bushel_management.db")
        sys.exit(1)
    
    try:
        # Connect to database
        print(f"Connecting to database: {db_path}")
        db = create_db_session(db_path)
        print("? Database connected successfully\n")
        
        # Generate contracts report
        show_contracts_report(db, output_file)
        
        # Close database connection
        db.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Get optional output file from command line
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    main(output_file=output_file)
