import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

load_dotenv()

db_url = os.getenv("DATABASE_URL", "postgresql://postgres:hello@localhost:5432/Invoice")

engine = create_engine(db_url)

Base = declarative_base()


class Invoice(Base):
    __tablename__ = 'Invoices'
    id       = Column(Integer, primary_key=True)
    user_id  = Column(Integer, ForeignKey('Users.id'), nullable=True)  # owner of this invoice
    name     = Column(String)
    product  = Column(String)
    quantity = Column(Integer, nullable=False)
    ppc      = Column(Integer, nullable=False)
    Total    = Column(Integer)
    invoice_number = Column(Integer, nullable=True)



class User(Base):
    __tablename__ = 'Users'
    id              = Column(Integer, primary_key=True)
    username        = Column(String, unique=True)
    email           = Column(String, unique=True, nullable=True)
    disable         = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)


Base.metadata.create_all(engine)
