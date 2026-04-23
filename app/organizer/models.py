import enum
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

# ==========================================
# 1. ENUM Definitions
# ==========================================
class RoleEnum(enum.Enum):
    Admin = 'Admin'
    Organizer = 'Organizer'
    Customer = 'Customer'

class AccountStatusEnum(enum.Enum):
    Active = 'Active'
    Suspended = 'Suspended'
    Banned = 'Banned'

class EventStatusEnum(enum.Enum):
    Pending = 'Pending'
    Confirmed = 'Confirmed'
    Completed = 'Completed'
    Cancelled = 'Cancelled'

class PaymentStatusEnum(enum.Enum):
    Unpaid = 'Unpaid'
    Pending = 'Pending'
    Partial = 'Partial'
    Paid = 'Paid'
    Failed = 'Failed'
    Refunded = 'Refunded'

# ==========================================
# 2. Core Users & Profiles
# ==========================================
class UserMain(Base):
    __tablename__ = 'user_main'
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)

    # RELATIONSHIPS (1-to-1). 'uselist=False' means one user has exactly one profile.
    customer_profile = relationship("CustomerInfo", backref="user", uselist=False, cascade="all, delete-orphan")
    organizer_profile = relationship("OrganizerInfo", backref="user", uselist=False, cascade="all, delete-orphan")
    admin_profile = relationship("AdminInfo", backref="user", uselist=False, cascade="all, delete-orphan")


class CustomerInfo(Base):
    __tablename__ = 'customer_info'
    customer_id = Column(String(50), ForeignKey('user_main.id', ondelete='CASCADE'), primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)


class OrganizerInfo(Base):
    __tablename__ = 'organizer_info'
    org_id = Column(String(50), ForeignKey('user_main.id', ondelete='CASCADE'), primary_key=True)
    company_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    primary_category = Column(String(50))
    is_verified = Column(Boolean, default=False)
    
    # RELATIONSHIP: An organizer can have many listings
    listings = relationship("ServiceListing", backref="organizer", cascade="all, delete-orphan")


class AdminInfo(Base):
    __tablename__ = 'admin_info'
    admin_id = Column(String(50), ForeignKey('user_main.id', ondelete='CASCADE'), primary_key=True)
    access_level = Column(String(50), default='Support')


class UserStatus(Base):
    __tablename__ = 'user_status'
    user_id = Column(String(50), ForeignKey('user_main.id', ondelete='CASCADE'), primary_key=True)
    status = Column(Enum(AccountStatusEnum), default=AccountStatusEnum.Active)
    reason = Column(Text)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

# ==========================================
# 3. Services & Offerings
# ==========================================
class ServiceListing(Base):
    __tablename__ = 'service_listings'
    id = Column(String(50), primary_key=True)
    org_id = Column(String(50), ForeignKey('organizer_info.org_id', ondelete='CASCADE'))
    category = Column(String(50), nullable=False)
    title = Column(String(150), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    is_deleted = Column(Boolean, nullable=True, default=False)

    # RELATIONSHIPS: One listing has many images and many addons
    images = relationship("ListingImage", backref="listing", cascade="all, delete-orphan")
    addons = relationship("ServiceAddon", backref="listing", cascade="all, delete-orphan")


class ListingImage(Base):
    __tablename__ = 'listing_images'
    id = Column(String(50), primary_key=True)
    listing_id = Column(String(50), ForeignKey('service_listings.id', ondelete='CASCADE'))
    image_url = Column(Text, nullable=False)


class ServiceAddon(Base):
    __tablename__ = 'service_addons'
    id = Column(String(50), primary_key=True)
    listing_id = Column(String(50), ForeignKey('service_listings.id', ondelete='CASCADE'))
    addon_name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

# ==========================================
# 4. Master Orders & Events
# ==========================================
class Event(Base):
    __tablename__ = 'events'
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey('customer_info.customer_id'))
    org_id = Column(String(50), ForeignKey('organizer_info.org_id'))
    event_date = Column(Date, nullable=False)
    status = Column(Enum(EventStatusEnum), default=EventStatusEnum.Pending)

    # RELATIONSHIP (1-to-1): One event has exactly one master order
    order = relationship("EventOrder", backref="event", uselist=False, cascade="all, delete-orphan")
    customer = relationship("CustomerInfo", backref="events")

class EventOrder(Base):
    __tablename__ = 'event_orders'
    id = Column(String(50), primary_key=True)
    event_id = Column(String(50), ForeignKey('events.id', ondelete='CASCADE'))
    listing_id = Column(String(50), ForeignKey('service_listings.id'))
    base_price_at_booking = Column(Numeric(10, 2), nullable=False)
    total_addons_cost = Column(Numeric(10, 2), default=0.00)
    final_total_price = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.Unpaid)

    # RELATIONSHIPS: One order has many addon selections, milestones, and transactions
    selections = relationship("EventAddonSelection", backref="order", cascade="all, delete-orphan")
    milestones = relationship("PaymentMilestone", backref="order", cascade="all, delete-orphan")
    financial_summary = relationship("FinancialSummary", backref="order", uselist=False, cascade="all, delete-orphan")
    listing = relationship("ServiceListing", backref="orders")

class EventAddonSelection(Base):
    __tablename__ = 'event_addon_selections'
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey('event_orders.id', ondelete='CASCADE'))
    addon_id = Column(String(50), ForeignKey('service_addons.id'))
    unit_price = Column(Numeric(10, 2), nullable=False)
    
    # RELATIONSHIP: Links the selection back to the actual Addon details (like its name)
    addon_details = relationship("ServiceAddon")

# ==========================================
# 5. Financials
# ==========================================
class PaymentMilestone(Base):
    __tablename__ = 'payment_milestones'
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey('event_orders.id', ondelete='CASCADE'))
    amount = Column(Numeric(10, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.Unpaid)


class TransactionLog(Base):
    __tablename__ = 'transaction_log'
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey('event_orders.id', ondelete='SET NULL'))
    user_id = Column(String(50), ForeignKey('user_main.id'))
    org_id = Column(String(50), ForeignKey('organizer_info.org_id'))
    gateway_ref = Column(String(100))
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(PaymentStatusEnum), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())


class FinancialSummary(Base):
    __tablename__ = 'financial_summaries'
    id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey('event_orders.id', ondelete='CASCADE'))
    total_revenue = Column(Numeric(10, 2), default=0.00)
    total_cost = Column(Numeric(10, 2), default=0.00)
    net_profit = Column(Numeric(10, 2), default=0.00)

# ==========================================
# 6. Comms, AI & Analytics
# ==========================================
class ChatbotInteraction(Base):
    __tablename__ = 'chatbot_interactions'
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey('customer_info.customer_id', ondelete='CASCADE'))
    query_text = Column(Text, nullable=False)
    ai_response = Column(JSONB)
    timestamp = Column(DateTime, server_default=func.now())


class ChatRoom(Base):
    __tablename__ = 'chat_rooms'
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey('customer_info.customer_id'))
    org_id = Column(String(50), ForeignKey('organizer_info.org_id'))
    event_id = Column(String(50), ForeignKey('events.id', ondelete='CASCADE'))

    customer = relationship("CustomerInfo", foreign_keys=[customer_id])
    organizer = relationship("OrganizerInfo", foreign_keys=[org_id])

    # RELATIONSHIP: One room has many messages
    messages = relationship("Message", backref="room", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = 'messages'
    id = Column(String(50), primary_key=True)
    room_id = Column(String(50), ForeignKey('chat_rooms.id', ondelete='CASCADE'))
    sender_id = Column(String(50), ForeignKey('user_main.id'))
    message_text = Column(Text)
    image_url = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())


class VendorReview(Base):
    __tablename__ = 'vendor_reviews'
    id = Column(String(50), primary_key=True)
    event_id = Column(String(50), ForeignKey('events.id', ondelete='CASCADE'))
    vendor_id = Column(String(50), ForeignKey('organizer_info.org_id'))
    rating = Column(Integer)
    comment = Column(Text)


class VendorAnalytics(Base):
    __tablename__ = 'vendor_analytics'
    org_id = Column(String(50), ForeignKey('organizer_info.org_id', ondelete='CASCADE'), primary_key=True)
    total_events = Column(Integer, default=0)
    total_earnings = Column(Numeric(10, 2), default=0.00)