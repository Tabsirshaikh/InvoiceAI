from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('ALTER TABLE "Invoices" ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "Users"(id)'))
    conn.commit()
    print("user_id column added (or already existed)")
