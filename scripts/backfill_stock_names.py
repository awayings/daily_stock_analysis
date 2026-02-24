#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
===================================
历史数据补充脚本：填充 stock_daily 表的 name 字段
===================================

功能：
为 stock_daily 表中现有的历史数据填充 name 字段

使用方法：
    python scripts/backfill_stock_names.py [--batch-size 100]

参数：
    --batch-size: 每批处理的股票数量（默认 100）
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage import DatabaseManager, StockDaily
from data_provider.base import DataFetcherManager
from sqlalchemy import select, func, and_

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_stock_codes_without_name(db: DatabaseManager, batch_size: int = None) -> List[str]:
    """
    获取 name 字段为空的股票代码列表
    
    Args:
        db: 数据库管理器
        batch_size: 批量大小（可选）
        
    Returns:
        股票代码列表
    """
    with db.get_session() as session:
        query = select(StockDaily.code).where(
            StockDaily.name.is_(None)
        ).distinct()
        
        if batch_size:
            query = query.limit(batch_size)
        
        result = session.execute(query).scalars().all()
        return list(result)


def get_all_stock_codes(db: DatabaseManager) -> List[str]:
    """
    获取所有股票代码列表
    
    Args:
        db: 数据库管理器
        
    Returns:
        股票代码列表
    """
    with db.get_session() as session:
        result = session.execute(
            select(StockDaily.code).distinct()
        ).scalars().all()
        return list(result)


def update_stock_names(
    db: DatabaseManager,
    stock_names: Dict[str, str]
) -> int:
    """
    批量更新股票名称
    
    Args:
        db: 数据库管理器
        stock_names: {股票代码: 股票名称} 字典
        
    Returns:
        更新的记录数
    """
    if not stock_names:
        return 0
    
    updated_count = 0
    
    with db.get_session() as session:
        try:
            for code, name in stock_names.items():
                if not name:
                    continue
                
                # 更新该股票所有记录的 name 字段
                result = session.execute(
                    StockDaily.__table__.update()
                    .where(StockDaily.code == code)
                    .values(name=name)
                )
                
                if result.rowcount > 0:
                    updated_count += result.rowcount
            
            session.commit()
            logger.info(f"成功更新 {len(stock_names)} 只股票的名称，共 {updated_count} 条记录")
            
        except Exception as e:
            session.rollback()
            logger.error(f"更新股票名称失败: {e}")
            raise
    
    return updated_count


def backfill_stock_names(batch_size: int = 100, force_all: bool = False):
    """
    补充股票名称数据
    
    Args:
        batch_size: 每批处理的股票数量
        force_all: 是否强制处理所有股票（包括已有名称的）
    """
    logger.info("=" * 60)
    logger.info("开始补充股票名称数据")
    logger.info("=" * 60)
    
    # 初始化
    db = DatabaseManager.get_instance()
    manager = DataFetcherManager()
    
    # 获取股票代码列表
    if force_all:
        logger.info("获取所有股票代码...")
        stock_codes = get_all_stock_codes(db)
    else:
        logger.info("获取 name 为空的股票代码...")
        stock_codes = get_stock_codes_without_name(db)
    
    if not stock_codes:
        logger.info("没有需要补充的股票名称，退出")
        return
    
    total = len(stock_codes)
    logger.info(f"共需处理 {total} 只股票")
    
    # 分批处理
    processed = 0
    success_count = 0
    failed_count = 0
    
    for i in range(0, total, batch_size):
        batch = stock_codes[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        logger.info(f"\n处理批次 {batch_num}/{total_batches}，共 {len(batch)} 只股票...")
        
        try:
            # 批量获取股票名称
            stock_names = manager.batch_get_stock_names(batch)
            
            if stock_names:
                # 更新数据库
                updated = update_stock_names(db, stock_names)
                success_count += len(stock_names)
                processed += len(batch)
                
                logger.info(f"批次 {batch_num} 完成：成功 {len(stock_names)} 只，更新 {updated} 条记录")
            else:
                failed_count += len(batch)
                logger.warning(f"批次 {batch_num} 失败：未能获取股票名称")
            
        except Exception as e:
            failed_count += len(batch)
            logger.error(f"批次 {batch_num} 处理失败: {e}")
            continue
        
        # 显示进度
        progress = (processed / total) * 100
        logger.info(f"总进度: {processed}/{total} ({progress:.1f}%)")
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("补充完成")
    logger.info("=" * 60)
    logger.info(f"总计: {total} 只股票")
    logger.info(f"成功: {success_count} 只")
    logger.info(f"失败: {failed_count} 只")
    logger.info(f"成功率: {(success_count/total*100):.1f}%")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='补充 stock_daily 表的 name 字段数据'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='每批处理的股票数量（默认 100）'
    )
    parser.add_argument(
        '--force-all',
        action='store_true',
        help='强制处理所有股票（包括已有名称的）'
    )
    
    args = parser.parse_args()
    
    try:
        backfill_stock_names(
            batch_size=args.batch_size,
            force_all=args.force_all
        )
    except KeyboardInterrupt:
        logger.info("\n用户中断，退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
