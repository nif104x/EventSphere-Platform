from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional, Any
from datetime import datetime, date
from decimal import Decimal

# Import the ENUMs you defined in models.py
from app.organizer.models import RoleEnum, AccountStatusEnum, EventStatusEnum, PaymentStatusEnum

# ==========================================
# 1. Core Users & Profiles
# ==========================================
class UserMainBase(BaseModel):
    id: str
    username: str
    role: RoleEnum
    # Password intentionally omitted for security in responses

    model_config = ConfigDict(from_attributes=True)

class CustomerInfoSchema(BaseModel):
    customer_id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrganizerInfoSchema(BaseModel):
    org_id: str
    company_name: str
    email: EmailStr
    primary_category: Optional[str] = None
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)

class UserStatusSchema(BaseModel):
    user_id: str
    status: AccountStatusEnum
    reason: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 2. Services & Offerings
# ==========================================
class ServiceListingSchema(BaseModel):
    id: str
    org_id: str
    category: str
    title: str
    base_price: Decimal

    model_config = ConfigDict(from_attributes=True)

class ServiceAddonSchema(BaseModel):
    id: str
    listing_id: str
    addon_name: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 3. Master Orders & Events
# ==========================================
class EventSchema(BaseModel):
    id: str
    customer_id: str
    org_id: str
    event_date: date
    status: EventStatusEnum

    model_config = ConfigDict(from_attributes=True)

class EventOrderSchema(BaseModel):
    id: str
    event_id: str
    listing_id: str
    base_price_at_booking: Decimal
    total_addons_cost: Decimal = Decimal('0.00')
    final_total_price: Decimal
    payment_status: PaymentStatusEnum

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 4. Financials
# ==========================================
class PaymentMilestoneSchema(BaseModel):
    id: str
    order_id: str
    amount: Decimal
    due_date: date
    status: PaymentStatusEnum

    model_config = ConfigDict(from_attributes=True)

class TransactionLogSchema(BaseModel):
    id: str
    order_id: Optional[str] = None
    user_id: str
    org_id: str
    gateway_ref: Optional[str] = None
    amount: Decimal
    status: PaymentStatusEnum
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# 5. Comms, AI & Analytics
# ==========================================
class ChatbotInteractionSchema(BaseModel):
    id: str
    customer_id: str
    query_text: str
    ai_response: Optional[dict[str, Any]] = None # Handles JSONB format
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class MessageSchema(BaseModel):
    id: str
    room_id: str
    sender_id: str
    message_text: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

class VendorReviewSchema(BaseModel):
    id: str
    event_id: str
    vendor_id: str
    rating: int = Field(ge=1, le=5) # Validates rating is between 1 and 5
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


###### EXTRA SCHEMA #######
class OrganizerRegisterSchema(BaseModel):
    # Removed id: str
    username: str
    password: str 
    company_name: str
    email: EmailStr
    primary_category: Optional[str] = None
    role: RoleEnum = RoleEnum.Organizer
    is_verified: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class userLoginSchema(BaseModel):
    username : str
    password : str

class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    id : str
    