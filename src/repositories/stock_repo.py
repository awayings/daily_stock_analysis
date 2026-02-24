# -*- coding: utf-8 -*-
"""
===================================
股票数据访问层
===================================

职责：
1. 封装股票数据的数据库操作
2. 提供日线数据查询接口
"""

import logging
from datetime import date
from typing import Optional, List, Dict, Any

import pandas as pd
from sqlalchemy import and_, desc, select

from src.storage import DatabaseManager, StockDaily

logger = logging.getLogger(__name__)


class StockRepository:
    """
    股票数据访问层
    
    封装 StockDaily 表的数据库操作
    """
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化数据访问层
        
        Args:
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()
    
    def get_latest(self, code: str, days: int = 2) -> List[StockDaily]:
        """
        获取最近 N 天的数据
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            StockDaily 对象列表（按日期降序）
        """
        try:
            return self.db.get_latest_data(code, days)
        except Exception as e:
            logger.error(f"获取最新数据失败: {e}")
            return []
    
    def get_range(
        self,
        code: str,
        start_date: date,
        end_date: date
    ) -> List[StockDaily]:
        """
        获取指定日期范围的数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            StockDaily 对象列表
        """
        try:
            return self.db.get_data_range(code, start_date, end_date)
        except Exception as e:
            logger.error(f"获取日期范围数据失败: {e}")
            return []
    
    def save_dataframe(
        self,
        df: pd.DataFrame,
        code: str,
        data_source: str = "Unknown",
        name: str = None
    ) -> int:
        """
        保存 DataFrame 到数据库
        
        Args:
            df: 包含日线数据的 DataFrame
            code: 股票代码
            data_source: 数据来源
            name: 股票中文名称（可选）
            
        Returns:
            保存的记录数
        """
        try:
            return self.db.save_daily_data(df, code, data_source, name)
        except Exception as e:
            logger.error(f"保存日线数据失败: {e}")
            return 0
    
    def has_today_data(self, code: str, target_date: Optional[date] = None) -> bool:
        """
        检查是否有指定日期的数据
        
        Args:
            code: 股票代码
            target_date: 目标日期（默认今天）
            
        Returns:
            是否存在数据
        """
        try:
            return self.db.has_today_data(code, target_date)
        except Exception as e:
            logger.error(f"检查数据存在失败: {e}")
            return False
    
    def get_analysis_context(
        self, 
        code: str, 
        target_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取分析上下文
        
        Args:
            code: 股票代码
            target_date: 目标日期
            
        Returns:
            分析上下文字典
        """
        try:
            return self.db.get_analysis_context(code, target_date)
        except Exception as e:
            logger.error(f"获取分析上下文失败: {e}")
            return None

    def get_start_daily(self, *, code: str, analysis_date: date) -> Optional[StockDaily]:
        """Return StockDaily for analysis_date (preferred) or nearest previous date."""
        with self.db.get_session() as session:
            row = session.execute(
                select(StockDaily)
                .where(and_(StockDaily.code == code, StockDaily.date <= analysis_date))
                .order_by(desc(StockDaily.date))
                .limit(1)
            ).scalars().first()
            return row

    def get_forward_bars(self, *, code: str, analysis_date: date, eval_window_days: int) -> List[StockDaily]:
        """Return forward daily bars after analysis_date, up to eval_window_days."""
        with self.db.get_session() as session:
            rows = session.execute(
                select(StockDaily)
                .where(and_(StockDaily.code == code, StockDaily.date > analysis_date))
                .order_by(StockDaily.date)
                .limit(eval_window_days)
            ).scalars().all()
            return list(rows)

    def get_all_stock_codes(self) -> List[str]:
        """
        获取所有不重复的股票代码
        
        Returns:
            股票代码列表
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import func
                result = session.execute(
                    select(StockDaily.code).distinct()
                ).scalars().all()
                return list(result)
        except Exception as e:
            logger.error(f"获取股票代码列表失败: {e}")
            return []

    def get_latest_date(self) -> Optional[date]:
        """
        获取所有股票中最新的数据日期
        
        Returns:
            最新日期，如果没有数据则返回 None
        """
        try:
            with self.db.get_session() as session:
                row = session.execute(
                    select(StockDaily.date)
                    .order_by(desc(StockDaily.date))
                    .limit(1)
                ).scalars().first()
                return row
        except Exception as e:
            logger.error(f"获取最新日期失败: {e}")
            return None

    def count_records_by_date(self, target_date: date) -> int:
        """
        统计指定日期的记录数
        
        Args:
            target_date: 目标日期
            
        Returns:
            记录数量
        """
        try:
            with self.db.get_session() as session:
                from sqlalchemy import func
                result = session.execute(
                    select(func.count()).where(StockDaily.date == target_date)
                ).scalar()
                return result or 0
        except Exception as e:
            logger.error(f"统计日期记录数失败: {e}")
            return 0

    def get_latest_quote(self, code: str) -> Optional[StockDaily]:
        """
        获取指定股票的最新行情
        
        Args:
            code: 股票代码
            
        Returns:
            最新的 StockDaily 对象，如果没有数据则返回 None
        """
        try:
            with self.db.get_session() as session:
                row = session.execute(
                    select(StockDaily)
                    .where(StockDaily.code == code)
                    .order_by(desc(StockDaily.date))
                    .limit(1)
                ).scalars().first()
                return row
        except Exception as e:
            logger.error(f"获取最新行情失败: {e}")
            return None

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索股票（支持代码和名称模糊匹配）
        
        从 stock_daily 表中获取最新时间戳的股票记录进行搜索
        
        Args:
            keyword: 搜索关键词（股票代码或名称）
            limit: 返回数量限制
            
        Returns:
            匹配的股票列表，每个元素包含 code, name, close, date
        """
        try:
            from sqlalchemy import func, or_, literal_column
            from sqlalchemy.sql import text
            
            logger.info(f"search_stocks called with keyword={keyword}, limit={limit}")
            
            with self.db.get_session() as session:
                result = session.execute(text("""
                    SELECT date FROM stock_daily
                    GROUP BY date
                    HAVING COUNT(DISTINCT code) >= 100
                    ORDER BY date DESC
                    LIMIT 1
                """)).scalar()
                
                logger.info(f"Latest date query result: {result}")
                
                if not result:
                    result = session.execute(
                        select(func.max(StockDaily.date))
                    ).scalar()
                    logger.debug(f"Fallback max date: {result}")
                
                if not result:
                    logger.warning("No date found in stock_daily table")
                    return []
                
                latest_date = result
                keyword_upper = keyword.upper()
                keyword_like = f"%{keyword}%"
                
                logger.info(f"Searching with latest_date={latest_date}, keyword_like={keyword_like}")
                
                query = text("""
                    SELECT DISTINCT code, name, close, date
                    FROM stock_daily
                    WHERE date = :latest_date
                    AND (
                        code LIKE :keyword_prefix
                        OR code LIKE :keyword_contains
                        OR name LIKE :keyword_contains
                    )
                    ORDER BY 
                        CASE 
                            WHEN code = :keyword_exact THEN 0
                            WHEN code LIKE :keyword_prefix THEN 1
                            WHEN name LIKE :keyword_prefix THEN 2
                            ELSE 3
                        END,
                        code
                    LIMIT :limit
                """)
                
                results = session.execute(
                    query,
                    {
                        "latest_date": latest_date,
                        "keyword_prefix": f"{keyword_upper}%",
                        "keyword_contains": keyword_like,
                        "keyword_exact": keyword_upper,
                        "limit": limit
                    }
                ).fetchall()
                
                logger.info(f"Query returned {len(results)} results")
                
                result_list = []
                for row in results:
                    code = row[0]
                    name = row[1]
                    close = row[2]
                    date = row[3]
                    
                    if not name:
                        names = self._get_stock_names([code])
                        name = names.get(code)
                    
                    result_list.append({
                        "code": code,
                        "name": name,
                        "close": float(close) if close else None,
                        "date": date.isoformat() if date else None
                    })
                
                return result_list
                
        except Exception as e:
            logger.error(f"搜索股票失败: {e}", exc_info=True)
            return []

    def _get_stock_names(self, codes: List[str]) -> Dict[str, str]:
        """
        批量获取股票名称
        
        Args:
            codes: 股票代码列表
            
        Returns:
            {股票代码: 股票名称} 字典
        """
        try:
            from data_provider.base import DataFetcherManager
            manager = DataFetcherManager()
            return manager.batch_get_stock_names(codes)
        except Exception as e:
            logger.warning(f"获取股票名称失败: {e}")
            return {}
