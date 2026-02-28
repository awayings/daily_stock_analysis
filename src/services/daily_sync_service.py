# -*- coding: utf-8 -*-
"""
===================================
日线数据同步服务
===================================

职责：
1. 批量同步股票日线数据
2. 多数据源故障切换
3. 同步进度跟踪与统计
4. 支持高效批量同步（Tushare/Efinance）
"""

import logging
from datetime import date, datetime, timedelta, time
from typing import Optional, Dict, Any, List, Tuple

from src.repositories.stock_repo import StockRepository
from src.storage import DatabaseManager

logger = logging.getLogger(__name__)


def get_default_sync_date() -> date:
    """
    Calculate default sync date based on current time.

    Rules:
    - Before 17:00 (5 PM): Use previous day
    - At or after 17:00 (5 PM): Use current day

    Returns:
        date: Default sync date
    """
    now = datetime.now()
    cutoff_time = time(17, 0, 0)

    if now.time() < cutoff_time:
        return (now - timedelta(days=1)).date()
    else:
        return now.date()


class DailyStockSyncService:
    """
    日线数据同步服务
    
    负责批量同步股票日线数据到数据库
    
    同步策略（按优先级）：
    1. Tushare 批量接口：一次请求获取全市场数据（最高效）
    2. Efinance 批量接口：分批获取多只股票数据
    3. 逐只同步：降级方案，逐只股票获取
    """
    
    def __init__(
        self,
        stock_repo: Optional[StockRepository] = None,
        db_manager: Optional[DatabaseManager] = None
    ):
        """
        初始化同步服务
        
        Args:
            stock_repo: 股票数据访问层（可选，默认自动创建）
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()
        self.repo = stock_repo or StockRepository(self.db)
    
    def sync_all_stocks(
        self,
        sync_date: Optional[date] = None,
        use_batch: bool = True
    ) -> Dict[str, Any]:
        """
        同步所有股票的日线数据
        
        流程（优先使用批量接口）：
        1. 尝试 Tushare 批量接口（最高效）
        2. 尝试 Efinance 批量接口
        3. 降级到逐只同步
        
        Args:
            sync_date: 同步日期（可选，默认根据时间自动选择：17:00前为前一天，17:00后为当天）
            use_batch: 是否使用批量接口（默认 True）
            
        Returns:
            同步统计结果:
            {
                "total": int,       # 总股票数
                "success": int,     # 成功数
                "failed": int,      # 失败数
                "data_sources": str, # 使用的数据源（逗号分隔）
                "errors": List[str], # 错误信息列表
                "sync_mode": str    # 同步模式：tushare_batch/efinance_batch/one_by_one
            }
        """
        if sync_date is None:
            sync_date = get_default_sync_date()
        
        logger.info(f"开始同步日线数据，目标日期: {sync_date}")
        
        if use_batch:
            result = self._try_batch_sync(sync_date)
            if result is not None:
                return result
        
        return self._sync_stocks_one_by_one(sync_date)
    
    def _try_batch_sync(self, sync_date: date) -> Optional[Dict[str, Any]]:
        """
        尝试使用批量接口同步
        
        优先级：
        1. Tushare 批量接口
        2. Efinance 批量接口
        
        Args:
            sync_date: 同步日期
            
        Returns:
            同步结果，失败返回 None
        """
        result = self._try_tushare_batch_sync(sync_date)
        if result is not None:
            return result
        
        result = self._try_efinance_batch_sync(sync_date)
        if result is not None:
            return result
        
        return None
    
    def _try_tushare_batch_sync(self, sync_date: date) -> Optional[Dict[str, Any]]:
        """
        Use Tushare batch interfaces to sync all data types.

        Calls three separate batch APIs:
        1. daily(trade_date) - A股 stocks
        2. fund_daily(trade_date) - ETF/LOF funds
        3. hk_daily(trade_date) - HK stocks

        Args:
            sync_date: Sync date

        Returns:
            Sync result dict, or None if all APIs fail
        """
        try:
            from data_provider.tushare_fetcher import TushareFetcher
            import pandas as pd

            fetcher = TushareFetcher()

            if fetcher._api is None:
                logger.info("[Batch Sync] Tushare Token not configured, skipping")
                return None

            logger.info("[Batch Sync] Using Tushare batch interfaces...")

            trade_date = sync_date.strftime('%Y-%m-%d')
            all_dfs = []
            data_types_synced = []
            errors = []

            df_a = fetcher.get_daily_data_by_date(trade_date)
            if df_a is not None and not df_a.empty:
                all_dfs.append(df_a)
                data_types_synced.append(f"A股({len(df_a)})")
                logger.info(f"[Batch Sync] A股: {len(df_a)} records")

            # df_fund = fetcher.get_fund_daily_data_by_date(trade_date)
            # if df_fund is not None and not df_fund.empty:
            #     all_dfs.append(df_fund)
            #     data_types_synced.append(f"基金({len(df_fund)})")
            #     logger.info(f"[Batch Sync] 基金: {len(df_fund)} records")

            # df_hk = fetcher.get_hk_daily_data_by_date(trade_date)
            # if df_hk is not None and not df_hk.empty:
            #     all_dfs.append(df_hk)
            #     data_types_synced.append(f"港股({len(df_hk)})")
            #     logger.info(f"[Batch Sync] 港股: {len(df_hk)} records")

            if not all_dfs:
                logger.warning("[Batch Sync] Tushare batch sync returned no data from any API")
                return None

            combined_df = pd.concat(all_dfs, ignore_index=True)
            logger.info(f"[Batch Sync] Combined total: {len(combined_df)} records from {len(all_dfs)} APIs")

            saved_count = self._save_batch_data(combined_df, "TushareFetcher")

            logger.info(f"[Batch Sync] Tushare batch sync complete: fetched {len(combined_df)}, saved {saved_count} records")
            logger.info(f"[Batch Sync] Data types synced: {', '.join(data_types_synced)}")

            return {
                "total": len(combined_df),
                "success": saved_count,
                "failed": 0,
                "data_sources": "TushareFetcher",
                "errors": errors,
                "sync_mode": "tushare_batch"
            }

        except Exception as e:
            logger.warning(f"[Batch Sync] Tushare batch sync failed: {e}")
            return None
    
    def _try_efinance_batch_sync(self, sync_date: date) -> Optional[Dict[str, Any]]:
        """
        使用 Efinance 批量接口同步
        
        分批获取多只股票数据
        
        Args:
            sync_date: 同步日期
            
        Returns:
            同步结果，失败返回 None
        """
        try:
            from data_provider.efinance_fetcher import EfinanceFetcher
            from data_provider.base import DataFetcherManager
            import pandas as pd
            
            fetcher = EfinanceFetcher()
            
            stock_codes = self._get_stock_codes()
            if not stock_codes:
                logger.warning("[批量同步] 未获取到股票代码列表")
                return None
            
            logger.info(f"[批量同步] 尝试使用 Efinance 批量接口，共 {len(stock_codes)} 只股票...")
            
            logger.info("[批量同步] 批量获取股票名称...")
            manager = DataFetcherManager()
            stock_names = manager.batch_get_stock_names(stock_codes)
            
            start_date = (sync_date - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = sync_date.strftime('%Y-%m-%d')
            
            df_dict = fetcher.get_daily_data_batch(
                stock_codes=stock_codes,
                start_date=start_date,
                end_date=end_date,
                batch_size=200
            )
            
            if not df_dict:
                logger.warning("[批量同步] Efinance 批量获取数据为空")
                return None
            
            all_dfs = []
            failed_codes = []
            
            for code, df in df_dict.items():
                if df is not None and not df.empty:
                    df['code'] = code
                    df['name'] = stock_names.get(code)
                    all_dfs.append(df)
                else:
                    failed_codes.append(code)
            
            if all_dfs:
                combined_df = pd.concat(all_dfs, ignore_index=True)
                logger.info(f"[批量同步] 开始批量保存 {len(combined_df)} 条记录...")
                saved_count = self.db.save_daily_data_batch(combined_df, "EfinanceFetcher")
                success_count = len([c for c in stock_codes if c not in failed_codes])
                logger.info(f"[批量同步] Efinance 批量同步完成: 保存 {saved_count} 条，成功 {success_count} 只股票，失败 {len(failed_codes)} 只")
            else:
                success_count = 0
                logger.warning("[批量同步] 无有效数据可保存")
            
            return {
                "total": len(stock_codes),
                "success": success_count,
                "failed": len(failed_codes),
                "data_sources": "EfinanceFetcher",
                "errors": [],
                "sync_mode": "efinance_batch"
            }
            
        except Exception as e:
            logger.warning(f"[批量同步] Efinance 批量同步失败: {e}")
            return None
    
    def _save_batch_data(self, df, data_source: str) -> int:
        """
        Save batch-fetched data with optimized name lookup.

        Optimization strategy:
        1. Check database for existing names first
        2. Only fetch names for codes not found in database
        3. This reduces API calls significantly for A股 and ETF/LOF data

        Args:
            df: DataFrame containing multiple stocks' data
            data_source: Data source name

        Returns:
            Number of stocks saved
        """
        import pandas as pd
        from data_provider.base import DataFetcherManager

        if df is None or df.empty:
            return 0

        df_with_names = df.copy()

        if 'name' not in df_with_names.columns:
            df_with_names['name'] = None

        stock_codes = df_with_names['code'].unique().tolist()

        logger.info(f"[Batch Save] Checking database for existing names for {len(stock_codes)} codes...")
        existing_names = self.repo.get_existing_names(stock_codes)
        logger.info(f"[Batch Save] Found {len(existing_names)} names in database")

        codes_without_names = [code for code in stock_codes if code not in existing_names]

        if codes_without_names:
            logger.info(f"[Batch Save] Fetching names for {len(codes_without_names)} codes from data providers...")
            manager = DataFetcherManager()
            fetched_names = manager.batch_get_stock_names(codes_without_names)

            for code, name in fetched_names.items():
                if name:
                    df_with_names.loc[df_with_names['code'] == code, 'name'] = name
                    existing_names[code] = name
        else:
            logger.info(f"[Batch Save] All codes have names in database, skipping API calls")

        df_with_names['name'] = df_with_names['code'].map(existing_names).fillna(df_with_names['name'])

        logger.info(f"[Batch Save] Saving {len(df_with_names)} records...")
        saved_count = self.db.save_daily_data_batch(df_with_names, data_source)

        logger.info(f"[Batch Save] Saved {saved_count} records for {len(stock_codes)} stocks")
        return len(stock_codes)
    
    def _sync_stocks_one_by_one(self, sync_date: date) -> Dict[str, Any]:
        """
        逐只股票同步（降级方案）
        
        Args:
            sync_date: 同步日期
            
        Returns:
            同步统计结果
        """
        stock_codes = self._get_stock_codes()
        
        if not stock_codes:
            logger.warning("未获取到任何股票代码，同步终止")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "data_sources": "",
                "errors": ["未获取到股票代码列表"],
                "sync_mode": "one_by_one"
            }
        
        total = len(stock_codes)
        success_count = 0
        failed_count = 0
        data_sources_used = set()
        errors = []
        
        logger.info(f"逐只同步模式: 共需同步 {total} 只股票")
        
        for index, code in enumerate(stock_codes, start=1):
            try:
                success, data_source = self._sync_single_stock(code, sync_date)
                
                if success:
                    success_count += 1
                    if data_source:
                        data_sources_used.add(data_source)
                else:
                    failed_count += 1
                    errors.append(f"{code}: 同步失败")
                
            except Exception as e:
                failed_count += 1
                error_msg = f"{code}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"同步股票 {code} 异常: {e}")
            
            if index % 100 == 0:
                logger.info(
                    f"同步进度: {index}/{total} "
                    f"(成功: {success_count}, 失败: {failed_count})"
                )
        
        data_sources_str = ", ".join(sorted(data_sources_used))
        
        result = {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "data_sources": data_sources_str,
            "errors": errors[:100],
            "sync_mode": "one_by_one"
        }
        
        logger.info(
            f"同步完成: 总计 {total}, 成功 {success_count}, "
            f"失败 {failed_count}, 数据源: {data_sources_str}"
        )
        
        return result
    
    def _sync_single_stock(
        self,
        code: str,
        sync_date: date
    ) -> Tuple[bool, str]:
        """
        同步单只股票的日线数据
        
        流程：
        1. 使用 DataFetcherManager 获取数据
        2. 获取股票中文名称
        3. 保存到数据库
        
        Args:
            code: 股票代码
            sync_date: 同步日期
            
        Returns:
            Tuple[bool, str]: (是否成功, 数据源名称)
        """
        from data_provider.base import DataFetcherManager
        
        try:
            manager = DataFetcherManager()
            
            start_date = (sync_date - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = sync_date.strftime('%Y-%m-%d')
            
            df, data_source = manager.get_daily_data(
                stock_code=code,
                start_date=start_date,
                end_date=end_date,
                days=7
            )
            
            if df is None or df.empty:
                logger.warning(f"股票 {code} 未获取到数据")
                return False, ""
            
            # 获取股票名称
            stock_name = manager.get_stock_name(code)
            
            saved_count = self.repo.save_dataframe(df, code, data_source, stock_name)
            
            if saved_count > 0:
                logger.debug(f"股票 {code} 同步成功，保存 {saved_count} 条记录 (来源: {data_source})")
                return True, data_source
            else:
                logger.warning(f"股票 {code} 数据保存失败")
                return False, data_source
                
        except Exception as e:
            logger.error(f"同步股票 {code} 失败: {e}")
            return False, ""
    
    def _get_stock_codes(self) -> List[str]:
        """
        获取股票代码列表
        
        策略：
        1. 优先从数据库获取已有股票代码
        2. 如果数据库为空，从数据源获取全市场股票列表
        
        Returns:
            股票代码列表
        """
        codes = self.repo.get_all_stock_codes()
        
        if codes:
            logger.info(f"从数据库获取到 {len(codes)} 只股票代码")
            return codes
        
        logger.info("数据库中无股票代码，尝试从数据源获取")
        
        try:
            from data_provider.base import DataFetcherManager
            
            manager = DataFetcherManager()
            
            for fetcher in manager._fetchers:
                if hasattr(fetcher, 'get_stock_list'):
                    try:
                        stock_list = fetcher.get_stock_list()
                        if stock_list is not None and not stock_list.empty:
                            codes = stock_list['code'].tolist()
                            logger.info(
                                f"从 {fetcher.name} 获取到 {len(codes)} 只股票代码"
                            )
                            return codes
                    except Exception as e:
                        logger.warning(f"从 {fetcher.name} 获取股票列表失败: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"获取股票列表异常: {e}")
        
        return []
