"""
Database models for Bushel Management Reports (read-only).
These models match the schema in Bushel_Management/database/models.py
Updated manually when the main database schema changes.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

# Create base for models (read-only, no need for full database setup)
Base = declarative_base()


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
    
    # Dates
    date_sold = Column(Date, nullable=True)  # Date the contract was sold
    delivery_start = Column(Date, nullable=True)  # Delivery start date
    delivery_end = Column(Date, nullable=True)  # Delivery end date
    
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


class Bin(Base):
    """Model representing a storage bin (read-only)."""
    __tablename__ = "bins"
    
    id = Column(Integer, primary_key=True, index=True)
    bin_number = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)
    capacity_bushels = Column(Float, nullable=False)
    current_storage_bushels = Column(Float, default=0.0)
    crop_type = Column(String, nullable=True)
    status = Column(String, default="Available")  # Available, In Use, Maintenance
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def available_capacity(self) -> float:
        """Calculate available capacity."""
        return self.capacity_bushels - self.current_storage_bushels
    
    @property
    def utilization_percent(self) -> float:
        """Calculate utilization percentage."""
        if self.capacity_bushels == 0:
            return 0.0
        return (self.current_storage_bushels / self.capacity_bushels) * 100
    
    def __repr__(self):
        return f"<Bin(id={self.id}, bin_number='{self.bin_number}', capacity={self.capacity_bushels})>"


class StorageRecord(Base):
    """Model representing a storage transaction (read-only)."""
    __tablename__ = "storage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    bin_id = Column(Integer, ForeignKey("bins.id"), nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    transaction_type = Column(String, nullable=False)  # Add, Remove, Transfer
    quantity_bushels = Column(Float, nullable=False)
    crop_type = Column(String, nullable=True)
    transaction_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    # Relationships
    bin = relationship("Bin", back_populates="storage_records")
    
    def __repr__(self):
        return f"<StorageRecord(id={self.id}, bin_id={self.bin_id}, type='{self.transaction_type}', quantity={self.quantity_bushels})>"


# Update Bin relationship
Bin.storage_records = relationship("StorageRecord", back_populates="bin", cascade="all, delete-orphan")


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
    date_delivered = Column(Date, nullable=True)  # Delivery date or delivery period
    
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
    finished_date = Column(Date, nullable=False)  # Date when this harvest entry was completed
    status = Column(String, nullable=False, default="Partial")  # Partial or Complete
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<HarvestActual(id={self.id}, field='{self.field}', crop_year={self.crop_year}, crop='{self.crop}', bushels={self.bushels}, finished_date={self.finished_date}, status='{self.status}')>"













