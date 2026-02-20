# -*- coding: utf-8 -*-
"""
===================================
股票数据接口
===================================

职责：
1. 提供 GET /api/v1/stocks/{code}/quote 实时行情接口
2. 提供 GET /api/v1/stocks/{code}/history 历史行情接口
3. 提供 POST /api/v1/stocks/sync-daily 每日同步接口
"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, HTTPException, Query

from api.v1.schemas.stocks import (
    StockQuote,
    StockHistoryResponse,
    KLineData,
    SyncDailyResponse,
)
from api.v1.schemas.common import ErrorResponse
from src.services.stock_service import StockService
from src.services.daily_sync_service import DailyStockSyncService
from src.services.validation_service import DataValidationService
from src.storage import DatabaseManager
from src.notification import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{stock_code}/quote",
    response_model=StockQuote,
    responses={
        200: {"description": "行情数据"},
        404: {"description": "股票不存在", "model": ErrorResponse},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取股票实时行情",
    description="获取指定股票的最新行情数据"
)
def get_stock_quote(stock_code: str) -> StockQuote:
    """
    获取股票实时行情
    
    获取指定股票的最新行情数据
    
    Args:
        stock_code: 股票代码（如 600519、00700、AAPL）
        
    Returns:
        StockQuote: 实时行情数据
        
    Raises:
        HTTPException: 404 - 股票不存在
    """
    try:
        service = StockService()
        
        # 使用 def 而非 async def，FastAPI 自动在线程池中执行
        result = service.get_realtime_quote(stock_code)
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "not_found",
                    "message": f"未找到股票 {stock_code} 的行情数据"
                }
            )
        
        return StockQuote(
            stock_code=result.get("stock_code", stock_code),
            stock_name=result.get("stock_name"),
            current_price=result.get("current_price", 0.0),
            change=result.get("change"),
            change_percent=result.get("change_percent"),
            open=result.get("open"),
            high=result.get("high"),
            low=result.get("low"),
            prev_close=result.get("prev_close"),
            volume=result.get("volume"),
            amount=result.get("amount"),
            update_time=result.get("update_time")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实时行情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"获取实时行情失败: {str(e)}"
            }
        )


@router.get(
    "/{stock_code}/history",
    response_model=StockHistoryResponse,
    responses={
        200: {"description": "历史行情数据"},
        422: {"description": "不支持的周期参数", "model": ErrorResponse},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="获取股票历史行情",
    description="获取指定股票的历史 K 线数据"
)
def get_stock_history(
    stock_code: str,
    period: str = Query("daily", description="K 线周期", pattern="^(daily|weekly|monthly)$"),
    days: int = Query(30, ge=1, le=365, description="获取天数")
) -> StockHistoryResponse:
    """
    获取股票历史行情
    
    获取指定股票的历史 K 线数据
    
    Args:
        stock_code: 股票代码
        period: K 线周期 (daily/weekly/monthly)
        days: 获取天数
        
    Returns:
        StockHistoryResponse: 历史行情数据
    """
    try:
        service = StockService()
        
        # 使用 def 而非 async def，FastAPI 自动在线程池中执行
        result = service.get_history_data(
            stock_code=stock_code,
            period=period,
            days=days
        )
        
        # 转换为响应模型
        data = [
            KLineData(
                date=item.get("date"),
                open=item.get("open"),
                high=item.get("high"),
                low=item.get("low"),
                close=item.get("close"),
                volume=item.get("volume"),
                amount=item.get("amount"),
                change_percent=item.get("change_percent")
            )
            for item in result.get("data", [])
        ]
        
        return StockHistoryResponse(
            stock_code=stock_code,
            stock_name=result.get("stock_name"),
            period=period,
            data=data
        )
    
    except ValueError as e:
        # period 参数不支持的错误（如 weekly/monthly）
        raise HTTPException(
            status_code=422,
            detail={
                "error": "unsupported_period",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"获取历史行情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"获取历史行情失败: {str(e)}"
            }
        )


@router.post(
    "/sync-daily",
    response_model=SyncDailyResponse,
    responses={
        200: {"description": "同步完成"},
        207: {"description": "同步部分成功"},
        500: {"description": "服务器错误", "model": ErrorResponse},
    },
    summary="执行每日数据同步",
    description="同步所有股票的日线数据并执行数据验证"
)
def sync_daily(
    sync_date: str = Query(None, description="同步日期（YYYY-MM-DD 格式，默认今天）", pattern=r"^\d{4}-\d{2}-\d{2}$"),
    notify: bool = Query(False, description="是否发送钉钉通知")
) -> SyncDailyResponse:
    """
    执行每日数据同步
    
    同步所有股票的日线数据，执行数据验证，并可选发送钉钉通知
    
    Args:
        sync_date: 同步日期（可选，默认今天）
        notify: 是否发送钉钉通知（默认 False）
        
    Returns:
        SyncDailyResponse: 同步结果统计
    """
    try:
        target_date = None
        if sync_date:
            try:
                target_date = datetime.strptime(sync_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "invalid_date",
                        "message": f"日期格式错误: {sync_date}，应为 YYYY-MM-DD"
                    }
                )
        
        if target_date is None:
            target_date = date.today()
        
        logger.info(f"开始执行每日同步，日期: {target_date}，通知: {notify}")
        
        sync_service = DailyStockSyncService()
        sync_result = sync_service.sync_all_stocks(sync_date=target_date)
        
        validation_service = DataValidationService()
        validation_result = validation_service.validate(
            sync_date=target_date,
            sync_stats=sync_result
        )
        
        db = DatabaseManager.get_instance()
        db.save_sync_statistics({
            "sync_date": target_date,
            "total_stocks": sync_result.get("total", 0),
            "success_count": sync_result.get("success", 0),
            "failed_count": sync_result.get("failed", 0),
            "data_sources": sync_result.get("data_sources", ""),
            "validation_passed": validation_result.get("passed", False),
            "validation_details": validation_result
        })
        
        if notify:
            try:
                notification_service = NotificationService()
                title = f"每日数据同步完成 - {target_date}"
                content = (
                    f"### {title}\n\n"
                    f"- **同步日期**: {target_date}\n"
                    f"- **总股票数**: {sync_result.get('total', 0)}\n"
                    f"- **成功数**: {sync_result.get('success', 0)}\n"
                    f"- **失败数**: {sync_result.get('failed', 0)}\n"
                    f"- **数据源**: {sync_result.get('data_sources', 'N/A')}\n"
                    f"- **验证结果**: {'通过' if validation_result.get('passed', False) else '失败'}\n"
                    f"- **验证详情**: {validation_result.get('validation_details', 'N/A')}"
                )
                notification_service.send_dingtalk_message(title, content)
                logger.info("钉钉通知发送成功")
            except Exception as e:
                logger.warning(f"钉钉通知发送失败: {e}")
        
        response = SyncDailyResponse(
            total_count=sync_result.get("total", 0),
            success_count=sync_result.get("success", 0),
            failed_count=sync_result.get("failed", 0),
            data_sources=sync_result.get("data_sources", ""),
            validation_passed=validation_result.get("passed", False),
            validation_details=validation_result
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"每日同步失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": f"每日同步失败: {str(e)}"
            }
        )
