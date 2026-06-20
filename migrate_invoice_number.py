from database import engine, Invoice, User
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# 1. Alter table to add column if not exists
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS invoice_number INTEGER'))
    conn.commit()
    print("Column invoice_number added or already exists.")

# 2. Backfill sequential invoice numbers grouped by user_id
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Get distinct user_ids (including None) from Invoices table
    user_ids = [row[0] for row in session.query(Invoice.user_id).distinct().all()]
    
    for uid in user_ids:
        # Fetch all invoices for this user, ordered by primary key id
        invoices = session.query(Invoice).filter(Invoice.user_id == uid).order_by(Invoice.id).all()
        print(f"User {uid}: Found {len(invoices)} invoices.")
        
        # Assign sequential number starting from 1
        for idx, inv in enumerate(invoices, start=1):
            inv.invoice_number = idx
            print(f"  Invoice ID {inv.id} -> invoice_number = {idx}")
            
    session.commit()
    print("Database backfill completed successfully!")
except Exception as e:
    session.rollback()
    print(f"Error during migration: {e}")
finally:
    session.close()
