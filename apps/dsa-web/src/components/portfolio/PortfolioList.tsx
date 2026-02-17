import React from 'react';
import { PortfolioCard } from './PortfolioCard';
import type { PortfolioListItem } from '../../api/portfolio';

interface PortfolioListProps {
  portfolios: PortfolioListItem[];
  isLoading?: boolean;
  onDelete?: (id: number) => void;
}

export const PortfolioList: React.FC<PortfolioListProps> = ({
  portfolios,
  isLoading = false,
  onDelete,
}) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="portfolio-card glass-card animate-pulse">
            <div className="skeleton-line w-3/4 h-4 mb-2"></div>
            <div className="skeleton-line w-1/2 h-3 mb-4"></div>
            <div className="skeleton-line w-full h-8 mb-2"></div>
            <div className="skeleton-line w-2/3 h-3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (portfolios.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 mb-4 rounded-xl bg-elevated flex items-center justify-center">
          <svg className="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h3 className="text-base font-medium text-white mb-1.5">创建您的第一个投资组合</h3>
        <p className="text-xs text-muted text-center max-w-xs">
          开始追踪您的投资收益
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {portfolios.map((portfolio) => (
        <PortfolioCard
          key={portfolio.id}
          portfolio={portfolio}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};

export default PortfolioList;
