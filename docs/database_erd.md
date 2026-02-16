# 数据库ERD图 (实体关系图)

生成时间: 2026-02-16 10:18:20

## 表结构概览

本系统包含以下5个核心数据表：

| 表名 | 描述 | UNIQUE KEY |
|------|------|------------|
| stock_daily | 股票日线数据 | code + date |
| news_intel | 新闻情报数据 | url |
| analysis_history | 分析历史记录 | id (自增) |
| backtest_results | 回测结果 | analysis_history_id + eval_window_days + engine_version |
| backtest_summaries | 回测汇总 | scope + code + eval_window_days + engine_version |

## 实体关系图 (Mermaid)

```mermaid
erDiagram
    stock_daily {
        VARCHAR code PK "股票代码（如 600519, 000001）"
        DATE date PK "交易日期"
        BIGINT id "自增主键"
        FLOAT open "开盘价"
        FLOAT high "最高价"
        FLOAT low "最低价"
        FLOAT close "收盘价"
        FLOAT volume "成交量（股）"
        FLOAT amount "成交额（元）"
        FLOAT pct_chg "涨跌幅（%）"
        FLOAT ma5 "5日均线"
        FLOAT ma10 "10日均线"
        FLOAT ma20 "20日均线"
        FLOAT volume_ratio "量比"
        VARCHAR data_source "数据来源（如 AkshareFetcher）"
        DATETIME created_at "创建时间"
        DATETIME updated_at "更新时间"
    }
    
    news_intel {
        VARCHAR url PK "新闻URL（唯一键）"
        BIGINT id "自增主键"
        VARCHAR query_id "关联用户查询操作"
        VARCHAR code "股票代码"
        VARCHAR name "股票名称"
        VARCHAR dimension "搜索维度：latest_news/risk_check/earnings/market_analysis/industry"
        VARCHAR query "搜索查询内容"
        VARCHAR provider "数据提供商"
        VARCHAR title "新闻标题"
        TEXT snippet "新闻摘要"
        VARCHAR source "新闻来源"
        DATETIME published_date "发布时间"
        DATETIME fetched_at "入库时间"
        VARCHAR query_source "查询来源：bot/web/cli/system"
        VARCHAR requester_platform "请求平台"
        VARCHAR requester_user_id "用户ID"
        VARCHAR requester_user_name "用户名"
        VARCHAR requester_chat_id "会话ID"
        VARCHAR requester_message_id "消息ID"
        VARCHAR requester_query "原始查询"
    }
    
    analysis_history {
        BIGINT id PK "主键"
        VARCHAR query_id "关联查询链路"
        VARCHAR code "股票代码"
        VARCHAR name "股票名称"
        VARCHAR report_type "报告类型"
        INT sentiment_score "情绪分数"
        VARCHAR operation_advice "操作建议"
        VARCHAR trend_prediction "趋势预测"
        TEXT analysis_summary "分析摘要"
        TEXT raw_result "原始结果JSON"
        TEXT news_content "新闻内容"
        TEXT context_snapshot "上下文快照JSON"
        FLOAT ideal_buy "理想买点（用于回测）"
        FLOAT secondary_buy "次级买点（用于回测）"
        FLOAT stop_loss "止损价（用于回测）"
        FLOAT take_profit "止盈价（用于回测）"
        DATETIME created_at "创建时间"
    }
    
    backtest_results {
        INT analysis_history_id PK "关联分析记录ID"
        INT eval_window_days PK "评估窗口天数"
        VARCHAR engine_version PK "引擎版本"
        BIGINT id "自增主键"
        VARCHAR code "股票代码（冗余字段，便于按股票筛选）"
        DATE analysis_date "分析日期"
        VARCHAR eval_status "评估状态"
        DATETIME evaluated_at "评估时间"
        VARCHAR operation_advice "操作建议快照（避免未来分析字段变化导致回测不可解释）"
        VARCHAR position_recommendation "仓位建议：long/cash"
        FLOAT start_price "起始价格"
        FLOAT end_close "结束价格"
        FLOAT max_high "最高价"
        FLOAT min_low "最低价"
        FLOAT stock_return_pct "股票收益率"
        VARCHAR direction_expected "预期方向：up/down/flat/not_down"
        BOOL direction_correct "方向是否正确"
        VARCHAR outcome "结果：win/loss/neutral"
        FLOAT stop_loss "止损价（仅 long 且配置了止盈/止损时有意义）"
        FLOAT take_profit "止盈价"
        BOOL hit_stop_loss "是否触发止损"
        BOOL hit_take_profit "是否触发止盈"
        VARCHAR first_hit "首次触发：take_profit/stop_loss/ambiguous/neither/not_applicable"
        DATE first_hit_date "首次触发日期"
        INT first_hit_trading_days "首次触发交易天数"
        FLOAT simulated_entry_price "模拟入场价（long-only）"
        FLOAT simulated_exit_price "模拟出场价"
        VARCHAR simulated_exit_reason "出场原因：stop_loss/take_profit/window_end/cash/ambiguous_stop_loss"
        FLOAT simulated_return_pct "模拟收益率"
    }
    
    backtest_summaries {
        VARCHAR scope PK "范围：overall/stock"
        VARCHAR code PK "股票代码（overall时为空）"
        INT eval_window_days PK "评估窗口天数"
        VARCHAR engine_version PK "引擎版本"
        BIGINT id "自增主键"
        DATETIME computed_at "计算时间"
        INT total_evaluations "总评估数"
        INT completed_count "完成数"
        INT insufficient_count "数据不足数"
        INT long_count "做多数"
        INT cash_count "空仓数"
        INT win_count "盈利数"
        INT loss_count "亏损数"
        INT neutral_count "中性数"
        FLOAT direction_accuracy_pct "方向准确率"
        FLOAT win_rate_pct "胜率"
        FLOAT neutral_rate_pct "中性率"
        FLOAT avg_stock_return_pct "平均股票收益"
        FLOAT avg_simulated_return_pct "平均模拟收益"
        FLOAT stop_loss_trigger_rate "止损触发率（仅 long 且配置止盈/止损时统计）"
        FLOAT take_profit_trigger_rate "止盈触发率"
        FLOAT ambiguous_rate "模糊率"
        FLOAT avg_days_to_first_hit "平均触发天数"
        TEXT advice_breakdown_json "建议分布JSON"
        TEXT diagnostics_json "诊断JSON"
    }
    
    analysis_history ||--o{ backtest_results : "has"
    backtest_results ||--o| backtest_summaries : "aggregates to"
```

## 表关系说明

### 1. stock_daily (股票日线数据)
- **UNIQUE KEY**: `code` + `date` (同一股票同一日期只有一条记录)
- **用途**: 存储每日行情数据和技术指标
- **字段说明**:
  - `code`: 股票代码（如 600519, 000001）
  - `date`: 交易日期
  - `open/high/low/close`: OHLC 开高低收价格
  - `volume`: 成交量（股）
  - `amount`: 成交额（元）
  - `pct_chg`: 涨跌幅（%）
  - `ma5/ma10/ma20`: 5/10/20日均线
  - `volume_ratio`: 量比
  - `data_source`: 数据来源（如 AkshareFetcher）

### 2. news_intel (新闻情报)
- **UNIQUE KEY**: `url` (按URL去重)
- **用途**: 存储搜索到的新闻情报
- **字段说明**:
  - `url`: 新闻URL（唯一键）
  - `query_id`: 关联用户查询操作
  - `code/name`: 股票代码/名称
  - `dimension`: 搜索维度（latest_news/risk_check/earnings/market_analysis/industry）
  - `query`: 搜索查询内容
  - `provider`: 数据提供商
  - `title/snippet/source`: 新闻标题/摘要/来源
  - `published_date`: 发布时间
  - `fetched_at`: 入库时间
  - `query_source`: 查询来源（bot/web/cli/system）
  - `requester_*`: 请求者相关信息（平台、用户ID、用户名、会话ID、消息ID、原始查询）

### 3. analysis_history (分析历史)
- **UNIQUE KEY**: `id` (自增)
- **索引**: `code` + `created_at`
- **用途**: 保存每次分析结果
- **字段说明**:
  - `id`: 主键
  - `query_id`: 关联查询链路
  - `code/name`: 股票代码/名称
  - `report_type`: 报告类型
  - `sentiment_score`: 情绪分数
  - `operation_advice`: 操作建议
  - `trend_prediction`: 趋势预测
  - `analysis_summary`: 分析摘要
  - `raw_result`: 原始结果JSON
  - `news_content`: 新闻内容
  - `context_snapshot`: 上下文快照JSON
  - `ideal_buy/secondary_buy`: 理想买点/次级买点（用于回测）
  - `stop_loss/take_profit`: 止损价/止盈价（用于回测）

### 4. backtest_results (回测结果)
- **UNIQUE KEY**: `analysis_history_id` + `eval_window_days` + `engine_version`
- **外键**: `analysis_history_id` -> `analysis_history.id`
- **用途**: 存储单条分析记录的回测结果
- **字段说明**:
  - `analysis_history_id`: 关联分析记录ID
  - `eval_window_days`: 评估窗口天数
  - `engine_version`: 引擎版本
  - `code`: 股票代码（冗余字段，便于按股票筛选）
  - `analysis_date`: 分析日期
  - `eval_status/evaluated_at`: 评估状态/时间
  - `operation_advice`: 操作建议快照（避免未来分析字段变化导致回测不可解释）
  - `position_recommendation`: 仓位建议（long/cash）
  - `start_price/end_close/max_high/min_low`: 价格数据
  - `stock_return_pct`: 股票收益率
  - `direction_expected`: 预期方向（up/down/flat/not_down）
  - `direction_correct`: 方向是否正确
  - `outcome`: 结果（win/loss/neutral）
  - `stop_loss/take_profit`: 止损价/止盈价（仅 long 且配置了止盈/止损时有意义）
  - `hit_stop_loss/hit_take_profit`: 是否触发止损/止盈
  - `first_hit`: 首次触发（take_profit/stop_loss/ambiguous/neither/not_applicable）
  - `first_hit_date/first_hit_trading_days`: 首次触发日期/交易天数
  - `simulated_entry_price/exit_price`: 模拟入场价/出场价（long-only）
  - `simulated_exit_reason`: 出场原因（stop_loss/take_profit/window_end/cash/ambiguous_stop_loss）
  - `simulated_return_pct`: 模拟收益率

### 5. backtest_summaries (回测汇总)
- **UNIQUE KEY**: `scope` + `code` + `eval_window_days` + `engine_version`
- **用途**: 存储按股票或全局的回测汇总指标
- **字段说明**:
  - `scope`: 范围（overall/stock）
  - `code`: 股票代码（overall时为空）
  - `eval_window_days`: 评估窗口天数
  - `engine_version`: 引擎版本
  - `computed_at`: 计算时间
  - `total_evaluations/completed_count/insufficient_count`: 总评估数/完成数/数据不足数
  - `long_count/cash_count`: 做多数/空仓数
  - `win_count/loss_count/neutral_count`: 盈利数/亏损数/中性数
  - `direction_accuracy_pct`: 方向准确率
  - `win_rate_pct/neutral_rate_pct`: 胜率/中性率
  - `avg_stock_return_pct/avg_simulated_return_pct`: 平均股票收益/平均模拟收益
  - `stop_loss_trigger_rate/take_profit_trigger_rate`: 止损触发率/止盈触发率（仅 long 且配置止盈/止损时统计）
  - `ambiguous_rate`: 模糊率
  - `avg_days_to_first_hit`: 平均触发天数
  - `advice_breakdown_json/diagnostics_json`: 建议分布JSON/诊断JSON

## Doris UNIQUE KEY 模型设计

迁移到Doris后，所有表使用UNIQUE KEY模型：

| 表名 | UNIQUE KEY字段 | 分布键(DISTRIBUTED BY) |
|------|----------------|------------------------|
| stock_daily | code, date | HASH(code) |
| news_intel | url | HASH(url) |
| analysis_history | id | HASH(id) |
| backtest_results | analysis_history_id, eval_window_days, engine_version | HASH(analysis_history_id) |
| backtest_summaries | scope, code, eval_window_days, engine_version | HASH(scope) |

## 注意事项

1. **字段顺序**: Doris UNIQUE KEY模型要求主键字段必须在表定义的最前面
2. **id字段处理**: 保留id字段但移至主键字段之后，类型改为BIGINT以支持AUTO_INCREMENT
3. **外键关系**: Doris不支持外键约束，应用层需要维护数据一致性
4. **分布键选择**: 分布键必须是UNIQUE KEY的一部分
5. **分区策略**: 可根据需要添加RANGE分区（如按日期分区）
