# -*- coding: utf-8 -*-
"""
===================================
投资组合 API Schemas
===================================

职责：
1. 定义投资组合相关的 Pydantic 请求/响应模型
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class HoldingCreate(BaseModel):
    """持仓创建请求"""
    code: str = Field(..., description="股票代码")
    entry_price: float = Field(..., gt=0, description="建仓价格")
    weight: float = Field(..., gt=0, le=100, description="仓位占比")


class HoldingUpdate(BaseModel):
    """持仓更新请求"""
    entry_price: Optional[float] = Field(None, gt=0, description="建仓价格")
    weight: Optional[float] = Field(None, gt=0, le=100, description="仓位占比")


class HoldingResponse(BaseModel):
    """持仓响应"""
    id: int
    portfolio_id: Optional[int] = None
    code: str
    name: Optional[str] = None
    entry_price: float
    current_price: Optional[float] = None
    weight: float
    shares: Optional[float] = None
    pnl_pct: Optional[float] = None
    is_closed: bool = False
    added_at: Optional[str] = None
    updated_at: Optional[str] = None


class PortfolioCreate(BaseModel):
    """创建组合请求"""
    name: str = Field(..., min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, max_length=500, description="组合描述")
    initial_capital: Optional[float] = Field(None, gt=0, description="初始资金")
    currency: str = Field("CNY", description="货币代码")
    holdings: Optional[List[HoldingCreate]] = Field(None, description="初始持仓列表")


class PortfolioUpdate(BaseModel):
    """更新组合请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组合名称")
    description: Optional[str] = Field(None, max_length=500, description="组合描述")
    initial_capital: Optional[float] = Field(None, gt=0, description="初始资金")


class PortfolioSummary(BaseModel):
    """组合摘要"""
    total_value: float
    total_pnl_pct: float
    total_pnl_amount: float
    holdings_count: int


class PortfolioListItem(BaseModel):
    """组合列表项"""
    id: int
    name: str
    description: Optional[str] = None
    holdings_count: int
    total_value: float
    total_pnl_pct: float
    total_pnl_amount: float
    is_deleted: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PortfolioListResponse(BaseModel):
    """组合列表响应"""
    items: List[PortfolioListItem]
    total: int
    page: int
    limit: int


class PortfolioResponse(BaseModel):
    """组合响应"""
    id: int
    name: str
    description: Optional[str] = None
    initial_capital: Optional[float] = None
    currency: str
    is_deleted: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    holdings: List[HoldingResponse] = []
    summary: Optional[PortfolioSummary] = None


class PortfolioDeleteResponse(BaseModel):
    """删除组合响应"""
    id: int
    name: str
    is_deleted: bool
    deleted_at: Optional[str] = None
    history_preserved: bool


class ClosePositionRequest(BaseModel):
    """平仓请求"""
    price_type: str = Field(..., description="价格类型: current/specified")
    specified_price: Optional[float] = Field(None, gt=0, description="指定价格")
    quantity_type: str = Field(..., description="数量类型: all/partial")
    quantity: Optional[float] = Field(None, gt=0, description="平仓数量")
    ratio: Optional[float] = Field(None, ge=0, le=100, description="平仓比例")


class ClosePositionPnl(BaseModel):
    """平仓盈亏信息"""
    amount: float
    percentage: float
    realized: bool


class ClosePositionRemaining(BaseModel):
    """剩余持仓信息"""
    shares: float
    weight: float


class ClosePositionResponse(BaseModel):
    """平仓响应"""
    id: int
    portfolio_id: int
    code: str
    name: Optional[str] = None
    entry_price: float
    close_price: float
    close_quantity: float
    close_type: str
    is_closed: bool
    closed_at: Optional[str] = None
    pnl: ClosePositionPnl
    remaining: ClosePositionRemaining
    weight_rebalance_required: bool = False


class BatchHoldingsRequest(BaseModel):
    """批量添加持仓请求"""
    holdings: List[HoldingCreate] = Field(..., description="持仓列表")
    rebalance_mode: str = Field("none", description="重平衡模式: none/equal/keep_existing")


class BatchHoldingsResponse(BaseModel):
    """批量添加持仓响应"""
    added_count: int
    skipped_count: int
    holdings: List[HoldingResponse]
    weight_summary: Dict[str, Any]


class RebalanceResponse(BaseModel):
    """平均分配仓位响应"""
    portfolio_id: int
    holdings_count: int
    new_weight_each: float
    holdings: List[Dict[str, Any]]


class CalculateResponse(BaseModel):
    """计算响应"""
    portfolio_id: int
    calculated_at: str
    snapshot_date: str
    total_value: float
    total_pnl_pct: float
    holdings_updated: int
    status: str


class HoldingSnapshotResponse(BaseModel):
    """持仓快照响应"""
    id: int
    history_id: int
    code: str
    name: Optional[str] = None
    entry_price: float
    current_price: Optional[float] = None
    weight: float
    pnl_pct: Optional[float] = None
    weighted_pnl: Optional[float] = None
    created_at: Optional[str] = None


class PortfolioHistoryItem(BaseModel):
    """历史记录项"""
    id: int
    portfolio_id: int
    snapshot_date: Optional[str] = None
    total_value: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    unrealized_pnl_amount: Optional[float] = None
    realized_pnl_amount: float = 0
    cumulative_realized_pnl: float = 0
    total_pnl_pct: Optional[float] = None
    total_pnl_amount: Optional[float] = None
    active_holdings_count: int = 0
    closed_holdings_count: int = 0
    calculation_status: str
    error_message: Optional[str] = None
    calculated_at: Optional[str] = None
    holdings: List[HoldingSnapshotResponse] = []


class PortfolioHistoryResponse(BaseModel):
    """历史记录响应"""
    portfolio_id: int
    items: List[PortfolioHistoryItem]
    total: int
    page: int
    limit: int


class PerformanceDataPoint(BaseModel):
    """收益走势数据点"""
    date: Optional[str] = None
    total_value: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    unrealized_pnl_amount: Optional[float] = None
    realized_pnl_amount: float = 0
    cumulative_realized_pnl: float = 0
    total_pnl_pct: Optional[float] = None


class PerformanceStatistics(BaseModel):
    """收益统计"""
    total_return_pct: Optional[float] = None
    unrealized_return_pct: Optional[float] = None
    realized_return_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    best_day: Optional[Dict[str, Any]] = None
    worst_day: Optional[Dict[str, Any]] = None


class PerformanceResponse(BaseModel):
    """收益走势响应"""
    portfolio_id: int
    view_mode: str
    date_range: Dict[str, str]
    data_points: List[PerformanceDataPoint]
    statistics: PerformanceStatistics


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    constraint: Optional[str] = None


class PortfolioErrorResponse(BaseModel):
    """错误响应"""
    error: Dict[str, Any]
