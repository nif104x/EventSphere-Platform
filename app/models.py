from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class UserMain(Base):
    __tablename__ = "user_main"
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

    customer_profile = relationship(
        "CustomerInfo", back_populates="user", uselist=False
    )
    organizer_profile = relationship(
        "OrganizerInfo", back_populates="user", uselist=False
    )
    admin_profile = relationship("AdminInfo", back_populates="user", uselist=False)
    status_row = relationship("UserStatus", back_populates="user", uselist=False)


class CustomerInfo(Base):
    __tablename__ = "customer_info"
    customer_id = Column(
        String(50), ForeignKey("user_main.id", ondelete="CASCADE"), primary_key=True
    )
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)

    user = relationship("UserMain", back_populates="customer_profile")


class OrganizerInfo(Base):
    __tablename__ = "organizer_info"
    org_id = Column(
        String(50), ForeignKey("user_main.id", ondelete="CASCADE"), primary_key=True
    )
    company_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    primary_category = Column(String(50))
    is_verified = Column(Boolean, default=False)

    user = relationship("UserMain", back_populates="organizer_profile")
    listings = relationship("ServiceListing", back_populates="organizer")


class AdminInfo(Base):
    __tablename__ = "admin_info"
    admin_id = Column(
        String(50), ForeignKey("user_main.id", ondelete="CASCADE"), primary_key=True
    )
    access_level = Column(String(50))

    user = relationship("UserMain", back_populates="admin_profile")


class UserStatus(Base):
    __tablename__ = "user_status"
    user_id = Column(
        String(50), ForeignKey("user_main.id", ondelete="CASCADE"), primary_key=True
    )
    status = Column(String(50))
    reason = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("UserMain", back_populates="status_row")


class ServiceListing(Base):
    __tablename__ = "service_listings"
    id = Column(String(50), primary_key=True)
    org_id = Column(String(50), ForeignKey("organizer_info.org_id", ondelete="CASCADE"))
    category = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    is_deleted = Column(Boolean, nullable=True)

    organizer = relationship("OrganizerInfo", back_populates="listings")
    addons = relationship("ServiceAddon", back_populates="listing")
    images = relationship("ListingImage", back_populates="listing")


class ListingImage(Base):
    __tablename__ = "listing_images"
    id = Column(String(50), primary_key=True)
    listing_id = Column(
        String(50), ForeignKey("service_listings.id", ondelete="CASCADE")
    )
    image_url = Column(Text, nullable=False)

    listing = relationship("ServiceListing", back_populates="images")


class ServiceAddon(Base):
    __tablename__ = "service_addons"
    id = Column(String(50), primary_key=True)
    listing_id = Column(
        String(50), ForeignKey("service_listings.id", ondelete="CASCADE")
    )
    addon_name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    listing = relationship("ServiceListing", back_populates="addons")


class Event(Base):
    __tablename__ = "events"
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customer_info.customer_id"))
    org_id = Column(String(50), ForeignKey("organizer_info.org_id"))
    event_date = Column(Date, nullable=False)
    status = Column(String(50))

    customer = relationship("CustomerInfo")
    organizer = relationship("OrganizerInfo")
    orders = relationship("EventOrder", back_populates="event")


class EventOrder(Base):
    __tablename__ = "event_orders"
    id = Column(String(50), primary_key=True)
    event_id = Column(String(50), ForeignKey("events.id", ondelete="CASCADE"))
    listing_id = Column(String(50), ForeignKey("service_listings.id"))
    base_price_at_booking = Column(Numeric(10, 2), nullable=False)
    total_addons_cost = Column(Numeric(10, 2))
    final_total_price = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(50))

    event = relationship("Event", back_populates="orders")
    listing = relationship("ServiceListing")
    selections = relationship("EventAddonSelection", back_populates="order")
    milestones = relationship("PaymentMilestone", back_populates="order")


class EventAddonSelection(Base):
    __tablename__ = "event_addon_selections"
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("event_orders.id", ondelete="CASCADE"))
    addon_id = Column(String(50), ForeignKey("service_addons.id"))
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("EventOrder", back_populates="selections")
    addon = relationship("ServiceAddon")


class PaymentMilestone(Base):
    __tablename__ = "payment_milestones"
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("event_orders.id", ondelete="CASCADE"))
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(50))

    order = relationship("EventOrder", back_populates="milestones")
