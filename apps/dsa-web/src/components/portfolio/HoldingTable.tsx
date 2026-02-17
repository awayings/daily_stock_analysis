import React from 'react';
import type { Holding } from '../../api/portfolio';

interface HoldingTableProps {
  holdings: Holding[];
  onClosePosition?: (holding: Holding) => void;
}

function formatCurrency(value?: number): string {
  if (value == null || isNaN(value)) return '¥--';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPnl(value?: number): string {
  if (value == null || isNaN(value)) return '--';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function formatWeight(value?: number): string {
  if (value == null || isNaN(value)) return '--';
  return `${value.toFixed(2)}%`;
}

export const HoldingTable: React.FC<HoldingTableProps> = ({ holdings, onClosePosition }) => {
  const activeHoldings = holdings.filter(h => !h.isClosed);
  const closedHoldings = holdings.filter(h => h.isClosed);

  return (
    <div className="holdings-table">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-elevated text-left">
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">代码</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">名称</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">建仓价格</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">当前价格</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">占比</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-right">盈亏</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider">状态</th>
            <th className="px-3 py-2.5 text-xs font-medium text-secondary uppercase tracking-wider text-center">操作</th>
          </tr>
        </thead>
        <tbody>
          {activeHoldings.map((holding) => (
            <tr key={holding.id} className="border-t border-white/5 hover:bg-hover transition-colors">
              <td className="px-3 py-2 font-mono text-cyan text-xs">{holding.code}</td>
              <td className="px-3 py-2 text-xs text-white">{holding.name || '--'}</td>
              <td className="px-3 py-2 text-xs font-mono text-right text-secondary">{formatCurrency(holding.entryPrice)}</td>
              <td className="px-3 py-2 text-xs font-mono text-right text-white">{formatCurrency(holding.currentPrice)}</td>
              <td className="px-3 py-2 text-xs font-mono text-right text-secondary">{formatWeight(holding.weight)}</td>
              <td className={`px-3 py-2 text-xs font-mono text-right ${(holding.pnlPct ?? 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                {formatPnl(holding.pnlPct)}
              </td>
              <td className="px-3 py-2">
                <span className="badge badge-success text-xs">活跃</span>
              </td>
              <td className="px-3 py-2 text-center">
                {onClosePosition && (
                  <button
                    className="btn-close-position text-xs"
                    onClick={() => onClosePosition(holding)}
                  >
                    平仓
                  </button>
                )}
              </td>
            </tr>
          ))}
          {closedHoldings.length > 0 && (
            <>
              <tr className="border-t border-white/5">
                <td colSpan={8} className="px-3 py-2 text-xs text-muted bg-white/[0.02]">
                  ──────────────── 已平仓持仓 ─────────────────────
                </td>
              </tr>
              {closedHoldings.map((holding) => (
                <tr key={holding.id} className="border-t border-white/5 bg-white/[0.02] opacity-60">
                  <td className="px-3 py-2 font-mono text-muted text-xs">{holding.code}</td>
                  <td className="px-3 py-2 text-xs text-secondary">{holding.name || '--'}</td>
                  <td className="px-3 py-2 text-xs font-mono text-right text-muted">{formatCurrency(holding.entryPrice)}</td>
                  <td className="px-3 py-2 text-xs font-mono text-right text-muted">{formatCurrency(holding.closePrice || holding.currentPrice)}</td>
                  <td className="px-3 py-2 text-xs font-mono text-right text-muted">--</td>
                  <td className={`px-3 py-2 text-xs font-mono text-right ${((holding.closePrice ?? 0) - (holding.entryPrice ?? 0)) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {formatPnl(((holding.closePrice ?? 0) / (holding.entryPrice ?? 1) - 1) * 100)}
                  </td>
                  <td className="px-3 py-2">
                    <span className="badge badge-neutral text-xs">已平仓</span>
                  </td>
                  <td className="px-3 py-2 text-xs text-muted text-center">
                    {holding.closePrice && holding.closeQuantity
                      ? `${holding.closeQuantity}股 @ ${formatCurrency(holding.closePrice)}`
                      : '--'}
                  </td>
                </tr>
              ))}
            </>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default HoldingTable;
