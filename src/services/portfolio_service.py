# -*- coding: utf-8 -*-
"""
===================================
投资组合业务逻辑层
===================================

职责：
1. 封装投资组合的业务逻辑
2. 实现组合管理、持仓管理、收益计算等功能
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from src.repositories.portfolio_repo import PortfolioRepository
from src.storage import Portfolio, PortfolioHolding

logger = logging.getLogger(__name__)


class PortfolioService:
    """投资组合业务逻辑层"""

    MAX_PORTFOLIOS = 10
    MAX_HOLDINGS_PER_PORTFOLIO = 50
    DEFAULT_INITIAL_CAPITAL = Decimal('100000')

    def __init__(self):
        self.repo = PortfolioRepository()

    def _get_stock_service(self):
        """获取股票服务"""
        try:
            from src.services.stock_service import StockService
            return StockService()
        except ImportError:
            logger.warning("StockService 未找到")
            return None

    def create_portfolio(
        self,
        name: str,
        description: Optional[str] = None,
        initial_capital: Optional[Decimal] = None,
        currency: str = 'CNY',
        holdings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """创建投资组合"""
        if not name or len(name.strip()) == 0:
            raise ValueError("PORTFOLIO_001: 请输入组合名称")

        if len(name) > 100:
            raise ValueError("PORTFOLIO_002: 组合名称不能超过100个字符")

        existing = self.repo.get_portfolio_by_name(name)
        if existing:
            raise ValueError("PORTFOLIO_003: 组合名称已存在")

        count = self.repo.count_portfolios()
        if count >= self.MAX_PORTFOLIOS:
            raise ValueError(f"PORTFOLIO_006: 最多创建 {self.MAX_PORTFOLIOS} 个组合")


        # if holdings:
        #     total_weight = sum(h.get('weight', 0) for h in holdings)
        #     if abs(total_weight - 100) > 0.01:
        #         raise ValueError("PORTFOLIO_005: 仓位占比总和必须等于100%")

        portfolio = self.repo.create_portfolio(
            name=name,
            description=description,
            initial_capital=initial_capital,
            currency=currency
        )

        created_holdings = []
        if holdings:
            stock_service = self._get_stock_service()
            for h in holdings:
                code = h['code']
                name = stock_service.get_realtime_quote_from_db(code).get('stock_name') if stock_service else h.get('name', code)
                entry_price = Decimal(str(h['entry_price']))
                last_price = Decimal(str(h.get('last_price', h['entry_price'])))

                holding = self.repo.add_holding(
                    portfolio_id=portfolio.id,
                    code=code,
                    name=name,
                    entry_price=entry_price,
                    last_price=last_price,
                    weight=Decimal(str(h['weight']))
                )
                created_holdings.append(holding)

        return self._build_portfolio_response(portfolio, created_holdings)

    def get_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """获取组合详情"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        holdings = self.repo.get_holdings(portfolio_id)
        return self._build_portfolio_response(portfolio, holdings)

    def get_portfolio_list(
        self,
        include_deleted: bool = False,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取组合列表"""
        portfolios, total = self.repo.get_portfolio_list(include_deleted, page, limit)

        items = []
        for p in portfolios:
            holdings = self.repo.get_holdings(p.id)
            summary = self._calculate_summary(p, holdings)
            items.append({
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'holdings_count': summary['holdings_count'],
                'total_value': summary['total_value'],
                'total_pnl_pct': summary['total_pnl_pct'],
                'total_pnl_amount': summary['total_pnl_amount'],
                'is_deleted': p.is_deleted,
                'created_at': p.created_at.isoformat() if p.created_at else None,
                'updated_at': p.updated_at.isoformat() if p.updated_at else None,
            })

        return {
            'items': items,
            'total': total,
            'page': page,
            'limit': limit
        }

    def update_portfolio(
        self,
        portfolio_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        initial_capital: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """更新组合信息"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        if name is not None:
            if len(name.strip()) == 0:
                raise ValueError("PORTFOLIO_001: 请输入组合名称")
            if len(name) > 100:
                raise ValueError("PORTFOLIO_002: 组合名称不能超过100个字符")

            existing = self.repo.get_portfolio_by_name(name, include_deleted=True)
            if existing and existing.id != portfolio_id:
                raise ValueError("PORTFOLIO_003: 组合名称已存在")

        kwargs = {}
        if name is not None:
            kwargs['name'] = name
        if description is not None:
            kwargs['description'] = description
        if initial_capital is not None:
            if initial_capital <= 0:
                raise ValueError("PORTFOLIO_007: 初始资金必须为正数")
            kwargs['initial_capital'] = initial_capital

        updated = self.repo.update_portfolio(portfolio_id, **kwargs)
        holdings = self.repo.get_holdings(portfolio_id)
        return self._build_portfolio_response(updated, holdings)

    def delete_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """删除组合"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        success = self.repo.soft_delete_portfolio(portfolio_id)
        if success:
            return {
                'id': portfolio_id,
                'name': portfolio.name,
                'is_deleted': True,
                'deleted_at': datetime.now().isoformat(),
                'history_preserved': True
            }
        raise ValueError("SYSTEM_001: 删除失败")

    def restore_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """恢复已删除组合"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        success = self.repo.restore_portfolio(portfolio_id)
        if success:
            holdings = self.repo.get_holdings(portfolio_id)
            return self._build_portfolio_response(self.repo.get_portfolio_by_id(portfolio_id), holdings)
        raise ValueError("SYSTEM_001: 恢复失败")

    def add_holding(
        self,
        portfolio_id: int,
        code: str,
        entry_price: Decimal,
        weight: Decimal,
        last_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """添加持仓"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        count = self.repo.count_holdings(portfolio_id)
        if count >= self.MAX_HOLDINGS_PER_PORTFOLIO:
            raise ValueError(f"HOLDING_004: 每组合最多 {self.MAX_HOLDINGS_PER_PORTFOLIO} 个持仓")

        if weight <= 0 or weight > 100:
            raise ValueError("HOLDING_003: 仓位占比必须在0.01到100之间")

        if entry_price <= 0:
            raise ValueError("HOLDING_002: 建仓价格必须为正数")

        existing_holdings = self.repo.get_holdings(portfolio_id, include_closed=True)
        total_weight = sum(h.weight for h in existing_holdings if not h.is_closed)
        if total_weight + weight > 100:
            raise ValueError("PORTFOLIO_005: 仓位占比总和不能超过100%")

        stock_service = self._get_stock_service()
        name = stock_service.get_realtime_quote_from_db(code).get('stock_name') if stock_service else code

        if last_price is None:
            last_price = entry_price

        holding = self.repo.add_holding(
            portfolio_id=portfolio_id,
            code=code,
            name=name,
            entry_price=entry_price,
            last_price=last_price,
            weight=weight
        )

        return self._build_holding_response(holding)

    def update_holding(
        self,
        portfolio_id: int,
        holding_id: int,
        entry_price: Optional[Decimal] = None,
        weight: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """更新持仓"""
        holding = self.repo.get_holding_by_id(holding_id)
        if not holding:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")

        if holding.portfolio_id != portfolio_id:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")

        if holding.is_closed:
            raise ValueError("HOLDING_ALREADY_CLOSED: 持仓已平仓")

        kwargs = {}
        if entry_price is not None:
            if entry_price <= 0:
                raise ValueError("HOLDING_002: 建仓价格必须为正数")
            kwargs['entry_price'] = entry_price

        if weight is not None:
            if weight <= 0 or weight > 100:
                raise ValueError("HOLDING_003: 仓位占比必须在0.01到100之间")

            holdings = self.repo.get_holdings(portfolio_id)
            total_weight = sum(h.weight for h in holdings if h.id != holding_id)
            if total_weight + weight > 100:
                raise ValueError("PORTFOLIO_005: 仓位占比总和不能超过100%")
            kwargs['weight'] = weight

        updated = self.repo.update_holding(holding_id, **kwargs)
        return self._build_holding_response(updated)

    def close_position(
        self,
        portfolio_id: int,
        holding_id: int,
        price_type: str,
        specified_price: Optional[Decimal] = None,
        quantity_type: str = 'all',
        quantity: Optional[Decimal] = None,
        ratio: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """平仓持仓"""
        holding = self.repo.get_holding_by_id(holding_id)
        if not holding:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")

        if holding.portfolio_id != portfolio_id:
            raise ValueError("HOLDING_NOT_FOUND: 持仓不存在")

        if holding.is_closed:
            raise ValueError("HOLDING_ALREADY_CLOSED: 持仓已平仓")

        if price_type not in ('current', 'specified'):
            raise ValueError("CLOSE_001: 价格类型无效")

        if price_type == 'specified':
            if not specified_price or specified_price <= 0:
                raise ValueError("CLOSE_001: 平仓价格必须为正数")

        if quantity_type not in ('all', 'partial'):
            raise ValueError("CLOSE_002: 数量类型无效")

        stock_service = self._get_stock_service()

        if price_type == 'current':
            quote = stock_service.get_realtime_quote_from_db(holding.code) if stock_service else None
            if not quote:
                raise ValueError("CLOSE_004: 无法获取当前收盘价")
            close_price = Decimal(str(quote['current_price']))
        else:
            close_price = specified_price

        current_shares = holding.shares or Decimal('0')
        if quantity_type == 'all':
            close_quantity = current_shares
        else:
            if not quantity or quantity <= 0:
                raise ValueError("CLOSE_003: 平仓数量必须大于0")
            if quantity > current_shares:
                raise ValueError("CLOSE_002: 平仓数量不能超过当前持仓数量")
            close_quantity = quantity

        close_type = 'full' if quantity_type == 'all' and close_quantity == current_shares else 'partial'

        updated_holding = self.repo.close_holding(
            holding_id=holding_id,
            close_price=close_price,
            close_quantity=close_quantity,
            close_type=close_type
        )

        pnl_amount = (close_price - holding.entry_price) * close_quantity
        pnl_pct = ((close_price / holding.entry_price - 1) * 100) if holding.entry_price > 0 else Decimal('0')

        remaining_shares = current_shares - close_quantity
        remaining_weight = (remaining_shares / current_shares * holding.weight) if current_shares and current_shares > 0 else Decimal('0')

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
            'weight_rebalance_required': abs(float(remaining_weight) + (float(holding.weight) - float(updated_holding.weight)) - 100) > 0.01 if updated_holding else False
        }

    def batch_add_holdings(
        self,
        portfolio_id: int,
        holdings: List[Dict[str, Any]],
        rebalance_mode: str = 'none'
    ) -> Dict[str, Any]:
        """批量添加持仓"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        existing_holdings = self.repo.get_holdings(portfolio_id, include_closed=True)
        existing_active = [h for h in existing_holdings if not h.is_closed]

        total_weight = sum(h.weight for h in existing_active)

        stock_service = self._get_stock_service()

        added_holdings = []
        skipped = 0

        for h in holdings:
            code = h['code']
            entry_price = Decimal(str(h['entry_price']))
            last_price = Decimal(str(h.get('last_price', h['entry_price'])))
            weight = Decimal(str(h['weight']))

            existing = next((eh for eh in existing_active if eh.code == code), None)
            if existing:
                skipped += 1
                continue

            if rebalance_mode == 'equal':
                continue

            if total_weight + weight > 100:
                skipped += 1
                continue

            name = stock_service.get_realtime_quote_from_db(code).get('stock_name') if stock_service else h.get('name', code)

            holding = self.repo.add_holding(
                portfolio_id=portfolio_id,
                code=code,
                name=name,
                entry_price=entry_price,
                last_price=last_price,
                weight=weight
            )
            added_holdings.append(holding)
            total_weight += weight

        all_holdings = self.repo.get_holdings(portfolio_id, include_closed=True)
        final_total = sum(h.weight for h in all_holdings if not h.is_closed)

        return {
            'added_count': len(added_holdings),
            'skipped_count': skipped,
            'holdings': [self._build_holding_response(h) for h in added_holdings],
            'weight_summary': {
                'total': float(final_total),
                'remaining': float(100 - final_total),
                'is_valid': final_total <= 100
            }
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

    def calculate_portfolio(self, portfolio_id: int) -> Dict[str, Any]:
        """手动触发组合计算"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        return self._execute_calculation(portfolio)

    def calculate_all_portfolios(self) -> Dict[str, Any]:
        """计算所有活跃组合"""
        portfolios = self.repo.get_portfolio_list(include_deleted=False, limit=1000)[0]

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

    def get_history(
        self,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取历史记录"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        histories, total = self.repo.get_history(portfolio_id, start_date, end_date, page, limit)

        items = []
        for h in histories:
            snapshots = self.repo.get_holding_snapshots(h.id)
            items.append({
                **h.to_dict(),
                'holdings': [s.to_dict() for s in snapshots]
            })

        return {
            'portfolio_id': portfolio_id,
            'items': items,
            'total': total,
            'page': page,
            'limit': limit
        }

    def get_performance(
        self,
        portfolio_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        view_mode: str = 'portfolio'
    ) -> Dict[str, Any]:
        """获取收益走势数据"""
        portfolio = self.repo.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        histories, _ = self.repo.get_history(portfolio_id, start_date, end_date, 1, 1000)

        data_points = []
        for h in histories:
            snapshots = self.repo.get_holding_snapshots(h.id)
            holdings_data = {}
            for snapshot in snapshots:
                holdings_data[snapshot.code] = {
                    'pnl_pct': float(snapshot.pnl_pct) if snapshot.pnl_pct else 0,
                    'weighted_pnl': float(snapshot.weighted_pnl) if snapshot.weighted_pnl else 0,
                }

            data_points.append({
                'date': h.snapshot_date.isoformat() if h.snapshot_date else None,
                'total_value': float(h.total_value) if h.total_value else None,
                'unrealized_pnl_pct': float(h.unrealized_pnl_pct) if h.unrealized_pnl_pct else None,
                'unrealized_pnl_amount': float(h.unrealized_pnl_amount) if h.unrealized_pnl_amount else None,
                'realized_pnl_amount': float(h.realized_pnl_amount) if h.realized_pnl_amount else 0,
                'cumulative_realized_pnl': float(h.cumulative_realized_pnl) if h.cumulative_realized_pnl else 0,
                'total_pnl_pct': float(h.total_pnl_pct) if h.total_pnl_pct else None,
                'holdings': holdings_data,
            })

        data_points.reverse()

        statistics = {}
        if data_points and len(data_points) >= 2:
            first = data_points[0]
            last = data_points[-1]
            total_value_start = first.get('total_value') or 100000
            total_value_end = last.get('total_value') or 100000

            total_return_pct = ((total_value_end - total_value_start) / total_value_start * 100) if total_value_start else 0

            unrealized_start = first.get('unrealized_pnl_pct') or 0
            unrealized_end = last.get('unrealized_pnl_pct') or 0
            unrealized_return_pct = unrealized_end - unrealized_start

            realized_start = 0
            realized_end = last.get('cumulative_realized_pnl') or 0
            realized_return_pct = (realized_end / total_value_start * 100) if total_value_start else 0

            daily_returns = []
            max_value = total_value_start
            max_drawdown_pct = 0
            best_day = {'date': '', 'pnlPct': float('-inf')}
            worst_day = {'date': '', 'pnlPct': float('inf')}

            for i in range(1, len(data_points)):
                prev_value = data_points[i-1].get('total_value') or total_value_start
                curr_value = data_points[i].get('total_value') or total_value_start
                daily_return = ((curr_value - prev_value) / prev_value * 100) if prev_value else 0
                daily_returns.append(daily_return)

                if curr_value > max_value:
                    max_value = curr_value
                drawdown = ((max_value - curr_value) / max_value * 100) if max_value else 0
                if drawdown > max_drawdown_pct:
                    max_drawdown_pct = drawdown

                if daily_return > best_day['pnlPct']:
                    best_day = {'date': data_points[i].get('date') or '', 'pnlPct': daily_return}
                if daily_return < worst_day['pnlPct']:
                    worst_day = {'date': data_points[i].get('date') or '', 'pnlPct': daily_return}

            statistics = {
                'total_return_pct': round(total_return_pct, 2),
                'unrealized_return_pct': round(unrealized_return_pct, 2),
                'realized_return_pct': round(realized_return_pct, 2),
                'max_drawdown_pct': round(max_drawdown_pct, 2),
                'best_day': best_day if best_day['date'] else None,
                'worst_day': worst_day if worst_day['date'] else None,
            }

        return {
            'portfolio_id': portfolio_id,
            'view_mode': view_mode,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'data_points': data_points,
            'statistics': statistics
        }

    def _execute_calculation(self, portfolio) -> Dict[str, Any]:
        """执行组合计算"""
        holdings = self.repo.get_holdings(portfolio.id, include_closed=True)

        stock_service = self._get_stock_service()
        current_prices = {}
        for h in holdings:
            if not h.is_closed:
                quote = stock_service.get_realtime_quote_from_db(h.code) if stock_service else None
                if quote:
                    current_price = Decimal(str(quote['current_price']))
                    current_prices[h.code] = current_price
                    self.repo.update_holding(h.id, last_price=current_price)

        last_history = self.repo.get_latest_history(portfolio.id)
        cumulative_realized_pnl = Decimal(str(last_history.cumulative_realized_pnl)) if last_history else Decimal('0')

        unrealized_pnl = Decimal('0')
        active_count = 0
        snapshots = []

        for h in holdings:
            if not h.is_closed:
                current_price = current_prices.get(h.code, h.last_price)
                pnl_pct = ((current_price / h.last_price - 1) * 100) if h.last_price > 0 else Decimal('0')
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

        since = last_history.calculated_at if last_history and last_history.calculated_at else datetime.now() - timedelta(days=7)
        closed_holdings = self.repo.get_closed_holdings_since(portfolio.id, since)
        realized_pnl = Decimal('0')
        closed_count = 0

        for h in closed_holdings:
            pnl = (h.close_price - h.entry_price) * h.close_quantity
            realized_pnl += pnl
            closed_count += 1

        cumulative_realized_pnl += realized_pnl

        initial_capital = Decimal(str(portfolio.initial_capital or self.DEFAULT_INITIAL_CAPITAL))
        unrealized_pnl_amount = unrealized_pnl * initial_capital / 100 if initial_capital > 0 else Decimal('0')
        total_pnl_amount = unrealized_pnl_amount + cumulative_realized_pnl
        total_pnl_pct = (total_pnl_amount / initial_capital * 100) if initial_capital > 0 else Decimal('0')
        total_value = initial_capital + total_pnl_amount

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

    def _build_portfolio_response(self, portfolio, holdings: List) -> Dict[str, Any]:
        """构建组合响应"""
        stock_service = self._get_stock_service()

        holdings_data = []
        for h in holdings:
            quote = stock_service.get_realtime_quote_from_db(h.code) if stock_service else None
            current_price = Decimal(str(quote['current_price'])) if quote else h.entry_price

            pnl_pct = ((current_price / h.entry_price - 1) * 100) if h.entry_price > 0 else Decimal('0')
            weighted_pnl = pnl_pct * h.weight / 100

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

        summary = self._calculate_summary(portfolio, holdings)

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
            'summary': summary
        }

    def _build_holding_response(self, holding) -> Dict[str, Any]:
        """构建持仓响应"""
        stock_service = self._get_stock_service()

        quote = stock_service.get_realtime_quote_from_db(holding.code) if stock_service else None
        current_price = Decimal(str(quote['current_price'])) if quote else holding.last_price

        pnl_pct = ((current_price / holding.last_price - 1) * 100) if holding.last_price > 0 else Decimal('0')

        return {
            'id': holding.id,
            'portfolio_id': holding.portfolio_id,
            'code': holding.code,
            'name': holding.name,
            'entry_price': float(holding.entry_price),
            'last_price': float(holding.last_price),
            'current_price': float(current_price),
            'weight': float(holding.weight),
            'shares': float(holding.shares) if holding.shares else None,
            'pnl_pct': float(pnl_pct),
            'is_closed': holding.is_closed,
            'added_at': holding.added_at.isoformat() if holding.added_at else None,
            'updated_at': holding.updated_at.isoformat() if holding.updated_at else None
        }

    def _calculate_summary(self, portfolio, holdings) -> Dict[str, Any]:
        """计算组合摘要"""
        stock_service = self._get_stock_service()

        total_pnl = Decimal('0')
        total_value = Decimal('0')
        active_holdings = [h for h in holdings if not h.is_closed]

        for h in active_holdings:
            quote = stock_service.get_realtime_quote_from_db(h.code) if stock_service else None
            current_price = Decimal(str(quote['current_price'])) if quote else h.last_price

            pnl_pct = ((current_price / h.last_price - 1) * 100) if h.last_price > 0 else Decimal('0')
            weighted_pnl = pnl_pct * h.weight / 100
            total_pnl += weighted_pnl

        initial_capital = Decimal(str(portfolio.initial_capital or self.DEFAULT_INITIAL_CAPITAL))
        total_value = initial_capital + total_pnl * initial_capital / 100
        total_pnl_amount = total_pnl * initial_capital / 100

        return {
            'total_value': float(total_value),
            'total_pnl_pct': float(total_pnl),
            'total_pnl_amount': float(total_pnl_amount),
            'holdings_count': len(active_holdings)
        }
