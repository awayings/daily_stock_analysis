import type React from 'react';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { SummaryCard, PerformanceChart } from '../components/portfolio';
import { usePortfolioStore } from '../stores';

const PortfolioPerformancePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentPortfolio,
    performance,
    isLoading,
    error,
    fetchPortfolio,
    fetchPerformance,
    clearError,
  } = usePortfolioStore();

  const [dateRange, setDateRange] = useState<'1w' | '1m' | '3m' | '6m' | '1y'>('1m');
  const [viewMode, setViewMode] = useState<'portfolio' | 'holdings'>('portfolio');

  const portfolioId = parseInt(id || '0', 10);

  const loadData = useCallback(() => {
    if (portfolioId) {
      fetchPortfolio(portfolioId);
      const daysMap: Record<string, number> = { '1w': 7, '1m': 30, '3m': 90, '6m': 180, '1y': 365 };
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

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

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
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
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

  const holdingsInfo = currentPortfolio?.holdings
    ?.filter(h => !h.isClosed)
    .map(h => ({ code: h.code, name: h.name })) || [];

  const closedHoldings = currentPortfolio?.holdings
    ?.filter(h => h.isClosed) || [];

  return (
    <div className="min-h-screen flex flex-col">
      {error && (
        <div className="fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border border-danger/30 bg-danger/10 backdrop-blur-sm animate-slide-in-right">
          <span className="text-danger">✕</span>
          <span className="text-sm text-white">{error}</span>
          <button
            onClick={clearError}
            className="text-muted hover:text-white transition-colors"
          >
            ×
          </button>
        </div>
      )}

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

        <div className="glass-card p-4">
          {isLoading && performance && (
            <div className="absolute inset-0 bg-[#08080c]/50 flex items-center justify-center z-10">
              <div className="w-6 h-6 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
            </div>
          )}
          <PerformanceChart
            dataPoints={performance?.dataPoints || []}
            viewMode={viewMode}
            holdings={holdingsInfo}
          />
        </div>

        <div className="flex gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#00d4ff] rounded"></span>
            <span className="text-xs text-muted">总盈亏</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#00ff88] rounded border-dashed border-t border-t-[#00ff88]"></span>
            <span className="text-xs text-muted">浮动盈亏</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-[#ffaa00] rounded border-dashed border-t border-t-[#ffaa00]"></span>
            <span className="text-xs text-muted">已实现盈亏</span>
          </div>
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
              subtitle={stats.unrealizedReturnPct >= 0 ? '+' : ''}
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

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SummaryCard
              title="最佳交易日"
              value={stats.bestDay?.pnlPct != null ? `${stats.bestDay.pnlPct >= 0 ? '+' : ''}${stats.bestDay.pnlPct.toFixed(2)}%` : '--'}
              subtitle={stats.bestDay?.date ? new Date(stats.bestDay.date).toLocaleDateString('zh-CN') : undefined}
              trend={stats.bestDay?.pnlPct && stats.bestDay.pnlPct >= 0 ? 'up' : 'down'}
            />
            <SummaryCard
              title="最差交易日"
              value={stats.worstDay?.pnlPct != null ? `${stats.worstDay.pnlPct >= 0 ? '+' : ''}${stats.worstDay.pnlPct.toFixed(2)}%` : '--'}
              subtitle={stats.worstDay?.date ? new Date(stats.worstDay.date).toLocaleDateString('zh-CN') : undefined}
              trend={stats.worstDay?.pnlPct && stats.worstDay.pnlPct >= 0 ? 'up' : 'down'}
            />
            <SummaryCard
              title="活跃持仓"
              value={`${currentPortfolio?.holdings?.filter(h => !h.isClosed).length || 0}只`}
              trend="neutral"
            />
            <SummaryCard
              title="本周平仓"
              value={`${performance?.dataPoints?.[performance.dataPoints.length - 1]?.holdings ? Object.keys(performance.dataPoints[performance.dataPoints.length - 1].holdings || {}).filter(k => {
                const h = currentPortfolio?.holdings?.find(hold => hold.code === k);
                return h?.isClosed;
              }).length : 0}只`}
              trend="neutral"
            />
          </div>
        )}

        {currentPortfolio && holdingsInfo.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-medium text-white mb-3">持仓收益分解</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-elevated text-left">
                    <th className="px-3 py-2 text-xs font-medium text-secondary">代码</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary">名称</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">贡献度</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">收益率</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">占比</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary">区间收益</th>
                  </tr>
                </thead>
                <tbody>
                  {currentPortfolio.holdings.filter(h => !h.isClosed).map((holding) => {
                    const weightedPnl = holding.pnlPct * holding.weight / 100;
                    const barWidth = Math.min(Math.abs(holding.pnlPct) * 10, 100);
                    return (
                      <tr key={holding.id} className="border-t border-white/5">
                        <td className="px-3 py-2 font-mono text-cyan text-xs">{holding.code}</td>
                        <td className="px-3 py-2 text-xs text-white">{holding.name}</td>
                        <td className={`px-3 py-2 text-right font-mono text-xs ${weightedPnl >= 0 ? 'text-success' : 'text-danger'}`}>
                          {weightedPnl >= 0 ? '+' : ''}{weightedPnl.toFixed(2)}%
                        </td>
                        <td className={`px-3 py-2 text-right font-mono text-xs ${(holding.pnlPct ?? 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                          {(holding.pnlPct ?? 0) >= 0 ? '+' : ''}{(holding.pnlPct ?? 0).toFixed(2)}%
                        </td>
                        <td className="px-3 py-2 text-right font-mono text-xs text-secondary">{holding.weight}%</td>
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-elevated rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${(holding.pnlPct ?? 0) >= 0 ? 'bg-success' : 'bg-danger'}`}
                                style={{ width: `${barWidth}%` }}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {closedHoldings.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm font-medium text-white mb-3">已平仓持仓收益</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-elevated text-left">
                    <th className="px-3 py-2 text-xs font-medium text-secondary">代码</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary">名称</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">收益率</th>
                    <th className="px-3 py-2 text-xs font-medium text-secondary text-right">平仓盈亏</th>
                  </tr>
                </thead>
                <tbody>
                  {closedHoldings.map((holding) => {
                    const pnlAmount = holding.closeQuantity && holding.closePrice && holding.entryPrice
                      ? (holding.closePrice - holding.entryPrice) * holding.closeQuantity
                      : 0;
                    const pnlPct = holding.entryPrice > 0 && holding.closePrice
                      ? ((holding.closePrice - holding.entryPrice) / holding.entryPrice) * 100
                      : 0;
                    return (
                      <tr key={holding.id} className="border-t border-white/5 opacity-60">
                        <td className="px-3 py-2 font-mono text-xs text-muted">{holding.code}</td>
                        <td className="px-3 py-2 text-xs text-secondary">{holding.name}</td>
                        <td className={`px-3 py-2 text-right font-mono text-xs ${pnlPct >= 0 ? 'text-success' : 'text-danger'}`}>
                          {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%
                        </td>
                        <td className={`px-3 py-2 text-right font-mono text-xs ${pnlAmount >= 0 ? 'text-success' : 'text-danger'}`}>
                          {pnlAmount >= 0 ? '+' : ''}¥{Math.abs(pnlAmount).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    );
                  })}
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
