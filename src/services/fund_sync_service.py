# -*- coding: utf-8 -*-
"""
===================================
基金数据同步服务
===================================

职责：
1. 同步 ETF 基金日线数据到 stock_daily 表
2. 同步 LOF 基金日线数据到 stock_daily 表
3. 使用 spot 接口一次调用获取全量数据

数据源：
- ETF: ak.fund_etf_spot_em() - 包含完整 OHLCV 数据
- LOF: ak.fund_lof_spot_em() - 包含完整 OHLCV 数据
"""

import logging
from datetime import date
from typing import Optional, Dict, Any

from src.storage import DatabaseManager

logger = logging.getLogger(__name__)


class FundSyncService:
    """
    基金数据同步服务

    负责将 ETF/LOF 基金数据同步到 stock_daily 表
    使用 spot 接口一次调用获取全量数据，高效且节省 API 调用次数
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化同步服务

        Args:
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()

    def sync_etf_daily(self) -> Dict[str, Any]:
        """
        Sync all ETF daily data to stock_daily table.

        Priority:
        1. East Money (fund_etf_spot_em) - primary source
        2. Sina (fund_etf_category_sina) - backup source

        Returns:
            Sync statistics:
            {
                "total": int,       # Total ETF count
                "saved": int,       # Saved records count
                "data_source": str, # Data source name
                "errors": List[str] # Error messages
            }
        """
        from data_provider.akshare_fetcher import AkshareFetcher

        logger.info("[ETF同步] 开始同步 ETF 日线数据...")

        result = {
            "total": 0,
            "saved": 0,
            "data_source": "",
            "errors": []
        }

        try:
            fetcher = AkshareFetcher()
            df = None
            data_source = ""

            df = fetcher.get_etf_spot_data()

            if df is not None and not df.empty:
                data_source = "akshare_etf"
                logger.info(f"[ETF同步] 东财接口获取成功: {len(df)} 条")
            else:
                logger.warning("[ETF同步] 东财接口未获取到数据，尝试新浪接口...")
                df = fetcher.get_etf_spot_data_sina()
                if df is not None and not df.empty:
                    data_source = "akshare_etf_sina"
                    logger.info(f"[ETF同步] 新浪接口获取成功: {len(df)} 条")
                else:
                    logger.warning("[ETF同步] 新浪接口也未获取到数据")

            if df is None or df.empty:
                result["errors"].append("东财和新浪接口均未获取到 ETF 数据")
                return result

            result["total"] = len(df)
            result["data_source"] = data_source

            saved_count = self.db.save_daily_data_batch(df, data_source)
            result["saved"] = saved_count

            logger.info(f"[ETF同步] 同步完成: 数据源={data_source}, 获取 {result['total']} 条, 保存 {saved_count} 条")

        except Exception as e:
            error_msg = f"ETF 同步失败: {e}"
            logger.error(f"[ETF同步] {error_msg}")
            result["errors"].append(error_msg)

        return result

    def sync_lof_daily(self) -> Dict[str, Any]:
        """
        Sync all LOF daily data to stock_daily table.

        Priority:
        1. East Money (fund_lof_spot_em) - primary source
        2. Sina (fund_etf_category_sina) - backup source

        Returns:
            Sync statistics:
            {
                "total": int,       # Total LOF count
                "saved": int,       # Saved records count
                "data_source": str, # Data source name
                "errors": List[str] # Error messages
            }
        """
        from data_provider.akshare_fetcher import AkshareFetcher

        logger.info("[LOF同步] 开始同步 LOF 日线数据...")

        result = {
            "total": 0,
            "saved": 0,
            "data_source": "",
            "errors": []
        }

        try:
            fetcher = AkshareFetcher()
            df = None
            data_source = ""

            df = fetcher.get_lof_spot_data()

            if df is not None and not df.empty:
                data_source = "akshare_lof"
                logger.info(f"[LOF同步] 东财接口获取成功: {len(df)} 条")
            else:
                logger.warning("[LOF同步] 东财接口未获取到数据，尝试新浪接口...")
                df = fetcher.get_lof_spot_data_sina()
                if df is not None and not df.empty:
                    data_source = "akshare_lof_sina"
                    logger.info(f"[LOF同步] 新浪接口获取成功: {len(df)} 条")
                else:
                    logger.warning("[LOF同步] 新浪接口也未获取到数据")

            if df is None or df.empty:
                result["errors"].append("东财和新浪接口均未获取到 LOF 数据")
                return result

            result["total"] = len(df)
            result["data_source"] = data_source

            saved_count = self.db.save_daily_data_batch(df, data_source)
            result["saved"] = saved_count

            logger.info(f"[LOF同步] 同步完成: 数据源={data_source}, 获取 {result['total']} 条, 保存 {saved_count} 条")

        except Exception as e:
            error_msg = f"LOF 同步失败: {e}"
            logger.error(f"[LOF同步] {error_msg}")
            result["errors"].append(error_msg)

        return result

    def sync_all_funds(self) -> Dict[str, Any]:
        """
        Sync both ETF and LOF daily data.

        Returns:
            Combined sync statistics:
            {
                "etf": {...},       # ETF sync result
                "lof": {...},       # LOF sync result
                "total_saved": int, # Total saved records
                "has_errors": bool  # Whether there are errors
            }
        """
        logger.info("[基金同步] 开始同步全部基金数据...")

        etf_result = self.sync_etf_daily()
        lof_result = self.sync_lof_daily()

        total_saved = etf_result["saved"] + lof_result["saved"]
        has_errors = bool(etf_result["errors"] or lof_result["errors"])

        result = {
            "etf": etf_result,
            "lof": lof_result,
            "total_saved": total_saved,
            "has_errors": has_errors
        }

        logger.info(f"[基金同步] 全部同步完成: ETF {etf_result['saved']} 条, "
                   f"LOF {lof_result['saved']} 条, 共 {total_saved} 条")

        return result
