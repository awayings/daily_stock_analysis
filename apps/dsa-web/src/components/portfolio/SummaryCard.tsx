import React from 'react';

interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

function formatPnl(value?: number | string): string {
  if (value == null) return '--';
  if (typeof value === 'string') return value;
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  className = '',
}) => {
  const isPositive = trend === 'up';
  const isNegative = trend === 'down';

  return (
    <div className={`glass-card p-4 ${className}`}>
      <span className="label-uppercase text-xs text-muted">{title}</span>
      <div className={`text-2xl font-bold font-mono mt-1 ${
        isPositive ? 'text-success' : isNegative ? 'text-danger' : 'text-white'
      }`}>
        {String(value).includes('%') || String(value).includes('¥') ? value : formatPnl(value as number)}
      </div>
      {subtitle && (
        <span className="text-xs text-muted mt-1 block">{subtitle}</span>
      )}
    </div>
  );
};

export default SummaryCard;
