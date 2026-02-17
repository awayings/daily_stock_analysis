import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { PortfolioListItem } from '../../api/portfolio';

interface PortfolioCardProps {
  portfolio: PortfolioListItem;
  onDelete?: (id: number) => void;
}

function formatCurrency(value?: number): string {
  if (value == null || isNaN(value)) return '¥0.00';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
}

function formatPnl(value?: number): string {
  if (value == null || isNaN(value)) return '0.00%';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function timeAgo(dateString?: string): string {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}天前更新`;
  if (hours > 0) return `${hours}小时前更新`;
  if (minutes > 0) return `${minutes}分钟前更新`;
  return '刚刚更新';
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio, onDelete }) => {
  const navigate = useNavigate();
  const isPositive = (portfolio.totalPnlPct ?? 0) >= 0;

  const handleClick = () => {
    navigate(`/portfolios/${portfolio.id}`);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete && confirm(`确定要删除"${portfolio.name}"吗？`)) {
      onDelete(portfolio.id);
    }
  };

  return (
    <div
      className="portfolio-card glass-card cursor-pointer"
      onClick={handleClick}
    >
      <div className="card-header">
        <div className="card-title">
          <span className="name text-white font-semibold">{portfolio.name}</span>
          <span className="badge badge-cyan text-xs">
            {portfolio.holdingsCount}个持仓
          </span>
        </div>
        <div className="card-actions flex gap-1">
          <button
            className="btn-icon p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            title="编辑"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/portfolios/${portfolio.id}/edit`);
            }}
          >
            <svg className="w-4 h-4 text-muted hover:text-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            className="btn-icon p-1.5 rounded-lg hover:bg-white/5 transition-colors"
            title="删除"
            onClick={handleDelete}
          >
            <svg className="w-4 h-4 text-muted hover:text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <div className="card-body">
        <div className={`pnl-display text-2xl font-bold font-mono ${isPositive ? 'text-success' : 'text-danger'}`}>
          {formatPnl(portfolio.totalPnlPct)}
          <span className="text-base ml-1">{isPositive ? '📈' : '📉'}</span>
        </div>
        <div className="value-display mt-2">
          <span className="label text-xs text-muted">总市值</span>
          <span className="value text-sm font-mono text-secondary ml-2">
            {formatCurrency(portfolio.totalValue)}
          </span>
        </div>
      </div>

      <div className="card-footer mt-3 pt-3 border-t border-white/5">
        <span className="timestamp text-xs text-muted">{timeAgo(portfolio.updatedAt)}</span>
      </div>
    </div>
  );
};

export default PortfolioCard;
