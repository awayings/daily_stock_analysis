# 投资组合管理模块 - 界面设计规范

**版本：** 1.0.0  
**设计系统：** 深色终端主题  
**主色调：** 青色 (#00d4ff)

---

## 目录

1. [设计系统概述](#1-设计系统概述)
2. [导航结构](#2-导航结构)
3. [页面设计](#3-页面设计)
4. [组件规范](#4-组件规范)
5. [交互模式](#5-交互模式)
6. [响应式设计](#6-响应式设计)
7. [动画规范](#7-动画规范)

---

## 1. 设计系统概述

### 1.1 色彩规范

```
主色调：
├── 青色（主色）：     #00d4ff
├── 青色暗色：         #00a8cc
└── 青色光晕：         rgba(0, 212, 255, 0.4)

状态色：
├── 成功（绿色）：     #00ff88
├── 警告（琥珀色）：   #ffaa00
├── 危险（红色）：     #ff4466
└── 中性（灰色）：     #606070

背景色：
├── 基础背景：         #08080c
├── 卡片背景：         #0d0d14
├── 浮层背景：         #12121a
└── 悬停背景：         #1a1a24

文字色：
├── 主要文字：         #ffffff
├── 次要文字：         #a0a0b0
└── 弱化文字：         #606070

边框色：
├── 暗色边框：         rgba(255, 255, 255, 0.06)
├── 默认边框：         rgba(255, 255, 255, 0.1)
└── 强调边框：         rgba(0, 212, 255, 0.3)
```

### 1.2 字体规范

```
字体族：'Inter', 'SF Pro Display', system-ui, sans-serif

字体大小：
├── 超小：   11px（标签、徽章）
├── 小：     12px（次要文字）
├── 基础：   14px（正文）
├── 大：     16px（强调）
├── 加大：   18px（标题）
└── 超大：   24px（页面标题）

字体粗细：
├── 常规：   400
├── 中等：   500
├── 半粗：   600
└── 粗体：   700
```

### 1.3 间距规范

```
间距单位（rem）：
├── 0.5:  2px
├── 1:    4px
├── 1.5:  6px
├── 2:    8px
├── 3:    12px
├── 4:    16px
├── 5:    20px
├── 6:    24px
└── 8:    32px
```

### 1.4 圆角规范

```
├── 小：   4px  （徽章、小元素）
├── 中：   8px  （输入框、按钮）
├── 大：   12px （卡片、弹窗）
└── 超大： 16px （Dock项）
```

---

## 2. 导航结构

### 2.1 Dock导航更新

现有Dock导航将新增组合图标：

```
Dock导航项（垂直排列）：
┌─────────────────┐
│  📊 Logo        │  ← 现有
├─────────────────┤
│  🏠 首页        │  ← 现有
│  📋 组合        │  ← 新增
│  📊 回测        │  ← 现有
│  ⚙️ 设置        │  ← 现有
└─────────────────┘
```

### 2.2 组合图标

```tsx
const PortfolioIcon: React.FC<{ active?: boolean }> = ({ active }) => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      strokeWidth={active ? 2 : 1.5}
      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
    />
  </svg>
);
```

### 2.3 路由结构

```
/portfolios                    → 组合列表页
/portfolios/create             → 创建组合页
/portfolios/:id                → 组合详情页
/portfolios/:id/edit           → 编辑组合页
/portfolios/:id/performance    → 收益走势页
```

---

## 3. 页面设计

### 3.1 组合列表页

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 页头                                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ 组合管理                                    [+ 新建组合]            │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ 主内容区                                                                │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                                                                     │ │
│ │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │ │
│ │  │ 组合卡片        │  │ 组合卡片        │  │ 组合卡片        │     │ │
│ │  │                 │  │                 │  │                 │     │ │
│ │  │ 科技成长组合    │  │ 价值投资组合    │  │ 分红收益组合    │     │ │
│ │  │ 5个持仓         │  │ 8个持仓         │  │ 3个持仓         │     │ │
│ │  │ +2.5% 📈        │  │ -1.2% 📉        │  │ +0.8% 📈        │     │ │
│ │  │ ¥102,500        │  │ ¥98,800         │  │ ¥50,400         │     │ │
│ │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │ │
│ │                                                                     │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 空状态（无组合时显示）                                       │   │ │
│ │  │                                                             │   │ │
│ │  │         📊                                                  │   │ │
│ │  │    创建您的第一个投资组合                                   │   │ │
│ │  │    开始追踪您的投资收益                                     │   │ │
│ │  │         [创建组合]                                          │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 组合卡片组件

```html
<div class="portfolio-card glass-card">
  <div class="card-header">
    <div class="card-title">
      <span class="name">科技成长组合</span>
      <span class="badge badge-cyan">5个持仓</span>
    </div>
    <div class="card-actions">
      <button class="btn-icon" title="编辑">
        <svg><!-- 编辑图标 --></svg>
      </button>
      <button class="btn-icon" title="删除">
        <svg><!-- 删除图标 --></svg>
      </button>
    </div>
  </div>
  
  <div class="card-body">
    <div class="pnl-display positive">
      <span class="pnl-value">+2.50%</span>
      <span class="pnl-icon">📈</span>
    </div>
    <div class="value-display">
      <span class="label">总市值</span>
      <span class="value">¥102,500.00</span>
    </div>
  </div>
  
  <div class="card-footer">
    <span class="timestamp">2小时前更新</span>
  </div>
</div>
```

#### CSS样式

```css
.portfolio-card {
  width: 280px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.portfolio-card:hover {
  transform: translateY(-4px);
  border-color: var(--border-accent);
  box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
}

.portfolio-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.portfolio-card .name {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.portfolio-card .pnl-display {
  font-size: 24px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.portfolio-card .pnl-display.positive {
  color: var(--color-success);
}

.portfolio-card .pnl-display.negative {
  color: var(--color-danger);
}

.portfolio-card .value-display .value {
  font-size: 14px;
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
}
```

---

### 3.2 创建组合页

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 页头                                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ ← 返回组合列表                                                      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ 主内容区                                                                │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │                                                                     │ │
│ │  创建新组合                                                         │ │
│ │  ─────────────                                                      │ │
│ │                                                                     │ │
│ │  组合名称 *                                                         │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 请输入组合名称...                                            │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  描述（可选）                                                       │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 添加组合描述...                                              │   │ │
│ │  │                                                             │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  初始资金（可选）                                                   │ │
│ │  ┌──────────────────────┐  ┌──────────────┐                        │ │
│ │  │ 100000.00           │  │ CNY ▼        │                        │ │
│ │  └──────────────────────┘  └──────────────┘                        │ │
│ │                                                                     │ │
│ │  ─────────────                                                      │ │
│ │                                                                     │ │
│ │  添加持仓                                                           │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ [手动选择]  [批量导入]                                      │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 🔍 搜索股票代码或名称...                                     │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  持仓列表                                                           │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 代码   │ 名称         │ 建仓价格  │ 仓位占比 │ 操作        │   │ │
│ │  ├────────┼──────────────┼───────────┼──────────┼─────────────┤   │ │
│ │  │ 600519 │ 贵州茅台     │ 1800.00   │ 50.00%   │ [×]         │   │ │
│ │  │ 00700  │ 腾讯控股     │ 350.00    │ 30.00%   │ [×]         │   │ │
│ │  │ AAPL   │ 苹果公司     │ 180.00    │ 20.00%   │ [×]         │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  仓位汇总                                                           │ │
│ │  ┌─────────────────────────────────────────────────────────────┐   │ │
│ │  │ 仓位占比总和：100.00%  ✓                                     │   │ │
│ │  │ [平均分配]                                                   │   │ │
│ │  └─────────────────────────────────────────────────────────────┘   │ │
│ │                                                                     │ │
│ │  ─────────────                                                      │ │
│ │                                                                     │ │
│ │  [取消]                                  [创建组合]                 │ │
│ │                                                                     │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 添加持仓弹窗

```
┌─────────────────────────────────────────────────────────────┐
│ 添加持仓                                              [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  股票代码 *                                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 🔍 600519                                              │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 📊 600519 - 贵州茅台股份有限公司                       │ │
│  │ 📊 600519.SH - 贵州茅台（上海）                         │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  建仓价格 *                                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ¥ 1800.00                                              │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  仓位占比 *                                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 25.00 %                                                │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│                              [取消]  [添加到组合]           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 批量导入弹窗

```
┌─────────────────────────────────────────────────────────────┐
│ 批量导入持仓                                          [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  上传文件                                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │           📄 拖放CSV文件到此处                          │ │
│  │              或点击选择文件                              │ │
│  │                                                         │ │
│  │           支持格式：.csv                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  文件格式示例                                                │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ code,entry_price,weight                                │ │
│  │ 600519,1800.00,50                                      │ │
│  │ 00700,350.00,30                                        │ │
│  │ AAPL,180.00,20                                         │ │
│  └───────────────────────────────────────────────────────┘ │
│  [下载模板]                                                  │
│                                                             │
│  预览                                                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ✓ 600519  │ 1800.00  │ 50.00%                         │ │
│  │ ✓ 00700   │ 350.00   │ 30.00%                         │ │
│  │ ✗ INVALID │ 180.00   │ 20.00%  │ 代码不存在           │ │
│  │ ⚠ AAPL    │ --       │ 20.00%  │ 缺少价格             │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│                              [取消]  [导入有效数据(3条)]    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 3.3 组合详情页

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 页头                                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ ← 返回        科技成长组合                        [编辑] [⋮]        │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ 主内容区                                                                │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 摘要卡片                                                              ││
│ │ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         ││
│ │ │ 总市值     │ │ 总盈亏     │ │ 持仓数     │ │ 最佳表现   │         ││
│ │ │ ¥102,500   │ │ +2.50%     │ │ 5只股票    │ │ 600519     │         ││
│ │ │            │ │ +¥2,500    │ │            │ │ +5.2%      │         ││
│ │ └────────────┘ └────────────┘ └────────────┘ └────────────┘         ││
│ │                                                                      ││
│ │ 标签页                                                               ││
│ │ ┌──────────────────────────────────────────────────────────────────┐││
│ │ │ [持仓列表]  [收益走势]  [历史记录]                               │││
│ │ └──────────────────────────────────────────────────────────────────┘││
│ │                                                                      ││
│ │ 持仓表格                                                             ││
│ │ ┌──────────────────────────────────────────────────────────────────┐││
│ │ │ 代码  │ 名称           │ 建仓价格  │ 当前价格  │ 占比  │ 盈亏   │││
│ │ ├───────┼────────────────┼───────────┼───────────┼───────┼────────┤││
│ │ │600519 │ 贵州茅台       │ 1800.00   │ 1890.00   │50.00% │+5.00%  │││
│ │ │00700  │ 腾讯控股       │ 350.00    │ 340.00    │30.00% │-2.86%  │││
│ │ │AAPL   │ 苹果公司       │ 180.00    │ 185.00    │20.00% │+2.78%  │││
│ │ └──────────────────────────────────────────────────────────────────┘││
│ │                                                                      ││
│ │ 仓位分布图                                                           ││
│ │ ┌──────────────────────────────────────────────────────────────────┐││
│ │ │                                                                  │││
│ │ │     ████████████████████████████████ 50% 600519 贵州茅台         │││
│ │ │     ████████████████████ 30% 00700 腾讯控股                      │││
│ │ │     ████████████ 20% AAPL 苹果公司                               │││
│ │ │                                                                  │││
│ │ └──────────────────────────────────────────────────────────────────┘││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

#### 持仓表格组件

```html
<div class="holdings-table">
  <table class="w-full text-sm">
    <thead>
      <tr class="bg-elevated text-left">
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">
          代码
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">
          名称
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">
          建仓价格
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">
          当前价格
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">
          占比
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">
          盈亏
        </th>
        <th class="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">
          状态
        </th>
      </tr>
    </thead>
    <tbody>
      <tr class="border-t border-white/5 hover:bg-hover transition-colors">
        <td class="px-3 py-2 font-mono text-cyan text-xs">600519</td>
        <td class="px-3 py-2 text-xs text-white">贵州茅台</td>
        <td class="px-3 py-2 text-xs font-mono text-right text-secondary">¥1,800.00</td>
        <td class="px-3 py-2 text-xs font-mono text-right text-white">¥1,890.00</td>
        <td class="px-3 py-2 text-xs font-mono text-right text-secondary">50.00%</td>
        <td class="px-3 py-2 text-xs font-mono text-right text-success">+5.00%</td>
        <td class="px-3 py-2">
          <span class="badge badge-success">活跃</span>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

---

### 3.4 收益走势页

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 页头                                                                    │
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │ ← 返回        收益走势 - 科技成长组合                   [导出]      │ │
│ └─────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│ 主内容区                                                                │
│ ┌──────────────────────────────────────────────────────────────────────┐│
│ │ 控制栏                                                                ││
│ │ ┌──────────────────────────────────────────────────────────────────┐ ││
│ │ │ 时间范围：[1周] [1月] [3月] [6月] [1年] [自定义]                 │ ││
│ │ │ 视图：[○ 组合总体] [● 各持仓独立]                                │ ││
│ │ └──────────────────────────────────────────────────────────────────┘ ││
│ │                                                                      ││
│ │ 图表区域                                                             ││
│ │ ┌──────────────────────────────────────────────────────────────────┐ ││
│ │ │  +5% ┤                          ╭─────╮                          │ ││
│ │ │      │                        ╭─╯     ╰─╮                        │ ││
│ │ │   0% ┼────────────────────────╯         ╰────────────────────    │ ││
│ │ │  -5% ┤                                                          │ ││
│ │ │      └────────────────────────────────────────────────────────── │ ││
│ │ │       2月1日  2月5日  2月10日 2月15日 2月20日 2月25日            │ ││
│ │ └──────────────────────────────────────────────────────────────────┘ ││
│ │                                                                      ││
│ │ 图例                                                                 ││
│ │ ┌──────────────────────────────────────────────────────────────────┐ ││
│ │ │ ── 组合总体  ── 600519  ── 00700  ── AAPL                       │ ││
│ │ └──────────────────────────────────────────────────────────────────┘ ││
│ │                                                                      ││
│ │ 统计面板                                                             ││
│ │ ┌──────────────────────────────────────────────────────────────────┐ ││
│ │ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │ ││
│ │ │ │ 总收益率    │ │ 最大回撤    │ │ 最佳交易日  │ │ 最差交易日  │  │ ││
│ │ │ │ +2.50%      │ │ -1.20%      │ │ +1.50%      │ │ -0.80%      │  │ ││
│ │ │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │ ││
│ │ └──────────────────────────────────────────────────────────────────┘ ││
│ │                                                                      ││
│ │ 持仓收益分解                                                         ││
│ │ ┌──────────────────────────────────────────────────────────────────┐ ││
│ │ │ 代码    │ 贡献度   │ 收益率   │ 占比   │ 区间收益               │ ││
│ │ ├─────────┼──────────┼──────────┼────────┼────────────────────────┤ ││
│ │ │ 600519  │ +2.50%   │ +5.00%   │ 50.00% │ ████████████           │ ││
│ │ │ 00700   │ -0.86%   │ -2.86%   │ 30.00% │ ███░░░░░░░             │ ││
│ │ │ AAPL    │ +0.56%   │ +2.78%   │ 20.00% │ ██████░░░░░            │ ││
│ │ └──────────────────────────────────────────────────────────────────┘ ││
│ │                                                                      ││
│ └──────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

#### 图表悬停提示

```
┌─────────────────────────────────────┐
│ 2026年2月14日                       │
│ ─────────────────────               │
│ 组合：+2.35%                        │
│                                     │
│ 600519：+4.80%                      │
│ 00700：-1.50%                       │
│ AAPL：+2.20%                        │
│                                     │
│ 总市值：¥102,350                    │
└─────────────────────────────────────┘
```

---

### 3.5 删除确认弹窗

```
┌─────────────────────────────────────────────────────────────┐
│ 删除组合                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚠️  确定要删除"科技成长组合"吗？                            │
│                                                             │
│  此操作将从列表中隐藏该组合，但所有历史数据将被保留。        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ ☐ 同时删除所有历史记录                                 │ │
│  │   （此操作不可恢复）                                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  您可以从设置中恢复已删除的组合。                            │
│                                                             │
│                              [取消]  [删除组合]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 组件规范

### 4.1 摘要卡片

```tsx
interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon?: React.ReactNode;
  className?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon,
  className,
}) => (
  <Card variant="gradient" padding="md" className={className}>
    <div className="flex items-start justify-between">
      <div>
        <span className="label-uppercase">{title}</span>
        <div className={`text-2xl font-bold font-mono mt-1 ${
          trend === 'up' ? 'text-success' : 
          trend === 'down' ? 'text-danger' : 
          'text-white'
        }`}>
          {value}
        </div>
        {subtitle && (
          <span className="text-xs text-muted mt-1">{subtitle}</span>
        )}
      </div>
      {icon && (
        <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center">
          {icon}
        </div>
      )}
    </div>
  </Card>
);
```

### 4.2 盈亏徽章

```tsx
interface PnlBadgeProps {
  value: number;
  showSign?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const PnlBadge: React.FC<PnlBadgeProps> = ({ value, showSign = true, size = 'md' }) => {
  const isPositive = value >= 0;
  const formatted = `${showSign ? (isPositive ? '+' : '') : ''}${value.toFixed(2)}%`;
  
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };
  
  return (
    <span className={`
      inline-flex items-center rounded-md font-mono font-medium
      ${sizeClasses[size]}
      ${isPositive 
        ? 'bg-success/10 text-success border border-success/20' 
        : 'bg-danger/10 text-danger border border-danger/20'
      }
    `}>
      {isPositive ? '↑' : '↓'} {formatted}
    </span>
  );
};
```

### 4.3 仓位占比输入

```tsx
interface WeightInputProps {
  value: number;
  onChange: (value: number) => void;
  total: number;
  disabled?: boolean;
}

const WeightInput: React.FC<WeightInputProps> = ({
  value,
  onChange,
  total,
  disabled,
}) => {
  const isValid = Math.abs(total - 100) < 0.01;
  
  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        disabled={disabled}
        min={0}
        max={100}
        step={0.01}
        className="input-terminal w-20 text-right"
      />
      <span className="text-secondary">%</span>
      {!isValid && (
        <span className="text-xs text-warning">
          总计：{total.toFixed(2)}%
        </span>
      )}
    </div>
  );
};
```

### 4.4 股票搜索

```tsx
interface StockSearchProps {
  onSelect: (stock: StockInfo) => void;
  placeholder?: string;
}

const StockSearch: React.FC<StockSearchProps> = ({ onSelect, placeholder }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<StockInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const debouncedSearch = useDebouncedCallback(async (q: string) => {
    if (q.length < 1) {
      setResults([]);
      return;
    }
    setIsLoading(true);
    try {
      const data = await stockApi.search(q);
      setResults(data);
    } finally {
      setIsLoading(false);
    }
  }, 300);
  
  return (
    <div className="relative">
      <div className="relative">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted">
          {/* 搜索图标 */}
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            debouncedSearch(e.target.value);
          }}
          placeholder={placeholder || "搜索股票..."}
          className="input-terminal pl-10 w-full"
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
          </div>
        )}
      </div>
      
      {results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-elevated border border-white/10 rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
          {results.map((stock) => (
            <button
              key={stock.code}
              onClick={() => {
                onSelect(stock);
                setQuery('');
                setResults([]);
              }}
              className="w-full px-3 py-2 text-left hover:bg-hover transition-colors flex items-center gap-2"
            >
              <span className="font-mono text-cyan text-sm">{stock.code}</span>
              <span className="text-secondary text-sm">{stock.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

## 5. 交互模式

### 5.1 悬停状态

| 元素 | 默认状态 | 悬停状态 | 激活状态 |
|-----|---------|---------|---------|
| 组合卡片 | 边框：white/5 | 边框：cyan/30，translateY(-4px) | 缩放：0.98 |
| 主按钮 | 青色渐变 | 阴影光晕 | translateY(1px) |
| 次按钮 | 透明边框 | 边框：cyan/30，文字：cyan | 背景：white/5 |
| 表格行 | 背景：透明 | 背景：hover | 左边框：cyan |
| 输入框 | 边框：white/10 | 边框：white/15 | 边框：cyan/30，光晕 |

### 5.2 加载状态

#### 骨架屏加载

```html
<div class="portfolio-card skeleton">
  <div class="skeleton-line w-3/4 h-4 mb-2"></div>
  <div class="skeleton-line w-1/2 h-3 mb-4"></div>
  <div class="skeleton-line w-full h-8 mb-2"></div>
  <div class="skeleton-line w-2/3 h-3"></div>
</div>
```

```css
.skeleton-line {
  background: linear-gradient(
    90deg,
    var(--bg-elevated) 25%,
    var(--bg-hover) 50%,
    var(--bg-elevated) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 4px;
}

@keyframes skeleton-pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### 5.3 Toast通知

```tsx
interface ToastProps {
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const Toast: React.FC<ToastProps> = ({ type, message, action }) => {
  const icons = {
    success: '✓',
    warning: '⚠',
    error: '✕',
    info: 'ℹ',
  };
  
  const colors = {
    success: 'border-success/30 bg-success/10',
    warning: 'border-warning/30 bg-warning/10',
    error: 'border-danger/30 bg-danger/10',
    info: 'border-cyan/30 bg-cyan/10',
  };
  
  return (
    <div className={`
      fixed bottom-4 right-4 z-50
      flex items-center gap-3 px-4 py-3 rounded-lg
      border backdrop-blur-sm
      animate-slide-in-right
      ${colors[type]}
    `}>
      <span className="text-lg">{icons[type]}</span>
      <span className="text-sm">{message}</span>
      {action && (
        <button
          onClick={action.onClick}
          className="text-xs text-cyan hover:underline"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};
```

---

## 6. 响应式设计

### 6.1 断点

| 断点 | 宽度 | 布局 |
|-----|------|------|
| 移动端 | < 768px | 单列，卡片堆叠 |
| 平板 | 768px - 1279px | 两列网格 |
| 桌面 | ≥ 1280px | 三列网格 |

### 6.2 移动端适配

```
移动端布局（< 768px）：
┌─────────────────────┐
│ 页头                │
│ 组合管理        [+] │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ 组合卡片        │ │
│ │ （全宽）        │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ 组合卡片        │ │
│ └─────────────────┘ │
└─────────────────────┘

Dock导航（移动端）：
- 定位在底部
- 水平布局
- 仅显示图标（无文字）
```

### 6.3 触控交互

| 手势 | 操作 |
|-----|------|
| 点击 | 选择/打开 |
| 长按 | 显示上下文菜单 |
| 左滑 | 删除选项 |
| 下拉 | 刷新 |

---

## 7. 动画规范

### 7.1 页面过渡

```css
/* 页面进入 */
.page-enter {
  opacity: 0;
  transform: translateY(10px);
}

.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: all 0.3s ease-out;
}

/* 页面退出 */
.page-exit {
  opacity: 1;
}

.page-exit-active {
  opacity: 0;
  transition: opacity 0.2s ease-in;
}
```

### 7.2 卡片动画

```css
/* 卡片悬停 */
.portfolio-card {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.3s ease,
              border-color 0.3s ease;
}

.portfolio-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 212, 255, 0.15);
}

/* 卡片点击 */
.portfolio-card:active {
  transform: translateY(-2px) scale(0.98);
}
```

### 7.3 图表动画

```css
/* 折线图绘制 */
.chart-line {
  stroke-dasharray: 1000;
  stroke-dashoffset: 1000;
  animation: draw-line 1.5s ease-out forwards;
}

@keyframes draw-line {
  to {
    stroke-dashoffset: 0;
  }
}

/* 数据点出现 */
.chart-point {
  opacity: 0;
  transform: scale(0);
  animation: point-appear 0.3s ease-out forwards;
  animation-delay: calc(var(--index) * 50ms);
}

@keyframes point-appear {
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### 7.4 弹窗动画

```css
/* 弹窗背景 */
.modal-backdrop {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.modal-backdrop.active {
  opacity: 1;
}

/* 弹窗内容 */
.modal-content {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-backdrop.active .modal-content {
  opacity: 1;
  transform: scale(1) translateY(0);
}
```

---

## 附录A：图标库

| 图标 | SVG路径 | 用途 |
|-----|---------|------|
| 组合 | M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10 | 导航图标 |
| 添加 | M12 4v16m8-8H4 | 添加按钮 |
| 编辑 | M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z | 编辑操作 |
| 删除 | M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16 | 删除操作 |
| 图表 | M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z | 收益走势 |
| 导出 | M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4 | 导出操作 |
| 恢复 | M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15 | 恢复操作 |

---

## 附录B：无障碍检查清单

- [ ] 所有交互元素有焦点指示器
- [ ] 颜色对比度符合WCAG AA标准（文字4.5:1）
- [ ] 所有图片有替代文本
- [ ] 表单字段有关联标签
- [ ] 错误消息通过屏幕阅读器播报
- [ ] 弹窗对话框捕获焦点
- [ ] 所有交互支持键盘导航
- [ ] 图表有文本替代
- [ ] 动画尊重prefers-reduced-motion设置
- [ ] 触控目标至少44x44px
