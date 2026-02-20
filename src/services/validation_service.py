# -*- coding: utf-8 -*-
"""
===================================
数据验证服务
===================================

职责：
1. 同步后数据完整性验证
2. 持仓数据更新检查
3. 同步数量波动分析
"""

import logging
from datetime import date
from typing import Dict, Any, List, Optional

from src.repositories.stock_repo import StockRepository
from src.repositories.portfolio_repo import PortfolioRepository
from src.storage import DatabaseManager

logger = logging.getLogger(__name__)


class DataValidationService:
    """
    数据验证服务
    
    负责同步后的数据完整性验证
    """
    
    DEFAULT_VARIANCE_THRESHOLD = 0.10
    
    def __init__(
        self,
        stock_repo: Optional[StockRepository] = None,
        portfolio_repo: Optional[PortfolioRepository] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        初始化验证服务
        
        Args:
            stock_repo: 股票数据访问层（可选，默认自动创建）
            portfolio_repo: 投资组合数据访问层（可选，默认自动创建）
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()
        self.stock_repo = stock_repo or StockRepository(self.db)
        self.portfolio_repo = portfolio_repo or PortfolioRepository(self.db)
    
    def validate(
        self,
        sync_date: date,
        sync_stats: Dict[str, Any],
        variance_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        主验证方法 - 执行所有验证检查
        
        Args:
            sync_date: 同步日期
            sync_stats: 同步统计信息，包含 success_count 等字段
            variance_threshold: 数量波动阈值（可选，默认 10%）
            
        Returns:
            综合验证结果:
            {
                "passed": bool,           # 整体是否通过
                "holdings_validation": {...},  # 持仓验证结果
                "count_validation": {...},     # 数量验证结果
                "validation_details": str      # 验证详情摘要
            }
        """
        logger.info(f"开始数据验证，同步日期: {sync_date}")
        
        holdings_result = self.validate_holdings_updated(sync_date)
        
        current_count = sync_stats.get("success", 0)
        count_result = self.validate_sync_count_variance(
            current_count=current_count,
            threshold=variance_threshold
        )
        
        all_passed = holdings_result.get("passed", False) and count_result.get("passed", False)
        
        details_parts = []
        if not holdings_result.get("passed", False):
            missing = holdings_result.get("missing_stocks", [])
            details_parts.append(
                f"持仓验证失败: {len(missing)}/{holdings_result.get('total_holdings', 0)} 只股票缺少数据"
            )
        
        if not count_result.get("passed", False):
            variance_pct = count_result.get("variance_pct", 0)
            details_parts.append(
                f"数量验证失败: 波动 {variance_pct:.1%} 超过阈值 {count_result.get('threshold', 0):.1%}"
            )
        
        if all_passed:
            details_parts.append("所有验证通过")
        
        result = {
            "passed": all_passed,
            "holdings_validation": holdings_result,
            "count_validation": count_result,
            "validation_details": "; ".join(details_parts)
        }
        
        if all_passed:
            logger.info(f"数据验证通过: {result['validation_details']}")
        else:
            logger.warning(f"数据验证失败: {result['validation_details']}")
        
        return result
    
    def validate_holdings_updated(self, sync_date: date) -> Dict[str, Any]:
        """
        验证投资组合持仓是否有同步日期的数据
        
        检查所有活跃持仓在 stock_daily 表中是否有 sync_date 的数据
        
        Args:
            sync_date: 同步日期
            
        Returns:
            验证结果:
            {
                "passed": bool,           # 是否通过（无缺失）
                "missing_stocks": List[str],  # 缺少数据的股票代码列表
                "total_holdings": int     # 总持仓数量
            }
        """
        logger.info(f"验证持仓数据更新，日期: {sync_date}")
        
        all_holdings = self._get_all_active_holdings()
        total_holdings = len(all_holdings)
        
        if total_holdings == 0:
            logger.info("无活跃持仓，跳过持仓验证")
            return {
                "passed": True,
                "missing_stocks": [],
                "total_holdings": 0
            }
        
        missing_stocks = []
        
        for holding in all_holdings:
            code = holding.code
            has_data = self.stock_repo.has_today_data(code, sync_date)
            
            if not has_data:
                missing_stocks.append(code)
                logger.warning(f"持仓 {code} 缺少 {sync_date} 的数据")
        
        passed = len(missing_stocks) == 0
        
        result = {
            "passed": passed,
            "missing_stocks": missing_stocks,
            "total_holdings": total_holdings
        }
        
        if passed:
            logger.info(f"持仓验证通过: {total_holdings} 只持仓均有数据")
        else:
            logger.warning(
                f"持仓验证失败: {len(missing_stocks)}/{total_holdings} 只持仓缺少数据"
            )
        
        return result
    
    def validate_sync_count_variance(
        self,
        current_count: int,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        验证同步数量与历史记录的波动
        
        比较当前同步成功数量与上一次同步的成功数量，
        如果波动超过阈值则验证失败
        
        Args:
            current_count: 当前同步成功数量
            threshold: 波动阈值（可选，默认 10%）
            
        Returns:
            验证结果:
            {
                "passed": bool,           # 是否通过
                "variance_pct": float,    # 波动百分比
                "previous_count": int,    # 上次同步成功数量
                "threshold": float        # 使用的阈值
            }
        """
        if threshold is None:
            threshold = self.DEFAULT_VARIANCE_THRESHOLD
        
        logger.info(f"验证同步数量波动: 当前数量={current_count}, 阈值={threshold:.1%}")
        
        previous_stats = self.db.get_latest_sync_statistics()
        
        if previous_stats is None:
            logger.info("无历史同步记录，跳过数量波动验证")
            return {
                "passed": True,
                "variance_pct": 0.0,
                "previous_count": 0,
                "threshold": threshold
            }
        
        previous_count = previous_stats.success_count or 0
        
        if previous_count == 0:
            logger.info("上次同步成功数量为 0，跳过数量波动验证")
            return {
                "passed": True,
                "variance_pct": 0.0,
                "previous_count": 0,
                "threshold": threshold
            }
        
        variance_pct = abs(current_count - previous_count) / previous_count
        
        passed = variance_pct <= threshold
        
        result = {
            "passed": passed,
            "variance_pct": variance_pct,
            "previous_count": previous_count,
            "threshold": threshold
        }
        
        if passed:
            logger.info(
                f"数量波动验证通过: 当前={current_count}, 上次={previous_count}, "
                f"波动={variance_pct:.1%}"
            )
        else:
            logger.warning(
                f"数量波动验证失败: 当前={current_count}, 上次={previous_count}, "
                f"波动={variance_pct:.1%} 超过阈值 {threshold:.1%}"
            )
        
        return result
    
    def _get_all_active_holdings(self) -> List[Any]:
        """
        获取所有投资组合的活跃持仓
        
        Returns:
            活跃持仓列表
        """
        from sqlalchemy import text
        from src.storage import Portfolio
        
        all_holdings = []
        
        with self.db.get_session() as session:
            portfolios = session.execute(
                text("SELECT id FROM portfolios WHERE is_deleted = 0")
            ).fetchall()
            
            for (portfolio_id,) in portfolios:
                holdings = self.portfolio_repo.get_holdings(
                    portfolio_id=portfolio_id,
                    include_closed=False
                )
                all_holdings.extend(holdings)
        
        return all_holdings
