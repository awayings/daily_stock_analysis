#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库查看工具
用于查看 stock_analysis.db 中的数据
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.storage import DatabaseManager, StockDaily, NewsIntel, AnalysisHistory, BacktestResult, BacktestSummary
from sqlalchemy import func, desc, text


def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def show_stock_daily_stats():
    """显示股票日线数据统计"""
    print_section("股票日线数据统计 (StockDaily)")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        # 总记录数
        total_count = session.query(func.count(StockDaily.id)).scalar()
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("暂无数据")
            return
        
        # 股票数量
        stock_count = session.query(func.count(func.distinct(StockDaily.code))).scalar()
        print(f"股票数量: {stock_count}")
        
        # 日期范围
        date_range = session.query(
            func.min(StockDaily.date),
            func.max(StockDaily.date)
        ).first()
        print(f"日期范围: {date_range[0]} 至 {date_range[1]}")
        
        # 最新数据
        print("\n最新 10 条记录:")
        latest = session.query(StockDaily).order_by(
            desc(StockDaily.date),
            desc(StockDaily.created_at)
        ).limit(10).all()
        
        for record in latest:
            print(f"  {record.code} | {record.date} | 收盘: {record.close:.2f} | 涨跌: {record.pct_chg:.2f}% | 成交量: {record.volume:,.0f}")


def show_news_intel_stats():
    """显示新闻情报统计"""
    print_section("新闻情报统计 (NewsIntel)")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        # 总记录数
        total_count = session.query(func.count(NewsIntel.id)).scalar()
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("暂无数据")
            return
        
        # 按股票统计
        print("\n按股票统计 (前 10):")
        stock_stats = session.query(
            NewsIntel.code,
            func.count(NewsIntel.id).label('count')
        ).group_by(NewsIntel.code).order_by(
            desc('count')
        ).limit(10).all()
        
        for code, count in stock_stats:
            print(f"  {code}: {count} 条")
        
        # 按维度统计
        print("\n按维度统计:")
        dimension_stats = session.query(
            NewsIntel.dimension,
            func.count(NewsIntel.id).label('count')
        ).group_by(NewsIntel.dimension).all()
        
        for dimension, count in dimension_stats:
            print(f"  {dimension}: {count} 条")
        
        # 最新新闻
        print("\n最新 5 条新闻:")
        latest = session.query(NewsIntel).order_by(
            desc(NewsIntel.fetched_at)
        ).limit(5).all()
        
        for record in latest:
            print(f"  [{record.code}] {record.title[:60]}...")
            print(f"    来源: {record.source} | 时间: {record.fetched_at}")


def show_analysis_history_stats():
    """显示分析历史统计"""
    print_section("分析历史统计 (AnalysisHistory)")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        # 总记录数
        total_count = session.query(func.count(AnalysisHistory.id)).scalar()
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("暂无数据")
            return
        
        # 按股票统计
        print("\n按股票统计 (前 10):")
        stock_stats = session.query(
            AnalysisHistory.code,
            func.count(AnalysisHistory.id).label('count')
        ).group_by(AnalysisHistory.code).order_by(
            desc('count')
        ).limit(10).all()
        
        for code, count in stock_stats:
            print(f"  {code}: {count} 条")
        
        # 按操作建议统计
        print("\n按操作建议统计:")
        advice_stats = session.query(
            AnalysisHistory.operation_advice,
            func.count(AnalysisHistory.id).label('count')
        ).group_by(AnalysisHistory.operation_advice).all()
        
        for advice, count in advice_stats:
            print(f"  {advice}: {count} 条")
        
        # 最新分析
        print("\n最新 5 条分析:")
        latest = session.query(AnalysisHistory).order_by(
            desc(AnalysisHistory.created_at)
        ).limit(5).all()
        
        for record in latest:
            print(f"  [{record.code}] {record.operation_advice} | 情绪: {record.sentiment_score} | {record.created_at}")
            if record.analysis_summary:
                print(f"    摘要: {record.analysis_summary[:80]}...")


def show_backtest_stats():
    """显示回测统计"""
    print_section("回测统计 (BacktestResult & BacktestSummary)")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        # 回测结果统计
        result_count = session.query(func.count(BacktestResult.id)).scalar()
        print(f"回测结果记录数: {result_count}")
        
        if result_count > 0:
            # 按结果统计
            print("\n按回测结果统计:")
            outcome_stats = session.query(
                BacktestResult.outcome,
                func.count(BacktestResult.id).label('count')
            ).group_by(BacktestResult.outcome).all()
            
            for outcome, count in outcome_stats:
                print(f"  {outcome}: {count} 条")
        
        # 回测汇总统计
        summary_count = session.query(func.count(BacktestSummary.id)).scalar()
        print(f"\n回测汇总记录数: {summary_count}")
        
        if summary_count > 0:
            print("\n回测汇总:")
            summaries = session.query(BacktestSummary).all()
            
            for summary in summaries:
                print(f"  范围: {summary.scope} | 股票: {summary.code or '全局'}")
                print(f"    总评估: {summary.total_evaluations} | 完成: {summary.completed_count}")
                print(f"    胜率: {summary.win_rate_pct:.1f}% | 准确率: {summary.direction_accuracy_pct:.1f}%")
                print(f"    平均收益: {summary.avg_simulated_return_pct:.2f}%")


def show_all_tables():
    """显示所有表的概览"""
    print_section("数据库概览")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        tables = [
            ("StockDaily", StockDaily),
            ("NewsIntel", NewsIntel),
            ("AnalysisHistory", AnalysisHistory),
            ("BacktestResult", BacktestResult),
            ("BacktestSummary", BacktestSummary),
        ]
        
        for table_name, model in tables:
            count = session.query(func.count(model.id)).scalar()
            print(f"{table_name:20s}: {count:,} 条记录")


def interactive_query():
    """交互式查询"""
    print_section("交互式查询")
    print("输入 SQL 查询语句（输入 'quit' 退出）")
    
    db = DatabaseManager.get_instance()
    with db.get_session() as session:
        while True:
            try:
                sql = input("\nSQL> ").strip()
                
                if sql.lower() in ('quit', 'exit', 'q'):
                    break
                
                if not sql:
                    continue
                
                # 执行查询
                result = session.execute(text(sql))
                
                # 显示结果
                rows = result.fetchall()
                if rows:
                    # 获取列名
                    columns = result.keys()
                    print(f"\n找到 {len(rows)} 条记录:")
                    
                    # 打印表头
                    print(" | ".join(str(col) for col in columns))
                    print("-" * 80)
                    
                    # 打印前 20 行
                    for row in rows[:20]:
                        print(" | ".join(str(val) for val in row))
                    
                    if len(rows) > 20:
                        print(f"... (还有 {len(rows) - 20} 条记录)")
                else:
                    print("未找到匹配的记录")
                    
            except Exception as e:
                print(f"错误: {e}")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  股票分析数据库查看工具")
    print("="*60)
    
    # 显示菜单
    print("\n请选择操作:")
    print("  1. 显示数据库概览")
    print("  2. 显示股票日线数据统计")
    print("  3. 显示新闻情报统计")
    print("  4. 显示分析历史统计")
    print("  5. 显示回测统计")
    print("  6. 交互式 SQL 查询")
    print("  7. 显示所有统计")
    print("  0. 退出")
    
    while True:
        try:
            choice = input("\n请输入选项 (0-7): ").strip()
            
            if choice == '0':
                print("\n再见！")
                break
            elif choice == '1':
                show_all_tables()
            elif choice == '2':
                show_stock_daily_stats()
            elif choice == '3':
                show_news_intel_stats()
            elif choice == '4':
                show_analysis_history_stats()
            elif choice == '5':
                show_backtest_stats()
            elif choice == '6':
                interactive_query()
            elif choice == '7':
                show_all_tables()
                show_stock_daily_stats()
                show_news_intel_stats()
                show_analysis_history_stats()
                show_backtest_stats()
            else:
                print("无效选项，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == "__main__":
    main()
