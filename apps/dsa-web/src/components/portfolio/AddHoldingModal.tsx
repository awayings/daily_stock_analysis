import React, { useState } from 'react';
import { Button } from '../common';
import { StockSearchInput } from './StockSearchInput';
import type { StockSearchResult } from '../../api/stocks';

interface AddHoldingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (data: { code: string; entryPrice: number; weight: number; lastPrice?: number }) => void;
}

export const AddHoldingModal: React.FC<AddHoldingModalProps> = ({ isOpen, onClose, onAdd }) => {
  const [code, setCode] = useState('');
  const [stockName, setStockName] = useState('');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [entryPrice, setEntryPrice] = useState('');
  const [lastPrice, setLastPrice] = useState('');
  const [weight, setWeight] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleStockSelect = (selectedCode: string, stock?: StockSearchResult) => {
    setCode(selectedCode);
    if (stock) {
      setStockName(stock.name || '');
      if (stock.close) {
        setCurrentPrice(stock.close);
        setEntryPrice(stock.close.toFixed(2));
        setLastPrice(stock.close.toFixed(2));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || !entryPrice || !weight) return;

    setIsLoading(true);
    try {
      onAdd({
        code: code.toUpperCase(),
        entryPrice: parseFloat(entryPrice),
        lastPrice: lastPrice ? parseFloat(lastPrice) : undefined,
        weight: parseFloat(weight),
      });
      setCode('');
      setStockName('');
      setCurrentPrice(null);
      setEntryPrice('');
      setLastPrice('');
      setWeight('');
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop active" onClick={onClose}>
      <div className="modal-content max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header flex justify-between items-center p-4 border-b border-white/5">
          <h3 className="text-lg font-semibold text-white">添加持仓</h3>
          <button onClick={onClose} className="text-muted hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-xs text-secondary mb-1.5">股票代码 *</label>
            <StockSearchInput
              value={code}
              onChange={handleStockSelect}
              placeholder="搜索股票代码或名称..."
            />
            {stockName && (
              <p className="mt-1 text-xs text-muted">{stockName}</p>
            )}
          </div>

          <div>
            <label className="block text-xs text-secondary mb-1.5">建仓价格 *</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted">¥</span>
              <input
                type="number"
                step="0.01"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                placeholder={currentPrice ? `当前价: ¥${currentPrice.toFixed(2)}` : "0.00"}
                className="input-terminal w-full pl-7"
                required
              />
            </div>
            {currentPrice && (
              <p className="mt-1 text-xs text-muted">当前价格: ¥{currentPrice.toFixed(2)}</p>
            )}
          </div>

          <div>
            <label className="block text-xs text-secondary mb-1.5">上次价格 (可选)</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted">¥</span>
              <input
                type="number"
                step="0.01"
                value={lastPrice}
                onChange={(e) => setLastPrice(e.target.value)}
                placeholder="默认为建仓价格"
                className="input-terminal w-full pl-7"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-secondary mb-1.5">仓位占比 *</label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="0.00"
                className="input-terminal w-full pr-8"
                required
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-muted">%</span>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" variant="primary" isLoading={isLoading}>
              添加到组合
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddHoldingModal;
