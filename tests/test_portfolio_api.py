# -*- coding: utf-8 -*-
"""
===================================
投资组合 API 单元测试
===================================

职责：
1. 测试投资组合 API 端点的功能
2. 覆盖正常流程、边界条件和错误处理
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime

from fastapi.testclient import TestClient


@pytest.fixture
def mock_portfolio_service():
    """Mock PortfolioService"""
    with patch('api.v1.endpoints.portfolios._get_portfolio_service') as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def client():
    """创建测试客户端"""
    from api.app import create_app
    app = create_app()
    return TestClient(app)


class TestPortfolioAPI:
    """投资组合 API 测试类"""

    def test_create_portfolio_success(self, client, mock_portfolio_service):
        """测试成功创建组合"""
        mock_portfolio_service.create_portfolio.return_value = {
            'id': 1,
            'name': '测试组合',
            'description': '测试描述',
            'initial_capital': 100000.0,
            'currency': 'CNY',
            'is_deleted': False,
            'created_at': '2026-02-17T10:00:00',
            'updated_at': '2026-02-17T10:00:00',
            'holdings': [],
            'summary': {
                'total_value': 100000.0,
                'total_pnl_pct': 0.0,
                'total_pnl_amount': 0.0,
                'holdings_count': 0
            }
        }

        response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "测试组合",
                "description": "测试描述",
                "initial_capital": 100000,
                "currency": "CNY"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['name'] == '测试组合'
        assert data['initial_capital'] == 100000.0

    def test_create_portfolio_empty_name(self, client, mock_portfolio_service):
        """测试组合名称为空 - Pydantic验证会在请求阶段拦截"""
        response = client.post(
            "/api/v1/portfolios",
            json={"name": ""}
        )
        assert response.status_code == 422

    def test_create_portfolio_duplicate_name(self, client, mock_portfolio_service):
        """测试重复名称"""
        mock_portfolio_service.create_portfolio.side_effect = ValueError("PORTFOLIO_003: 组合名称已存在")

        response = client.post(
            "/api/v1/portfolios",
            json={"name": "已存在组合"}
        )

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_create_portfolio_invalid_weights(self, client, mock_portfolio_service):
        """测试仓位占比超过100%"""
        mock_portfolio_service.create_portfolio.side_effect = ValueError("PORTFOLIO_005: 仓位占比总和不能超过100%")

        response = client.post(
            "/api/v1/portfolios",
            json={
                "name": "测试组合",
                "holdings": [
                    {"code": "600519", "entry_price": 1800, "weight": 30},
                    {"code": "00700", "entry_price": 350, "weight": 50}
                ]
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_get_portfolios(self, client, mock_portfolio_service):
        """测试获取组合列表"""
        mock_portfolio_service.get_portfolio_list.return_value = {
            'items': [
                {
                    'id': 1,
                    'name': '测试组合',
                    'description': '测试描述',
                    'holdings_count': 2,
                    'total_value': 102000.0,
                    'total_pnl_pct': 2.0,
                    'total_pnl_amount': 2000.0,
                    'is_deleted': False,
                    'created_at': '2026-02-17T10:00:00',
                    'updated_at': '2026-02-17T12:00:00'
                }
            ],
            'total': 1,
            'page': 1,
            'limit': 20
        }

        response = client.get("/api/v1/portfolios")

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1
        assert data['total'] == 1

    def test_get_portfolio_not_found(self, client, mock_portfolio_service):
        """测试获取不存在的组合"""
        mock_portfolio_service.get_portfolio.side_effect = ValueError("PORTFOLIO_NOT_FOUND: 组合不存在")

        response = client.get("/api/v1/portfolios/99999")

        assert response.status_code == 400

    def test_get_portfolio_detail(self, client, mock_portfolio_service):
        """测试获取组合详情"""
        mock_portfolio_service.get_portfolio.return_value = {
            'id': 1,
            'name': '测试组合',
            'description': '测试描述',
            'initial_capital': 100000.0,
            'currency': 'CNY',
            'is_deleted': False,
            'created_at': '2026-02-17T10:00:00',
            'updated_at': '2026-02-17T12:00:00',
            'holdings': [
                {
                    'id': 1,
                    'code': '600519',
                    'name': '贵州茅台',
                    'entry_price': 1800.0,
                    'current_price': 1850.0,
                    'weight': 50.0,
                    'pnl_pct': 2.78,
                    'weighted_pnl': 1.39,
                    'is_closed': False,
                    'added_at': '2026-02-17T10:00:00'
                }
            ],
            'summary': {
                'total_value': 102000.0,
                'total_pnl_pct': 2.0,
                'total_pnl_amount': 2000.0,
                'holdings_count': 1
            }
        }

        response = client.get("/api/v1/portfolios/1")

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == '测试组合'
        assert len(data['holdings']) == 1

    def test_update_portfolio(self, client, mock_portfolio_service):
        """测试更新组合"""
        mock_portfolio_service.update_portfolio.return_value = {
            'id': 1,
            'name': '更新后的组合',
            'description': '更新描述',
            'initial_capital': 120000.0,
            'currency': 'CNY',
            'is_deleted': False,
            'created_at': '2026-02-17T10:00:00',
            'updated_at': '2026-02-17T14:00:00',
            'holdings': [],
            'summary': {
                'total_value': 120000.0,
                'total_pnl_pct': 0.0,
                'total_pnl_amount': 0.0,
                'holdings_count': 0
            }
        }

        response = client.put(
            "/api/v1/portfolios/1",
            json={
                "name": "更新后的组合",
                "description": "更新描述",
                "initial_capital": 120000
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == '更新后的组合'

    def test_delete_portfolio(self, client, mock_portfolio_service):
        """测试删除组合"""
        mock_portfolio_service.delete_portfolio.return_value = {
            'id': 1,
            'name': '测试组合',
            'is_deleted': True,
            'deleted_at': '2026-02-17T14:00:00',
            'history_preserved': True
        }

        response = client.delete("/api/v1/portfolios/1")

        assert response.status_code == 200
        data = response.json()
        assert data['is_deleted'] == True

    def test_restore_portfolio(self, client, mock_portfolio_service):
        """测试恢复组合"""
        mock_portfolio_service.restore_portfolio.return_value = {
            'id': 1,
            'name': '测试组合',
            'description': None,
            'initial_capital': 100000.0,
            'currency': 'CNY',
            'is_deleted': False,
            'created_at': '2026-02-17T10:00:00',
            'updated_at': '2026-02-17T14:00:00',
            'holdings': [],
            'summary': {
                'total_value': 100000.0,
                'total_pnl_pct': 0.0,
                'total_pnl_amount': 0.0,
                'holdings_count': 0
            }
        }

        response = client.post("/api/v1/portfolios/1/restore")

        assert response.status_code == 200
        data = response.json()
        assert data['is_deleted'] == False

    def test_add_holding(self, client, mock_portfolio_service):
        """测试添加持仓"""
        mock_portfolio_service.add_holding.return_value = {
            'id': 1,
            'portfolio_id': 1,
            'code': '600519',
            'name': '贵州茅台',
            'entry_price': 1800.0,
            'current_price': 1850.0,
            'weight': 50.0,
            'pnl_pct': 2.78,
            'is_closed': False,
            'added_at': '2026-02-17T10:00:00'
        }

        response = client.post(
            "/api/v1/portfolios/1/holdings",
            json={
                "code": "600519",
                "entry_price": 1800,
                "weight": 50
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data['code'] == '600519'

    def test_update_holding(self, client, mock_portfolio_service):
        """测试更新持仓"""
        mock_portfolio_service.update_holding.return_value = {
            'id': 1,
            'portfolio_id': 1,
            'code': '600519',
            'entry_price': 1850.0,
            'weight': 60.0,
            'is_closed': False
        }

        response = client.put(
            "/api/v1/portfolios/1/holdings/1",
            json={
                "entry_price": 1850,
                "weight": 60
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['weight'] == 60.0

    def test_close_position_all(self, client, mock_portfolio_service):
        """测试全部平仓"""
        mock_portfolio_service.close_position.return_value = {
            'id': 1,
            'portfolio_id': 1,
            'code': '600519',
            'name': '贵州茅台',
            'entry_price': 1800.0,
            'close_price': 1850.0,
            'close_quantity': 100.0,
            'close_type': 'full',
            'is_closed': True,
            'closed_at': '2026-02-17T14:00:00',
            'pnl': {
                'amount': 5000.0,
                'percentage': 2.78,
                'realized': True
            },
            'remaining': {
                'shares': 0,
                'weight': 0
            },
            'weight_rebalance_required': False
        }

        response = client.post(
            "/api/v1/portfolios/1/holdings/1/closePosition",
            json={
                "price_type": "current",
                "quantity_type": "all"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['is_closed'] == True
        assert data['close_type'] == 'full'

    def test_close_position_invalid_quantity(self, client, mock_portfolio_service):
        """测试平仓数量超过持仓"""
        mock_portfolio_service.close_position.side_effect = ValueError("CLOSE_002: 平仓数量不能超过当前持仓数量")

        response = client.post(
            "/api/v1/portfolios/1/holdings/1/closePosition",
            json={
                "price_type": "specified",
                "specified_price": 1900,
                "quantity_type": "partial",
                "quantity": 999
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert 'detail' in data

    def test_close_position_already_closed(self, client, mock_portfolio_service):
        """测试平仓已平仓的持仓"""
        mock_portfolio_service.close_position.side_effect = ValueError("HOLDING_ALREADY_CLOSED: 持仓已平仓")

        response = client.post(
            "/api/v1/portfolios/1/holdings/1/closePosition",
            json={
                "price_type": "current",
                "quantity_type": "all"
            }
        )

        assert response.status_code == 400

    def test_batch_add_holdings(self, client, mock_portfolio_service):
        """测试批量添加持仓"""
        mock_portfolio_service.batch_add_holdings.return_value = {
            'added_count': 2,
            'skipped_count': 0,
            'holdings': [
                {
                    'id': 1,
                    'code': '600519',
                    'name': '贵州茅台',
                    'entry_price': 1800.0,
                    'weight': 30.0
                }
            ],
            'weight_summary': {
                'total': 100.0,
                'is_valid': True
            }
        }

        response = client.post(
            "/api/v1/portfolios/1/holdings/batch",
            json={
                "holdings": [
                    {"code": "600519", "entry_price": 1800, "weight": 30},
                    {"code": "00700", "entry_price": 350, "weight": 20}
                ],
                "rebalance_mode": "none"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['added_count'] == 2

    def test_rebalance_holdings(self, client, mock_portfolio_service):
        """测试平均分配仓位"""
        mock_portfolio_service.rebalance_weights.return_value = {
            'portfolio_id': 1,
            'holdings_count': 5,
            'new_weight_each': 20.0,
            'holdings': [
                {'id': 1, 'code': '600519', 'weight': 20.0},
                {'id': 2, 'code': '00700', 'weight': 20.0}
            ]
        }

        response = client.post("/api/v1/portfolios/1/holdings/rebalance")

        assert response.status_code == 200
        data = response.json()
        assert data['new_weight_each'] == 20.0

    def test_calculate_portfolio(self, client, mock_portfolio_service):
        """测试触发计算"""
        mock_portfolio_service.calculate_portfolio.return_value = {
            'portfolio_id': 1,
            'calculated_at': '2026-02-17T15:00:00',
            'snapshot_date': '2026-02-17',
            'total_value': 102500.0,
            'total_pnl_pct': 2.5,
            'holdings_updated': 5,
            'status': 'success'
        }

        response = client.post("/api/v1/portfolios/1/calculate")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

    def test_get_history(self, client, mock_portfolio_service):
        """测试获取历史记录"""
        mock_portfolio_service.get_history.return_value = {
            'portfolio_id': 1,
            'items': [
                {
                    'id': 1,
                    'portfolio_id': 1,
                    'snapshot_date': '2026-02-14',
                    'total_value': 102500.0,
                    'unrealized_pnl_pct': 2.0,
                    'unrealized_pnl_amount': 2000.0,
                    'realized_pnl_amount': 500.0,
                    'cumulative_realized_pnl': 1500.0,
                    'total_pnl_pct': 3.5,
                    'total_pnl_amount': 3500.0,
                    'active_holdings_count': 5,
                    'closed_holdings_count': 0,
                    'calculation_status': 'success',
                    'calculated_at': '2026-02-14T18:00:00',
                    'holdings': []
                }
            ],
            'total': 1,
            'page': 1,
            'limit': 20
        }

        response = client.get("/api/v1/portfolios/1/history")

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 1

    def test_get_performance(self, client, mock_portfolio_service):
        """测试获取收益走势"""
        mock_portfolio_service.get_performance.return_value = {
            'portfolio_id': 1,
            'view_mode': 'portfolio',
            'date_range': {
                'start': '2026-01-17',
                'end': '2026-02-17'
            },
            'data_points': [
                {
                    'date': '2026-02-14',
                    'total_value': 102500.0,
                    'total_pnl_pct': 2.5,
                    'holdings': {
                        '600519': {'pnl_pct': 2.5, 'weighted_pnl': 1.25}
                    }
                }
            ],
            'statistics': {
                'total_return_pct': 2.5,
                'best_day': {'date': '2026-02-10', 'pnlPct': 1.5},
                'worst_day': {'date': '2026-02-05', 'pnlPct': -0.8}
            }
        }

        response = client.get("/api/v1/portfolios/1/performance")

        assert response.status_code == 200
        data = response.json()
        assert len(data['data_points']) == 1

    def test_export_portfolio_csv(self, client, mock_portfolio_service):
        """测试导出 CSV"""
        mock_portfolio_service.get_history.return_value = {
            'items': [
                {
                    'snapshot_date': '2026-02-14',
                    'total_value': 100000.0,
                    'total_pnl_pct': 2.0,
                    'total_pnl_amount': 2000.0
                }
            ]
        }

        response = client.get(
            "/api/v1/portfolios/1/export",
            params={"format": "csv"}
        )

        assert response.status_code == 200
        assert 'text/csv' in response.headers['content-type']

    def test_export_portfolio_json(self, client, mock_portfolio_service):
        """测试导出 JSON"""
        mock_portfolio_service.get_history.return_value = {
            'items': [
                {
                    'snapshot_date': '2026-02-14',
                    'total_value': 100000.0
                }
            ]
        }

        response = client.get(
            "/api/v1/portfolios/1/export",
            params={"format": "json"}
        )

        assert response.status_code == 200
        assert 'application/json' in response.headers['content-type']


class TestHoldingValidation:
    """持仓验证测试类"""

    def test_holding_weight_range(self):
        """测试仓位占比范围验证"""
        from api.v1.schemas.portfolio import HoldingCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            HoldingCreate(
                code="600519",
                entry_price=1800.0,
                weight=150.0  # 超过100
            )

    def test_holding_entry_price_positive(self):
        """测试建仓价格必须为正"""
        from api.v1.schemas.portfolio import HoldingCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            HoldingCreate(
                code="600519",
                entry_price=-100.0,
                weight=50.0
            )


class TestPortfolioValidation:
    """组合验证测试类"""

    def test_portfolio_name_length(self):
        """测试组合名称长度验证"""
        from api.v1.schemas.portfolio import PortfolioCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PortfolioCreate(
                name="a" * 101  # 超过100字符
            )

    def test_portfolio_initial_capital_positive(self):
        """测试初始资金必须为正"""
        from api.v1.schemas.portfolio import PortfolioCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PortfolioCreate(
                name="测试组合",
                initial_capital=-1000.0
            )
