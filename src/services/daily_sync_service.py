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
from datetime import date, timedelta
from typing import Optional, Dict, Any, List, Tuple

from src.repositories.stock_repo import StockRepository
from src.storage import DatabaseManager

logger = logging.getLogger(__name__)


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
            sync_date: 同步日期（可选，默认今天）
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
            sync_date = date.today()
        
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
        使用 Tushare 批量接口同步
        
        一次请求获取全市场数据，最高效
        
        Args:
            sync_date: 同步日期
            
        Returns:
            同步结果，失败返回 None
        """
        try:
            from data_provider.tushare_fetcher import TushareFetcher
            
            fetcher = TushareFetcher()
            
            if fetcher._api is None:
                logger.info("[批量同步] Tushare 未配置 Token，跳过")
                return None
            
            logger.info("[批量同步] 尝试使用 Tushare 批量接口...")
            
            trade_date = sync_date.strftime('%Y-%m-%d')
            df = fetcher.get_daily_data_by_date(trade_date)
            
            if df is None or df.empty:
                logger.warning("[批量同步] Tushare 批量获取数据为空")
                return None
            
            saved_count = self._save_batch_data(df, "TushareFetcher")
            
            logger.info(f"[批量同步] Tushare 批量同步完成: 获取 {len(df)} 条，保存 {saved_count} 条")
            
            return {
                "total": len(df),
                "success": saved_count,
                "failed": 0,
                "data_sources": "TushareFetcher",
                "errors": [],
                "sync_mode": "tushare_batch"
            }
            
        except Exception as e:
            logger.warning(f"[批量同步] Tushare 批量同步失败: {e}")
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
        保存批量获取的数据
        
        Args:
            df: 包含多只股票数据的 DataFrame
            data_source: 数据源名称
            
        Returns:
            成功保存的股票数量
        """
        import pandas as pd
        from data_provider.base import DataFetcherManager
        
        if df is None or df.empty:
            return 0
        
        stock_codes = df['code'].unique().tolist()
        logger.info(f"[批量保存] 批量获取 {len(stock_codes)} 只股票名称...")
        manager = DataFetcherManager()
        stock_names = manager.batch_get_stock_names(stock_codes)
        
        df_with_names = df.copy()
        df_with_names['name'] = df_with_names['code'].map(stock_names)
        
        logger.info(f"[批量保存] 开始批量保存 {len(df)} 条记录...")
        saved_count = self.db.save_daily_data_batch(df_with_names, data_source)
        
        logger.info(f"[批量保存] 保存完成: {saved_count} 条记录，涉及 {len(stock_codes)} 只股票")
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
