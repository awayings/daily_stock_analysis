import type React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { PerformanceChart } from './PerformanceChart';
import type { PerformanceResponse } from '../../api/portfolio';

interface PerformancePanelProps {
  performance: PerformanceResponse | null;
  isLoading: boolean;
  onFetchPerformance: (params?: { startDate?: string; endDate?: string; viewMode?: string }) => Promise<void>;
}

type TimeRange = '1w' | '1m' | '3m' | '6m' | '1y';

const TIME_RANGES: { key: TimeRange; label: string; days: number }[] = [
  { key: '1w', label: '1周', days: 7 },
  { key: '1m', label: '1月', days: 30 },
  { key: '3m', label: '3月', days: 90 },
  { key: '6m', label: '6月', days: 180 },
  { key: '1y', label: '1年', days: 365 },
];

const formatCurrency = (value?: number): string => {
  if (value == null) return '¥0.00';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
};

const formatPnl = (value?: number): string => {
  if (value == null) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}月${date.getDate()}日`;
};

export const PerformancePanel: React.FC<PerformancePanelProps> = ({
  performance,
  isLoading,
  onFetchPerformance,
}) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('1m');
  const [viewMode, setViewMode] = useState<'portfolio' | 'holdings'>('portfolio');

  const handleTimeRangeChange = useCallback((range: TimeRange) => {
    setTimeRange(range);
    const selectedRange = TIME_RANGES.find(r => r.key === range);
    if (selectedRange) {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - selectedRange.days);
      
      onFetchPerformance({
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        viewMode,
      });
    }
  }, [onFetchPerformance, viewMode]);

  const handleViewModeChange = useCallback((mode: 'portfolio' | 'holdings') => {
    setViewMode(mode);
    const selectedRange = TIME_RANGES.find(r => r.key === timeRange);
    if (selectedRange) {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - selectedRange.days);
      
      onFetchPerformance({
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        viewMode: mode,
      });
    }
  }, [onFetchPerformance, timeRange]);

  useEffect(() => {
    const selectedRange = TIME_RANGES.find(r => r.key === timeRange);
    if (selectedRange) {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - selectedRange.days);
      
      onFetchPerformance({
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0],
        viewMode,
      });
    }
  }, []);

  const stats = performance?.statistics;
  const dataPoints = performance?.dataPoints || [];

  const holdings = performance?.dataPoints?.[0]?.holdings 
    ? Object.entries(performance.dataPoints[0].holdings).map(([code]) => ({ code, name: code }))
    : [];

  if (isLoading && !performance) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted">时间范围：</span>
          <div className="flex gap-1">
            {TIME_RANGES.map((range) => (
              <button
                key={range.key}
                onClick={() => handleTimeRangeChange(range.key)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  timeRange === range.key
                    ? 'bg-cyan/20 text-cyan border border-cyan/30'
                    : 'text-muted hover:text-white hover:bg-white/5'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-muted">视图：</span>
          <div className="flex gap-1">
            <button
              onClick={() => handleViewModeChange('portfolio')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'portfolio'
                  ? 'bg-cyan/20 text-cyan border border-cyan/30'
                  : 'text-muted hover:text-white hover:bg-white/5'
              }`}
            >
              组合总体
            </button>
            <button
              onClick={() => handleViewModeChange('holdings')}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
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
        <PerformanceChart
          dataPoints={dataPoints}
          viewMode={viewMode}
          holdings={holdings}
        />
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card p-4">
            <div className="text-xs text-muted uppercase tracking-wider mb-1">总收益率</div>
            <div className={`text-xl font-bold font-mono ${
              (stats.totalReturnPct || 0) >= 0 ? 'text-success' : 'text-danger'
            }`}>
              {formatPnl(stats.totalReturnPct)}
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-muted uppercase tracking-wider mb-1">浮动盈亏</div>
            <div className={`text-xl font-bold font-mono ${
              (stats.unrealizedReturnPct || 0) >= 0 ? 'text-success' : 'text-danger'
            }`}>
              {formatPnl(stats.unrealizedReturnPct)}
            </div>
            <div className="text-xs text-muted mt-1">
              {formatCurrency((performance?.dataPoints?.[performance.dataPoints.length - 1]?.unrealizedPnlAmount) || 0)}
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-muted uppercase tracking-wider mb-1">已实现盈亏</div>
            <div className={`text-xl font-bold font-mono ${
              (stats.realizedReturnPct || 0) >= 0 ? 'text-success' : 'text-danger'
            }`}>
              {formatPnl(stats.realizedReturnPct)}
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-muted uppercase tracking-wider mb-1">最大回撤</div>
            <div className="text-xl font-bold font-mono text-danger">
              {formatPnl(stats.maxDrawdownPct)}
            </div>
          </div>
        </div>
      )}

      {stats && (stats.bestDay || stats.worstDay) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.bestDay && (
            <div className="glass-card p-4">
              <div className="text-xs text-muted uppercase tracking-wider mb-1">最佳交易日</div>
              <div className="text-xl font-bold font-mono text-success">
                {formatPnl(stats.bestDay.pnlPct)}
              </div>
              <div className="text-xs text-muted mt-1">
                {formatDate(stats.bestDay.date)}
              </div>
            </div>
          )}
          {stats.worstDay && (
            <div className="glass-card p-4">
              <div className="text-xs text-muted uppercase tracking-wider mb-1">最差交易日</div>
              <div className="text-xl font-bold font-mono text-danger">
                {formatPnl(stats.worstDay.pnlPct)}
              </div>
              <div className="text-xs text-muted mt-1">
                {formatDate(stats.worstDay.date)}
              </div>
            </div>
          )}
        </div>
      )}

      {holdings.length > 0 && (
        <div className="glass-card p-4">
          <h3 className="text-sm font-medium text-white mb-4">持仓收益分解</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted uppercase tracking-wider border-b border-white/5">
                  <th className="px-3 py-2.5 font-medium">代码</th>
                  <th className="px-3 py-2.5 font-medium text-right">收益率</th>
                  <th className="px-3 py-2.5 font-medium text-right">占比</th>
                  <th className="px-3 py-2.5 font-medium text-right">贡献度</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding) => {
                  const latestPoint = dataPoints[dataPoints.length - 1];
                  const holdingData = latestPoint?.holdings?.[holding.code];
                  const pnlPct = holdingData?.pnlPct || 0;
                  const weightedPnl = holdingData?.weightedPnl || 0;
                  
                  return (
                    <tr key={holding.code} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="px-3 py-3">
                        <span className="text-cyan font-mono text-xs">{holding.code}</span>
                      </td>
                      <td className={`px-3 py-3 text-right font-mono text-xs ${
                        pnlPct >= 0 ? 'text-success' : 'text-danger'
                      }`}>
                        {formatPnl(pnlPct)}
                      </td>
                      <td className="px-3 py-3 text-right font-mono text-xs text-secondary">
                        --
                      </td>
                      <td className={`px-3 py-3 text-right font-mono text-xs ${
                        weightedPnl >= 0 ? 'text-success' : 'text-danger'
                      }`}>
                        {formatPnl(weightedPnl)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformancePanel;
