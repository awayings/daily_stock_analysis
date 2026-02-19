# -*- coding: utf-8 -*-
"""
===================================
投资组合数据访问层
===================================

职责：
1. 封装投资组合的数据库操作
2. 提供组合、持仓、历史快照的 CRUD 接口
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy import and_, func, select, or_
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, Portfolio, PortfolioHolding, PortfolioHistory, HoldingSnapshot

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """投资组合数据访问层"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()

    def create_portfolio(
        self,
        name: str,
        description: Optional[str] = None,
        initial_capital: Optional[Decimal] = None,
        currency: str = 'CNY'
    ) -> Portfolio:
        """创建组合"""
        with self.db.get_session() as session:
            portfolio = Portfolio(
                name=name,
                description=description,
                initial_capital=initial_capital,
                currency=currency
            )
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            return portfolio

    def get_portfolio_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """根据ID获取组合"""
        with self.db.get_session() as session:
            return session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalars().first()

    def get_portfolio_by_name(self, name: str, include_deleted: bool = False) -> Optional[Portfolio]:
        """根据名称获取组合"""
        with self.db.get_session() as session:
            conditions = [Portfolio.name == name]
            if not include_deleted:
                conditions.append(Portfolio.is_deleted == False)
            return session.execute(
                select(Portfolio).where(and_(*conditions))
            ).scalars().first()

    def get_portfolio_list(
        self,
        include_deleted: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Portfolio], int]:
        """获取组合列表"""
        with self.db.get_session() as session:
            query = select(Portfolio)
            if not include_deleted:
                query = query.where(Portfolio.is_deleted == False)

            query = query.order_by(Portfolio.created_at.desc())

            total = len(session.execute(query).scalars().all())

            query = query.offset((page - 1) * limit).limit(limit)
            items = session.execute(query).scalars().all()

            return list(items), total

    def update_portfolio(self, portfolio_id: int, **kwargs) -> Optional[Portfolio]:
        """更新组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalars().first()

            if portfolio:
                for key, value in kwargs.items():
                    if hasattr(portfolio, key):
                        setattr(portfolio, key, value)
                session.commit()
                session.refresh(portfolio)

            return portfolio

    def soft_delete_portfolio(self, portfolio_id: int) -> bool:
        """软删除组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalars().first()

            if portfolio:
                portfolio.is_deleted = True
                portfolio.deleted_at = datetime.now()
                session.commit()
                return True
            return False

    def restore_portfolio(self, portfolio_id: int) -> bool:
        """恢复已删除组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalars().first()

            if portfolio:
                portfolio.is_deleted = False
                portfolio.deleted_at = None
                session.commit()
                return True
            return False

    def count_portfolios(self, include_deleted: bool = False) -> int:
        """统计组合数量"""
        with self.db.get_session() as session:
            query = select(func.count(Portfolio.id))
            if not include_deleted:
                query = query.where(Portfolio.is_deleted == False)
            return session.execute(query).scalar() or 0

    def add_holding(
        self,
        portfolio_id: int,
        code: str,
        name: str,
        entry_price: Decimal,
        last_price: Decimal,
        weight: Decimal,
        shares: Optional[Decimal] = None
    ) -> PortfolioHolding:
        """添加持仓"""
        with self.db.get_session() as session:
            holding = PortfolioHolding(
                portfolio_id=portfolio_id,
                code=code,
                name=name,
                entry_price=entry_price,
                last_price=last_price,
                weight=weight,
                shares=shares
            )
            session.add(holding)
            session.commit()
            session.refresh(holding)
            return holding

    def get_holdings(
        self,
        portfolio_id: int,
        include_closed: bool = False
    ) -> List[PortfolioHolding]:
        """获取组合的所有持仓"""
        with self.db.get_session() as session:
            query = select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id
            )
            if not include_closed:
                query = query.where(PortfolioHolding.is_closed == False)
            return list(session.execute(query).scalars().all())

    def get_holding_by_id(self, holding_id: int) -> Optional[PortfolioHolding]:
        """根据ID获取持仓"""
        with self.db.get_session() as session:
            return session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalars().first()

    def update_holding(self, holding_id: int, **kwargs) -> Optional[PortfolioHolding]:
        """更新持仓"""
        with self.db.get_session() as session:
            holding = session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalars().first()

            if holding:
                for key, value in kwargs.items():
                    if hasattr(holding, key):
                        setattr(holding, key, value)
                session.commit()
                session.refresh(holding)

            return holding

    def close_holding(
        self,
        holding_id: int,
        close_price: Decimal,
        close_quantity: Decimal,
        close_type: str
    ) -> Optional[PortfolioHolding]:
        """平仓持仓"""
        with self.db.get_session() as session:
            holding = session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalars().first()

            if holding:
                holding.is_closed = True
                holding.close_price = close_price
                holding.close_quantity = close_quantity
                holding.close_type = close_type
                holding.closed_at = datetime.now()
                session.commit()
                session.refresh(holding)

            return holding

    def get_closed_holdings_since(
        self,
        portfolio_id: int,
        since: datetime
    ) -> List[PortfolioHolding]:
        """获取指定时间后平仓的持仓"""
        with self.db.get_session() as session:
            return list(session.execute(
                select(PortfolioHolding).where(
                    and_(
                        PortfolioHolding.portfolio_id == portfolio_id,
                        PortfolioHolding.is_closed == True,
                        PortfolioHolding.closed_at >= since
                    )
                )
            ).scalars().all())

    def count_holdings(self, portfolio_id: int, include_closed: bool = False) -> int:
        """统计持仓数量"""
        with self.db.get_session() as session:
            query = select(func.count(PortfolioHolding.id)).where(
                PortfolioHolding.portfolio_id == portfolio_id
            )
            if not include_closed:
                query = query.where(PortfolioHolding.is_closed == False)
            return session.execute(query).scalar() or 0

    def save_history(
        self,
        portfolio_id: int,
        snapshot_date: date,
        data: Dict[str, Any]
    ) -> PortfolioHistory:
        """保存历史快照"""
        with self.db.get_session() as session:
            history = PortfolioHistory(
                portfolio_id=portfolio_id,
                snapshot_date=snapshot_date,
                total_value=data.get('total_value'),
                unrealized_pnl_pct=data.get('unrealized_pnl_pct'),
                unrealized_pnl_amount=data.get('unrealized_pnl_amount'),
                realized_pnl_amount=data.get('realized_pnl_amount', 0),
                cumulative_realized_pnl=data.get('cumulative_realized_pnl', 0),
                total_pnl_pct=data.get('total_pnl_pct'),
                total_pnl_amount=data.get('total_pnl_amount'),
                active_holdings_count=data.get('active_holdings_count', 0),
                closed_holdings_count=data.get('closed_holdings_count', 0),
                calculation_status=data.get('calculation_status', 'success'),
                error_message=data.get('error_message')
            )
            session.add(history)
            session.flush()
            
            result = PortfolioHistory(
                id=history.id,
                portfolio_id=history.portfolio_id,
                snapshot_date=history.snapshot_date,
                total_value=history.total_value,
                unrealized_pnl_pct=history.unrealized_pnl_pct,
                unrealized_pnl_amount=history.unrealized_pnl_amount,
                realized_pnl_amount=history.realized_pnl_amount,
                cumulative_realized_pnl=history.cumulative_realized_pnl,
                total_pnl_pct=history.total_pnl_pct,
                total_pnl_amount=history.total_pnl_amount,
                active_holdings_count=history.active_holdings_count,
                closed_holdings_count=history.closed_holdings_count,
                calculation_status=history.calculation_status,
                calculated_at=history.calculated_at,
                error_message=history.error_message
            )
            session.commit()
            return result

    def get_history(
        self,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[PortfolioHistory], int]:
        """获取历史快照"""
        with self.db.get_session() as session:
            query = select(PortfolioHistory).where(
                PortfolioHistory.portfolio_id == portfolio_id
            )

            if start_date:
                query = query.where(PortfolioHistory.snapshot_date >= start_date)
            if end_date:
                query = query.where(PortfolioHistory.snapshot_date <= end_date)

            query = query.order_by(PortfolioHistory.snapshot_date.desc())

            total = len(session.execute(query).scalars().all())

            query = query.offset((page - 1) * limit).limit(limit)
            items = session.execute(query).scalars().all()

            return list(items), total

    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        """获取最新的历史快照"""
        with self.db.get_session() as session:
            return session.execute(
                select(PortfolioHistory)
                .where(PortfolioHistory.portfolio_id == portfolio_id)
                .order_by(PortfolioHistory.snapshot_date.desc())
                .limit(1)
            ).scalars().first()

    def save_holding_snapshots(
        self,
        history_id: int,
        snapshots: List[Dict[str, Any]]
    ) -> List[HoldingSnapshot]:
        """保存持仓快照"""
        with self.db.get_session() as session:
            result_snapshots = []
            for data in snapshots:
                snapshot = HoldingSnapshot(
                    history_id=history_id,
                    code=data['code'],
                    name=data.get('name'),
                    entry_price=data['entry_price'],
                    current_price=data.get('current_price'),
                    weight=data['weight'],
                    pnl_pct=data.get('pnl_pct'),
                    weighted_pnl=data.get('weighted_pnl')
                )
                session.add(snapshot)
                session.flush()
                
                result_snapshots.append(HoldingSnapshot(
                    id=snapshot.id,
                    history_id=snapshot.history_id,
                    code=snapshot.code,
                    name=snapshot.name,
                    entry_price=snapshot.entry_price,
                    current_price=snapshot.current_price,
                    weight=snapshot.weight,
                    pnl_pct=snapshot.pnl_pct,
                    weighted_pnl=snapshot.weighted_pnl
                ))

            session.commit()
            return result_snapshots

    def get_holding_snapshots(self, history_id: int) -> List[HoldingSnapshot]:
        """获取持仓快照"""
        with self.db.get_session() as session:
            return list(session.execute(
                select(HoldingSnapshot).where(
                    HoldingSnapshot.history_id == history_id
                )
            ).scalars().all())
