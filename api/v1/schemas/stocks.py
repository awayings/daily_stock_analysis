# -*- coding: utf-8 -*-
"""
===================================
股票数据相关模型
===================================

职责：
1. 定义股票实时行情模型
2. 定义历史 K 线数据模型
"""

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class StockQuote(BaseModel):
    """股票实时行情"""
    
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    current_price: float = Field(..., description="当前价格")
    change: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅 (%)")
    open: Optional[float] = Field(None, description="开盘价")
    high: Optional[float] = Field(None, description="最高价")
    low: Optional[float] = Field(None, description="最低价")
    prev_close: Optional[float] = Field(None, description="昨收价")
    volume: Optional[float] = Field(None, description="成交量（股）")
    amount: Optional[float] = Field(None, description="成交额（元）")
    update_time: Optional[str] = Field(None, description="更新时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "current_price": 1800.00,
                "change": 15.00,
                "change_percent": 0.84,
                "open": 1785.00,
                "high": 1810.00,
                "low": 1780.00,
                "prev_close": 1785.00,
                "volume": 10000000,
                "amount": 18000000000,
                "update_time": "2024-01-01T15:00:00"
            }
        }


class KLineData(BaseModel):
    """K 线数据点"""
    
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: Optional[float] = Field(None, description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    change_percent: Optional[float] = Field(None, description="涨跌幅 (%)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-01",
                "open": 1785.00,
                "high": 1810.00,
                "low": 1780.00,
                "close": 1800.00,
                "volume": 10000000,
                "amount": 18000000000,
                "change_percent": 0.84
            }
        }


class StockHistoryResponse(BaseModel):
    """股票历史行情响应"""
    
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    period: str = Field(..., description="K 线周期")
    data: List[KLineData] = Field(default_factory=list, description="K 线数据列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "period": "daily",
                "data": []
            }
        }


class SyncDailyRequest(BaseModel):
    """每日同步请求"""
    
    date: Optional[str] = Field(None, description="同步日期（YYYY-MM-DD 格式，默认今天）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15"
            }
        }


class SyncDailyResponse(BaseModel):
    """每日同步响应"""
    
    total_count: int = Field(..., description="总股票数")
    success_count: int = Field(..., description="成功同步数")
    failed_count: int = Field(..., description="失败数")
    data_sources: str = Field(..., description="使用的数据源（逗号分隔）")
    validation_passed: bool = Field(..., description="数据验证是否通过")
    validation_details: Dict[str, Any] = Field(..., description="验证详情")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 5000,
                "success_count": 4950,
                "failed_count": 50,
                "data_sources": "akshare, eastmoney",
                "validation_passed": True,
                "validation_details": {
                    "passed": True,
                    "holdings_validation": {
                        "passed": True,
                        "missing_stocks": [],
                        "total_holdings": 10
                    },
                    "count_validation": {
                        "passed": True,
                        "variance_pct": 0.02,
                        "previous_count": 4850,
                        "threshold": 0.1
                    },
                    "validation_details": "所有验证通过"
                }
            }
        }


class StockSearchResult(BaseModel):
    """股票搜索结果"""

    code: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    close: Optional[float] = Field(None, description="最新收盘价")
    date: Optional[str] = Field(None, description="数据日期")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "600519",
                "name": "贵州茅台",
                "close": 1800.00,
                "date": "2024-01-15"
            }
        }


class StockSearchResponse(BaseModel):
    """股票搜索响应"""

    total: int = Field(..., description="总结果数")
    items: List[StockSearchResult] = Field(default_factory=list, description="搜索结果列表")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "items": [
                    {"code": "600519", "name": "贵州茅台", "close": 1800.00, "date": "2024-01-15"},
                    {"code": "000858", "name": "五粮液", "close": 150.00, "date": "2024-01-15"}
                ]
            }
        }
