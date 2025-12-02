from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Wishlist(Base):
    __tablename__ = "wishlists"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    accommodation_id = Column(String, ForeignKey("accommodations.id"), index=True)
    notify_when_bookable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
