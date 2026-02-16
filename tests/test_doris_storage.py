# -*- coding: utf-8 -*-
"""
===================================
Doris 存储层测试
===================================

测试 Doris UNIQUE KEY 模型的数据存储和查询功能
"""

import unittest
import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from sqlalchemy import text

from src.config import Config, get_config
from src.storage import (
    DatabaseManager, 
    StockDaily, 
    NewsIntel, 
    AnalysisHistory,
    BacktestResult,
    BacktestSummary,
    ALL_MODELS,
    get_db
)


class TestDorisConfig(unittest.TestCase):
    """测试 Doris 配置加载"""
    
    @classmethod
    def setUpClass(cls):
        """测试前重置配置"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
    
    def test_config_loading(self):
        """测试配置加载"""
        config = get_config()
        
        self.assertEqual(config.database_type, 'doris', "数据库类型应该是 doris")
        self.assertEqual(config.doris_host, '10.43.50.254', "Doris 主机配置错误")
        self.assertEqual(config.doris_port, 9030, "Doris 端口配置错误")
        self.assertEqual(config.doris_user, 'doris', "Doris 用户配置错误")
        self.assertEqual(config.doris_password, 'doris1234', "Doris 密码配置错误")
        self.assertEqual(config.doris_database, 'stock_analysis', "Doris 数据库名配置错误")
    
    def test_db_url_format(self):
        """测试数据库 URL 格式"""
        config = get_config()
        db_url = config.get_db_url()
        
        self.assertTrue(db_url.startswith('doris+pymysql://'), "URL 应该使用 doris+pymysql 协议")
        self.assertIn('charset=utf8mb4', db_url, "URL 应该包含 charset=utf8mb4")


class TestDorisConnection(unittest.TestCase):
    """测试 Doris 连接"""
    
    @classmethod
    def setUpClass(cls):
        """测试前重置实例"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
    
    def test_connection(self):
        """测试数据库连接"""
        db = DatabaseManager.get_instance()
        
        self.assertTrue(db.is_doris, "应该使用 Doris 数据库")
        
        with db.get_session() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            self.assertEqual(result[0], 1, "数据库连接应该正常")


class TestDorisTableStructure(unittest.TestCase):
    """测试 Doris 表结构"""
    
    @classmethod
    def setUpClass(cls):
        """测试前重置实例"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
        cls.db = DatabaseManager.get_instance()
    
    def test_tables_exist(self):
        """测试表是否存在"""
        with self.db.get_session() as session:
            for model in ALL_MODELS:
                table_name = model.__tablename__
                result = session.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                self.assertIsNotNone(result.fetchone(), f"表 {table_name} 应该存在")
    
    def test_stock_daily_structure(self):
        """测试 stock_daily 表结构"""
        with self.db.get_session() as session:
            result = session.execute(text("DESC stock_daily"))
            columns = {row[0]: row[1] for row in result.fetchall()}
            
            self.assertIn('code', columns, "stock_daily 应该有 code 列")
            self.assertIn('date', columns, "stock_daily 应该有 date 列")
            self.assertIn('close', columns, "stock_daily 应该有 close 列")
    
    def test_unique_key_model(self):
        """测试 UNIQUE KEY 模型"""
        with self.db.get_session() as session:
            result = session.execute(text("SHOW CREATE TABLE stock_daily"))
            create_stmt = result.fetchone()[1]
            
            self.assertIn('UNIQUE KEY', create_stmt, "stock_daily 应该使用 UNIQUE KEY 模型")
            self.assertIn('`code`', create_stmt, "UNIQUE KEY 应该包含 code")
            self.assertIn('`date`', create_stmt, "UNIQUE KEY 应该包含 date")


class TestStockDailyCRUD(unittest.TestCase):
    """测试股票日线数据 CRUD 操作"""
    
    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
        cls.db = DatabaseManager.get_instance()
        cls.test_code = 'TEST99'
        cls.test_date = date(2026, 2, 16)
    
    def setUp(self):
        """每个测试前清理测试数据"""
        with self.db.get_session() as session:
            session.execute(text(f"DELETE FROM stock_daily WHERE code = '{self.test_code}'"))
            session.commit()
    
    def test_insert_stock_daily(self):
        """测试插入日线数据"""
        test_df = pd.DataFrame({
            'date': [self.test_date],
            'open': [100.0],
            'high': [105.0],
            'low': [98.0],
            'close': [103.0],
            'volume': [1000000],
            'amount': [103000000],
            'pct_chg': [3.0],
            'ma5': [100.0],
            'ma10': [99.0],
            'ma20': [98.0],
            'volume_ratio': [1.5],
        })
        
        saved = self.db.save_daily_data(test_df, self.test_code, 'UnitTest')
        self.assertGreater(saved, 0, "应该成功保存数据")
        
        has_data = self.db.has_today_data(self.test_code, self.test_date)
        self.assertTrue(has_data, "应该能查询到保存的数据")
    
    def test_upsert_stock_daily(self):
        """测试 UNIQUE KEY 自动更新"""
        test_df1 = pd.DataFrame({
            'date': [self.test_date],
            'open': [100.0],
            'high': [105.0],
            'low': [98.0],
            'close': [103.0],
            'volume': [1000000],
            'amount': [103000000],
            'pct_chg': [3.0],
            'ma5': [100.0],
            'ma10': [99.0],
            'ma20': [98.0],
            'volume_ratio': [1.5],
        })
        
        self.db.save_daily_data(test_df1, self.test_code, 'UnitTest')
        
        test_df2 = pd.DataFrame({
            'date': [self.test_date],
            'open': [102.0],
            'high': [108.0],
            'low': [100.0],
            'close': [107.0],
            'volume': [1200000],
            'amount': [128400000],
            'pct_chg': [4.0],
            'ma5': [102.0],
            'ma10': [101.0],
            'ma20': [100.0],
            'volume_ratio': [1.8],
        })
        
        self.db.save_daily_data(test_df2, self.test_code, 'UnitTest')
        
        latest = self.db.get_latest_data(self.test_code, days=1)
        self.assertEqual(len(latest), 1, "应该只有一条记录")
        self.assertEqual(latest[0].close, 107.0, "收盘价应该更新为 107.0")
    
    def test_get_latest_data(self):
        """测试获取最新数据"""
        dates = [self.test_date - timedelta(days=i) for i in range(3)]
        
        for i, d in enumerate(dates):
            test_df = pd.DataFrame({
                'date': [d],
                'open': [100.0 + i],
                'high': [105.0 + i],
                'low': [98.0 + i],
                'close': [103.0 + i],
                'volume': [1000000],
                'amount': [103000000],
                'pct_chg': [1.0],
                'ma5': [100.0],
                'ma10': [99.0],
                'ma20': [98.0],
                'volume_ratio': [1.5],
            })
            self.db.save_daily_data(test_df, self.test_code, 'UnitTest')
        
        latest = self.db.get_latest_data(self.test_code, days=2)
        self.assertEqual(len(latest), 2, "应该返回2条数据")
        self.assertEqual(latest[0].date, self.test_date, "第一条应该是最新日期")


class TestNewsIntelCRUD(unittest.TestCase):
    """测试新闻情报 CRUD 操作"""
    
    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
        cls.db = DatabaseManager.get_instance()
        cls.test_code = 'TEST99'
    
    def test_news_unique_key(self):
        """测试新闻 URL 唯一键"""
        from src.search_service import SearchResponse, SearchResult
        
        news1 = SearchResponse(
            query='测试查询',
            provider='test',
            results=[
                SearchResult(
                    title='测试新闻1',
                    url='https://test.com/news/unique_key_test_1',
                    snippet='摘要1',
                    source='测试来源',
                    published_date=datetime.now()
                )
            ]
        )
        
        saved1 = self.db.save_news_intel(self.test_code, '测试股票', 'latest_news', '测试查询', news1)
        self.assertGreater(saved1, 0, "应该成功保存新闻")
        
        news2 = SearchResponse(
            query='测试查询',
            provider='test',
            results=[
                SearchResult(
                    title='测试新闻1更新',
                    url='https://test.com/news/unique_key_test_1',
                    snippet='摘要1更新',
                    source='测试来源',
                    published_date=datetime.now()
                )
            ]
        )
        
        saved2 = self.db.save_news_intel(self.test_code, '测试股票', 'latest_news', '测试查询', news2)
        
        recent = self.db.get_recent_news(self.test_code, days=1, limit=10)
        filtered = [n for n in recent if n.url == 'https://test.com/news/unique_key_test_1']
        self.assertEqual(len(filtered), 1, "相同URL应该只有一条记录")
        self.assertEqual(filtered[0].title, '测试新闻1更新', "标题应该更新")


class TestAnalysisHistoryCRUD(unittest.TestCase):
    """测试分析历史 CRUD 操作"""
    
    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
        cls.db = DatabaseManager.get_instance()
    
    def test_save_and_query_analysis(self):
        """测试保存和查询分析历史"""
        from dataclasses import dataclass
        
        @dataclass
        class MockResult:
            code: str = 'TEST99'
            name: str = '测试股票'
            sentiment_score: int = 80
            operation_advice: str = '买入'
            trend_prediction: str = '上涨'
            analysis_summary: str = '测试摘要'
            
            def to_dict(self):
                return {
                    'code': self.code,
                    'name': self.name,
                    'sentiment_score': self.sentiment_score,
                    'operation_advice': self.operation_advice,
                    'trend_prediction': self.trend_prediction,
                    'analysis_summary': self.analysis_summary,
                }
        
        result = MockResult()
        query_id = 'test_query_' + datetime.now().strftime('%Y%m%d%H%M%S')
        
        saved = self.db.save_analysis_history(result, query_id, 'simple', '测试新闻内容')
        self.assertEqual(saved, 1, "应该成功保存分析历史")
        
        history = self.db.get_analysis_history(query_id=query_id)
        self.assertEqual(len(history), 1, "应该能查询到分析历史")
        self.assertEqual(history[0].code, 'TEST99', "股票代码应该正确")


class TestBacktestCRUD(unittest.TestCase):
    """测试回测数据 CRUD 操作"""
    
    @classmethod
    def setUpClass(cls):
        """测试前初始化"""
        Config.reset_instance()
        DatabaseManager.reset_instance()
        cls.db = DatabaseManager.get_instance()
    
    def test_backtest_result_unique_key(self):
        """测试回测结果唯一键"""
        from src.repositories.backtest_repo import BacktestRepository
        
        repo = BacktestRepository(self.db)
        
        result1 = BacktestResult(
            analysis_history_id=999999,
            code='TEST99',
            analysis_date=date.today(),
            eval_window_days=10,
            engine_version='v1',
            eval_status='completed',
            outcome='win',
        )
        
        repo.save_result(result1)
        
        result2 = BacktestResult(
            analysis_history_id=999999,
            code='TEST99',
            analysis_date=date.today(),
            eval_window_days=10,
            engine_version='v1',
            eval_status='completed',
            outcome='loss',
        )
        
        repo.save_result(result2)
        
        results, total = repo.get_results_paginated(code='TEST99', days=30, offset=0, limit=10)
        filtered = [r for r in results if r.analysis_history_id == 999999]
        self.assertLessEqual(len(filtered), 1, "相同唯一键应该只有一条记录")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDorisConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDorisConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestDorisTableStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestStockDailyCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestNewsIntelCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisHistoryCRUD))
    suite.addTests(loader.loadTestsFromTestCase(TestBacktestCRUD))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 60)
    print("Doris 存储层测试")
    print("=" * 60)
    
    result = run_tests()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    sys.exit(0 if result.wasSuccessful() else 1)
