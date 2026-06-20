from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from database import engine, Invoice, User
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from userauth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from datetime import timedelta
from db import get_db


# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class Invoices(BaseModel):
    name:     Annotated[str, Field(..., title='name of the customer', max_length=50)]
    product:  Annotated[str, Field(..., description='select the product')]
    quantity: Annotated[int, Field(description='enter the quantity', gt=0)]
    ppc:      Annotated[int, Field(description='enter the price per pc', gt=0)]
    Total:    Annotated[int, Field(description='total price')]


class filterrequest(BaseModel):
    order:  Annotated[str, Field(..., description='select the order')]
    filter: Annotated[str, Field(..., description="select the factor")]


class updateinvoice(BaseModel):
    name:     Annotated[Optional[str], Field(None, title='name of the customer', max_length=50)]
    product:  Annotated[Optional[str], Field(None, description='select the product')]
    quantity: Annotated[Optional[int], Field(None, description='enter the quantity', gt=0)]
    ppc:      Annotated[Optional[int], Field(None, description='enter the price per pc', gt=0)]


class RegisterRequest(BaseModel):
    username: Annotated[str, Field(..., max_length=50)]
    password: Annotated[str, Field(..., min_length=6)]


# ─────────────────────────────────────────────
# APP + CORS
# ─────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/auth", StaticFiles(directory="auth"), name="auth")
app.mount("/invoice", StaticFiles(directory="invoice"), name="invoice")
app.mount("/records", StaticFiles(directory="records"), name="records")

@app.get("/")
@app.get("/index.html")
def hello():
    return FileResponse('index.html')


# ─────────────────────────────────────────────
# ROUTE: Add invoice  (auth required)
# POST /add
# ─────────────────────────────────────────────

@app.post('/add')
def adddata(
    invoiceobj: Invoices,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Calculate the next invoice_number for this user
    max_num = db.query(Invoice.invoice_number).filter(Invoice.user_id == current_user.id).order_by(Invoice.invoice_number.desc()).first()
    next_num = 1 if (max_num is None or max_num[0] is None) else max_num[0] + 1

    invoice = Invoice(
        user_id  = current_user.id,      # stamp: this invoice belongs to the logged-in user
        name     = invoiceobj.name,
        product  = invoiceobj.product,
        quantity = invoiceobj.quantity,
        ppc      = invoiceobj.ppc,
        Total    = invoiceobj.Total,
        invoice_number = next_num
    )
    db.add(invoice)
    db.commit()
    return {
        "message": "Invoice Submitted Successfully",
        "customer": invoiceobj.name,
        "total": invoiceobj.Total
    }


# ─────────────────────────────────────────────
# ROUTE: Get all records  (auth required)
# GET /records
# ─────────────────────────────────────────────

@app.get("/records")
def fetchdata(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only return invoices that belong to the logged-in user
    invoices = db.query(Invoice).filter(Invoice.user_id == current_user.id).all()
    return [
        {
            "id":       invoice.invoice_number or invoice.id,
            "db_id":    invoice.id,
            "client":   invoice.name,
            "quantity": invoice.quantity,
            "ppc":      invoice.ppc,
            "Total":    invoice.Total
        }
        for invoice in invoices
    ]


# ─────────────────────────────────────────────
# ROUTE: Filter / sort records  (auth required)
# POST /filter
# ─────────────────────────────────────────────

@app.post('/filter')
def sorting(
    data: filterrequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    column = getattr(Invoice, data.filter)

    # Base query — only this user's invoices
    query = db.query(Invoice).filter(Invoice.user_id == current_user.id)

    if data.order == 'descending order':
        invoices = query.order_by(column.desc()).all()
    else:
        invoices = query.order_by(column).all()

    return [
        {
            "id":       invoice.invoice_number or invoice.id,
            "db_id":    invoice.id,
            "client":   invoice.name,
            "quantity": invoice.quantity,
            "ppc":      invoice.ppc,
            "Total":    invoice.Total
        }
        for invoice in invoices
    ]


# ─────────────────────────────────────────────
# ROUTE: Update invoice  (auth required)
# PUT /update/{invoice_id}
# ─────────────────────────────────────────────

@app.put('/update/{invoice_id}')
def upddatadb(
    invoice_id: int,
    updinvoice: updateinvoice,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Find the invoice AND confirm it belongs to the logged-in user
    record = db.query(Invoice).filter(
        Invoice.id      == invoice_id,
        Invoice.user_id == current_user.id   # ownership check
    ).first()

    if record is None:
        # Either doesn't exist OR belongs to a different user — same 404 either way
        # (don't reveal whether another user's invoice exists)
        raise HTTPException(status_code=404, detail="Invoice not found")

    if updinvoice.name is not None:
        record.name = updinvoice.name

    if updinvoice.product is not None:
        record.product = updinvoice.product

    if updinvoice.quantity is not None:
        record.quantity = updinvoice.quantity

    if updinvoice.ppc is not None:
        record.ppc = updinvoice.ppc

    if record.quantity is not None and record.ppc is not None:
        record.Total = record.quantity * record.ppc

    db.commit()
    return {"message": "Updated successfully"}


# ─────────────────────────────────────────────
# ROUTE 1: Register a new user
# POST /register
# ─────────────────────────────────────────────

@app.post('/register')
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter_by(username=data.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        disable=False
    )
    db.add(new_user)
    db.commit()

    return {
        "message": "User registered successfully",
        "username": data.username
    }


# ─────────────────────────────────────────────
# ROUTE 2: Login → returns JWT token
# POST /token
# ─────────────────────────────────────────────

@app.post('/token')
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ─────────────────────────────────────────────
# ROUTE 3: Get current logged-in user's info
# GET /me
# ─────────────────────────────────────────────

@app.get('/me')
def get_me(current_user: User = Depends(get_current_active_user)):
    return {
        "username": current_user.username,
        "disabled": current_user.disable
    }