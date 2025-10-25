from sqlalchemy import Column, Integer, Text, JSON, ForeignKey, DateTime, Date, BigInteger, Float
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)

    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    stock_tickers = Column(JSON, nullable=False)
    objective_function = Column(Text, nullable=False)
    rebalance_interval = Column(Text, nullable=False)
    period = Column(Text, nullable=True)
    last_optimized_at = Column(DateTime(timezone=True))
    next_optimize_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="portfolios")
    weights = relationship("PortfolioWeights", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioWeights(Base):
    __tablename__ = "portfolio_weights"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    calculation_date = Column(DateTime(timezone=True), nullable=False)
    weights = Column(JSON, nullable=False)

    portfolio = relationship("Portfolio", back_populates="weights")


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(Text, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    adj_close = Column(Float)
    volume = Column(BigInteger)


