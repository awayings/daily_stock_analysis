import type React from 'react';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { HoldingTable, AddHoldingModal, ClosePositionModal, SummaryCard, HistoryPanel, PerformancePanel } from '../components/portfolio';
import { usePortfolioStore } from '../stores';
import type { Holding, ClosePositionRequest } from '../api/portfolio';

const PortfolioDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentPortfolio,
    history,
    performance,
    isLoading,
    error,
    fetchPortfolio,
    fetchHistory,
    fetchPerformance,
    addHolding,
    closePosition,
    rebalanceHoldings,
    calculatePortfolio,
    clearError,
  } = usePortfolioStore();

  const [activeTab, setActiveTab] = useState<'holdings' | 'performance' | 'history'>('holdings');
  const [showAddHolding, setShowAddHolding] = useState(false);
  const [closePositionHolding, setClosePositionHolding] = useState<Holding | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyHasMore, setHistoryHasMore] = useState(true);

  const portfolioId = parseInt(id || '0', 10);

  const loadPortfolio = useCallback(() => {
    if (portfolioId) {
      fetchPortfolio(portfolioId);
    }
  }, [portfolioId, fetchPortfolio]);

  const loadHistory = useCallback(() => {
    if (portfolioId) {
      fetchHistory(portfolioId, { page: 1, limit: 20 });
      setHistoryPage(1);
      setHistoryHasMore(true);
    }
  }, [portfolioId, fetchHistory]);

  const loadHistoryMore = useCallback(() => {
    if (portfolioId && historyHasMore) {
      fetchHistory(portfolioId, { page: historyPage + 1, limit: 20 }).then(() => {
        setHistoryPage(prev => prev + 1);
      });
    }
  }, [portfolioId, historyHasMore, historyPage, fetchHistory]);

  const loadPerformance = useCallback(() => {
    if (portfolioId) {
      fetchPerformance(portfolioId, { viewMode: 'portfolio' });
    }
  }, [portfolioId, fetchPerformance]);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  useEffect(() => {
    if (activeTab === 'history') {
      loadHistory();
    } else if (activeTab === 'performance') {
      loadPerformance();
    }
  }, [activeTab, loadHistory, loadPerformance]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleAddHolding = async (data: { code: string; entryPrice: number; weight: number }) => {
    try {
      await addHolding(portfolioId, data);
      setShowAddHolding(false);
      setToast({ type: 'success', message: '添加持仓成功' });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || '添加持仓失败' });
    }
  };

  const handleClosePosition = async (data: ClosePositionRequest) => {
    if (!closePositionHolding) return;
    try {
      const result = await closePosition(portfolioId, closePositionHolding.id, data);
      setClosePositionHolding(null);
      setToast({
        type: 'success',
        message: `${closePositionHolding.code} 平仓成功，盈亏: ${result.pnl.amount >= 0 ? '+' : ''}¥${result.pnl.amount.toFixed(2)}`
      });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || '平仓失败' });
    }
  };

  const handleRebalance = async () => {
    try {
      await rebalanceHoldings(portfolioId);
      setToast({ type: 'success', message: '仓位重平衡成功' });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || '仓位重平衡失败' });
    }
  };

  const handleCalculate = async () => {
    try {
      await calculatePortfolio(portfolioId);
      await fetchPortfolio(portfolioId);
      setToast({ type: 'success', message: '计算完成' });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || '计算失败' });
    }
  };

  if (isLoading && !currentPortfolio) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-10 h-10 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
      </div>
    );
  }

  if (!currentPortfolio) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <p className="text-muted mb-4">组合不存在</p>
        <Button variant="secondary" onClick={() => navigate('/portfolios')}>
          返回列表
        </Button>
      </div>
    );
  }

  const summary = currentPortfolio.summary;
  const activeHoldings = currentPortfolio.holdings.filter(h => !h.isClosed);
  const closedHoldings = currentPortfolio.holdings.filter(h => h.isClosed);

  const formatCurrency = (value?: number) => {
    if (value == null) return '¥0.00';
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPnl = (value?: number) => {
    if (value == null) return '0.00%';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex-shrink-0 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/portfolios')}
              className="flex items-center gap-2 text-muted hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
            <h1 className="text-xl font-semibold text-white">{currentPortfolio.name}</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => navigate(`/portfolios/${portfolioId}/edit`)}>
              编辑
            </Button>
            <Button variant="ghost" size="sm" onClick={handleCalculate}>
              计算
            </Button>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-4 mt-4 p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">
          {error}
        </div>
      )}

      {toast && (
        <div className={`fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm animate-slide-in-right ${
          toast.type === 'success'
            ? 'border-success/30 bg-success/10 text-success'
            : 'border-danger/30 bg-danger/10 text-danger'
        }`}>
          <span>{toast.type === 'success' ? '✓' : '✕'}</span>
          <span className="text-sm">{toast.message}</span>
        </div>
      )}

      <main className="flex-1 overflow-auto p-4 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard
            title="总市值"
            value={formatCurrency(summary.totalValue)}
          />
          <SummaryCard
            title="总盈亏"
            value={formatPnl(summary.totalPnlPct)}
            subtitle={formatCurrency(summary.totalPnlAmount)}
            trend={summary.totalPnlPct >= 0 ? 'up' : 'down'}
          />
          <SummaryCard
            title="持仓数"
            value={`${activeHoldings.length}只活跃`}
            subtitle={closedHoldings.length > 0 ? `${closedHoldings.length}只已平仓` : undefined}
          />
          <SummaryCard
            title="最佳表现"
            value={activeHoldings.length > 0 ? activeHoldings[0].code : '--'}
            subtitle={activeHoldings.length > 0 ? formatPnl(activeHoldings[0].pnlPct) : undefined}
          />
        </div>

        <div className="flex gap-4 border-b border-white/5">
          {(['holdings', 'performance', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'text-cyan border-b-2 border-cyan'
                  : 'text-muted hover:text-white'
              }`}
            >
              {tab === 'holdings' ? '持仓列表' : tab === 'performance' ? '收益走势' : '历史记录'}
            </button>
          ))}
        </div>

        {activeTab === 'holdings' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <Button variant="outline" size="sm" onClick={() => setShowAddHolding(true)}>
                添加持仓
              </Button>
              {activeHoldings.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleRebalance}>
                  重新平衡
                </Button>
              )}
            </div>

            <div className="glass-card overflow-hidden">
              {currentPortfolio.holdings.length > 0 ? (
                <HoldingTable
                  holdings={currentPortfolio.holdings}
                  onClosePosition={(holding) => setClosePositionHolding(holding)}
                />
              ) : (
                <div className="text-center py-12 text-muted">
                  暂无持仓
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <PerformancePanel
            performance={performance}
            isLoading={isLoading}
            onFetchPerformance={(params) => fetchPerformance(portfolioId, params)}
          />
        )}

        {activeTab === 'history' && (
          <HistoryPanel
            items={history}
            isLoading={isLoading}
            onLoadMore={loadHistoryMore}
            hasMore={historyHasMore}
          />
        )}
      </main>

      <AddHoldingModal
        isOpen={showAddHolding}
        onClose={() => setShowAddHolding(false)}
        onAdd={handleAddHolding}
      />

      <ClosePositionModal
        isOpen={!!closePositionHolding}
        holding={closePositionHolding}
        onClose={() => setClosePositionHolding(null)}
        onConfirm={handleClosePosition}
      />
    </div>
  );
};

export default PortfolioDetailPage;
