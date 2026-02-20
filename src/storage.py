# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - 存储层
===================================

职责：
1. 管理 SQLite/Doris 数据库连接（单例模式）
2. 定义 ORM 数据模型（支持 Doris UNIQUE KEY 模型）
3. 提供数据存取接口
4. 实现智能更新逻辑（断点续传）
"""

import atexit
import hashlib
import json
import logging
import re
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple

import pandas as pd
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    Integer,
    BigInteger,
    ForeignKey,
    Index,
    UniqueConstraint,
    Text,
    Numeric,
    select,
    and_,
    desc,
    text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session,
)
from sqlalchemy.exc import IntegrityError

from src.config import get_config

logger = logging.getLogger(__name__)

SQLITE_BASE = declarative_base()

if TYPE_CHECKING:
    from src.search_service import SearchResponse


def _get_doris_base():
    """延迟导入 DorisBase，避免在非 Doris 环境下导入失败"""
    try:
        from doris_alchemy import DorisBase as _DorisBase
        return _DorisBase
    except ImportError:
        logger.warning("doris-alchemy 未安装，将使用标准 SQLAlchemy Base")
        return SQLITE_BASE


def _get_doris_distributed():
    """延迟导入 Doris 分布式函数"""
    try:
        from doris_alchemy import HASH
        return HASH
    except ImportError:
        return None


class StockDaily(SQLITE_BASE):
    """
    股票日线数据模型
    
    存储每日行情数据和计算的技术指标
    支持多股票、多日期的唯一约束
    
    Doris UNIQUE KEY 模型：
    - 主键: code, date
    - 分布: HASH(code)
    """
    __tablename__ = 'stock_daily'
    
    __table_args__ = (
        UniqueConstraint('code', 'date', name='uix_code_date'),
        Index('ix_code_date', 'code', 'date'),
        {'extend_existing': True},
    )
    
    code = Column(String(10), nullable=False, primary_key=True)  # 股票代码（如 600519, 000001）
    date = Column(Date, nullable=False, primary_key=True)  # 交易日期
    id = Column(BigInteger, nullable=False, autoincrement=True)  # 自增主键
    
    open = Column(Float)  # 开盘价
    high = Column(Float)  # 最高价
    low = Column(Float)  # 最低价
    close = Column(Float)  # 收盘价
    
    volume = Column(Float)  # 成交量（股）
    amount = Column(Float)  # 成交额（元）
    pct_chg = Column(Float)  # 涨跌幅（%）
    
    ma5 = Column(Float)  # 5日均线
    ma10 = Column(Float)  # 10日均线
    ma20 = Column(Float)  # 20日均线
    volume_ratio = Column(Float)  # 量比
    
    data_source = Column(String(50))  # 记录数据来源（如 AkshareFetcher）
    created_at = Column(DateTime, default=datetime.now)  # 创建时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间
    
    doris_unique_key = ('code', 'date')
    doris_distributed_by = None
    
    def __repr__(self):
        return f"<StockDaily(code={self.code}, date={self.date}, close={self.close})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'date': self.date,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'amount': self.amount,
            'pct_chg': self.pct_chg,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'volume_ratio': self.volume_ratio,
            'data_source': self.data_source,
        }


class NewsIntel(SQLITE_BASE):
    """
    新闻情报数据模型

    存储搜索到的新闻情报条目，用于后续分析与查询
    
    Doris UNIQUE KEY 模型：
    - 主键: url
    - 分布: HASH(url)
    """
    __tablename__ = 'news_intel'

    __table_args__ = (
        UniqueConstraint('url', name='uix_news_url'),
        Index('ix_news_code_pub', 'code', 'published_date'),
        {'extend_existing': True},
    )

    url = Column(String(1000), nullable=False, primary_key=True)  # 新闻URL（唯一键）
    id = Column(BigInteger, nullable=False, autoincrement=True)  # 自增主键
    
    query_id = Column(String(64))  # 关联用户查询操作
    code = Column(String(10), nullable=False)  # 股票代码
    name = Column(String(50))  # 股票名称
    
    dimension = Column(String(32))  # 搜索维度：latest_news / risk_check / earnings / market_analysis / industry
    query = Column(String(255))  # 搜索查询内容
    provider = Column(String(32))  # 数据提供商
    
    title = Column(String(300), nullable=False)  # 新闻标题
    snippet = Column(Text)  # 新闻摘要
    source = Column(String(100))  # 新闻来源
    published_date = Column(DateTime)  # 发布时间
    
    fetched_at = Column(DateTime, default=datetime.now)  # 入库时间
    query_source = Column(String(32))  # 查询来源：bot/web/cli/system
    requester_platform = Column(String(20))  # 请求平台
    requester_user_id = Column(String(64))  # 用户ID
    requester_user_name = Column(String(64))  # 用户名
    requester_chat_id = Column(String(64))  # 会话ID
    requester_message_id = Column(String(64))  # 消息ID
    requester_query = Column(String(255))  # 原始查询

    doris_unique_key = ('url',)
    doris_distributed_by = None

    def __repr__(self) -> str:
        return f"<NewsIntel(code={self.code}, title={self.title[:20] if self.title else 'N/A'}...)>"


class AnalysisHistory(SQLITE_BASE):
    """
    分析结果历史记录模型

    保存每次分析结果，支持按 query_id/股票代码检索
    
    Doris UNIQUE KEY 模型：
    - 主键: id (自增)
    - 分布: HASH(id)
    """
    __tablename__ = 'analysis_history'

    __table_args__ = (
        Index('ix_analysis_code_time', 'code', 'created_at'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # 主键
    query_id = Column(String(64))  # 关联查询链路
    
    code = Column(String(10), nullable=False)  # 股票代码
    name = Column(String(50))  # 股票名称
    report_type = Column(String(16))  # 报告类型
    
    sentiment_score = Column(Integer)  # 情绪分数
    operation_advice = Column(String(20))  # 操作建议
    trend_prediction = Column(String(50))  # 趋势预测
    analysis_summary = Column(Text)  # 分析摘要
    
    raw_result = Column(Text)  # 原始结果JSON
    news_content = Column(Text)  # 新闻内容
    context_snapshot = Column(Text)  # 上下文快照JSON
    
    ideal_buy = Column(Float)  # 理想买点（用于回测）
    secondary_buy = Column(Float)  # 次级买点（用于回测）
    stop_loss = Column(Float)  # 止损价（用于回测）
    take_profit = Column(Float)  # 止盈价（用于回测）
    
    created_at = Column(DateTime, default=datetime.now)  # 创建时间

    doris_unique_key = ('id',)
    doris_distributed_by = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'query_id': self.query_id,
            'code': self.code,
            'name': self.name,
            'report_type': self.report_type,
            'sentiment_score': self.sentiment_score,
            'operation_advice': self.operation_advice,
            'trend_prediction': self.trend_prediction,
            'analysis_summary': self.analysis_summary,
            'raw_result': self.raw_result,
            'news_content': self.news_content,
            'context_snapshot': self.context_snapshot,
            'ideal_buy': self.ideal_buy,
            'secondary_buy': self.secondary_buy,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class BacktestResult(SQLITE_BASE):
    """
    单条分析记录的回测结果
    
    Doris UNIQUE KEY 模型：
    - 主键: analysis_history_id, eval_window_days, engine_version
    - 分布: HASH(analysis_history_id)
    """

    __tablename__ = 'backtest_results'

    __table_args__ = (
        UniqueConstraint(
            'analysis_history_id',
            'eval_window_days',
            'engine_version',
            name='uix_backtest_analysis_window_version',
        ),
        Index('ix_backtest_code_date', 'code', 'analysis_date'),
        {'extend_existing': True},
    )

    analysis_history_id = Column(Integer, nullable=False, primary_key=True)  # 关联分析记录ID
    eval_window_days = Column(Integer, nullable=False, default=10, primary_key=True)  # 评估窗口天数
    engine_version = Column(String(16), nullable=False, default='v1', primary_key=True)  # 引擎版本
    id = Column(BigInteger, nullable=False, autoincrement=True)  # 自增主键
    
    code = Column(String(10), nullable=False)  # 股票代码（冗余字段，便于按股票筛选）
    analysis_date = Column(Date)  # 分析日期
    
    eval_status = Column(String(16), nullable=False, default='pending')  # 评估状态
    evaluated_at = Column(DateTime, default=datetime.now)  # 评估时间
    
    operation_advice = Column(String(20))  # 操作建议快照（避免未来分析字段变化导致回测不可解释）
    position_recommendation = Column(String(8))  # 仓位建议：long/cash
    
    start_price = Column(Float)  # 起始价格
    end_close = Column(Float)  # 结束价格
    max_high = Column(Float)  # 最高价
    min_low = Column(Float)  # 最低价
    stock_return_pct = Column(Float)  # 股票收益率
    
    direction_expected = Column(String(16))  # 预期方向：up/down/flat/not_down
    direction_correct = Column(Boolean, nullable=True)  # 方向是否正确
    outcome = Column(String(16))  # 结果：win/loss/neutral
    
    stop_loss = Column(Float)  # 止损价（仅 long 且配置了止盈/止损时有意义）
    take_profit = Column(Float)  # 止盈价
    hit_stop_loss = Column(Boolean)  # 是否触发止损
    hit_take_profit = Column(Boolean)  # 是否触发止盈
    first_hit = Column(String(16))  # 首次触发：take_profit/stop_loss/ambiguous/neither/not_applicable
    first_hit_date = Column(Date)  # 首次触发日期
    first_hit_trading_days = Column(Integer)  # 首次触发交易天数
    
    simulated_entry_price = Column(Float)  # 模拟入场价（long-only）
    simulated_exit_price = Column(Float)  # 模拟出场价
    simulated_exit_reason = Column(String(24))  # 出场原因：stop_loss/take_profit/window_end/cash/ambiguous_stop_loss
    simulated_return_pct = Column(Float)  # 模拟收益率

    doris_unique_key = ('analysis_history_id', 'eval_window_days', 'engine_version')
    doris_distributed_by = None


class BacktestSummary(SQLITE_BASE):
    """
    回测汇总指标（按股票或全局）
    
    Doris UNIQUE KEY 模型：
    - 主键: scope, code, eval_window_days, engine_version
    - 分布: HASH(scope)
    """

    __tablename__ = 'backtest_summaries'

    __table_args__ = (
        UniqueConstraint(
            'scope',
            'code',
            'eval_window_days',
            'engine_version',
            name='uix_backtest_summary_scope_code_window_version',
        ),
        {'extend_existing': True},
    )

    scope = Column(String(16), nullable=False, primary_key=True)  # 范围：overall/stock
    code = Column(String(16), primary_key=True)  # 股票代码（overall时为空）
    eval_window_days = Column(Integer, nullable=False, default=10, primary_key=True)  # 评估窗口天数
    engine_version = Column(String(16), nullable=False, default='v1', primary_key=True)  # 引擎版本
    id = Column(BigInteger, nullable=False, autoincrement=True)  # 自增主键
    
    computed_at = Column(DateTime, default=datetime.now)  # 计算时间
    
    total_evaluations = Column(Integer, default=0)  # 总评估数
    completed_count = Column(Integer, default=0)  # 完成数
    insufficient_count = Column(Integer, default=0)  # 数据不足数
    long_count = Column(Integer, default=0)  # 做多数
    cash_count = Column(Integer, default=0)  # 空仓数
    
    win_count = Column(Integer, default=0)  # 盈利数
    loss_count = Column(Integer, default=0)  # 亏损数
    neutral_count = Column(Integer, default=0)  # 中性数
    
    direction_accuracy_pct = Column(Float)  # 方向准确率
    win_rate_pct = Column(Float)  # 胜率
    neutral_rate_pct = Column(Float)  # 中性率
    
    avg_stock_return_pct = Column(Float)  # 平均股票收益
    avg_simulated_return_pct = Column(Float)  # 平均模拟收益
    
    stop_loss_trigger_rate = Column(Float)  # 止损触发率（仅 long 且配置止盈/止损时统计）
    take_profit_trigger_rate = Column(Float)  # 止盈触发率
    ambiguous_rate = Column(Float)  # 模糊率
    avg_days_to_first_hit = Column(Float)  # 平均触发天数
    
    advice_breakdown_json = Column(Text)  # 建议分布JSON
    diagnostics_json = Column(Text)  # 诊断JSON

    doris_unique_key = ('scope', 'code', 'eval_window_days', 'engine_version')
    doris_distributed_by = None


class Portfolio(SQLITE_BASE):
    """
    投资组合模型

    存储投资组合的基本信息

    Doris UNIQUE KEY 模型：
    - 主键: id
    - 分布: HASH(id)
    """
    __tablename__ = 'portfolios'

    __table_args__ = (
        Index('ix_portfolios_created', 'created_at'),
        Index('ix_portfolios_deleted', 'is_deleted', 'deleted_at'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    initial_capital = Column(Numeric(18, 4))
    currency = Column(String(10), default='CNY')
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    doris_unique_key = ('id',)
    doris_distributed_by = None

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name={self.name})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'initial_capital': float(self.initial_capital) if self.initial_capital else None,
            'currency': self.currency,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PortfolioHolding(SQLITE_BASE):
    """
    持仓模型

    存储投资组合中的股票持仓信息

    Doris UNIQUE KEY 模型：
    - 主键: id
    - 分布: HASH(portfolio_id)
    """
    __tablename__ = 'portfolio_holdings'

    __table_args__ = (
        Index('ix_holdings_portfolio', 'portfolio_id'),
        Index('ix_holdings_code', 'code'),
        Index('ix_holdings_closed', 'portfolio_id', 'is_closed'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id = Column(BigInteger, ForeignKey('portfolios.id'), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100))
    entry_price = Column(Numeric(18, 4), nullable=False)
    last_price = Column(Numeric(18, 4), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    shares = Column(Numeric(18, 4))
    is_closed = Column(Integer, default=0)
    close_price = Column(Numeric(18, 4))
    close_quantity = Column(Numeric(18, 4))
    close_type = Column(String(20))
    added_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    doris_unique_key = ('id',)
    doris_distributed_by = None

    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, code={self.code}, weight={self.weight})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'code': self.code,
            'name': self.name,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'last_price': float(self.last_price) if self.last_price else None,
            'weight': float(self.weight) if self.weight else None,
            'shares': float(self.shares) if self.shares else None,
            'is_closed': self.is_closed,
            'close_price': float(self.close_price) if self.close_price else None,
            'close_quantity': float(self.close_quantity) if self.close_quantity else None,
            'close_type': self.close_type,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class PortfolioHistory(SQLITE_BASE):
    """
    历史快照模型

    存储每周计算生成的组合收益快照

    Doris UNIQUE KEY 模型：
    - 主键: portfolio_id, snapshot_date
    - 分布: HASH(portfolio_id)
    """
    __tablename__ = 'portfolio_history'

    __table_args__ = (
        Index('ix_history_portfolio_date', 'portfolio_id', 'snapshot_date'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id = Column(BigInteger, ForeignKey('portfolios.id'), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    total_value = Column(Numeric(18, 4))
    unrealized_pnl_pct = Column(Numeric(10, 4))
    unrealized_pnl_amount = Column(Numeric(18, 4))
    realized_pnl_amount = Column(Numeric(18, 4), default=0)
    cumulative_realized_pnl = Column(Numeric(18, 4), default=0)
    total_pnl_pct = Column(Numeric(10, 4))
    total_pnl_amount = Column(Numeric(18, 4))
    active_holdings_count = Column(Integer, default=0)
    closed_holdings_count = Column(Integer, default=0)
    calculation_status = Column(String(20), default='pending')
    error_message = Column(Text)
    calculated_at = Column(DateTime, default=datetime.now)

    doris_unique_key = ('portfolio_id', 'snapshot_date')
    doris_distributed_by = None

    def __repr__(self):
        return f"<PortfolioHistory(id={self.id}, portfolio_id={self.portfolio_id}, snapshot_date={self.snapshot_date})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None,
            'total_value': float(self.total_value) if self.total_value else None,
            'unrealized_pnl_pct': float(self.unrealized_pnl_pct) if self.unrealized_pnl_pct else None,
            'unrealized_pnl_amount': float(self.unrealized_pnl_amount) if self.unrealized_pnl_amount else None,
            'realized_pnl_amount': float(self.realized_pnl_amount) if self.realized_pnl_amount else 0,
            'cumulative_realized_pnl': float(self.cumulative_realized_pnl) if self.cumulative_realized_pnl else 0,
            'total_pnl_pct': float(self.total_pnl_pct) if self.total_pnl_pct else None,
            'total_pnl_amount': float(self.total_pnl_amount) if self.total_pnl_amount else None,
            'active_holdings_count': self.active_holdings_count,
            'closed_holdings_count': self.closed_holdings_count,
            'calculation_status': self.calculation_status,
            'error_message': self.error_message,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
        }


class HoldingSnapshot(SQLITE_BASE):
    """
    持仓快照模型

    存储每个历史快照时间点的持仓详情

    Doris UNIQUE KEY 模型：
    - 主键: id
    - 分布: HASH(history_id)
    """
    __tablename__ = 'holding_snapshots'

    __table_args__ = (
        Index('ix_snapshots_history', 'history_id'),
        Index('ix_snapshots_code', 'code'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    history_id = Column(BigInteger, ForeignKey('portfolio_history.id'), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100))
    entry_price = Column(Numeric(18, 4), nullable=False)
    current_price = Column(Numeric(18, 4))
    weight = Column(Numeric(5, 2), nullable=False)
    pnl_pct = Column(Numeric(10, 4))
    weighted_pnl = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.now)

    doris_unique_key = ('id',)
    doris_distributed_by = None

    def __repr__(self):
        return f"<HoldingSnapshot(id={self.id}, history_id={self.history_id}, code={self.code})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'history_id': self.history_id,
            'code': self.code,
            'name': self.name,
            'entry_price': float(self.entry_price) if self.entry_price else None,
            'current_price': float(self.current_price) if self.current_price else None,
            'weight': float(self.weight) if self.weight else None,
            'pnl_pct': float(self.pnl_pct) if self.pnl_pct else None,
            'weighted_pnl': float(self.weighted_pnl) if self.weighted_pnl else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SyncStatistics(SQLITE_BASE):
    """
    同步统计记录模型

    存储每日股票数据同步的统计信息，用于追踪同步历史

    Doris UNIQUE KEY 模型：
    - 主键: id
    - 分布: HASH(id)
    """
    __tablename__ = 'sync_statistics'

    __table_args__ = (
        Index('ix_sync_statistics_sync_date', 'sync_date'),
        Index('ix_sync_statistics_synced_at', 'synced_at'),
        {'extend_existing': True},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sync_date = Column(Date, nullable=False)
    total_stocks = Column(Integer)
    success_count = Column(Integer)
    failed_count = Column(Integer)
    data_sources = Column(String(255))
    validation_passed = Column(Boolean)
    validation_details = Column(Text)
    synced_at = Column(DateTime, default=datetime.now)

    doris_unique_key = ('id',)
    doris_distributed_by = None

    def __repr__(self):
        return f"<SyncStatistics(id={self.id}, sync_date={self.sync_date}, success={self.success_count}/{self.total_stocks})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'sync_date': self.sync_date.isoformat() if self.sync_date else None,
            'total_stocks': self.total_stocks,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'data_sources': self.data_sources,
            'validation_passed': self.validation_passed,
            'validation_details': self.validation_details,
            'synced_at': self.synced_at.isoformat() if self.synced_at else None,
        }


ALL_MODELS = [
    StockDaily,
    NewsIntel,
    AnalysisHistory,
    BacktestResult,
    BacktestSummary,
    Portfolio,
    PortfolioHolding,
    PortfolioHistory,
    HoldingSnapshot,
    SyncStatistics,
]


class DatabaseManager:
    """
    数据库管理器 - 单例模式
    
    职责：
    1. 管理数据库连接池
    2. 提供 Session 上下文管理
    3. 封装数据存取操作
    4. 支持 SQLite 和 Doris
    """
    
    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False
    _is_doris: bool = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_url: Optional[str] = None):
        """
        初始化数据库管理器
        
        Args:
            db_url: 数据库连接 URL（可选，默认从配置读取）
        """
        if getattr(self, '_initialized', False):
            return
        
        if db_url is None:
            config = get_config()
            db_url = config.get_db_url()
            self._is_doris = config.database_type == 'doris'
        
        self._engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
        )
        
        self._SessionLocal = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
        )
        
        if not self._is_doris:
            SQLITE_BASE.metadata.create_all(self._engine)
        else:
            logger.info("Doris 模式：跳过自动创建表，需要手动创建表")
            self._create_doris_tables()

        self._initialized = True
        logger.info(f"数据库初始化完成: {db_url.split('@')[-1] if '@' in db_url else db_url} (类型: {'Doris' if self._is_doris else 'SQLite'})")

        atexit.register(DatabaseManager._cleanup_engine, self._engine)
    
    def _create_doris_tables(self) -> None:
        """创建 Doris 表（使用 UNIQUE KEY 模型）"""
        try:
            HASH = _get_doris_distributed()
            
            with self._engine.connect() as conn:
                for model in ALL_MODELS:
                    table_name = model.__tablename__
                    
                    result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                    if result.fetchone():
                        logger.info(f"Doris 表 {table_name} 已存在，跳过创建")
                        continue
                    
                    create_sql = self._generate_doris_create_table_sql(model, HASH)
                    if create_sql:
                        conn.execute(text(create_sql))
                        conn.commit()
                        logger.info(f"Doris 表 {table_name} 创建成功")
                        
        except Exception as e:
            logger.warning(f"创建 Doris 表时出错: {e}")
    
    def _generate_doris_create_table_sql(self, model, HASH) -> Optional[str]:
        """生成 Doris CREATE TABLE SQL"""
        table_name = model.__tablename__
        unique_key = getattr(model, 'doris_unique_key', None)
        
        if not unique_key:
            return None
        
        key_columns_sql = []
        other_columns_sql = []
        
        for col in model.__table__.columns:
            col_type = self._get_doris_column_type(col)
            nullable = "" if col.nullable else " NOT NULL"
            auto_inc = " AUTO_INCREMENT" if col.autoincrement and col.name == 'id' else ""
            default_val = ""
            if col.default is not None:
                if hasattr(col.default, 'arg'):
                    if callable(col.default.arg):
                        pass
                    else:
                        default_val = f" DEFAULT '{col.default.arg}'"
            
            col_sql = f"    `{col.name}` {col_type}{nullable}{auto_inc}{default_val}"
            
            if col.name in unique_key:
                key_columns_sql.append((unique_key.index(col.name), col_sql))
            else:
                other_columns_sql.append(col_sql)
        
        key_columns_sql.sort(key=lambda x: x[0])
        columns_sql = [col_sql for _, col_sql in key_columns_sql] + other_columns_sql
        
        unique_key_sql = f"UNIQUE KEY ({', '.join([f'`{k}`' for k in unique_key])})"
        
        if HASH:
            if table_name == 'stock_daily':
                dist_sql = "DISTRIBUTED BY HASH(`code`) BUCKETS 3"
            elif table_name == 'news_intel':
                dist_sql = "DISTRIBUTED BY HASH(`url`) BUCKETS 3"
            elif table_name == 'analysis_history':
                dist_sql = "DISTRIBUTED BY HASH(`id`) BUCKETS 3"
            elif table_name == 'backtest_results':
                dist_sql = "DISTRIBUTED BY HASH(`analysis_history_id`) BUCKETS 3"
            elif table_name == 'backtest_summaries':
                dist_sql = "DISTRIBUTED BY HASH(`scope`) BUCKETS 3"
            else:
                dist_sql = f"DISTRIBUTED BY HASH(`{unique_key[0]}`) BUCKETS 3"
        else:
            dist_sql = f"DISTRIBUTED BY HASH(`{unique_key[0]}`) BUCKETS 3"
        
        properties = '''PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
)'''
        
        sql = f"""CREATE TABLE IF NOT EXISTS `{table_name}` (
{',\n'.join(columns_sql)}
)
{unique_key_sql}
{dist_sql}
{properties}"""
        
        return sql
    
    def _get_doris_column_type(self, col) -> str:
        """获取 Doris 列类型"""
        col_type = str(col.type)
        
        type_mapping = {
            'INTEGER': 'INT',
            'BIGINT': 'BIGINT',
            'SMALLINT': 'SMALLINT',
            'TINYINT': 'TINYINT',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR',
            'STRING': 'VARCHAR',
            'TEXT': 'STRING',
            'FLOAT': 'DOUBLE',
            'DOUBLE': 'DOUBLE',
            'DECIMAL': 'DECIMAL',
            'NUMERIC': 'DECIMAL',
            'BOOLEAN': 'BOOLEAN',
            'DATE': 'DATE',
            'DATETIME': 'DATETIME',
        }
        
        for key, value in type_mapping.items():
            if col_type.upper().startswith(key):
                if key == 'VARCHAR':
                    match = re.search(r'VARCHAR\((\d+)\)', col_type.upper())
                    if match:
                        return f"VARCHAR({match.group(1)})"
                if key == 'CHAR':
                    match = re.search(r'CHAR\((\d+)\)', col_type.upper())
                    if match:
                        return f"CHAR({match.group(1)})"
                if key in ('DECIMAL', 'NUMERIC'):
                    match = re.search(r'(?:DECIMAL|NUMERIC)\((\d+),?\s*(\d*)\)', col_type.upper())
                    if match:
                        precision = match.group(1)
                        scale = match.group(2) if match.group(2) else '0'
                        return f"DECIMAL({precision}, {scale})"
                return value
        
        return 'STRING'
    
    @property
    def is_doris(self) -> bool:
        """是否使用 Doris 数据库"""
        return self._is_doris
    
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            if hasattr(cls._instance, '_engine') and cls._instance._engine is not None:
                cls._instance._engine.dispose()
            cls._instance._initialized = False
            cls._instance = None

    @classmethod
    def _cleanup_engine(cls, engine) -> None:
        """
        清理数据库引擎（atexit 钩子）

        确保程序退出时关闭所有数据库连接，避免 ResourceWarning

        Args:
            engine: SQLAlchemy 引擎对象
        """
        try:
            if engine is not None:
                engine.dispose()
                logger.debug("数据库引擎已清理")
        except Exception as e:
            logger.warning(f"清理数据库引擎时出错: {e}")
    
    def get_session(self) -> Session:
        """
        获取数据库 Session
        
        使用示例:
            with db.get_session() as session:
                # 执行查询
                session.commit()  # 如果需要
        """
        if not getattr(self, '_initialized', False) or not hasattr(self, '_SessionLocal'):
            raise RuntimeError(
                "DatabaseManager 未正确初始化。"
                "请确保通过 DatabaseManager.get_instance() 获取实例。"
            )
        session = self._SessionLocal()
        try:
            return session
        except Exception:
            session.close()
            raise
    
    def has_today_data(self, code: str, target_date: Optional[date] = None) -> bool:
        """
        检查是否已有指定日期的数据
        
        用于断点续传逻辑：如果已有数据则跳过网络请求
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            是否存在数据
        """
        if target_date is None:
            target_date = date.today()
        
        with self.get_session() as session:
            result = session.execute(
                select(StockDaily).where(
                    and_(
                        StockDaily.code == code,
                        StockDaily.date == target_date
                    )
                )
            ).scalars().first()
            
            return result is not None
    
    def get_latest_data(
        self, 
        code: str, 
        days: int = 2
    ) -> List[StockDaily]:
        """
        获取最近 N 天的数据
        
        用于计算"相比昨日"的变化
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            StockDaily 对象列表（按日期降序）
        """
        with self.get_session() as session:
            results = session.execute(
                select(StockDaily)
                .where(StockDaily.code == code)
                .order_by(desc(StockDaily.date))
                .limit(days)
            ).scalars().all()
            
            return list(results)

    def save_news_intel(
        self,
        code: str,
        name: str,
        dimension: str,
        query: str,
        response: 'SearchResponse',
        query_context: Optional[Dict[str, str]] = None
    ) -> int:
        """
        保存新闻情报到数据库

        去重策略：
        - 优先按 URL 去重（唯一约束）
        - URL 缺失时按 title + source + published_date 进行软去重

        关联策略：
        - query_context 记录用户查询信息（平台、用户、会话、原始指令等）
        - Doris UNIQUE KEY 模型自动实现 UPSERT
        - SQLite 使用先查询后更新/插入
        """
        if not response or not response.results:
            return 0

        saved_count = 0
        query_ctx = query_context or {}
        current_query_id = (query_ctx.get("query_id") or "").strip()

        with self.get_session() as session:
            try:
                for item in response.results:
                    title = (item.title or '').strip()
                    url = (item.url or '').strip()
                    source = (item.source or '').strip()
                    snippet = (item.snippet or '').strip()
                    published_date = self._parse_published_date(item.published_date)

                    if not title and not url:
                        continue

                    url_key = url or self._build_fallback_url_key(
                        code=code,
                        title=title,
                        source=source,
                        published_date=published_date
                    )

                    record = NewsIntel(
                        url=url_key,
                        code=code,
                        name=name,
                        dimension=dimension,
                        query=query,
                        provider=response.provider,
                        title=title,
                        snippet=snippet,
                        source=source,
                        published_date=published_date,
                        fetched_at=datetime.now(),
                        query_id=current_query_id or None,
                        query_source=query_ctx.get("query_source"),
                        requester_platform=query_ctx.get("requester_platform"),
                        requester_user_id=query_ctx.get("requester_user_id"),
                        requester_user_name=query_ctx.get("requester_user_name"),
                        requester_chat_id=query_ctx.get("requester_chat_id"),
                        requester_message_id=query_ctx.get("requester_message_id"),
                        requester_query=query_ctx.get("requester_query"),
                    )
                    session.merge(record)
                    saved_count += 1

                session.commit()
                logger.info(f"保存新闻情报成功: {code}, 处理 {saved_count} 条")

            except Exception as e:
                session.rollback()
                logger.error(f"保存新闻情报失败: {e}")
                raise

        return saved_count

    def get_recent_news(self, code: str, days: int = 7, limit: int = 20) -> List[NewsIntel]:
        """
        获取指定股票最近 N 天的新闻情报
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.get_session() as session:
            results = session.execute(
                select(NewsIntel)
                .where(
                    and_(
                        NewsIntel.code == code,
                        NewsIntel.fetched_at >= cutoff_date
                    )
                )
                .order_by(desc(NewsIntel.fetched_at))
                .limit(limit)
            ).scalars().all()

            return list(results)

    def get_news_intel_by_query_id(self, query_id: str, limit: int = 20) -> List[NewsIntel]:
        """
        根据 query_id 获取新闻情报列表

        Args:
            query_id: 分析记录唯一标识
            limit: 返回数量限制

        Returns:
            NewsIntel 列表（按发布时间或抓取时间倒序）
        """
        from sqlalchemy import func

        with self.get_session() as session:
            results = session.execute(
                select(NewsIntel)
                .where(NewsIntel.query_id == query_id)
                .order_by(
                    desc(func.coalesce(NewsIntel.published_date, NewsIntel.fetched_at)),
                    desc(NewsIntel.fetched_at)
                )
                .limit(limit)
            ).scalars().all()

            return list(results)

    def save_analysis_history(
        self,
        result: Any,
        query_id: str,
        report_type: str,
        news_content: Optional[str],
        context_snapshot: Optional[Dict[str, Any]] = None,
        save_snapshot: bool = True
    ) -> int:
        """
        保存分析结果历史记录
        """
        if result is None:
            return 0

        sniper_points = self._extract_sniper_points(result)
        raw_result = self._build_raw_result(result)
        context_text = None
        if save_snapshot and context_snapshot is not None:
            context_text = self._safe_json_dumps(context_snapshot)

        record = AnalysisHistory(
            query_id=query_id,
            code=result.code,
            name=result.name,
            report_type=report_type,
            sentiment_score=result.sentiment_score,
            operation_advice=result.operation_advice,
            trend_prediction=result.trend_prediction,
            analysis_summary=result.analysis_summary,
            raw_result=self._safe_json_dumps(raw_result),
            news_content=news_content,
            context_snapshot=context_text,
            ideal_buy=sniper_points.get("ideal_buy"),
            secondary_buy=sniper_points.get("secondary_buy"),
            stop_loss=sniper_points.get("stop_loss"),
            take_profit=sniper_points.get("take_profit"),
            created_at=datetime.now(),
        )

        with self.get_session() as session:
            try:
                session.add(record)
                session.commit()
                return 1
            except Exception as e:
                session.rollback()
                logger.error(f"保存分析历史失败: {e}")
                return 0

    def get_analysis_history(
        self,
        code: Optional[str] = None,
        query_id: Optional[str] = None,
        days: int = 30,
        limit: int = 50
    ) -> List[AnalysisHistory]:
        """
        Query analysis history records.

        Notes:
        - If query_id is provided, perform exact lookup and ignore days window.
        - If query_id is not provided, apply days-based time filtering.
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        with self.get_session() as session:
            conditions = []

            if query_id:
                conditions.append(AnalysisHistory.query_id == query_id)
            else:
                conditions.append(AnalysisHistory.created_at >= cutoff_date)

            if code:
                conditions.append(AnalysisHistory.code == code)

            results = session.execute(
                select(AnalysisHistory)
                .where(and_(*conditions))
                .order_by(desc(AnalysisHistory.created_at))
                .limit(limit)
            ).scalars().all()

            return list(results)
    
    def get_analysis_history_paginated(
        self,
        code: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        offset: int = 0,
        limit: int = 20
    ) -> Tuple[List[AnalysisHistory], int]:
        """
        分页查询分析历史记录（带总数）
        
        Args:
            code: 股票代码筛选
            start_date: 开始日期（含）
            end_date: 结束日期（含）
            offset: 偏移量（跳过前 N 条）
            limit: 每页数量
            
        Returns:
            Tuple[List[AnalysisHistory], int]: (记录列表, 总数)
        """
        from sqlalchemy import func
        
        with self.get_session() as session:
            conditions = []
            
            if code:
                conditions.append(AnalysisHistory.code == code)
            if start_date:
                conditions.append(AnalysisHistory.created_at >= datetime.combine(start_date, datetime.min.time()))
            if end_date:
                conditions.append(AnalysisHistory.created_at < datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
            
            where_clause = and_(*conditions) if conditions else True
            
            total_query = select(func.count(AnalysisHistory.id)).where(where_clause)
            total = session.execute(total_query).scalar() or 0
            
            data_query = (
                select(AnalysisHistory)
                .where(where_clause)
                .order_by(desc(AnalysisHistory.created_at))
                .offset(offset)
                .limit(limit)
            )
            results = session.execute(data_query).scalars().all()
            
            return list(results), total
    
    def get_data_range(
        self, 
        code: str, 
        start_date: date, 
        end_date: date
    ) -> List[StockDaily]:
        """
        获取指定日期范围的数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            StockDaily 对象列表
        """
        with self.get_session() as session:
            results = session.execute(
                select(StockDaily)
                .where(
                    and_(
                        StockDaily.code == code,
                        StockDaily.date >= start_date,
                        StockDaily.date <= end_date
                    )
                )
                .order_by(StockDaily.date)
            ).scalars().all()
            
            return list(results)
    
    def save_daily_data(
        self, 
        df: pd.DataFrame, 
        code: str,
        data_source: str = "Unknown"
    ) -> int:
        """
        保存日线数据到数据库
        
        策略：
        - Doris UNIQUE KEY 模型自动实现 UPSERT
        - SQLite 使用 merge 或先查询后更新/插入
        
        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源名称
            
        Returns:
            新增/更新的记录数
        """
        if df is None or df.empty:
            logger.warning(f"保存数据为空，跳过 {code}")
            return 0
        
        saved_count = 0
        
        with self.get_session() as session:
            try:
                for _, row in df.iterrows():
                    row_date = row.get('date')
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, '%Y-%m-%d').date()
                    elif isinstance(row_date, datetime):
                        row_date = row_date.date()
                    elif isinstance(row_date, pd.Timestamp):
                        row_date = row_date.date()
                    
                    record = StockDaily(
                        code=code,
                        date=row_date,
                        open=row.get('open'),
                        high=row.get('high'),
                        low=row.get('low'),
                        close=row.get('close'),
                        volume=row.get('volume'),
                        amount=row.get('amount'),
                        pct_chg=row.get('pct_chg'),
                        ma5=row.get('ma5'),
                        ma10=row.get('ma10'),
                        ma20=row.get('ma20'),
                        volume_ratio=row.get('volume_ratio'),
                        data_source=data_source,
                    )
                    
                    if self.is_doris:
                        session.merge(record)
                    else:
                        existing = session.execute(
                            select(StockDaily).where(
                                and_(
                                    StockDaily.code == code,
                                    StockDaily.date == row_date
                                )
                            )
                        ).scalars().first()
                        
                        if existing:
                            existing.open = row.get('open')
                            existing.high = row.get('high')
                            existing.low = row.get('low')
                            existing.close = row.get('close')
                            existing.volume = row.get('volume')
                            existing.amount = row.get('amount')
                            existing.pct_chg = row.get('pct_chg')
                            existing.ma5 = row.get('ma5')
                            existing.ma10 = row.get('ma10')
                            existing.ma20 = row.get('ma20')
                            existing.volume_ratio = row.get('volume_ratio')
                            existing.data_source = data_source
                            existing.updated_at = datetime.now()
                        else:
                            session.add(record)
                            saved_count += 1
                
                session.commit()
                logger.info(f"保存 {code} 数据成功，处理 {len(df)} 条")
                
            except Exception as e:
                session.rollback()
                logger.error(f"保存 {code} 数据失败: {e}")
                raise
        
        return len(df) if self.is_doris else saved_count
    
    def get_analysis_context(
        self, 
        code: str,
        target_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取分析所需的上下文数据
        
        返回今日数据 + 昨日数据的对比信息
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            包含今日数据、昨日对比等信息的字典
        """
        if target_date is None:
            target_date = date.today()
        
        recent_data = self.get_latest_data(code, days=2)
        
        if not recent_data:
            logger.warning(f"未找到 {code} 的数据")
            return None
        
        today_data = recent_data[0]
        yesterday_data = recent_data[1] if len(recent_data) > 1 else None
        
        context = {
            'code': code,
            'date': today_data.date.isoformat(),
            'today': today_data.to_dict(),
        }
        
        if yesterday_data:
            context['yesterday'] = yesterday_data.to_dict()
            
            if yesterday_data.volume and yesterday_data.volume > 0:
                context['volume_change_ratio'] = round(
                    today_data.volume / yesterday_data.volume, 2
                )
            
            if yesterday_data.close and yesterday_data.close > 0:
                context['price_change_ratio'] = round(
                    (today_data.close - yesterday_data.close) / yesterday_data.close * 100, 2
                )
            
            context['ma_status'] = self._analyze_ma_status(today_data)
        
        return context
    
    def _analyze_ma_status(self, data: StockDaily) -> str:
        """
        分析均线形态
        
        判断条件：
        - 多头排列：close > ma5 > ma10 > ma20
        - 空头排列：close < ma5 < ma10 < ma20
        - 震荡整理：其他情况
        """
        close = data.close or 0
        ma5 = data.ma5 or 0
        ma10 = data.ma10 or 0
        ma20 = data.ma20 or 0
        
        if close > ma5 > ma10 > ma20 > 0:
            return "多头排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空头排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震荡整理 ↔️"

    @staticmethod
    def _parse_published_date(value: Optional[str]) -> Optional[datetime]:
        """
        解析发布时间字符串（失败返回 None）
        """
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()
        if not text:
            return None

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass

        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
        ):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _safe_json_dumps(data: Any) -> str:
        """
        安全序列化为 JSON 字符串
        """
        try:
            return json.dumps(data, ensure_ascii=False, default=str)
        except Exception:
            return json.dumps(str(data), ensure_ascii=False)

    @staticmethod
    def _build_raw_result(result: Any) -> Dict[str, Any]:
        """
        生成完整分析结果字典
        """
        data = result.to_dict() if hasattr(result, "to_dict") else {}
        data.update({
            'data_sources': getattr(result, 'data_sources', ''),
            'raw_response': getattr(result, 'raw_response', None),
        })
        return data

    @staticmethod
    def _parse_sniper_value(value: Any) -> Optional[float]:
        """
        解析狙击点位数值
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).replace(',', '').strip()
        if not text:
            return None

        try:
            return float(text)
        except ValueError:
            pass

        colon_pos = max(text.rfind("："), text.rfind(":"))
        yuan_pos = text.find("元", colon_pos + 1 if colon_pos != -1 else 0)
        if yuan_pos != -1:
            segment_start = colon_pos + 1 if colon_pos != -1 else 0
            segment = text[segment_start:yuan_pos]
            
            matches = list(re.finditer(r"-?\d+(?:\.\d+)?", segment))
            valid_numbers = []
            for m in matches:
                start_idx = m.start()
                if start_idx >= 2:
                    prefix = segment[start_idx-2:start_idx].upper()
                    if prefix == "MA":
                        continue
                valid_numbers.append(m.group())
            
            if valid_numbers:
                try:
                    return float(valid_numbers[-1])
                except ValueError:
                    pass
        return None

    def _extract_sniper_points(self, result: Any) -> Dict[str, Optional[float]]:
        """
        抽取狙击点位数据
        """
        raw_points = {}
        if hasattr(result, "get_sniper_points"):
            raw_points = result.get_sniper_points() or {}

        return {
            "ideal_buy": self._parse_sniper_value(raw_points.get("ideal_buy")),
            "secondary_buy": self._parse_sniper_value(raw_points.get("secondary_buy")),
            "stop_loss": self._parse_sniper_value(raw_points.get("stop_loss")),
            "take_profit": self._parse_sniper_value(raw_points.get("take_profit")),
        }

    @staticmethod
    def _build_fallback_url_key(
        code: str,
        title: str,
        source: str,
        published_date: Optional[datetime]
    ) -> str:
        """
        生成无 URL 时的去重键（确保稳定且较短）
        """
        date_str = published_date.isoformat() if published_date else ""
        raw_key = f"{code}|{title}|{source}|{date_str}"
        digest = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
        return f"no-url:{code}:{digest}"

    def save_sync_statistics(self, stats: Dict[str, Any]) -> int:
        """
        保存同步统计数据

        Args:
            stats: 同步统计字典，包含以下字段：
                - sync_date: 同步日期（date 类型或字符串）
                - total_stocks: 尝试同步的股票总数
                - success_count: 成功数量
                - failed_count: 失败数量
                - data_sources: 数据源列表（逗号分隔的字符串）
                - validation_passed: 验证是否通过
                - validation_details: 验证详情（字典，会转为 JSON）

        Returns:
            保存的记录 ID，失败返回 0
        """
        sync_date_val = stats.get('sync_date')
        if isinstance(sync_date_val, str):
            sync_date_val = datetime.strptime(sync_date_val, '%Y-%m-%d').date()
        elif isinstance(sync_date_val, datetime):
            sync_date_val = sync_date_val.date()

        validation_details = stats.get('validation_details')
        if isinstance(validation_details, dict):
            validation_details = self._safe_json_dumps(validation_details)

        record = SyncStatistics(
            sync_date=sync_date_val,
            total_stocks=stats.get('total_stocks'),
            success_count=stats.get('success_count'),
            failed_count=stats.get('failed_count'),
            data_sources=stats.get('data_sources'),
            validation_passed=stats.get('validation_passed'),
            validation_details=validation_details,
            synced_at=datetime.now(),
        )

        with self.get_session() as session:
            try:
                session.merge(record)
                session.commit()
                logger.info(f"保存同步统计成功: sync_date={sync_date_val}, success={stats.get('success_count')}/{stats.get('total_stocks')}")
                return record.id or 1
            except Exception as e:
                session.rollback()
                logger.error(f"保存同步统计失败: {e}")
                return 0

    def get_latest_sync_statistics(self) -> Optional[SyncStatistics]:
        """
        获取最近一次同步统计记录

        Returns:
            最新的 SyncStatistics 对象，如果没有记录则返回 None
        """
        with self.get_session() as session:
            result = session.execute(
                select(SyncStatistics)
                .order_by(desc(SyncStatistics.synced_at))
                .limit(1)
            ).scalars().first()

            return result


def get_db() -> DatabaseManager:
    """获取数据库管理器实例的快捷方式"""
    return DatabaseManager.get_instance()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    db = get_db()
    
    print("=== 数据库测试 ===")
    print(f"数据库初始化成功")
    print(f"数据库类型: {'Doris' if db.is_doris else 'SQLite'}")
    
    has_data = db.has_today_data('600519')
    print(f"茅台今日是否有数据: {has_data}")
    
    test_df = pd.DataFrame({
        'date': [date.today()],
        'open': [1800.0],
        'high': [1850.0],
        'low': [1780.0],
        'close': [1820.0],
        'volume': [10000000],
        'amount': [18200000000],
        'pct_chg': [1.5],
        'ma5': [1810.0],
        'ma10': [1800.0],
        'ma20': [1790.0],
        'volume_ratio': [1.2],
    })
    
    saved = db.save_daily_data(test_df, '600519', 'TestSource')
    print(f"保存测试数据: {saved} 条")
    
    context = db.get_analysis_context('600519')
    print(f"分析上下文: {context}")
