import type React from 'react';
import { useCallback } from 'react';
import type { PortfolioHistoryItem } from '../../api/portfolio';

interface HistoryPanelProps {
  items: PortfolioHistoryItem[];
  isLoading: boolean;
  onLoadMore: () => void;
  hasMore: boolean;
}

const formatDate = (dateStr: string | undefined): string => {
  if (!dateStr) return '--';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};

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

export const HistoryPanel: React.FC<HistoryPanelProps> = ({
  items,
  isLoading,
  onLoadMore,
  hasMore,
}) => {
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    const { scrollTop, scrollHeight, clientHeight } = target;
    if (scrollHeight - scrollTop - clientHeight < 100 && hasMore && !isLoading) {
      onLoadMore();
    }
  }, [hasMore, isLoading, onLoadMore]);

  if (isLoading && items.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="w-6 h-6 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[200px] text-muted">
        <svg className="w-12 h-12 mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p>暂无历史记录</p>
        <p className="text-xs mt-1">请先添加持仓并触发计算</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" onScroll={handleScroll}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted uppercase tracking-wider border-b border-white/5">
              <th className="px-3 py-2.5 font-medium">日期</th>
              <th className="px-3 py-2.5 font-medium text-right">总市值</th>
              <th className="px-3 py-2.5 font-medium text-right">浮动盈亏</th>
              <th className="px-3 py-2.5 font-medium text-right">已实现盈亏</th>
              <th className="px-3 py-2.5 font-medium text-right">总盈亏</th>
              <th className="px-3 py-2.5 font-medium text-center">持仓数</th>
              <th className="px-3 py-2.5 font-medium text-center">状态</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className="border-b border-white/5 hover:bg-white/[0.02] transition-colors"
              >
                <td className="px-3 py-3 text-white font-mono text-xs">
                  {formatDate(item.snapshotDate)}
                </td>
                <td className="px-3 py-3 text-right font-mono text-secondary text-xs">
                  {formatCurrency(item.totalValue)}
                </td>
                <td className={`px-3 py-3 text-right font-mono text-xs ${
                  (item.unrealizedPnlPct || 0) >= 0 ? 'text-success' : 'text-danger'
                }`}>
                  {formatPnl(item.unrealizedPnlPct)}
                  <div className="text-[10px] opacity-70">
                    {formatCurrency(item.unrealizedPnlAmount)}
                  </div>
                </td>
                <td className={`px-3 py-3 text-right font-mono text-xs ${
                  (item.realizedPnlAmount || 0) >= 0 ? 'text-success' : 'text-danger'
                }`}>
                  {formatCurrency(item.realizedPnlAmount)}
                </td>
                <td className={`px-3 py-3 text-right font-mono text-xs ${
                  (item.totalPnlPct || 0) >= 0 ? 'text-success' : 'text-danger'
                }`}>
                  {formatPnl(item.totalPnlPct)}
                  <div className="text-[10px] opacity-70">
                    {formatCurrency(item.totalPnlAmount)}
                  </div>
                </td>
                <td className="px-3 py-3 text-center text-secondary text-xs">
                  <span className="text-success">{item.activeHoldingsCount}</span>
                  {item.closedHoldingsCount > 0 && (
                    <span className="text-muted"> / {item.closedHoldingsCount}</span>
                  )}
                </td>
                <td className="px-3 py-3 text-center">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    item.calculationStatus === 'success'
                      ? 'bg-success/10 text-success'
                      : item.calculationStatus === 'failed'
                      ? 'bg-danger/10 text-danger'
                      : 'bg-warning/10 text-warning'
                  }`}>
                    {item.calculationStatus === 'success' ? '成功' : 
                     item.calculationStatus === 'failed' ? '失败' : '处理中'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {isLoading && (
        <div className="flex justify-center py-4">
          <div className="w-5 h-5 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
        </div>
      )}

      {!hasMore && items.length > 0 && (
        <div className="text-center py-3 text-muted/50 text-xs">
          已加载全部 {items.length} 条记录
        </div>
      )}
    </div>
  );
};

export default HistoryPanel;
