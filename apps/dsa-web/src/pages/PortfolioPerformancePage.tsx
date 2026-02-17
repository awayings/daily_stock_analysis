import type React from 'react';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { SummaryCard } from '../components/portfolio';
import { usePortfolioStore } from '../stores';

const PortfolioPerformancePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentPortfolio,
    performance,
    isLoading,
    fetchPortfolio,
    fetchPerformance,
  } = usePortfolioStore();

  const [dateRange, setDateRange] = useState<'1w' | '1m' | '3m' | '6m' | '1y'>('1m');
  const [viewMode, setViewMode] = useState<'portfolio' | 'holdings'>('portfolio');

  const portfolioId = parseInt(id || '0', 10);

  const loadData = useCallback(() => {
    if (portfolioId) {
      fetchPortfolio(portfolioId);
      const daysMap = { '1w': 7, '1m': 30, '3m': 90, '6m': 180, '1y': 365 };
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - daysMap[dateRange]);

      fetchPerformance(portfolioId, {
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        viewMode,
      });
    }
  }, [portfolioId, dateRange, viewMode, fetchPortfolio, fetchPerformance]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleExport = async () => {
    const { portfolioApi } = await import('../api/portfolio');
    try {
      const blob = await portfolioApi.export(portfolioId, {
        format: 'csv',
        scope: 'summary',
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio_${portfolioId}_performance.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
    }
  };

  if (isLoading && !performance) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
      </div>
    );
  }

  const stats = performance?.statistics;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex-shrink-0 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(`/portfolios/${portfolioId}`)}
              className="flex items-center gap-2 text-muted hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
            <h1 className="text-xl font-semibold text-white">
              收益走势 - {currentPortfolio?.name || '组合'}
            </h1>
          </div>
          <Button variant="outline" size="sm" onClick={handleExport}>
            导出
          </Button>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-4 space-y-4">
        <div className="glass-card p-4">
          <div className="flex flex-wrap gap-4 items-center justify-between">
            <div className="flex gap-2">
              {(['1w', '1m', '3m', '6m', '1y'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setDateRange(range)}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                    dateRange === range
                      ? 'bg-cyan/20 text-cyan border border-cyan/30'
                      : 'text-muted hover:text-white hover:bg-white/5'
                  }`}
                >
                  {range === '1w' ? '1周' : range === '1m' ? '1月' : range === '3m' ? '3月' : range === '6m' ? '6月' : '1年'}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('portfolio')}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  viewMode === 'portfolio'
                    ? 'bg-cyan/20 text-cyan border border-cyan/30'
                    : 'text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                组合总体
              </button>
              <button
                onClick={() => setViewMode('holdings')}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                  viewMode === 'holdings'
                    ? 'bg-cyan/20 text-cyan border border-cyan/30'
                    : 'text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                各持仓独立
              </button>
            </div>
          </div>
        </div>

        <div className="glass-card p-8 min-h-[300px] flex items-center justify-center">
          {performance?.dataPoints && performance.dataPoints.length > 0 ? (
            <div className="w-full">
              <div className="text-center text-muted mb-4">
                图表渲染区域 - {performance.dataPoints.length} 个数据点
              </div>
            </div>
          ) : (
            <div className="text-center text-muted">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <p>暂无收益数据</p>
              <p className="text-xs mt-1">请先添加持仓并触发计算</p>
            </div>
          )}
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SummaryCard
              title="总收益率"
              value={`${stats.totalReturnPct >= 0 ? '+' : ''}${stats.totalReturnPct.toFixed(2)}%`}
              trend={stats.totalReturnPct >= 0 ? 'up' : 'down'}
            />
            <SummaryCard
              title="浮动盈亏"
              value={`${stats.unrealizedReturnPct >= 0 ? '+' : ''}${stats.unrealizedReturnPct.toFixed(2)}%`}
              trend={stats.unrealizedReturnPct >= 0 ? 'up' : 'down'}
            />
            <SummaryCard
              title="已实现盈亏"
              value={`${stats.realizedReturnPct >= 0 ? '+' : ''}${stats.realizedReturnPct.toFixed(2)}%`}
              trend={stats.realizedReturnPct >= 0 ? 'up' : 'down'}
            />
            <SummaryCard
              title="最大回撤"
              value={`${stats.maxDrawdownPct.toFixed(2)}%`}
              trend="down"
            />
          </div>
        )}

        {performance?.dataPoints && performance.dataPoints.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-medium text-white mb-3">持仓收益分解</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-elevated text-left">
                    <th className="px-3 py-2 text-xs font-medium text-secondary">代码</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">贡献度</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">收益率</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">占比</th>
                  </tr>
                </thead>
                <tbody>
                  {currentPortfolio?.holdings.filter(h => !h.isClosed).map((holding) => (
                    <tr key={holding.id} className="border-t border-white/5">
                      <td className="px-3 py-2 font-mono text-cyan">{holding.code}</td>
                      <td className={`px-3 py-2 text-right font-mono ${(holding.weightedPnl ?? 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                        {(holding.weightedPnl ?? 0) >= 0 ? '+' : ''}{(holding.weightedPnl ?? 0).toFixed(2)}%
                      </td>
                      <td className={`px-3 py-2 text-right font-mono ${(holding.pnlPct ?? 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                        {(holding.pnlPct ?? 0) >= 0 ? '+' : ''}{(holding.pnlPct ?? 0).toFixed(2)}%
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-secondary">{holding.weight}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default PortfolioPerformancePage;
