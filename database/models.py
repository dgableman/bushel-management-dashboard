"""
Database models for Bushel Management Reports (read-only).
These models match the schema in Bushel_Management/database/models.py
Updated manually when the main database schema changes.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, TypeDecorator
from sqlalchemy.orm import relationship
from datetime import datetime, date
from sqlalchemy.ext.declarative import declarative_base
import re

# Create base for models (read-only, no need for full database setup)
Base = declarative_base()


class FlexibleDate(TypeDecorator):
    """
    Custom date type that handles multiple date formats.
    Handles both ISO format (YYYY-MM-DD) and US format (M-D-YYYY).
    For SQLite, uses String to bypass date parsing. For other DBs, uses Date.
    """
    impl = Date
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        """Return the underlying type for the given dialect."""
        if dialect.name == 'sqlite':
            # For SQLite, use String to prevent SQLAlchemy's date parser from running
            return dialect.type_descriptor(String())
        else:
            # For other databases, use Date type
            return dialect.type_descriptor(Date())
    
    def process_bind_param(self, value, dialect):
        """Convert Python value to database value."""
        if value is None:
            return None
        if isinstance(value, date):
            return value.isoformat()
        return str(value)
    
    def process_result_value(self, value, dialect):
        """Convert database value to Python date object."""
        if value is None:
            return None
        
        # If already a date object, return as-is
        if isinstance(value, date):
            return value
        
        # If it's bytes, decode to string first
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                return None
        
        # If it's not a string by now, try to convert it
        if not isinstance(value, str):
            try:
                value = str(value)
            except Exception:
                return None
        
        # Strip whitespace
        value = value.strip()
        if not value:
            return None
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            # Try ISO format with timestamp first (YYYY-MM-DD HH:MM:SS...)
            try:
                # Handle datetime strings with timestamps
                if ' ' in value or 'T' in value:
                    # Try common datetime formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']:
                        try:
                            return datetime.strptime(value.split('.')[0], fmt.split('.')[0]).date()
                        except (ValueError, IndexError):
                            continue
                    # If timestamp formats fail, try just the date part
                    date_part = value.split()[0] if ' ' in value else value.split('T')[0]
                    return datetime.strptime(date_part, '%Y-%m-%d').date()
            except (ValueError, IndexError, AttributeError):
                pass
            
            # Try ISO format (YYYY-MM-DD) without timestamp
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                pass
            
            # Try US format (M-D-YYYY or MM-DD-YYYY)
            # Match patterns like "6-1-2026" or "06-01-2026" or "6/1/2026"
            # First try with dashes
            match = re.match(r'(\d{1,2})-(\d{1,2})-(\d{4})', value)
            if match:
                month, day, year = match.groups()
                try:
                    return date(int(year), int(month), int(day))
                except ValueError:
                    pass
            
            # Try with slashes
            match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', value)
            if match:
                month, day, year = match.groups()
                try:
                    return date(int(year), int(month), int(day))
                except ValueError:
                    pass
            
            # Try other common formats
            for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            
            # Last resort: try to extract numbers and construct date
            # Pattern: any sequence of 1-2 digits, separator, 1-2 digits, separator, 4 digits
            match = re.match(r'(\d{1,2})[^\d]+(\d{1,2})[^\d]+(\d{4})', value)
            if match:
                part1, part2, year = match.groups()
                try:
                    # Try month-day-year (US format)
                    return date(int(year), int(part1), int(part2))
                except ValueError:
                    try:
                        # Try day-month-year (European format)
                        return date(int(year), int(part2), int(part1))
                    except ValueError:
                        pass
        
        # If all parsing fails, return None (but log for debugging)
        # We'll let the query continue rather than raising an error
        return None


class Contract(Base):
    """Model representing a crop contract (read-only)."""
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contract identification
    contract_number = Column(String, unique=True, index=True, nullable=False)
    
    # Financial fields
    basis = Column(Float, nullable=True)  # Basis price (can be negative)
    price = Column(Float, nullable=True)  # Price per bushel (dollar value)
    
    # Commodity and quantity
    commodity = Column(String, nullable=True)  # Commodity type (e.g., Soybeans, Corn)
    bushels = Column(Integer, nullable=True)  # Quantity in bushels
    
    # Buyer information
    buyer_name = Column(String, nullable=True)
    buyer_street = Column(String, nullable=True)
    buyer_city_state_zip = Column(String, nullable=True)
    
    # Dates (using FlexibleDate to handle various date formats in database)
    date_sold = Column(FlexibleDate, nullable=True)  # Date the contract was sold
    delivery_start = Column(FlexibleDate, nullable=True)  # Delivery start date
    delivery_end = Column(FlexibleDate, nullable=True)  # Delivery end date
    
    # PDF storage
    pdf_path = Column(String, nullable=True)  # Full path to scanned PDF
    pdf_file_name = Column(String, nullable=True)  # PDF filename for retrieval
    
    # Metadata
    status = Column(String, default="Active")  # Active, Completed, Cancelled, Referenced Only, Pending Import
    fill_status = Column(String, default="None")  # None, Partial, Filled, Over
    source = Column(String, nullable=True)  # "Manually Imported", "Auto-created from Settlement"
    needs_review = Column(Integer, default=0)  # 0 = False, 1 = True (boolean flag for contracts needing import)
    updates = Column(Text, nullable=True)  # Updates/notes field (renamed from notes)
    user_notes = Column(Text, nullable=True)  # User notes field
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Contract(id={self.id}, contract_number='{self.contract_number}', commodity='{self.commodity}', bushels={self.bushels})>"


class BinName(Base):
    """Model representing a bin name/definition (read-only)."""
    __tablename__ = "bin_names"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    bin_name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    sales_restriction = Column(String, nullable=True)
    preferred_crop = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BinName(id={self.id}, location='{self.location}', bin_name='{self.bin_name}', capacity={self.capacity})>"


class CropStorage(Base):
    """Model representing crop storage in bins (read-only)."""
    __tablename__ = "crop_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    bin_name = Column(String, nullable=False)
    crop_year = Column(Integer, nullable=False)
    crop = Column(String, nullable=False)
    initial_content = Column(Integer, nullable=False)
    current_content = Column(Integer, nullable=False)
    load_status = Column(String, nullable=False)  # Complete, Partial, etc.
    type = Column(String, nullable=False)  # Actual, Estimate, etc.
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<CropStorage(id={self.id}, location='{self.location}', bin_name='{self.bin_name}', crop='{self.crop}', current={self.current_content})>"


# Note: StorageRecord model removed as it references the old 'bins' table
# which doesn't exist. Storage information is now in bin_names and crop_storage tables.
# class StorageRecord(Base):
#     """Model representing a storage transaction (read-only)."""
#     __tablename__ = "storage_records"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
#     contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
#     transaction_type = Column(String, nullable=False)  # Add, Remove, Transfer
#     quantity_bushels = Column(Float, nullable=False)
#     crop_type = Column(String, nullable=True)
#     transaction_date = Column(DateTime, default=datetime.utcnow)
#     notes = Column(Text, nullable=True)
#     
#     def __repr__(self):
#         return f"<StorageRecord(id={self.id}, bin_id={self.bin_id}, type='{self.transaction_type}', quantity={self.quantity_bushels})>"


class Settlement(Base):
    """Model representing a settlement record (read-only)."""
    __tablename__ = "settlements"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Settlement identification
    settlement_ID = Column(String, nullable=True, index=True)  # Settlement No from document
    
    # Status indicator
    status = Column(String, nullable=True)  # "Header" for header row, "Contract found", "Contract not found", etc.
    
    # PDF storage
    pdf_path = Column(String, nullable=True)  # Full path to scanned PDF
    pdf_name = Column(String, nullable=True)  # PDF filename for retrieval
    
    # Contract reference
    contract_id = Column(String, nullable=True, index=True)  # Contract number text (stores the contract_number from contracts table)
    
    # Delivery information
    date_delivered = Column(FlexibleDate, nullable=True)  # Delivery date or delivery period
    
    # Quantity and pricing
    bushels = Column(Integer, nullable=True)  # Net quantity in bushels (INTEGER in database)
    price = Column(Float, nullable=True)  # Trade price per bushel
    commodity = Column(String, nullable=True)  # Commodity type
    bushels_to_remove = Column(Integer, nullable=True)  # Bushels to remove
    
    # Storage
    bin = Column(String, nullable=True)  # Bin number or identifier
    
    # Financial amounts
    gross_amount = Column(Float, nullable=True)  # Gross amount
    net_amount = Column(Float, nullable=True)  # Net settled amount (for header row)
    adjustments = Column(Float, nullable=True)  # Adjustments (for header row only)
    
    # Buyer information (for header row, same for all contracts in settlement)
    buyer = Column(String, nullable=True)  # Buyer/Location name
    
    # Metadata
    source = Column(String, nullable=True)  # Source of settlement
    updates = Column(Text, nullable=True)  # Updates/notes field
    user_notes = Column(Text, nullable=True)  # User notes field
    line_number = Column(Integer, nullable=True)  # Line number in settlement document
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Settlement(id={self.id}, settlement_ID='{self.settlement_ID}', contract_id={self.contract_id})>"


class CommodityMapping(Base):
    """Model representing commodity name mappings (read-only)."""
    __tablename__ = "commodity_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String, nullable=False, unique=True)  # The variation/alias name
    standard_name = Column(String, nullable=False)  # The normalized/standard name
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<CommodityMapping(id={self.id}, alias='{self.alias}', standard_name='{self.standard_name}')>"


class CropTotals(Base):
    """Model representing aggregate crop totals by crop year (read-only)."""
    __tablename__ = "crop_totals"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_year = Column(Integer, nullable=False, index=True)
    crop = Column(String, nullable=False)
    initial_content = Column(Integer, nullable=False, default=0)  # Total bushels
    type = Column(String, nullable=False)  # "Estimate" or "Actual"
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<CropTotals(id={self.id}, crop_year={self.crop_year}, crop='{self.crop}', initial_content={self.initial_content}, type='{self.type}')>"


class HarvestActual(Base):
    """Model representing actual harvest records by field and crop year (read-only)."""
    __tablename__ = "harvest_actual"
    
    id = Column(Integer, primary_key=True, index=True)
    field = Column(String, nullable=False, index=True)
    crop_year = Column(Integer, nullable=False)
    crop = Column(String, nullable=False)
    bushels = Column(Integer, nullable=False, default=0)
    finished_date = Column(FlexibleDate, nullable=False)  # Date when this harvest entry was completed
    status = Column(String, nullable=False, default="Partial")  # Partial or Complete
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<HarvestActual(id={self.id}, field='{self.field}', crop_year={self.crop_year}, crop='{self.crop}', bushels={self.bushels}, finished_date={self.finished_date}, status='{self.status}')>"













