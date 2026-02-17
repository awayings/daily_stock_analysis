# 投资组合管理模块 - 详细设计文档

**版本：** 1.0.0  
**日期：** 2026-02-17  
**状态：** 草稿

---

## 目录

1. [数据层设计](#1-数据层设计)
2. [后端架构设计](#2-后端架构设计)
3. [前端架构设计](#3-前端架构设计)
4. [API接口规范](#4-api接口规范)
5. [测试策略](#5-测试策略)

---

## 1. 数据层设计

### 1.1 数据库概述

投资组合管理模块使用 Apache Doris 作为数据存储，依据现有 `sql/init_doris_tables.sql` 的建表规范，设计以下四张核心数据表。

### 1.2 表结构设计

#### 1.2.1 portfolios（投资组合表）

```sql
-- ===================================
-- 投资组合表 (portfolios)
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
    `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '软删除标记',
    `deleted_at` DATETIME COMMENT '删除时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);
```

#### 1.2.2 portfolio_holdings（持仓表）

```sql
-- ===================================
-- 持仓表 (portfolio_holdings)
-- ===================================
-- 存储投资组合中的股票持仓信息
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(portfolio_id)
CREATE TABLE IF NOT EXISTS `portfolio_holdings` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '自增主键',
    `portfolio_id` BIGINT NOT NULL COMMENT '组合ID',
    `code` VARCHAR(20) NOT NULL COMMENT '股票代码',
    `name` VARCHAR(100) COMMENT '股票名称',
    `entry_price` DECIMAL(18,4) NOT NULL COMMENT '建仓价格',
    `weight` DECIMAL(5,2) NOT NULL COMMENT '仓位占比(0-100)',
    `shares` DECIMAL(18,4) COMMENT '股数',
    `is_closed` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '平仓标记',
    `close_price` DECIMAL(18,4) COMMENT '平仓价格',
    `close_quantity` DECIMAL(18,4) COMMENT '平仓数量',
    `close_type` VARCHAR(20) COMMENT '平仓类型: full/partial',
    `added_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
    `closed_at` DATETIME COMMENT '平仓时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
)
UNIQUE KEY (`id`)
DISTRIBUTED BY HASH(`portfolio_id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);
```

#### 1.2.3 portfolio_history（历史快照表）

```sql
-- ===================================
-- 历史快照表 (portfolio_history)
-- ===================================
-- 存储每周计算生成的组合收益快照
-- UNIQUE KEY: portfolio_id, snapshot_date
-- DISTRIBUTED BY: HASH(portfolio_id)
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
UNIQUE KEY (`portfolio_id`, `snapshot_date`)
DISTRIBUTED BY HASH(`portfolio_id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);
```

#### 1.2.4 holding_snapshots（持仓快照表）

```sql
-- ===================================
-- 持仓快照表 (holding_snapshots)
-- ===================================
-- 存储每个历史快照时间点的持仓详情
-- UNIQUE KEY: id
-- DISTRIBUTED BY: HASH(history_id)
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
DISTRIBUTED BY HASH(`history_id`) BUCKETS 3
PROPERTIES (
    "replication_allocation" = "tag.location.default: 1"
);
```

### 1.3 数据库部署脚本

```sql
-- ===================================
-- 投资组合管理模块数据库部署脚本
-- ===================================
-- 使用方法:
-- mysql -h <host> -P <port> -u <user> -p<password> < init_portfolio_tables.sql

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_analysis;
USE stock_analysis;

-- 执行上述四张表的建表语句...

-- 验证表创建
SHOW TABLES;

-- 显示表结构
DESC portfolios;
DESC portfolio_holdings;
DESC portfolio_history;
DESC holding_snapshots;
```

### 1.4 ORM 模型定义

在 `src/storage.py` 中添加以下模型类：

```python
# -*- coding: utf-8 -*-
"""
===================================
投资组合模块 - ORM 模型定义
===================================
"""

class Portfolio(SQLITE_BASE):
    """投资组合模型"""
    __tablename__ = 'portfolios'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    initial_capital = Column(Numeric(18, 4))
    currency = Column(String(10), default='CNY')
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PortfolioHolding(SQLITE_BASE):
    """持仓模型"""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id = Column(BigInteger, ForeignKey('portfolios.id'), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100))
    entry_price = Column(Numeric(18, 4), nullable=False)
    weight = Column(Numeric(5, 2), nullable=False)
    shares = Column(Numeric(18, 4))
    is_closed = Column(Boolean, default=False)
    close_price = Column(Numeric(18, 4))
    close_quantity = Column(Numeric(18, 4))
    close_type = Column(String(20))
    added_at = Column(DateTime, default=datetime.now)
    closed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class PortfolioHistory(SQLITE_BASE):
    """历史快照模型"""
    __tablename__ = 'portfolio_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    portfolio_id = Column(BigInteger, ForeignKey('portfolios.id'), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    total_value = Column(Numeric(18, 4))
    unrealized_pnl_pct = Column(Numeric(10, 4))
    unrealized_pnl_amount = Column(Numeric(18, 4))
    realized_pnl_amount = Column(Numeric(18, 4), default=0)
    cumulative_realized_pnl = Column(Numeric(18, 4), default=0)
    total_pnl_pct = Column(Numeric(10, 4))
    total_pnl_amount = Column(Numeric(18, 4))
    active_holdings_count = Column(Integer, default=0)
    closed_holdings_count = Column(Integer, default=0)
    calculation_status = Column(String(20), default='pending')
    error_message = Column(Text)
    calculated_at = Column(DateTime, default=datetime.now)


class HoldingSnapshot(SQLITE_BASE):
    """持仓快照模型"""
    __tablename__ = 'holding_snapshots'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    history_id = Column(BigInteger, ForeignKey('portfolio_history.id'), nullable=False)
    code = Column(String(20), nullable=False)
    name = Column(String(100))
    entry_price = Column(Numeric(18, 4), nullable=False)
    current_price = Column(Numeric(18, 4))
    weight = Column(Numeric(5, 2), nullable=False)
    pnl_pct = Column(Numeric(10, 4))
    weighted_pnl = Column(Numeric(10, 4))
    created_at = Column(DateTime, default=datetime.now)
```

---

## 2. 后端架构设计

### 2.1 模块划分

基于现有项目结构，新增以下模块：

```
src/
├── repositories/
│   ├── __init__.py
│   ├── portfolio_repo.py      # 新增：组合数据访问层
│   └── ...
├── services/
│   ├── __init__.py
│   ├── portfolio_service.py   # 新增：组合业务逻辑层
│   └── ...
api/v1/
├── endpoints/
│   ├── portfolios.py          # 新增：组合API端点
│   └── ...
├── schemas/
│   ├── portfolio.py           # 新增：组合相关Schema
│   └── ...
```

### 2.2 代码修改范围

#### 2.2.1 需修改的现有文件

| 文件路径 | 修改内容 |
|---------|---------|
| `api/v1/router.py` | 添加 portfolios 路由 |
| `src/storage.py` | 添加 Portfolio、PortfolioHolding、PortfolioHistory、HoldingSnapshot 模型 |
| `src/config.py` | 添加组合相关配置项 |
| `src/scheduler.py` | 添加每周计算定时任务 |

#### 2.2.2 需创建的新文件

| 文件路径 | 职责 |
|---------|------|
| `src/repositories/portfolio_repo.py` | 组合数据访问层 |
| `src/services/portfolio_service.py` | 组合业务逻辑层 |
| `api/v1/endpoints/portfolios.py` | 组合API端点 |
| `api/v1/schemas/portfolio.py` | 组合API Schema |

### 2.3 核心业务流程时序图

#### 2.3.1 创建组合流程

```
┌──────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────┐
│  前端    │     │  API层     │     │   Service层     │     │  Repository层   │     │  数据库   │
└────┬─────┘     └──────┬──────┘     └────────┬─────────┘     └────────┬────────┘     └─────┬──────┘
     │                  │                      │                     │                   │
     │ POST /portfolios │                      │                     │                   │
     │─────────────────▶│                      │                     │                   │
     │                  │ CreatePortfolioReq  │                     │                   │
     │                  │─────────────────────▶│                     │                   │
     │                  │                      │ validate_request()  │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │ validate_name()  │
     │                  │                      │                      │─────────────────▶│
     │                  │                      │                      │◀─────────────────│
     │                  │                      │                      │                   │
     │                  │                      │ create_portfolio()  │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │ INSERT portfolios │
     │                  │                      │                      │─────────────────▶│
     │                  │                      │                      │◀─────────────────│
     │                  │                      │                      │                   │
     │                  │                      │ add_holdings()       │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │ INSERT holdings   │
     │                  │                      │                      │─────────────────▶│
     │                  │                      │                      │◀─────────────────│
     │                  │                      │                      │                   │
     │                  │ PortfolioResponse   │                     │                   │
     │                  │◀────────────────────│                     │                   │
     │                  │                      │                     │                   │
     │ 201 Created     │                      │                     │                   │
     │◀────────────────│                      │                     │                   │
```

#### 2.3.2 平仓操作流程

```
┌──────────┐     ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────┐
│  前端    │     │  API层     │     │   Service层     │     │  Repository层   │     │  数据库   │
└────┬─────┘     └──────┬──────┘     └────────┬─────────┘     └────────┬────────┘     └─────┬──────┘
     │                  │                      │                     │                   │
     │ POST /holdings/{id}/closePosition      │                     │                   │
     │─────────────────▶│                      │                     │                   │
     │                  │ ClosePositionReq    │                     │                   │
     │                  │─────────────────────▶│                     │                   │
     │                  │                      │ get_current_price() │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │ get_stock_quote() │
     │                  │                      │                      │─────────────────▶│
     │                  │                      │                      │◀─────────────────│
     │                  │                      │                      │                   │
     │                  │                      │ validate_close()    │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │                   │
     │                  │                      │ calculate_pnl()     │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │                   │
     │                  │                      │ execute_close()     │                   │
     │                  │                      │─────────────────────▶│                   │
     │                  │                      │                      │ UPDATE holding    │
     │                  │                      │                      │─────────────────▶│
     │                  │                      │                      │◀─────────────────│
     │                  │                      │                      │                   │
     │                  │ ClosePositionResp   │                     │                   │
     │                  │◀────────────────────│                     │                   │
     │                  │                      │                     │                   │
     │ 200 OK          │                      │                     │                   │
     │◀────────────────│                      │                     │                   │
```

#### 2.3.3 每周计算流程（定时任务）

```
┌────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌────────────┐
│  Scheduler │     │  PortfolioService│     │  Repository层  │     │  数据库   │
└─────┬──────┘     └────────┬─────────┘     └────────┬────────┘     └─────┬──────┘
      │                     │                       │                   │
      │ Cron: 每周五 18:00  │                       │                   │
      │────────────────────▶│                       │                   │
      │                     │                       │                   │
      │                     │ get_active_portfolios()                    │
      │                     │───────────────────────▶│                   │
      │                     │                       │ SELECT portfolios  │
      │                     │                       │ WHERE is_deleted=0 │
      │                     │                       │─────────────────▶│
      │                     │                       │◀─────────────────│
      │                     │                       │                   │
      │                     │ for each portfolio:  │                   │
      │                     │ ─────────────────────│                   │
      │                     │                       │                   │
      │                     │ get_holdings()       │                   │
      │                     │───────────────────────▶│                   │
      │                     │                       │                   │
      │                     │ get_current_prices() │                   │
      │                     │───────────────────────▶│                   │
      │                     │                       │                   │
      │                     │ calculate_pnl()      │                   │
      │                     │───────────────────────▶│                   │
      │                     │                       │                   │
      │                     │ get_closed_since()   │                   │
      │                     │───────────────────────▶│                   │
      │                     │                       │                   │
      │                     │ save_snapshot()      │                   │
      │                     │───────────────────────▶│                   │
      │                     │                       │ INSERT history    │
      │                     │                       │─────────────────▶│
      │                     │                       │                   │
      │                     │ save_holding_snapshots()                 │
      │                     │───────────────────────▶│                   │
      │                     │                       │                   │
      │                     │◀──────────────────────│                   │
      │                     │                       │                   │
      │ 计算完成            │                       │                   │
      │◀───────────────────┘                       │                   │
```

### 2.4 Repository 层设计

```python
# -*- coding: utf-8 -*-
"""
===================================
投资组合数据访问层
===================================
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, or_, func, select
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, Portfolio, PortfolioHolding, PortfolioHistory, HoldingSnapshot


class PortfolioRepository:
    """投资组合数据访问层"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()
    
    # ==================== Portfolio 操作 ====================
    
    def create(self, name: str, description: Optional[str] = None,
               initial_capital: Optional[Decimal] = None,
               currency: str = 'CNY') -> Portfolio:
        """创建组合"""
        with self.db.get_session() as session:
            portfolio = Portfolio(
                name=name,
                description=description,
                initial_capital=initial_capital,
                currency=currency
            )
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            return portfolio
    
    def get_by_id(self, portfolio_id: int) -> Optional[Portfolio]:
        """根据ID获取组合"""
        with self.db.get_session() as session:
            return session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalar_one_or_none()
    
    def get_by_name(self, name: str, include_deleted: bool = False) -> Optional[Portfolio]:
        """根据名称获取组合"""
        with self.db.get_session() as session:
            conditions = [Portfolio.name == name]
            if not include_deleted:
                conditions.append(Portfolio.is_deleted == False)
            return session.execute(
                select(Portfolio).where(and_(*conditions))
            ).scalar_one_or_none()
    
    def get_list(self, include_deleted: bool = False,
                  page: int = 1, limit: int = 20) -> tuple[List[Portfolio], int]:
        """获取组合列表"""
        with self.db.get_session() as session:
            query = select(Portfolio)
            if not include_deleted:
                query = query.where(Portfolio.is_deleted == False)
            
            # 获取总数
            total = len(session.execute(query).scalars().all())
            
            # 分页
            query = query.offset((page - 1) * limit).limit(limit)
            items = session.execute(query).scalars().all()
            
            return list(items), total
    
    def update(self, portfolio_id: int, **kwargs) -> Optional[Portfolio]:
        """更新组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalar_one_or_none()
            
            if portfolio:
                for key, value in kwargs.items():
                    if hasattr(portfolio, key):
                        setattr(portfolio, key, value)
                session.commit()
                session.refresh(portfolio)
            
            return portfolio
    
    def soft_delete(self, portfolio_id: int) -> bool:
        """软删除组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalar_one_or_none()
            
            if portfolio:
                portfolio.is_deleted = True
                portfolio.deleted_at = datetime.now()
                session.commit()
                return True
            return False
    
    def restore(self, portfolio_id: int) -> bool:
        """恢复已删除组合"""
        with self.db.get_session() as session:
            portfolio = session.execute(
                select(Portfolio).where(Portfolio.id == portfolio_id)
            ).scalar_one_or_none()
            
            if portfolio:
                portfolio.is_deleted = False
                portfolio.deleted_at = None
                session.commit()
                return True
            return False
    
    def count(self, include_deleted: bool = False) -> int:
        """统计组合数量"""
        with self.db.get_session() as session:
            query = select(func.count(Portfolio.id))
            if not include_deleted:
                query = query.where(Portfolio.is_deleted == False)
            return session.execute(query).scalar() or 0
    
    # ==================== Holdings 操作 ====================
    
    def add_holding(self, portfolio_id: int, code: str, name: str,
                    entry_price: Decimal, weight: Decimal,
                    shares: Optional[Decimal] = None) -> PortfolioHolding:
        """添加持仓"""
        with self.db.get_session() as session:
            holding = PortfolioHolding(
                portfolio_id=portfolio_id,
                code=code,
                name=name,
                entry_price=entry_price,
                weight=weight,
                shares=shares
            )
            session.add(holding)
            session.commit()
            session.refresh(holding)
            return holding
    
    def get_holdings(self, portfolio_id: int,
                     include_closed: bool = False) -> List[PortfolioHolding]:
        """获取组合的所有持仓"""
        with self.db.get_session() as session:
            query = select(PortfolioHolding).where(
                PortfolioHolding.portfolio_id == portfolio_id
            )
            if not include_closed:
                query = query.where(PortfolioHolding.is_closed == False)
            return list(session.execute(query).scalars().all())
    
    def get_holding_by_id(self, holding_id: int) -> Optional[PortfolioHolding]:
        """根据ID获取持仓"""
        with self.db.get_session() as session:
            return session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalar_one_or_none()
    
    def update_holding(self, holding_id: int, **kwargs) -> Optional[PortfolioHolding]:
        """更新持仓"""
        with self.db.get_session() as session:
            holding = session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalar_one_or_none()
            
            if holding:
                for key, value in kwargs.items():
                    if hasattr(holding, key):
                        setattr(holding, key, value)
                session.commit()
                session.refresh(holding)
            
            return holding
    
    def close_holding(self, holding_id: int, close_price: Decimal,
                      close_quantity: Decimal, close_type: str) -> Optional[PortfolioHolding]:
        """平仓持仓"""
        with self.db.get_session() as session:
            holding = session.execute(
                select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
            ).scalar_one_or_none()
            
            if holding:
                holding.is_closed = True
                holding.close_price = close_price
                holding.close_quantity = close_quantity
                holding.close_type = close_type
                holding.closed_at = datetime.now()
                session.commit()
                session.refresh(holding)
            
            return holding
    
    def get_closed_holdings_since(self, portfolio_id: int,
                                   since: datetime) -> List[PortfolioHolding]:
        """获取指定时间后平仓的持仓"""
        with self.db.get_session() as session:
            return list(session.execute(
                select(PortfolioHolding).where(
                    and_(
                        PortfolioHolding.portfolio_id == portfolio_id,
                        PortfolioHolding.is_closed == True,
                        PortfolioHolding.closed_at >= since
                    )
                ).scalars().all()
            ))
    
    def count_holdings(self, portfolio_id: int, include_closed: bool = False) -> int:
        """统计持仓数量"""
        with self.db.get_session() as session:
            query = select(func.count(PortfolioHolding.id)).where(
                PortfolioHolding.portfolio_id == portfolio_id
            )
            if not include_closed:
                query = query.where(PortfolioHolding.is_closed == False)
            return session.execute(query).scalar() or 0
    
    # ==================== History 操作 ====================
    
    def save_history(self, portfolio_id: int, snapshot_date: date,
                     data: Dict[str, Any]) -> PortfolioHistory:
        """保存历史快照"""
        with self.db.get_session() as session:
            history = PortfolioHistory(
                portfolio_id=portfolio_id,
                snapshot_date=snapshot_date,
                total_value=data.get('total_value'),
                unrealized_pnl_pct=data.get('unrealized_pnl_pct'),
                unrealized_pnl_amount=data.get('unrealized_pnl_amount'),
                realized_pnl_amount=data.get('realized_pnl_amount', 0),
                cumulative_realized_pnl=data.get('cumulative_realized_pnl', 0),
                total_pnl_pct=data.get('total_pnl_pct'),
                total_pnl_amount=data.get('total_pnl_amount'),
                active_holdings_count=data.get('active_holdings_count', 0),
                closed_holdings_count=data.get('closed_holdings_count', 0),
                calculation_status=data.get('calculation_status', 'success'),
                error_message=data.get('error_message')
            )
            session.add(history)
            session.commit()
            session.refresh(history)
            return history
    
    def get_history(self, portfolio_id: int, start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    page: int = 1, limit: int = 20) -> tuple[List[PortfolioHistory], int]:
        """获取历史快照"""
        with self.db.get_session() as session:
            query = select(PortfolioHistory).where(
                PortfolioHistory.portfolio_id == portfolio_id
            )
            
            if start_date:
                query = query.where(PortfolioHistory.snapshot_date >= start_date)
            if end_date:
                query = query.where(PortfolioHistory.snapshot_date <= end_date)
            
            query = query.order_by(PortfolioHistory.snapshot_date.desc())
            
            # 获取总数
            total = len(session.execute(query).scalars().all())
            
            # 分页
            query = query.offset((page - 1) * limit).limit(limit)
            items = session.execute(query).scalars().all()
            
            return list(items), total
    
    def get_latest_history(self, portfolio_id: int) -> Optional[PortfolioHistory]:
        """获取最新的历史快照"""
        with self.db.get_session() as session:
            return session.execute(
                select(PortfolioHistory)
                .where(PortfolioHistory.portfolio_id == portfolio_id)
                .order_by(PortfolioHistory.snapshot_date.desc())
                .limit(1)
            ).scalar_one_or_none()
    
    # ==================== Holding Snapshots 操作 ====================
    
    def save_holding_snapshots(self, history_id: int,
                                snapshots: List[Dict[str, Any]]) -> List[HoldingSnapshot]:
        """保存持仓快照"""
        with self.db.get_session() as session:
            results = []
            for data in snapshots:
                snapshot = HoldingSnapshot(
                    history_id=history_id,
                    code=data['code'],
                    name=data.get('name'),
                    entry_price=data['entry_price'],
                    current_price=data.get('current_price'),
                    weight=data['weight'],
                    pnl_pct=data.get('pnl_pct'),
                    weighted_pnl=data.get('weighted_pnl')
                )
                session.add(snapshot)
                results.append(snapshot)
            
            session.commit()
            for s in results:
                session.refresh(s)
            
            return results
    
    def get_holding_snapshots(self, history_id: int) -> List[HoldingSnapshot]:
        """获取持仓快照"""
        with self.db.get_session() as session:
            return list(session.execute(
                select(HoldingSnapshot).where(
                    HoldingSnapshot.history_id == history_id
                ).scalars().all()
            ))
```

### 2.5 Service 层设计

```python
# -*- coding: utf-8 -*-
"""
===================================
投资组合业务逻辑层
===================================
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from src.repositories.portfolio_repo import PortfolioRepository
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)


class PortfolioService:
    """投资组合业务逻辑层"""
    
    MAX_PORTFOLIOS = 10
    MAX_HOLDINGS_PER_PORTFOLIO = 50
    
    def __init__(self):
        self.repo = PortfolioRepository()
        self.stock_service = StockService()
    
    # ==================== 组合管理 ====================
    
    def create_portfolio(
        self,
        name: str,
        description: Optional[str] = None,
        initial_capital: Optional[Decimal] = None,
        currency: str = 'CNY',
        holdings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """创建投资组合"""
        # 验证名称唯一性
        existing = self.repo.get_by_name(name)
        if existing:
            raise ValueError("PORTFOLIO_003: 组合名称已存在")
        
        # 验证组合数量限制
        count = self.repo.count()
        if count >= self.MAX_PORTFOLIOS:
            raise ValueError(f"PORTFOLIO_006: 最多创建 {self.MAX_PORTFOLIOS} 个组合")
        
        # 验证并计算仓位占比总和
        total_weight = sum(h.get('weight', 0) for h in (holdings or []))
        if holdings and abs(total_weight - 100) > 0.01:
            raise ValueError("PORTFOLIO_005: 仓位占比总和必须等于100%")
        
        # 创建组合
        portfolio = self.repo.create(
            name=name,
            description=description,
            initial_capital=initial_capital,
            currency=currency
        )
        
        # 添加持仓
        created_holdings = []
        if holdings:
            for h in holdings:
                holding = self.add_holding(
                    portfolio.id,
                    code=h['code'],
                    entry_price=Decimal(str(h['entry_price'])),
                    weight=Decimal(str(h['weight']))
                )
                created_holdings.append(holding)
        
        return self._build_portfolio_response(portfolio, created_holdings)
    
    def add_holding(self, portfolio_id: int, code: str,
                    entry_price: Decimal, weight: Decimal) -> PortfolioHolding:
        """添加持仓"""
        # 验证持仓数量限制
        count = self.repo.count_holdings(portfolio_id)
        if count >= self.MAX_HOLDINGS_PER_PORTFOLIO:
            raise ValueError(f"HOLDING_004: 每组合最多 {self.MAX_HOLDINGS_PER_PORTFOLIO} 个持仓")
        
        # 获取股票名称
        quote = self.stock_service.get_realtime_quote(code)
        name = quote.get('stock_name') if quote else code
        
        # 添加持仓
        holding = self.repo.add_holding(
            portfolio_id=portfolio_id,
            code=code,
            name=name,
            entry_price=entry_price,
            weight=weight
        )
        
        return holding
    
    def update_holding(self, holding_id: int, **kwargs) -> Dict[str, Any]:
        """更新持仓"""
        holding = self.repo.update_holding(holding_id, **kwargs)
        if not holding:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")
        
        return self._build_holding_response(holding)
    
    def close_position(
        self,
        holding_id: int,
        price_type: str,
        specified_price: Optional[Decimal] = None,
        quantity_type: str = 'all',
        quantity: Optional[Decimal] = None,
        ratio: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """平仓持仓"""
        # 获取持仓信息
        holding = self.repo.get_holding_by_id(holding_id)
        if not holding:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")
        
        if holding.is_closed:
            raise ValueError("HOLDING_ALREADY_CLOSED: 持仓已平仓")
        
        # 获取平仓价格
        if price_type == 'current':
            quote = self.stock_service.get_realtime_quote(holding.code)
            if not quote:
                raise ValueError("CLOSE_004: 无法获取当前收盘价")
            close_price = Decimal(str(quote['current_price']))
        else:
            if not specified_price or specified_price <= 0:
                raise ValueError("CLOSE_001: 平仓价格必须为正数")
            close_price = specified_price
        
        # 计算平仓数量
        if quantity_type == 'all':
            close_quantity = holding.shares or Decimal('0')
        else:
            if not quantity or quantity <= 0:
                raise ValueError("CLOSE_003: 平仓数量必须大于0")
            if quantity > (holding.shares or Decimal('0')):
                raise ValueError("CLOSE_002: 平仓数量不能超过当前持仓数量")
            close_quantity = quantity
        
        close_type = 'full' if quantity_type == 'all' and close_quantity == holding.shares else 'partial'
        
        # 执行平仓
        updated_holding = self.repo.close_holding(
            holding_id=holding_id,
            close_price=close_price,
            close_quantity=close_quantity,
            close_type=close_type
        )
        
        # 计算盈亏
        pnl_amount = (close_price - holding.entry_price) * close_quantity
        pnl_pct = (close_price / holding.entry_price - 1) * 100 if holding.entry_price > 0 else 0
        
        # 剩余持仓信息
        remaining_shares = (holding.shares or Decimal('0')) - close_quantity
        remaining_weight = (remaining_shares / holding.shares * holding.weight) if holding.shares and holding.shares > 0 else Decimal('0')
        
        return {
            'id': updated_holding.id,
            'portfolio_id': updated_holding.portfolio_id,
            'code': updated_holding.code,
            'name': updated_holding.name,
            'entry_price': float(updated_holding.entry_price),
            'close_price': float(updated_holding.close_price),
            'close_quantity': float(updated_holding.close_quantity),
            'close_type': updated_holding.close_type,
            'is_closed': updated_holding.is_closed,
            'closed_at': updated_holding.closed_at.isoformat() if updated_holding.closed_at else None,
            'pnl': {
                'amount': float(pnl_amount),
                'percentage': float(pnl_pct),
                'realized': True
            },
            'remaining': {
                'shares': float(remaining_shares),
                'weight': float(remaining_weight)
            },
            'weight_rebalance_required': abs(remaining_weight + (holding.weight - updated_holding.weight) - 100) > 0.01
        }
    
    def rebalance_weights(self, portfolio_id: int) -> Dict[str, Any]:
        """平均分配仓位"""
        holdings = self.repo.get_holdings(portfolio_id)
        if not holdings:
            raise ValueError("PORTFOLIO_004: 组合至少需要包含一个持仓")
        
        new_weight = Decimal('100') / len(holdings)
        updated_holdings = []
        
        for h in holdings:
            updated = self.repo.update_holding(
                h.id,
                weight=new_weight.quantize(Decimal('0.01'))
            )
            updated_holdings.append({
                'id': updated.id,
                'code': updated.code,
                'weight': float(updated.weight)
            })
        
        return {
            'portfolio_id': portfolio_id,
            'holdings_count': len(holdings),
            'new_weight_each': float(new_weight.quantize(Decimal('0.01'))),
            'holdings': updated_holdings
        }
    
    # ==================== 每周计算 ====================
    
    def calculate_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """手动触发组合计算"""
        portfolio = self.repo.get_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")
        
        return self._execute_calculation(portfolio)
    
    def calculate_all_portfolios(self) -> Dict[str, Any]:
        """计算所有活跃组合"""
        portfolios = self.repo.get_list(include_deleted=False, limit=1000)[0]
        
        results = []
        for portfolio in portfolios:
            try:
                result = self._execute_calculation(portfolio)
                results.append(result)
            except Exception as e:
                logger.error(f"计算组合 {portfolio.id} 失败: {e}")
                results.append({
                    'portfolio_id': portfolio.id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'total': len(portfolios),
            'success': len([r for r in results if r.get('status') == 'success']),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'results': results
        }
    
    def _execute_calculation(self, portfolio) -> Dict[str, Any]:
        """执行组合计算"""
        # 获取持仓
        holdings = self.repo.get_holdings(portfolio.id, include_closed=True)
        
        # 获取当前价格
        current_prices = {}
        for h in holdings:
            if not h.is_closed:
                quote = self.stock_service.get_realtime_quote(h.code)
                if quote:
                    current_prices[h.code] = Decimal(str(quote['current_price']))
        
        # 获取上次计算的累计已实现盈亏
        last_history = self.repo.get_latest_history(portfolio.id)
        cumulative_realized_pnl = Decimal(str(last_history.cumulative_realized_pnl)) if last_history else Decimal('0')
        
        # 计算浮动盈亏
        unrealized_pnl = Decimal('0')
        active_count = 0
        snapshots = []
        
        for h in holdings:
            if not h.is_closed:
                current_price = current_prices.get(h.code, h.entry_price)
                pnl_pct = (current_price / h.entry_price - 1) * 100 if h.entry_price > 0 else 0
                weighted_pnl = pnl_pct * h.weight / 100
                unrealized_pnl += weighted_pnl
                active_count += 1
                
                snapshots.append({
                    'code': h.code,
                    'name': h.name,
                    'entry_price': float(h.entry_price),
                    'current_price': float(current_price),
                    'weight': float(h.weight),
                    'pnl_pct': float(pnl_pct),
                    'weighted_pnl': float(weighted_pnl)
                })
        
        # 计算本周已实现盈亏
        since = last_history.calculated_at if last_history else datetime.now() - timedelta(days=7)
        closed_holdings = self.repo.get_closed_holdings_since(portfolio.id, since)
        realized_pnl = Decimal('0')
        closed_count = 0
        
        for h in closed_holdings:
            pnl = (h.close_price - h.entry_price) * h.close_quantity
            realized_pnl += pnl
            closed_count += 1
            
            snapshots.append({
                'code': h.code,
                'name': h.name,
                'entry_price': float(h.entry_price),
                'current_price': float(h.close_price),
                'weight': 0,
                'pnl_pct': float((h.close_price / h.entry_price - 1) * 100) if h.entry_price > 0 else 0,
                'weighted_pnl': 0
            })
        
        # 累计已实现盈亏
        cumulative_realized_pnl += realized_pnl
        
        # 计算总盈亏
        initial_capital = Decimal(str(portfolio.initial_capital or 100000))
        unrealized_pnl_amount = unrealized_pct * initial_capital / 100 if initial_capital > 0 else 0
        total_pnl_amount = unrealized_pnl_amount + cumulative_realized_pnl
        total_pnl_pct = total_pnl_amount / initial_capital * 100 if initial_capital > 0 else 0
        total_value = initial_capital + total_pnl_amount
        
        # 保存历史快照
        history = self.repo.save_history(
            portfolio_id=portfolio.id,
            snapshot_date=date.today(),
            data={
                'total_value': float(total_value),
                'unrealized_pnl_pct': float(unrealized_pnl),
                'unrealized_pnl_amount': float(unrealized_pnl_amount),
                'realized_pnl_amount': float(realized_pnl),
                'cumulative_realized_pnl': float(cumulative_realized_pnl),
                'total_pnl_pct': float(total_pnl_pct),
                'total_pnl_amount': float(total_pnl_amount),
                'active_holdings_count': active_count,
                'closed_holdings_count': closed_count,
                'calculation_status': 'success'
            }
        )
        
        # 保存持仓快照
        self.repo.save_holding_snapshots(history.id, snapshots)
        
        return {
            'portfolio_id': portfolio.id,
            'calculated_at': datetime.now().isoformat(),
            'snapshot_date': date.today().isoformat(),
            'total_value': float(total_value),
            'total_pnl_pct': float(total_pnl_pct),
            'holdings_updated': active_count,
            'status': 'success'
        }
    
    # ==================== 辅助方法 ====================
    
    def _build_portfolio_response(self, portfolio, holdings: List) -> Dict[str, Any]:
        """构建组合响应"""
        # 获取当前价格和盈亏
        total_value = 0
        total_pnl = 0
        holdings_data = []
        
        for h in holdings:
            quote = self.stock_service.get_realtime_quote(h.code)
            current_price = Decimal(str(quote['current_price'])) if quote else h.entry_price
            
            pnl_pct = (current_price / h.entry_price - 1) * 100 if h.entry_price > 0 else 0
            weighted_pnl = pnl_pct * h.weight / 100
            total_pnl += weighted_pnl
            
            holdings_data.append({
                'id': h.id,
                'code': h.code,
                'name': h.name,
                'entry_price': float(h.entry_price),
                'current_price': float(current_price),
                'weight': float(h.weight),
                'pnl_pct': float(pnl_pct),
                'weighted_pnl': float(weighted_pnl),
                'is_closed': h.is_closed,
                'added_at': h.added_at.isoformat() if h.added_at else None
            })
        
        return {
            'id': portfolio.id,
            'name': portfolio.name,
            'description': portfolio.description,
            'initial_capital': float(portfolio.initial_capital) if portfolio.initial_capital else None,
            'currency': portfolio.currency,
            'is_deleted': portfolio.is_deleted,
            'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
            'updated_at': portfolio.updated_at.isoformat() if portfolio.updated_at else None,
            'holdings': holdings_data,
            'summary': {
                'total_value': total_value,
                'total_pnl_pct': float(total_pnl),
                'total_pnl_amount': float(total_pnl * (portfolio.initial_capital or 100000) / 100),
                'holdings_count': len(holdings_data)
            }
        }
    
    def _build_holding_response(self, holding) -> Dict[str, Any]:
        """构建持仓响应"""
        quote = self.stock_service.get_realtime_quote(holding.code)
        current_price = Decimal(str(quote['current_price'])) if quote else holding.entry_price
        
        pnl_pct = (current_price / holding.entry_price - 1) * 100 if holding.entry_price > 0 else 0
        
        return {
            'id': holding.id,
            'portfolio_id': holding.portfolio_id,
            'code': holding.code,
            'name': holding.name,
            'entry_price': float(holding.entry_price),
            'current_price': float(current_price),
            'weight': float(holding.weight),
            'shares': float(holding.shares) if holding.shares else None,
            'pnl_pct': float(pnl_pct),
            'is_closed': holding.is_closed,
            'added_at': holding.added_at.isoformat() if holding.added_at else None,
            'updated_at': holding.updated_at.isoformat() if holding.updated_at else None
        }
```

---

## 3. 前端架构设计

### 3.1 代码改动范围

基于现有 `apps/dsa-web/src/` 结构，需进行以下修改：

| 文件路径 | 修改内容 |
|---------|---------|
| `App.tsx` | 添加组合路由和Dock导航项 |
| `api/index.ts` | 添加 portfolio API 客户端 |
| `stores/index.ts` | 添加 portfolioStore |
| `pages/PortfolioListPage.tsx` | 新增：组合列表页 |
| `pages/PortfolioCreatePage.tsx` | 新增：创建组合页 |
| `pages/PortfolioDetailPage.tsx` | 新增：组合详情页 |
| `pages/PortfolioPerformancePage.tsx` | 新增：收益走势页 |
| `components/portfolio/*` | 新增：组合相关组件 |

### 3.2 路由配置

```typescript
// App.tsx 新增路由
const NAV_ITEMS: DockItem[] = [
    // ... 现有项
    {
        key: 'portfolios',
        label: '组合',
        to: '/portfolios',
        icon: PortfolioIcon,
    },
];

// 路由配置
<Route path="/portfolios" element={<PortfolioListPage/>}/>
<Route path="/portfolios/create" element={<PortfolioCreatePage/>}/>
<Route path="/portfolios/:id" element={<PortfolioDetailPage/>}/>
<Route path="/portfolios/:id/edit" element={<PortfolioEditPage/>}/>
<Route path="/portfolios/:id/performance" element={<PortfolioPerformancePage/>}/>
```

### 3.3 API 客户端

```typescript
// apps/dsa-web/src/api/portfolio.ts

import apiClient from './index';
import { AxiosRequestConfig } from 'axios';

export interface Holding {
  id: number;
  code: string;
  name: string;
  entry_price: number;
  current_price: number;
  weight: number;
  pnl_pct: number;
  weighted_pnl: number;
  is_closed: boolean;
  added_at: string;
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  initial_capital?: number;
  currency: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  holdings: Holding[];
  summary: {
    total_value: number;
    total_pnl_pct: number;
    total_pnl_amount: number;
    holdings_count: number;
  };
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  initial_capital?: number;
  currency?: string;
  holdings?: {
    code: string;
    entry_price: number;
    weight: number;
  }[];
}

export interface ClosePositionRequest {
  price_type: 'current' | 'specified';
  specified_price?: number;
  quantity_type: 'all' | 'partial';
  quantity?: number;
  ratio?: number;
}

export interface PortfolioHistoryItem {
  id: number;
  snapshot_date: string;
  total_value: number;
  unrealized_pnl_pct: number;
  unrealized_pnl_amount: number;
  realized_pnl_amount: number;
  cumulative_realized_pnl: number;
  total_pnl_pct: number;
  total_pnl_amount: number;
  active_holdings_count: number;
  closed_holdings_count: number;
  calculation_status: string;
  calculated_at: string;
}

export interface PerformanceData {
  portfolio_id: number;
  view_mode: string;
  date_range: {
    start: string;
    end: string;
  };
  data_points: {
    date: string;
    total_value: number;
    unrealized_pnl_pct: number;
    unrealized_pnl_amount: number;
    realized_pnl_amount: number;
    cumulative_realized_pnl: number;
    total_pnl_pct: number;
    holdings: Record<string, { pnl_pct: number; weighted_pnl: number }>;
  }[];
  statistics: {
    total_return_pct: number;
    unrealized_return_pct: number;
    realized_return_pct: number;
    max_drawdown_pct: number;
    best_day: { date: string; pnl_pct: number };
    worst_day: { date: string; pnl_pct: number };
  };
}

const portfolioApi = {
  // 组合管理
  create: (data: CreatePortfolioRequest) =>
    apiClient.post<Portfolio>('/portfolios', data),
  
  list: (params?: { include_deleted?: boolean; page?: number; limit?: number }) =>
    apiClient.get<{ items: Portfolio[]; total: number; page: number; limit: number }>(
      '/portfolios',
      { params }
    ),
  
  get: (id: number) =>
    apiClient.get<Portfolio>(`/portfolios/${id}`),
  
  update: (id: number, data: Partial<CreatePortfolioRequest>) =>
    apiClient.put<Portfolio>(`/portfolios/${id}`, data),
  
  delete: (id: number, params?: { delete_history?: boolean }) =>
    apiClient.delete<{ id: number; is_deleted: boolean }>(`/portfolios/${id}`, { params }),
  
  restore: (id: number) =>
    apiClient.post<Portfolio>(`/portfolios/${id}/restore`),
  
  // 持仓管理
  addHolding: (portfolioId: number, data: { code: string; entry_price: number; weight: number }) =>
    apiClient.post<Holding>(`/portfolios/${portfolioId}/holdings`, data),
  
  updateHolding: (portfolioId: number, holdingId: number, data: { entry_price?: number; weight?: number }) =>
    apiClient.put<Holding>(`/portfolios/${portfolioId}/holdings/${holdingId}`, data),
  
  closePosition: (portfolioId: number, holdingId: number, data: ClosePositionRequest) =>
    apiClient.post<any>(`/portfolios/${portfolioId}/holdings/${holdingId}/closePosition`, data),
  
  batchAddHoldings: (
    portfolioId: number,
    data: { holdings: { code: string; entry_price: number; weight: number }[]; rebalance_mode?: string }
  ) =>
    apiClient.post<{ added_count: number; holdings: Holding[] }>(
      `/portfolios/${portfolioId}/holdings/batch`,
      data
    ),
  
  rebalance: (portfolioId: number) =>
    apiClient.post<{ portfolio_id: number; holdings_count: number; new_weight_each: number }>(
      `/portfolios/${portfolioId}/holdings/rebalance`
    ),
  
  // 计算
  calculate: (portfolioId: number) =>
    apiClient.post<{ portfolio_id: number; status: string }>(`/portfolios/${portfolioId}/calculate`),
  
  // 历史与收益
  getHistory: (
    portfolioId: number,
    params?: { start_date?: string; end_date?: string; page?: number; limit?: number }
  ) =>
    apiClient.get<{ items: PortfolioHistoryItem[]; total: number }>(
      `/portfolios/${portfolioId}/history`,
      { params }
    ),
  
  getPerformance: (
    portfolioId: number,
    params?: { start_date?: string; end_date?: string; view_mode?: string }
  ) =>
    apiClient.get<PerformanceData>(`/portfolios/${portfolioId}/performance`, { params }),
  
  export: (
    portfolioId: number,
    params?: { format?: 'csv' | 'json'; scope?: string; start_date?: string; end_date?: string }
  ) =>
    apiClient.get(`/portfolios/${portfolioId}/export`, { params, responseType: 'blob' as AxiosRequestConfig['responseType'] }),
};

export default portfolioApi;
```

### 3.4 状态管理

```typescript
// apps/dsa-web/src/stores/portfolioStore.ts

import { create } from 'zustand';
import portfolioApi, { Portfolio, PortfolioHistoryItem, PerformanceData } from '../api/portfolio';

interface PortfolioState {
  portfolios: Portfolio[];
  currentPortfolio: Portfolio | null;
  history: PortfolioHistoryItem[];
  performance: PerformanceData | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchPortfolios: (params?: { include_deleted?: boolean }) => Promise<void>;
  fetchPortfolio: (id: number) => Promise<void>;
  createPortfolio: (data: any) => Promise<Portfolio>;
  updatePortfolio: (id: number, data: any) => Promise<void>;
  deletePortfolio: (id: number) => Promise<void>;
  restorePortfolio: (id: number) => Promise<void>;
  
  addHolding: (portfolioId: number, data: any) => Promise<void>;
  updateHolding: (portfolioId: number, holdingId: number, data: any) => Promise<void>;
  closePosition: (portfolioId: number, holdingId: number, data: any) => Promise<void>;
  rebalanceHoldings: (portfolioId: number) => Promise<void>;
  
  calculatePortfolio: (portfolioId: number) => Promise<void>;
  fetchHistory: (portfolioId: number, params?: any) => Promise<void>;
  fetchPerformance: (portfolioId: number, params?: any) => Promise<void>;
  
  clearError: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set, get) => ({
  portfolios: [],
  currentPortfolio: null,
  history: [],
  performance: null,
  isLoading: false,
  error: null,
  
  fetchPortfolios: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.list(params);
      set({ portfolios: response.data.items, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  
  fetchPortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.get(id);
      set({ currentPortfolio: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  
  createPortfolio: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.create(data);
      set(state => ({
        portfolios: [...state.portfolios, response.data],
        isLoading: false
      }));
      return response.data;
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  updatePortfolio: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.update(id, data);
      set(state => ({
        portfolios: state.portfolios.map(p => p.id === id ? response.data : p),
        currentPortfolio: state.currentPortfolio?.id === id ? response.data : state.currentPortfolio,
        isLoading: false
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  deletePortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      await portfolioApi.delete(id);
      set(state => ({
        portfolios: state.portfolios.filter(p => p.id !== id),
        isLoading: false
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  restorePortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.restore(id);
      set(state => ({
        portfolios: [...state.portfolios, response.data],
        isLoading: false
      }));
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  addHolding: async (portfolioId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.addHolding(portfolioId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: [...currentPortfolio.holdings, response.data]
          },
          isLoading: false
        });
      }
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  updateHolding: async (portfolioId, holdingId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.updateHolding(portfolioId, holdingId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: currentPortfolio.holdings.map(h => h.id === holdingId ? response.data : h)
          },
          isLoading: false
        });
      }
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  closePosition: async (portfolioId, holdingId, data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.closePosition(portfolioId, holdingId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: currentPortfolio.holdings.map(h => 
              h.id === holdingId ? { ...h, ...response.data } : h
            )
          },
          isLoading: false
        });
      }
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  rebalanceHoldings: async (portfolioId) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.rebalance(portfolioId);
      // 重新获取组合详情以更新持仓
      await get().fetchPortfolio(portfolioId);
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  calculatePortfolio: async (portfolioId) => {
    set({ isLoading: true, error: null });
    try {
      await portfolioApi.calculate(portfolioId);
      set({ isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
  
  fetchHistory: async (portfolioId, params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.getHistory(portfolioId, params);
      set({ history: response.data.items, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  
  fetchPerformance: async (portfolioId, params) => {
    set({ isLoading: true, error: null });
    try {
      const response = await portfolioApi.getPerformance(portfolioId, params);
      set({ performance: response.data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },
  
  clearError: () => set({ error: null }),
}));
```

### 3.5 前端组件结构

```
components/portfolio/
├── PortfolioCard.tsx          # 组合卡片组件
├── PortfolioList.tsx          # 组合列表组件
├── HoldingTable.tsx           # 持仓表格组件
├── AddHoldingModal.tsx        # 添加持仓弹窗
├── ClosePositionModal.tsx    # 平仓弹窗
├── DeleteConfirmModal.tsx     # 删除确认弹窗
├── RebalanceConfirmModal.tsx  # 重新平衡确认弹窗
├── ImportHoldingsModal.tsx    # 批量导入弹窗
├── PerformanceChart.tsx       # 收益走势图
├── WeightDistribution.tsx     # 仓位分布图
├── PnlBadge.tsx              # 盈亏徽章
├── SummaryCard.tsx            # 摘要卡片
└── index.ts                  # 导出入口
```

---

## 4. API接口规范

### 4.1 接口列表

| 方法 | 端点 | 描述 |
|-----|------|------|
| POST | /api/v1/portfolios | 创建组合 |
| GET | /api/v1/portfolios | 获取组合列表 |
| GET | /api/v1/portfolios/{id} | 获取组合详情 |
| PUT | /api/v1/portfolios/{id} | 更新组合信息 |
| DELETE | /api/v1/portfolios/{id} | 删除组合 |
| POST | /api/v1/portfolios/{id}/restore | 恢复已删除组合 |
| POST | /api/v1/portfolios/{id}/holdings | 添加持仓 |
| PUT | /api/v1/portfolios/{id}/holdings/{holding_id} | 更新持仓 |
| POST | /api/v1/portfolios/{id}/holdings/{holding_id}/closePosition | 平仓持仓 |
| POST | /api/v1/portfolios/{id}/holdings/batch | 批量添加持仓 |
| POST | /api/v1/portfolios/{id}/holdings/rebalance | 平均分配仓位 |
| POST | /api/v1/portfolios/{id}/calculate | 触发计算 |
| GET | /api/v1/portfolios/{id}/history | 获取历史记录 |
| GET | /api/v1/portfolios/{id}/performance | 获取收益走势数据 |
| GET | /api/v1/portfolios/{id}/export | 导出数据 |

### 4.2 请求/响应格式

#### 4.2.1 创建组合

**请求：**
```json
POST /api/v1/portfolios
{
  "name": "科技成长组合",
  "description": "高成长科技股组合",
  "initial_capital": 100000.00,
  "currency": "CNY",
  "holdings": [
    {
      "code": "600519",
      "entry_price": 1800.00,
      "weight": 50.00
    },
    {
      "code": "00700",
      "entry_price": 350.00,
      "weight": 50.00
    }
  ]
}
```

**响应（201）：**
```json
{
  "id": 1,
  "name": "科技成长组合",
  "description": "高成长科技股组合",
  "initial_capital": 100000.00,
  "currency": "CNY",
  "is_deleted": false,
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z",
  "holdings": [
    {
      "id": 1,
      "code": "600519",
      "name": "贵州茅台",
      "entry_price": 1800.00,
      "current_price": 1850.00,
      "weight": 50.00,
      "pnl_pct": 2.78,
      "weighted_pnl": 1.39,
      "is_closed": false,
      "added_at": "2026-02-17T10:00:00Z"
    }
  ],
  "summary": {
    "total_value": 102780.00,
    "total_pnl_pct": 2.78,
    "total_pnl_amount": 2780.00,
    "holdings_count": 2
  }
}
```

#### 4.2.2 平仓持仓

**请求：**
```json
POST /api/v1/portfolios/1/holdings/1/closePosition
{
  "price_type": "current",
  "specified_price": null,
  "quantity_type": "all",
  "quantity": null,
  "ratio": null
}
```

**响应（200）：**
```json
{
  "id": 1,
  "portfolio_id": 1,
  "code": "600519",
  "name": "贵州茅台",
  "entry_price": 1800.00,
  "close_price": 1850.00,
  "close_quantity": 100.00,
  "close_type": "full",
  "is_closed": true,
  "closed_at": "2026-02-17T14:00:00Z",
  "pnl": {
    "amount": 5000.00,
    "percentage": 2.78,
    "realized": true
  },
  "remaining": {
    "shares": 0,
    "weight": 0
  }
}
```

### 4.3 错误响应格式

```json
{
  "error": {
    "code": "PORTFOLIO_001",
    "message": "请输入组合名称",
    "details": {
      "field": "name",
      "constraint": "required"
    }
  }
}
```

**错误代码表：**

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| PORTFOLIO_001 | 400 | 组合名称为空 |
| PORTFOLIO_002 | 400 | 名称过长 |
| PORTFOLIO_003 | 400 | 组合名称已存在 |
| PORTFOLIO_004 | 400 | 组合至少需要包含一个持仓 |
| PORTFOLIO_005 | 400 | 仓位占比总和不为100% |
| PORTFOLIO_006 | 400 | 超过最大组合数量限制 |
| PORTFOLIO_NOT_FOUND | 404 | 组合不存在 |
| HOLDING_001 | 400 | 股票代码无效 |
| HOLDING_002 | 400 | 建仓价格为负 |
| HOLDING_003 | 400 | 仓位占比无效 |
| HOLDING_004 | 400 | 超过每组合最大持仓数量 |
| HOLDING_NOT_FOUND | 404 | 持仓不存在 |
| HOLDING_ALREADY_CLOSED | 409 | 持仓已平仓 |
| CLOSE_001 | 400 | 平仓价格必须为正数 |
| CLOSE_002 | 400 | 平仓数量不能超过当前持仓数量 |
| CLOSE_003 | 400 | 平仓数量必须大于0 |
| CLOSE_004 | 400 | 无法获取当前收盘价 |
| SYSTEM_001 | 500 | 数据库错误 |

---

## 5. 测试策略

### 5.1 测试环境

| 环境 | 用途 | 数据库 |
|-----|------|-------|
| 开发环境 | 本地开发调试 | SQLite (本地文件) |
| 测试环境 | 自动化测试 | MySQL (测试容器) |
| 预发布环境 | 集成测试 | Doris (预发布集群) |

### 5.2 测试类型

#### 5.2.1 单元测试

**测试范围：**

| 模块 | 测试类/函数 | 测试内容 |
|-----|------------|---------|
| Repository | PortfolioRepository | CRUD操作、数据验证 |
| Service | PortfolioService | 业务逻辑、边界条件 |
| Service | PnLCalculator | 盈亏计算公式 |
| API | PortfoliosEndpoint | 请求验证、响应格式 |

**测试用例示例：**

```python
# tests/test_portfolio_service.py

import pytest
from decimal import Decimal
from src.services.portfolio_service import PortfolioService
from src.repositories.portfolio_repo import PortfolioRepository


class TestPortfolioService:
    
    @pytest.fixture
    def service(self):
        return PortfolioService()
    
    @pytest.fixture
    def mock_repo(self, mocker):
        return mocker.patch('src.services.portfolio_service.PortfolioRepository')
    
    def test_create_portfolio_success(self, service, mock_repo):
        """测试成功创建组合"""
        mock_repo.get_by_name.return_value = None
        mock_repo.count.return_value = 5
        mock_repo.create.return_value = self._mock_portfolio()
        mock_repo.add_holding.return_value = self._mock_holding()
        
        result = service.create_portfolio(
            name="测试组合",
            description="测试描述",
            holdings=[
                {"code": "600519", "entry_price": 1800, "weight": 50},
                {"code": "00700", "entry_price": 350, "weight": 50}
            ]
        )
        
        assert result['name'] == "测试组合"
        assert len(result['holdings']) == 2
    
    def test_create_portfolio_duplicate_name(self, service, mock_repo):
        """测试重复名称创建失败"""
        mock_repo.get_by_name.return_value = self._mock_portfolio()
        
        with pytest.raises(ValueError) as exc_info:
            service.create_portfolio(name="已存在组合")
        
        assert "PORTFOLIO_003" in str(exc_info.value)
    
    def test_create_portfolio_exceed_limit(self, service, mock_repo):
        """测试超过组合数量限制"""
        mock_repo.get_by_name.return_value = None
        mock_repo.count.return_value = 10  # 已达上限
        
        with pytest.raises(ValueError) as exc_info:
            service.create_portfolio(name="新组合")
        
        assert "PORTFOLIO_006" in str(exc_info.value)
    
    def test_create_portfolio_invalid_weights(self, service, mock_repo):
        """测试仓位占比不正确"""
        mock_repo.get_by_name.return_value = None
        mock_repo.count.return_value = 5
        
        with pytest.raises(ValueError) as exc_info:
            service.create_portfolio(
                name="测试组合",
                holdings=[
                    {"code": "600519", "entry_price": 1800, "weight": 30},
                    {"code": "00700", "entry_price": 350, "weight": 50}
                ]
            )
        
        assert "PORTFOLIO_005" in str(exc_info.value)
    
    def test_close_position_all(self, service, mock_repo):
        """测试全部平仓"""
        mock_repo.get_holding_by_id.return_value = self._mock_holding(
            shares=Decimal('100'), entry_price=Decimal('1800')
        )
        mock_repo.update_holding.return_value = self._mock_holding(
            is_closed=True, close_price=Decimal('1850')
        )
        
        result = service.close_position(
            holding_id=1,
            price_type='current',
            quantity_type='all'
        )
        
        assert result['is_closed'] == True
        assert result['close_type'] == 'full'
        assert result['pnl']['realized'] == True
    
    def test_close_position_partial(self, service, mock_repo):
        """测试部分平仓"""
        mock_repo.get_holding_by_id.return_value = self._mock_holding(
            shares=Decimal('100'), entry_price=Decimal('1800'), weight=Decimal('50')
        )
        mock_repo.update_holding.return_value = self._mock_holding(
            is_closed=False, 
            close_price=Decimal('1850'),
            close_quantity=Decimal('50'),
            shares=Decimal('50'),
            weight=Decimal('25')
        )
        
        result = service.close_position(
            holding_id=1,
            price_type='current',
            quantity_type='partial',
            quantity=Decimal('50')
        )
        
        assert result['is_closed'] == False
        assert result['close_type'] == 'partial'
        assert result['remaining']['shares'] == 50
    
    def test_pnl_calculation(self, service):
        """测试盈亏计算"""
        entry_price = Decimal('100')
        current_price = Decimal('110')
        weight = Decimal('50')
        initial_capital = Decimal('100000')
        
        pnl_pct = (current_price / entry_price - 1) * 100
        weighted_pnl = pnl_pct * weight / 100
        pnl_amount = weighted_pnl * initial_capital / 100
        
        assert pnl_pct == 10
        assert weighted_pnl == 5
        assert pnl_amount == 5000
    
    def _mock_portfolio(self):
        return type('Portfolio', (), {
            'id': 1,
            'name': '测试组合',
            'description': '测试描述',
            'initial_capital': Decimal('100000'),
            'currency': 'CNY',
            'is_deleted': False,
            'created_at': None,
            'updated_at': None
        })()
    
    def _mock_holding(self, **kwargs):
        defaults = {
            'id': 1,
            'portfolio_id': 1,
            'code': '600519',
            'name': '贵州茅台',
            'entry_price': Decimal('1800'),
            'weight': Decimal('50'),
            'shares': Decimal('100'),
            'is_closed': False,
            'close_price': None,
            'close_quantity': None,
            'close_type': None,
            'added_at': None
        }
        defaults.update(kwargs)
        return type('Holding', (), defaults)()
```

#### 5.2.2 集成测试

```python
# tests/test_portfolio_api.py

import pytest
from fastapi.testclient import TestClient
from api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestPortfolioAPI:
    
    def test_create_portfolio(self, client):
        """测试创建组合API"""
        response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "测试组合",
                "description": "测试描述",
                "initial_capital": 100000,
                "holdings": [
                    {"code": "600519", "entry_price": 1800, "weight": 100}
                ]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == "测试组合"
        assert len(data['holdings']) == 1
    
    def test_get_portfolios(self, client):
        """测试获取组合列表"""
        response = client.get("/api/v1/portfolios")
        
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
    
    def test_get_portfolio_not_found(self, client):
        """测试获取不存在的组合"""
        response = client.get("/api/v1/portfolios/99999")
        
        assert response.status_code == 404
    
    def test_close_position_invalid_quantity(self, client):
        """测试平仓数量无效"""
        # 先创建一个组合和持仓
        create_response = client.post(
            "/api/v1/portfolios",
            json={"name": "测试组合", "holdings": [{"code": "600519", "entry_price": 1800, "weight": 100}]}
        )
        portfolio_id = create_response.json()['id']
        holding_id = create_response.json()['holdings'][0]['id']
        
        # 尝试平仓数量超过持仓
        response = client.post(
            f"/api/v1/portfolios/{portfolio_id}/holdings/{holding_id}/closePosition",
            json={
                "price_type": "specified",
                "specified_price": 1900,
                "quantity_type": "partial",
                "quantity": 999  # 超过持仓数量
            }
        )
        
        assert response.status_code == 400
        assert "CLOSE_002" in response.json()['error']['code']
```

#### 5.2.3 E2E测试（前端）

```typescript
// tests/e2e/portfolio.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Portfolio Management', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/portfolios');
  });
  
  test('create portfolio with holdings', async ({ page }) => {
    // 点击新建组合按钮
    await page.click('[data-testid="create-portfolio-btn"]');
    
    // 填写组合信息
    await page.fill('[data-testid="portfolio-name"]', '科技成长组合');
    await page.fill('[data-testid="portfolio-description"]', '测试组合');
    await page.fill('[data-testid="initial-capital"]', '100000');
    
    // 添加持仓
    await page.click('[data-testid="add-holding-btn"]');
    await page.fill('[data-testid="stock-search"]', '600519');
    await page.click('[data-testid="stock-result-0"]');
    await page.fill('[data-testid="entry-price"]', '1800');
    await page.fill('[data-testid="weight"]', '100');
    await page.click('[data-testid="add-holding-confirm"]');
    
    // 提交
    await page.click('[data-testid="submit-btn"]');
    
    // 验证成功
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
    await expect(page.locator('[data-testid="portfolio-name"]')).toContainText('科技成长组合');
  });
  
  test('close position', async ({ page }) => {
    // 进入组合详情
    await page.click('[data-testid="portfolio-card"] >> nth=0');
    
    // 点击平仓按钮
    await page.click('[data-testid="close-position-btn"] >> nth=0');
    
    // 确认平仓信息
    await page.click('[data-testid="price-type-current"]');
    await page.click('[data-testid="quantity-type-all"]');
    
    // 确认平仓
    await page.click('[data-testid="confirm-close-btn"]');
    
    // 验证成功
    await expect(page.locator('[data-testid="toast-success"]')).toBeVisible();
  });
  
  test('view performance chart', async ({ page }) => {
    // 进入组合详情
    await page.click('[data-testid="portfolio-card"] >> nth=0');
    
    // 切换到收益走势标签
    await page.click('[data-testid="tab-performance"]');
    
    // 验证图表渲染
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
    
    // 验证统计数据
    await expect(page.locator('[data-testid="stat-total-return"]')).toBeVisible();
  });
});
```

### 5.3 测试数据准备

```python
# tests/fixtures/portfolio.py

import pytest
from decimal import Decimal


@pytest.fixture
def sample_portfolio_data():
    """示例组合数据"""
    return {
        "name": "测试科技组合",
        "description": "用于测试的科技股组合",
        "initial_capital": Decimal("100000"),
        "currency": "CNY"
    }


@pytest.fixture
def sample_holdings_data():
    """示例持仓数据"""
    return [
        {
            "code": "600519",
            "name": "贵州茅台",
            "entry_price": Decimal("1800.00"),
            "weight": Decimal("50.00"),
            "shares": Decimal("100")
        },
        {
            "code": "00700",
            "name": "腾讯控股",
            "entry_price": Decimal("350.00"),
            "weight": Decimal("30.00"),
            "shares": Decimal("200")
        },
        {
            "code": "AAPL",
            "name": "苹果公司",
            "entry_price": Decimal("180.00"),
            "weight": Decimal("20.00"),
            "shares": Decimal("50")
        }
    ]


@pytest.fixture
def sample_history_data():
    """示例历史数据"""
    return [
        {
            "snapshot_date": "2026-02-14",
            "total_value": 102500.00,
            "unrealized_pnl_pct": 2.00,
            "unrealized_pnl_amount": 2000.00,
            "realized_pnl_amount": 500.00,
            "cumulative_realized_pnl": 1500.00,
            "total_pnl_pct": 3.50,
            "total_pnl_amount": 3500.00,
            "active_holdings_count": 3,
            "closed_holdings_count": 0,
            "calculation_status": "success"
        },
        {
            "snapshot_date": "2026-02-07",
            "total_value": 99000.00,
            "unrealized_pnl_pct": -1.00,
            "unrealized_pnl_amount": -1000.00,
            "realized_pnl_amount": 1000.00,
            "cumulative_realized_pnl": 1000.00,
            "total_pnl_pct": 0.00,
            "total_pnl_amount": 0.00,
            "active_holdings_count": 3,
            "closed_holdings_count": 1,
            "calculation_status": "success"
        }
    ]
```

### 5.4 测试覆盖矩阵

| 功能点 | 需求ID | 测试类型 | 测试用例数 | 优先级 |
|-------|--------|---------|-----------|--------|
| 创建组合 | FR-PM-001 | 单元/集成 | 5 | P0 |
| 手动添加持仓 | FR-PM-002 | 单元/集成 | 4 | P0 |
| 批量导入持仓 | FR-PM-003 | 单元/集成 | 3 | P1 |
| 平均分配仓位 | FR-PM-004 | 单元/集成 | 2 | P1 |
| 编辑组合 | FR-PM-005 | 单元/集成 | 3 | P0 |
| 平仓持仓 | FR-PM-005-1 | 单元/集成 | 5 | P0 |
| 部分平仓 | FR-PM-005-2 | 单元/集成 | 4 | P1 |
| 软删除组合 | FR-PM-006 | 单元/集成 | 2 | P1 |
| 恢复组合 | FR-PM-007 | 单元/集成 | 2 | P2 |
| 实时盈亏计算 | FR-PC-001 | 单元 | 6 | P0 |
| 每周自动计算 | FR-PC-002 | 集成 | 3 | P0 |
| 手动触发计算 | FR-PC-003 | 集成 | 2 | P2 |
| 组合历史记录 | FR-HD-001 | 单元/集成 | 3 | P0 |
| 历史查询 | FR-HD-002 | 集成 | 2 | P1 |
| 收益走势图 | FR-VZ-001 | E2E | 4 | P1 |
| 统计面板 | FR-VZ-002 | E2E | 2 | P2 |
| 导出组合数据 | FR-DE-001 | 集成 | 3 | P2 |

### 5.5 通过标准

| 指标 | 目标值 |
|-----|-------|
| 单元测试覆盖率 | ≥ 80% |
| 集成测试覆盖率 | ≥ 70% |
| E2E测试覆盖率 | 核心流程全覆盖 |
| 所有测试通过率 | 100% |
| 代码规范检查 | 通过 (flake8, mypy) |

---

## 附录A：修订历史

| 版本 | 日期 | 作者 | 变更内容 |
|-----|------|------|---------|
| 1.0.0 | 2026-02-17 | 系统 | 初始版本 |

## 附录B：参考文档

- [需求规格说明书](portfolio_requirements.md)
- [功能场景描述](portfolio_scenarios.md)
- [界面设计规范](portfolio_ui_design.md)
- [现有数据库ERD](../database_erd.md)
- [API规范](../architecture/api_spec.json)
