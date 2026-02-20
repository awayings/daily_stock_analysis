# -*- coding: utf-8 -*-
"""
===================================
股票数据服务层
===================================

职责：
1. 封装股票数据获取逻辑
2. 提供实时行情和历史数据接口
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List

from src.repositories.stock_repo import StockRepository

logger = logging.getLogger(__name__)


class StockService:
    """
    股票数据服务
    
    封装股票数据获取的业务逻辑
    """
    
    def __init__(self):
        """初始化股票数据服务"""
        self.repo = StockRepository()
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情
        
        Args:
            stock_code: 股票代码
            
        Returns:
            实时行情数据字典
        """
        try:
            # 调用数据获取器获取实时行情
            from data_provider.base import DataFetcherManager
            
            manager = DataFetcherManager()
            quote = manager.get_realtime_quote(stock_code)
            
            if quote is None:
                logger.warning(f"获取 {stock_code} 实时行情失败")
                return None
            
            # UnifiedRealtimeQuote 是 dataclass，使用 getattr 安全访问字段
            # 字段映射: UnifiedRealtimeQuote -> API 响应
            # - code -> stock_code
            # - name -> stock_name
            # - price -> current_price
            # - change_amount -> change
            # - change_pct -> change_percent
            # - open_price -> open
            # - high -> high
            # - low -> low
            # - pre_close -> prev_close
            # - volume -> volume
            # - amount -> amount
            return {
                "stock_code": getattr(quote, "code", stock_code),
                "stock_name": getattr(quote, "name", None),
                "current_price": getattr(quote, "price", 0.0) or 0.0,
                "change": getattr(quote, "change_amount", None),
                "change_percent": getattr(quote, "change_pct", None),
                "open": getattr(quote, "open_price", None),
                "high": getattr(quote, "high", None),
                "low": getattr(quote, "low", None),
                "prev_close": getattr(quote, "pre_close", None),
                "volume": getattr(quote, "volume", None),
                "amount": getattr(quote, "amount", None),
                "update_time": datetime.now().isoformat(),
            }
            
        except ImportError:
            logger.warning("DataFetcherManager 未找到，使用占位数据")
            return self._get_placeholder_quote(stock_code)
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}", exc_info=True)
            return None
    
    def get_history_data(
        self,
        stock_code: str,
        period: str = "daily",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取股票历史行情
        
        Args:
            stock_code: 股票代码
            period: K 线周期 (daily/weekly/monthly)
            days: 获取天数
            
        Returns:
            历史行情数据字典
            
        Raises:
            ValueError: 当 period 不是 daily 时抛出（weekly/monthly 暂未实现）
        """
        # 验证 period 参数，只支持 daily
        if period != "daily":
            raise ValueError(
                f"暂不支持 '{period}' 周期，目前仅支持 'daily'。"
                "weekly/monthly 聚合功能将在后续版本实现。"
            )
        
        try:
            # 调用数据获取器获取历史数据
            from data_provider.base import DataFetcherManager
            
            manager = DataFetcherManager()
            df, source = manager.get_daily_data(stock_code, days=days)
            
            if df is None or df.empty:
                logger.warning(f"获取 {stock_code} 历史数据失败")
                return {"stock_code": stock_code, "period": period, "data": []}
            
            # 获取股票名称
            stock_name = manager.get_stock_name(stock_code)
            
            # 转换为响应格式
            data = []
            for _, row in df.iterrows():
                date_val = row.get("date")
                if hasattr(date_val, "strftime"):
                    date_str = date_val.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_val)
                
                data.append({
                    "date": date_str,
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": float(row.get("close", 0)),
                    "volume": float(row.get("volume", 0)) if row.get("volume") else None,
                    "amount": float(row.get("amount", 0)) if row.get("amount") else None,
                    "change_percent": float(row.get("pct_chg", 0)) if row.get("pct_chg") else None,
                })
            
            return {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "period": period,
                "data": data,
            }
            
        except ImportError:
            logger.warning("DataFetcherManager 未找到，返回空数据")
            return {"stock_code": stock_code, "period": period, "data": []}
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}", exc_info=True)
            return {"stock_code": stock_code, "period": period, "data": []}
    
    def get_realtime_quote_from_db(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取股票实时行情（优先数据库，回退到外部API）

        Args:
            stock_code: 股票代码

        Returns:
            实时行情数据字典，格式与 get_realtime_quote() 一致
        """
        try:
            latest_records = self.repo.get_latest(stock_code, days=2)

            if latest_records:
                today_data = latest_records[0]
                yesterday_data = latest_records[1] if len(latest_records) > 1 else None

                prev_close = None
                change = None
                if yesterday_data and yesterday_data.close:
                    prev_close = yesterday_data.close
                    if today_data.close:
                        change = today_data.close - prev_close

                update_time = datetime.now().isoformat()
                if today_data.updated_at:
                    update_time = today_data.updated_at.isoformat()
                elif today_data.created_at:
                    update_time = today_data.created_at.isoformat()

                return {
                    "stock_code": today_data.code,
                    "stock_name": None,
                    "current_price": today_data.close or 0.0,
                    "change": change,
                    "change_percent": today_data.pct_chg,
                    "open": today_data.open,
                    "high": today_data.high,
                    "low": today_data.low,
                    "prev_close": prev_close,
                    "volume": today_data.volume,
                    "amount": today_data.amount,
                    "update_time": update_time,
                }

            logger.info(f"数据库无 {stock_code} 数据，从外部API获取")
            quote = self.get_realtime_quote(stock_code)

            if quote:
                self._save_quote_to_db(quote)

            return quote

        except Exception as e:
            logger.error(f"从数据库获取实时行情失败: {e}", exc_info=True)
            return None

    def _save_quote_to_db(self, quote: Dict[str, Any]) -> bool:
        """
        将行情数据保存到数据库

        Args:
            quote: 行情数据字典

        Returns:
            是否保存成功
        """
        try:
            import pandas as pd

            df = pd.DataFrame([{
                'date': date.today(),
                'open': quote.get('open'),
                'high': quote.get('high'),
                'low': quote.get('low'),
                'close': quote.get('current_price'),
                'volume': quote.get('volume'),
                'amount': quote.get('amount'),
                'pct_chg': quote.get('change_percent'),
            }])

            saved = self.repo.save_dataframe(
                df,
                code=quote.get('stock_code'),
                data_source='realtime_quote_cache'
            )

            if saved > 0:
                logger.info(f"已缓存 {quote.get('stock_code')} 行情数据到数据库")

            return saved > 0

        except Exception as e:
            logger.error(f"保存行情数据到数据库失败: {e}", exc_info=True)
            return False

    def _get_placeholder_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取占位行情数据（用于测试）

        Args:
            stock_code: 股票代码

        Returns:
            占位行情数据
        """
        return {
            "stock_code": stock_code,
            "stock_name": f"股票{stock_code}",
            "current_price": 0.0,
            "change": None,
            "change_percent": None,
            "open": None,
            "high": None,
            "low": None,
            "prev_close": None,
            "volume": None,
            "amount": None,
            "update_time": datetime.now().isoformat(),
        }
