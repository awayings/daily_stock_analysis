# -*- coding: utf-8 -*-
"""
===================================
Hong Kong Stock Data Sync Service
===================================

Syncs HK stock daily data to stock_daily table using Tushare hk_daily interface.

Requirements:
- Tushare Pro API with at least 2000 points
- Valid TUSHARE_TOKEN in environment

Reference:
- HK stock list: https://tushare.pro/document/2?doc_id=191
- HK daily data: https://tushare.pro/document/2?doc_id=192
"""

import logging
from datetime import date
from typing import Optional, Dict, Any

from src.storage import DatabaseManager

logger = logging.getLogger(__name__)


class HKStockSyncService:
    """
    Hong Kong Stock Data Sync Service

    Syncs HK stock daily data to stock_daily table using Tushare hk_daily interface.
    Uses batch fetch to get all HK stocks data in one API call.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the sync service.

        Args:
            db_manager: Database manager (optional, defaults to singleton)
        """
        self.db = db_manager or DatabaseManager.get_instance()

    def sync_hk_daily(self, sync_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Sync all HK stocks daily data for a specific date.

        Uses Tushare hk_daily(trade_date=...) to batch fetch all HK stocks.

        Args:
            sync_date: Date to sync (optional, defaults to today)

        Returns:
            Sync statistics:
            {
                "total": int,       # Total records fetched
                "saved": int,       # Saved records count
                "data_source": str, # Data source name
                "errors": List[str] # Error messages
            }
        """
        from data_provider.tushare_fetcher import TushareFetcher

        if sync_date is None:
            sync_date = date.today()

        logger.info(f"[港股同步] 开始同步港股日线数据，目标日期: {sync_date}")

        result = {
            "total": 0,
            "saved": 0,
            "data_source": "",
            "errors": []
        }

        try:
            fetcher = TushareFetcher()

            if fetcher._api is None:
                error_msg = "Tushare API 未初始化，请检查 TUSHARE_TOKEN 配置（港股接口需要2000积分）"
                logger.warning(f"[港股同步] {error_msg}")
                result["errors"].append(error_msg)
                return result

            trade_date = sync_date.strftime('%Y-%m-%d')
            df = fetcher.get_hk_daily_data_by_date(trade_date)

            if df is None or df.empty:
                error_msg = f"未获取到 {sync_date} 的港股数据"
                logger.warning(f"[港股同步] {error_msg}")
                result["errors"].append(error_msg)
                return result

            result["total"] = len(df)
            result["data_source"] = "TushareFetcher_hk"

            stock_names = self._get_hk_stock_names(fetcher, df['code'].tolist())

            df_with_names = df.copy()
            df_with_names['name'] = df_with_names['code'].map(stock_names)

            saved_count = self.db.save_daily_data_batch(df_with_names, result["data_source"])
            result["saved"] = saved_count

            logger.info(f"[港股同步] 同步完成: 获取 {result['total']} 条, 保存 {saved_count} 条")

        except Exception as e:
            error_msg = f"港股同步失败: {e}"
            logger.error(f"[港股同步] {error_msg}")
            result["errors"].append(error_msg)

        return result

    def sync_hk_stock_list(self, list_status: str = 'L') -> Dict[str, Any]:
        """
        Sync HK stock list (basic info).

        Args:
            list_status: 'L' for listed, 'D' for delisted, 'P' for suspended

        Returns:
            Sync statistics:
            {
                "total": int,
                "saved": int,
                "data_source": str,
                "errors": List[str]
            }
        """
        from data_provider.tushare_fetcher import TushareFetcher

        logger.info(f"[港股列表同步] 开始同步港股列表 (status={list_status})...")

        result = {
            "total": 0,
            "saved": 0,
            "data_source": "",
            "errors": []
        }

        try:
            fetcher = TushareFetcher()

            if fetcher._api is None:
                error_msg = "Tushare API 未初始化，请检查 TUSHARE_TOKEN 配置"
                logger.warning(f"[港股列表同步] {error_msg}")
                result["errors"].append(error_msg)
                return result

            df = fetcher.get_hk_stock_list(list_status=list_status)

            if df is None or df.empty:
                error_msg = "未获取到港股列表数据"
                logger.warning(f"[港股列表同步] {error_msg}")
                result["errors"].append(error_msg)
                return result

            result["total"] = len(df)
            result["data_source"] = "TushareFetcher_hk_basic"

            if not hasattr(self.db, 'save_hk_stock_list'):
                logger.info(f"[港股列表同步] 获取 {len(df)} 只港股信息（暂不支持持久化）")
                result["saved"] = len(df)
            else:
                saved_count = self.db.save_hk_stock_list(df)
                result["saved"] = saved_count

            logger.info(f"[港股列表同步] 同步完成: 获取 {result['total']} 只股票")

        except Exception as e:
            error_msg = f"港股列表同步失败: {e}"
            logger.error(f"[港股列表同步] {error_msg}")
            result["errors"].append(error_msg)

        return result

    def _get_hk_stock_names(self, fetcher, stock_codes: list) -> Dict[str, str]:
        """
        Get HK stock names from fetcher cache or API.

        Args:
            fetcher: TushareFetcher instance
            stock_codes: List of stock codes in local format (e.g., 'HK00001')

        Returns:
            Dict mapping stock code to name
        """
        names = {}

        if hasattr(fetcher, '_stock_name_cache'):
            for code in stock_codes:
                if code in fetcher._stock_name_cache:
                    names[code] = fetcher._stock_name_cache[code]

        if len(names) < len(stock_codes):
            try:
                stock_list = fetcher.get_hk_stock_list()
                if stock_list is not None and not stock_list.empty:
                    for _, row in stock_list.iterrows():
                        code = row.get('code')
                        name = row.get('name')
                        if code and name:
                            names[code] = name
            except Exception as e:
                logger.warning(f"[港股同步] 获取股票名称失败: {e}")

        return names
