from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Integer

from app.customer.database import Base
from enum import Enum as PyEnum

class AccountStatus(PyEnum):
    Active = "Active"
    Suspended = "Suspended"
    Banned = "Banned"

class EventStatus(PyEnum):
    Pending = "Pending"
    Confirmed = "Confirmed"
    Completed = "Completed"
    Cancelled = "Cancelled"

class PaymentStatus(PyEnum):
    Unpaid = "Unpaid"
    Pending = "Pending"
    Partial = "Partial"
    Paid = "Paid"
    Failed = "Failed"
    Refunded = "Refunded"

class RoleEnum(PyEnum):
    Admin = "Admin"
    Organizer = "Organizer"
    Customer = "Customer"

class UserMain(Base):
    __tablename__ = "user_main"
    id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(255))
    role = Column(Enum(RoleEnum))

class CustomerInfo(Base):
    __tablename__ = "customer_info"
    customer_id = Column(String(50), ForeignKey("user_main.id"), primary_key=True)
    full_name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    address = Column(String)

class OrganizerInfo(Base):
    __tablename__ = "organizer_info"
    org_id = Column(String(50), ForeignKey("user_main.id"), primary_key=True)
    company_name = Column(String(100))
    email = Column(String(100), unique=True)
    primary_category = Column(String(50))
    is_verified = Column(String)  # bool as string per schema

class ServiceListings(Base):
    __tablename__ = "service_listings"
    id = Column(String(50), primary_key=True, index=True)
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    category = Column(String(50))
    title = Column(String(150))
    base_price = Column(Numeric(10, 2))

class Events(Base):
    __tablename__ = "events"
    id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(50), ForeignKey("customer_info.customer_id"))
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    event_date = Column(Date)
    status = Column(Enum(EventStatus), default="Pending")

class EventOrders(Base):
    __tablename__ = "event_orders"
    id = Column(String(50), primary_key=True, index=True)
    event_id = Column(String(50), ForeignKey("events.id"))
    listing_id = Column(String(50), ForeignKey("service_listings.id"))
    base_price_at_booking = Column(Numeric(10, 2))
    total_addons_cost = Column(Numeric(10, 2), default=0)
    final_total_price = Column(Numeric(10, 2))
    payment_status = Column(Enum(PaymentStatus), default="Unpaid")


class VendorReviews(Base):
    __tablename__ = "vendor_reviews"
    id = Column(String(50), primary_key=True, index=True)
    event_id = Column(String(50), ForeignKey("events.id", ondelete="CASCADE"))
    vendor_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    rating = Column(Integer)
    comment = Column(String)


class VendorAnalytics(Base):
    __tablename__ = "vendor_analytics"
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"), primary_key=True)
    total_events = Column(Integer, default=0)
    total_earnings = Column(Numeric(10, 2), default=0)

