# -*- coding: utf-8 -*-
"""
===================================
投资组合 API 端点
===================================

职责：
1. 提供投资组合管理的 RESTful API 接口
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from api.v1.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioListResponse,
    PortfolioResponse,
    PortfolioDeleteResponse,
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
    ClosePositionRequest,
    ClosePositionResponse,
    BatchHoldingsRequest,
    BatchHoldingsResponse,
    RebalanceResponse,
    CalculateResponse,
    PortfolioHistoryResponse,
    PerformanceResponse,
    PortfolioErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Portfolios"])


def _handle_service_error(e: Exception) -> None:
    """处理服务层异常"""
    error_msg = str(e)
    if "PORTFOLIO_" in error_msg or "HOLDING_" in error_msg or "CLOSE_" in error_msg:
        code = error_msg.split(":")[0]
        message = error_msg.split(":")[1] if ":" in error_msg else error_msg
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": code, "message": message.strip()}
        )
    elif "NOT_FOUND" in error_msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "NOT_FOUND", "message": error_msg}
        )
    else:
        logger.error(f"服务错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "系统错误"}
        )


def _get_portfolio_service():
    """获取投资组合服务实例"""
    from src.services.portfolio_service import PortfolioService
    return PortfolioService()


@router.post(
    "",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": PortfolioErrorResponse},
    }
)
async def create_portfolio(request: PortfolioCreate):
    """创建投资组合"""
    try:
        service = _get_portfolio_service()

        holdings_data = None
        if request.holdings:
            holdings_data = [h.model_dump() for h in request.holdings]

        result = service.create_portfolio(
            name=request.name,
            description=request.description,
            initial_capital=Decimal(str(request.initial_capital)) if request.initial_capital else None,
            currency=request.currency,
            holdings=holdings_data
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"创建组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "创建组合失败"}
        )


@router.get(
    "",
    response_model=PortfolioListResponse,
)
async def get_portfolios(
    include_deleted: bool = Query(False, description="是否包含已删除组合"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取组合列表"""
    try:
        service = _get_portfolio_service()
        result = service.get_portfolio_list(
            include_deleted=include_deleted,
            page=page,
            limit=limit
        )
        return result

    except Exception as e:
        logger.error(f"获取组合列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "获取组合列表失败"}
        )


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    responses={
        404: {"model": PortfolioErrorResponse},
    }
)
async def get_portfolio(portfolio_id: int):
    """获取组合详情"""
    try:
        service = _get_portfolio_service()
        result = service.get_portfolio(portfolio_id)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"获取组合详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "获取组合详情失败"}
        )


@router.put(
    "/{portfolio_id}",
    response_model=PortfolioResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def update_portfolio(portfolio_id: int, request: PortfolioUpdate):
    """更新组合信息"""
    try:
        service = _get_portfolio_service()

        kwargs = {}
        if request.name is not None:
            kwargs['name'] = request.name
        if request.description is not None:
            kwargs['description'] = request.description
        if request.initial_capital is not None:
            kwargs['initial_capital'] = Decimal(str(request.initial_capital))

        result = service.update_portfolio(portfolio_id, **kwargs)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"更新组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "更新组合失败"}
        )


@router.delete(
    "/{portfolio_id}",
    response_model=PortfolioDeleteResponse,
    responses={
        404: {"model": PortfolioErrorResponse},
    }
)
async def delete_portfolio(portfolio_id: int):
    """删除组合"""
    try:
        service = _get_portfolio_service()
        result = service.delete_portfolio(portfolio_id)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"删除组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "删除组合失败"}
        )


@router.post(
    "/{portfolio_id}/restore",
    response_model=PortfolioResponse,
    responses={
        404: {"model": PortfolioErrorResponse},
    }
)
async def restore_portfolio(portfolio_id: int):
    """恢复已删除组合"""
    try:
        service = _get_portfolio_service()
        result = service.restore_portfolio(portfolio_id)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"恢复组合失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "恢复组合失败"}
        )


@router.post(
    "/{portfolio_id}/holdings",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def add_holding(portfolio_id: int, request: HoldingCreate):
    """添加持仓"""
    try:
        service = _get_portfolio_service()
        result = service.add_holding(
            portfolio_id=portfolio_id,
            code=request.code,
            entry_price=Decimal(str(request.entry_price)),
            weight=Decimal(str(request.weight)),
            last_price=Decimal(str(request.last_price)) if request.last_price else None
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"添加持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "添加持仓失败"}
        )


@router.put(
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=HoldingResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def update_holding(
    portfolio_id: int,
    holding_id: int,
    request: HoldingUpdate
):
    """更新持仓"""
    try:
        service = _get_portfolio_service()

        kwargs = {}
        if request.entry_price is not None:
            kwargs['entry_price'] = Decimal(str(request.entry_price))
        if request.weight is not None:
            kwargs['weight'] = Decimal(str(request.weight))

        result = service.update_holding(portfolio_id, holding_id, **kwargs)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"更新持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "更新持仓失败"}
        )


@router.post(
    "/{portfolio_id}/holdings/{holding_id}/closePosition",
    response_model=ClosePositionResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
        409: {"model": PortfolioErrorResponse},
    }
)
async def close_position(
    portfolio_id: int,
    holding_id: int,
    request: ClosePositionRequest
):
    """平仓持仓"""
    try:
        service = _get_portfolio_service()

        result = service.close_position(
            portfolio_id=portfolio_id,
            holding_id=holding_id,
            price_type=request.price_type,
            specified_price=Decimal(str(request.specified_price)) if request.specified_price else None,
            quantity_type=request.quantity_type,
            quantity=Decimal(str(request.quantity)) if request.quantity else None,
            ratio=Decimal(str(request.ratio)) if request.ratio else None
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"平仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "平仓失败"}
        )


@router.post(
    "/{portfolio_id}/holdings/batch",
    response_model=BatchHoldingsResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def batch_add_holdings(portfolio_id: int, request: BatchHoldingsRequest):
    """批量添加持仓"""
    try:
        service = _get_portfolio_service()

        holdings_data = [h.model_dump() for h in request.holdings]

        result = service.batch_add_holdings(
            portfolio_id=portfolio_id,
            holdings=holdings_data,
            rebalance_mode=request.rebalance_mode
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"批量添加持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "批量添加持仓失败"}
        )


@router.post(
    "/{portfolio_id}/holdings/rebalance",
    response_model=RebalanceResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def rebalance_holdings(portfolio_id: int):
    """平均分配仓位"""
    try:
        service = _get_portfolio_service()
        result = service.rebalance_weights(portfolio_id)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"仓位重平衡失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "仓位重平衡失败"}
        )


@router.post(
    "/{portfolio_id}/calculate",
    response_model=CalculateResponse,
    responses={
        400: {"model": PortfolioErrorResponse},
        404: {"model": PortfolioErrorResponse},
    }
)
async def calculate_portfolio(portfolio_id: int):
    """触发计算"""
    try:
        service = _get_portfolio_service()
        result = service.calculate_portfolio(portfolio_id)
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"计算失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "计算失败"}
        )


@router.get(
    "/{portfolio_id}/history",
    response_model=PortfolioHistoryResponse,
    responses={
        404: {"model": PortfolioErrorResponse},
    }
)
async def get_portfolio_history(
    portfolio_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """获取历史记录"""
    try:
        service = _get_portfolio_service()

        start = None
        end = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

        result = service.get_history(
            portfolio_id=portfolio_id,
            start_date=start,
            end_date=end,
            page=page,
            limit=limit
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "获取历史记录失败"}
        )


@router.get(
    "/{portfolio_id}/performance",
    response_model=PerformanceResponse,
    responses={
        404: {"model": PortfolioErrorResponse},
    }
)
async def get_portfolio_performance(
    portfolio_id: int,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    view_mode: str = Query("portfolio", description="视图模式: portfolio/holdings"),
):
    """获取收益走势数据"""
    try:
        service = _get_portfolio_service()

        start = None
        end = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

        result = service.get_performance(
            portfolio_id=portfolio_id,
            start_date=start,
            end_date=end,
            view_mode=view_mode
        )
        return result

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"获取收益走势失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "获取收益走势失败"}
        )


@router.get(
    "/{portfolio_id}/export",
    responses={
        200: {"content": {"text/csv": {}, "application/json": {}}},
        404: {"model": PortfolioErrorResponse},
    }
)
async def export_portfolio(
    portfolio_id: int,
    format: str = Query("csv", description="导出格式: csv/json"),
    scope: str = Query("summary", description="数据范围: summary/detailed"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
):
    """导出数据"""
    try:
        service = _get_portfolio_service()

        start = None
        end = None
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

        history = service.get_history(
            portfolio_id=portfolio_id,
            start_date=start,
            end_date=end,
            page=1,
            limit=1000
        )

        if format == "json":
            import json
            return Response(
                content=json.dumps(history, indent=2, ensure_ascii=False),
                media_type="application/json"
            )
        else:
            import csv
            import io

            output = io.StringIO()
            if scope == "summary":
                writer = csv.writer(output)
                writer.writerow([
                    "snapshot_date", "total_value", "unrealized_pnl_pct",
                    "realized_pnl_amount", "total_pnl_pct", "total_pnl_amount"
                ])
                for item in history.get("items", []):
                    writer.writerow([
                        item.get("snapshot_date"),
                        item.get("total_value"),
                        item.get("unrealized_pnl_pct"),
                        item.get("realized_pnl_amount"),
                        item.get("total_pnl_pct"),
                        item.get("total_pnl_amount"),
                    ])
            else:
                writer = csv.writer(output)
                writer.writerow([
                    "date", "code", "name", "entry_price",
                    "current_price", "weight", "pnl_pct", "weighted_pnl"
                ])
                for item in history.get("items", []):
                    for h in item.get("holdings", []):
                        writer.writerow([
                            item.get("snapshot_date"),
                            h.get("code"),
                            h.get("name"),
                            h.get("entry_price"),
                            h.get("current_price"),
                            h.get("weight"),
                            h.get("pnl_pct"),
                            h.get("weighted_pnl"),
                        ])

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_export.csv"}
            )

    except ValueError as e:
        _handle_service_error(e)
    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SYSTEM_001", "message": "导出失败"}
        )
