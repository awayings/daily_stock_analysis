-- ===================================
-- Apache Doris 数据库初始化脚本
-- UNIQUE KEY 模型表结构
-- ===================================
-- 
-- 使用方法:
-- mysql -h 10.43.50.254 -P 9030 -u doris -pdoris1234 < init_doris_tables.sql
--
-- 或在 Doris FE Web UI 中执行

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_analysis;

USE stock_analysis;

-- ===================================
-- 1. 股票日线数据表 (stock_daily)
-- ===================================
-- UNIQUE KEY: code, date
-- 分布: HASH(code)
CREATE TABLE IF NOT EXISTS `stock_daily` (
    `code` VARCHAR(10) NOT NULL COMMENT '股票代码',
    `date` DATE NOT NULL COMMENT '交易日期',
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `name` VARCHAR(50) COMMENT '股票中文名称',
    `open` DOUBLE COMMENT '开盘价',
    `high` DOUBLE COMMENT '最高价',
    `low` DOUBLE COMMENT '最低价',
    `close` DOUBLE COMMENT '收盘价',
    `volume` DOUBLE COMMENT '成交量(股)',
    `amount` DOUBLE COMMENT '成交额(元)',
    `pct_chg` DOUBLE COMMENT '涨跌幅(%)',
    `ma5` DOUBLE COMMENT '5日均线',
    `ma10` DOUBLE COMMENT '10日均线',
    `ma20` DOUBLE COMMENT '20日均线',
    `volume_ratio` DOUBLE COMMENT '量比',
    `data_source` VARCHAR(50) COMMENT '数据来源',
    `created_at` DATETIME COMMENT '创建时间',
    `updated_at` DATETIME COMMENT '更新时间'
)
UNIQUE KEY (`code`, `date`)
DISTRIBUTED BY HASH(`code`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 2. 新闻情报表 (news_intel)
-- ===================================
-- UNIQUE KEY: url
-- 分布: HASH(code)
CREATE TABLE IF NOT EXISTS `news_intel` (
    `url` VARCHAR(1000) NOT NULL COMMENT '新闻URL(唯一键)',
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `query_id` VARCHAR(64) COMMENT '查询ID',
    `code` VARCHAR(10) NOT NULL COMMENT '股票代码',
    `name` VARCHAR(50) COMMENT '股票名称',
    `dimension` VARCHAR(32) COMMENT '搜索维度',
    `query` VARCHAR(255) COMMENT '搜索查询',
    `provider` VARCHAR(32) COMMENT '数据提供商',
    `title` VARCHAR(300) NOT NULL COMMENT '新闻标题',
    `snippet` STRING COMMENT '新闻摘要',
    `source` VARCHAR(100) COMMENT '新闻来源',
    `published_date` DATETIME COMMENT '发布时间',
    `fetched_at` DATETIME COMMENT '抓取时间',
    `query_source` VARCHAR(32) COMMENT '查询来源',
    `requester_platform` VARCHAR(20) COMMENT '请求平台',
    `requester_user_id` VARCHAR(64) COMMENT '用户ID',
    `requester_user_name` VARCHAR(64) COMMENT '用户名',
    `requester_chat_id` VARCHAR(64) COMMENT '会话ID',
    `requester_message_id` VARCHAR(64) COMMENT '消息ID',
    `requester_query` VARCHAR(255) COMMENT '原始查询'
)
UNIQUE KEY (`url`)
DISTRIBUTED BY HASH(`url`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 3. 分析历史表 (analysis_history)
-- ===================================
-- UNIQUE KEY: id
-- 分布: HASH(id)
CREATE TABLE IF NOT EXISTS `analysis_history` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `query_id` VARCHAR(64) COMMENT '查询ID',
    `code` VARCHAR(10) NOT NULL COMMENT '股票代码',
    `name` VARCHAR(50) COMMENT '股票名称',
    `report_type` VARCHAR(16) COMMENT '报告类型',
    `sentiment_score` INT COMMENT '情绪分数',
    `operation_advice` VARCHAR(20) COMMENT '操作建议',
    `trend_prediction` VARCHAR(50) COMMENT '趋势预测',
    `analysis_summary` STRING COMMENT '分析摘要',
    `raw_result` STRING COMMENT '原始结果JSON',
    `news_content` STRING COMMENT '新闻内容',
    `context_snapshot` STRING COMMENT '上下文快照JSON',
    `ideal_buy` DOUBLE COMMENT '理想买点',
    `secondary_buy` DOUBLE COMMENT '次级买点',
    `stop_loss` DOUBLE COMMENT '止损价',
    `take_profit` DOUBLE COMMENT '止盈价',
    `created_at` DATETIME COMMENT '创建时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 4. 回测结果表 (backtest_results)
-- ===================================
-- UNIQUE KEY: analysis_history_id, eval_window_days, engine_version
-- 分布: HASH(analysis_history_id)
CREATE TABLE IF NOT EXISTS `backtest_results` (
    `analysis_history_id` INT NOT NULL COMMENT '分析记录ID',
    `eval_window_days` INT NOT NULL DEFAULT 10 COMMENT '评估窗口天数',
    `engine_version` VARCHAR(16) NOT NULL DEFAULT 'v1' COMMENT '引擎版本',
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `code` VARCHAR(10) NOT NULL COMMENT '股票代码',
    `analysis_date` DATE COMMENT '分析日期',
    `eval_status` VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '评估状态',
    `evaluated_at` DATETIME COMMENT '评估时间',
    `operation_advice` VARCHAR(20) COMMENT '操作建议',
    `position_recommendation` VARCHAR(8) COMMENT '仓位建议',
    `start_price` DOUBLE COMMENT '起始价格',
    `end_close` DOUBLE COMMENT '结束价格',
    `max_high` DOUBLE COMMENT '最高价',
    `min_low` DOUBLE COMMENT '最低价',
    `stock_return_pct` DOUBLE COMMENT '股票收益率',
    `direction_expected` VARCHAR(16) COMMENT '预期方向',
    `direction_correct` BOOLEAN COMMENT '方向正确',
    `outcome` VARCHAR(16) COMMENT '结果',
    `stop_loss` DOUBLE COMMENT '止损价',
    `take_profit` DOUBLE COMMENT '止盈价',
    `hit_stop_loss` BOOLEAN COMMENT '触发止损',
    `hit_take_profit` BOOLEAN COMMENT '触发止盈',
    `first_hit` VARCHAR(16) COMMENT '首次触发',
    `first_hit_date` DATE COMMENT '触发日期',
    `first_hit_trading_days` INT COMMENT '交易天数',
    `simulated_entry_price` DOUBLE COMMENT '模拟入场价',
    `simulated_exit_price` DOUBLE COMMENT '模拟出场价',
    `simulated_exit_reason` VARCHAR(24) COMMENT '出场原因',
    `simulated_return_pct` DOUBLE COMMENT '模拟收益率'
)
UNIQUE KEY (`analysis_history_id`, `eval_window_days`, `engine_version`)
DISTRIBUTED BY HASH(`analysis_history_id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 5. 回测汇总表 (backtest_summaries)
-- ===================================
-- UNIQUE KEY: scope, code, eval_window_days, engine_version
-- 分布: HASH(scope, code)
CREATE TABLE IF NOT EXISTS `backtest_summaries` (
    `scope` VARCHAR(16) NOT NULL COMMENT '范围(overall/stock)',
    `code` VARCHAR(16) NOT NULL COMMENT '股票代码(overall时为空)',
    `eval_window_days` INT NOT NULL DEFAULT 10 COMMENT '评估窗口天数',
    `engine_version` VARCHAR(16) NOT NULL DEFAULT 'v1' COMMENT '引擎版本',
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `computed_at` DATETIME COMMENT '计算时间',
    `total_evaluations` INT DEFAULT 0 COMMENT '总评估数',
    `completed_count` INT DEFAULT 0 COMMENT '完成数',
    `insufficient_count` INT DEFAULT 0 COMMENT '数据不足数',
    `long_count` INT DEFAULT 0 COMMENT '做多数',
    `cash_count` INT DEFAULT 0 COMMENT '空仓数',
    `win_count` INT DEFAULT 0 COMMENT '盈利数',
    `loss_count` INT DEFAULT 0 COMMENT '亏损数',
    `neutral_count` INT DEFAULT 0 COMMENT '中性数',
    `direction_accuracy_pct` DOUBLE COMMENT '方向准确率',
    `win_rate_pct` DOUBLE COMMENT '胜率',
    `neutral_rate_pct` DOUBLE COMMENT '中性率',
    `avg_stock_return_pct` DOUBLE COMMENT '平均股票收益',
    `avg_simulated_return_pct` DOUBLE COMMENT '平均模拟收益',
    `stop_loss_trigger_rate` DOUBLE COMMENT '止损触发率',
    `take_profit_trigger_rate` DOUBLE COMMENT '止盈触发率',
    `ambiguous_rate` DOUBLE COMMENT '模糊率',
    `avg_days_to_first_hit` DOUBLE COMMENT '平均触发天数',
    `advice_breakdown_json` STRING COMMENT '建议分布JSON',
    `diagnostics_json` STRING COMMENT '诊断JSON'
)
UNIQUE KEY (`scope`, `code`, `eval_window_days`, `engine_version`)
DISTRIBUTED BY HASH(`scope`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 验证表创建
-- ===================================
SHOW TABLES;

-- 显示表结构
DESC stock_daily;
DESC news_intel;
DESC analysis_history;
DESC backtest_results;
DESC backtest_summaries;
