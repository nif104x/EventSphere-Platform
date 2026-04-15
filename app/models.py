from sqlalchemy import Column, String, Numeric, Boolean, Date, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class OrganizerInfo(Base):
    __tablename__ = "organizer_info"
    org_id = Column(String(50), primary_key=True)
    company_name = Column(String(100))
    email = Column(String(100))


class ServiceListing(Base):
    __tablename__ = "service_listings"
    id = Column(String(50), primary_key=True)
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    category = Column(String(50))
    title = Column(String(150))
    base_price = Column(Numeric(10, 2))
    is_deleted = Column(Boolean, nullable=True)


class CustomerInfo(Base):
    __tablename__ = "customer_info"
    customer_id = Column(String(50), primary_key=True)
    full_name = Column(String(100))
    email = Column(String(100))


class Event(Base):
    __tablename__ = "events"
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customer_info.customer_id"))
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    event_date = Column(Date)
    status = Column(String(50))


class EventOrder(Base):
    __tablename__ = "event_orders"
    id = Column(String(50), primary_key=True)
    event_id = Column(String(50), ForeignKey("events.id"))
    listing_id = Column(String(50), ForeignKey("service_listings.id"))
    base_price_at_booking = Column(Numeric(10, 2))
    payment_status = Column(String(50))


class ServiceAddon(Base):
    __tablename__ = "service_addons"
    id = Column(String(50), primary_key=True)
    listing_id = Column(String(50), ForeignKey("service_listings.id"))
    addon_name = Column(String(100))
    price = Column(Numeric(10, 2))


class EventAddonSelection(Base):
    __tablename__ = "event_addon_selections"
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("event_orders.id"))
    addon_id = Column(String(50), ForeignKey("service_addons.id"))
    unit_price = Column(Numeric(10, 2))


class UserMain(Base):
    __tablename__ = "user_main"
    id = Column(String(50), primary_key=True)
    username = Column(String(50))
    role = Column(String(50))


class UserStatus(Base):
    __tablename__ = "user_status"
    user_id = Column(String(50), primary_key=True)
    status = Column(String(50))
    reason = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PaymentMilestone(Base):
    __tablename__ = "payment_milestones"
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("event_orders.id"))
    amount = Column(Numeric(10, 2))
    due_date = Column(Date)
    status = Column(String(50))

