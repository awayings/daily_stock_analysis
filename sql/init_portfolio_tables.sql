-- ===================================
-- 投资组合管理模块 - Doris 数据库脚本
-- UNIQUE KEY 模型表结构
-- ===================================
--
-- 使用方法:
-- mysql -h <host> -P 9030 -u <user> -p<password> < init_portfolio_tables.sql
--
-- 或在 Doris FE Web UI 中执行

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_analysis;

USE stock_analysis;

-- 删除旧表（如果存在）
DROP TABLE IF EXISTS `holding_snapshots`;
DROP TABLE IF EXISTS `portfolio_history`;
DROP TABLE IF EXISTS `portfolio_holdings`;
DROP TABLE IF EXISTS `portfolios`;

-- ===================================
-- 1. 投资组合表 (portfolios)
-- ===================================
-- 存储投资组合的基本信息
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(id)
CREATE TABLE IF NOT EXISTS `portfolios` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `name` VARCHAR(100) NOT NULL COMMENT '组合名称',
    `description` TEXT COMMENT '组合描述',
    `initial_capital` DECIMAL(18,4) COMMENT '初始投资金额',
    `currency` VARCHAR(10) NOT NULL DEFAULT 'CNY' COMMENT '货币代码',
    `is_deleted` INT NOT NULL DEFAULT 0 COMMENT '软删除标记',
    `deleted_at` DATETIME COMMENT '删除时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 2. 持仓表 (portfolio_holdings)
-- ===================================
-- 存储投资组合中的股票持仓信息
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(id)
CREATE TABLE IF NOT EXISTS `portfolio_holdings` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `portfolio_id` BIGINT NOT NULL COMMENT '组合ID',
    `code` VARCHAR(20) NOT NULL COMMENT '股票代码',
    `name` VARCHAR(100) COMMENT '股票名称',
    `entry_price` DECIMAL(18,4) NOT NULL COMMENT '建仓价格',
    `last_price` DECIMAL(18,4) NOT NULL COMMENT '上次更新价格',
    `weight` DECIMAL(5,2) NOT NULL COMMENT '仓位占比(0-100)',
    `shares` DECIMAL(18,4) COMMENT '股数',
    `is_closed` INT NOT NULL DEFAULT 0 COMMENT '平仓标记',
    `close_price` DECIMAL(18,4) COMMENT '平仓价格',
    `close_quantity` DECIMAL(18,4) COMMENT '平仓数量',
    `close_type` VARCHAR(20) COMMENT '平仓类型: full/partial',
    `added_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
    `closed_at` DATETIME COMMENT '平仓时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- 持仓表索引
CREATE INDEX IF NOT EXISTS `ix_holdings_portfolio` ON `portfolio_holdings`(`portfolio_id`);
CREATE INDEX IF NOT EXISTS `ix_holdings_code` ON `portfolio_holdings`(`code`);

-- ===================================
-- 3. 历史快照表 (portfolio_history)
-- ===================================
-- 存储每周计算生成的组合收益快照
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(id)
CREATE TABLE IF NOT EXISTS `portfolio_history` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `portfolio_id` BIGINT NOT NULL COMMENT '组合ID',
    `snapshot_date` DATE NOT NULL COMMENT '快照日期',
    `total_value` DECIMAL(18,4) COMMENT '组合总市值',
    `unrealized_pnl_pct` DECIMAL(10,4) COMMENT '浮动盈亏百分比',
    `unrealized_pnl_amount` DECIMAL(18,4) COMMENT '浮动盈亏金额',
    `realized_pnl_amount` DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '本周已实现盈亏金额',
    `cumulative_realized_pnl` DECIMAL(18,4) NOT NULL DEFAULT 0 COMMENT '累计已实现盈亏金额',
    `total_pnl_pct` DECIMAL(10,4) COMMENT '总盈亏百分比',
    `total_pnl_amount` DECIMAL(18,4) COMMENT '总盈亏金额',
    `active_holdings_count` INT NOT NULL DEFAULT 0 COMMENT '活跃持仓数量',
    `closed_holdings_count` INT NOT NULL DEFAULT 0 COMMENT '本周平仓数量',
    `calculation_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: success/partial/failed',
    `error_message` TEXT COMMENT '错误详情',
    `calculated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '计算时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- 历史表索引
CREATE INDEX IF NOT EXISTS `ix_history_portfolio_date` ON `portfolio_history`(`portfolio_id`);

-- ===================================
-- 4. 持仓快照表 (holding_snapshots)
-- ===================================
-- 存储每个历史快照时间点的持仓详情
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(id)
CREATE TABLE IF NOT EXISTS `holding_snapshots` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `history_id` BIGINT NOT NULL COMMENT '历史记录ID',
    `code` VARCHAR(20) NOT NULL COMMENT '股票代码',
    `name` VARCHAR(100) COMMENT '股票名称',
    `entry_price` DECIMAL(18,4) NOT NULL COMMENT '快照时建仓价',
    `current_price` DECIMAL(18,4) COMMENT '快照时当前价',
    `weight` DECIMAL(5,2) NOT NULL COMMENT '快照时仓位占比',
    `pnl_pct` DECIMAL(10,4) COMMENT '盈亏百分比',
    `weighted_pnl` DECIMAL(10,4) COMMENT '加权盈亏贡献',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '快照时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);

-- ===================================
-- 验证表创建
-- =================================--
SHOW TABLES;

-- 显示表结构
DESC portfolios;
DESC portfolio_holdings;
DESC portfolio_history;
DESC holding_snapshots;
