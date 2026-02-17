import React, { useState, useEffect } from 'react';
import { Button } from '../common';
import type { Holding, ClosePositionRequest } from '../../api/portfolio';

interface ClosePositionModalProps {
  isOpen: boolean;
  holding: Holding | null;
  onClose: () => void;
  onConfirm: (data: ClosePositionRequest) => void;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
  }).format(value);
}

export const ClosePositionModal: React.FC<ClosePositionModalProps> = ({
  isOpen,
  holding,
  onClose,
  onConfirm,
}) => {
  const [priceType, setPriceType] = useState<'current' | 'specified'>('current');
  const [specifiedPrice, setSpecifiedPrice] = useState<string>('');
  const [quantityType, setQuantityType] = useState<'all' | 'partial'>('all');
  const [quantity, setQuantity] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (holding) {
      setSpecifiedPrice(String(holding.currentPrice || ''));
      setQuantity(String(holding.shares || ''));
    }
  }, [holding]);

  if (!isOpen || !holding) return null;

  const actualPrice = priceType === 'current' ? holding.currentPrice : parseFloat(specifiedPrice) || 0;
  const actualQuantity = quantityType === 'all' ? (holding.shares || 0) : parseFloat(quantity) || 0;

  const pnlAmount = (actualPrice - holding.entryPrice) * actualQuantity;
  const pnlPct = holding.entryPrice > 0 ? ((actualPrice - holding.entryPrice) / holding.entryPrice) * 100 : 0;
  const closeAmount = actualPrice * actualQuantity;

  const remainingShares = (holding.shares || 0) - actualQuantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      onConfirm({
        priceType,
        specifiedPrice: priceType === 'specified' ? parseFloat(specifiedPrice) : undefined,
        quantityType,
        quantity: quantityType === 'partial' ? parseFloat(quantity) : undefined,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop active" onClick={onClose}>
      <div className="modal-content max-w-lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header flex justify-between items-center p-4 border-b border-white/5">
          <h3 className="text-lg font-semibold text-white">平仓持仓</h3>
          <button onClick={onClose} className="text-muted hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="glass-card p-3">
            <div className="flex items-center gap-2">
              <span className="font-mono text-cyan font-semibold">{holding.code}</span>
              <span className="text-white">{holding.name}</span>
            </div>
            <div className="flex gap-4 mt-2 text-xs text-secondary">
              <span>建仓价格：{formatCurrency(holding.entryPrice)}</span>
              <span>持仓数量：{holding.shares}股</span>
              <span>占比：{holding.weight}%</span>
            </div>
          </div>

          <div>
            <label className="block text-xs text-secondary mb-2">平仓方式</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-hover cursor-pointer">
                <input
                  type="radio"
                  name="priceType"
                  checked={priceType === 'current'}
                  onChange={() => setPriceType('current')}
                  className="accent-cyan"
                />
                <span className="text-sm">按当前收盘价卖出（推荐）</span>
              </label>
              {priceType === 'current' && (
                <div className="ml-6 flex items-center gap-2 p-2 bg-elevated rounded text-xs">
                  <span>当前收盘价：{formatCurrency(holding.currentPrice)}</span>
                </div>
              )}

              <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-hover cursor-pointer">
                <input
                  type="radio"
                  name="priceType"
                  checked={priceType === 'specified'}
                  onChange={() => setPriceType('specified')}
                  className="accent-cyan"
                />
                <span className="text-sm">指定价格卖出</span>
              </label>
              {priceType === 'specified' && (
                <div className="ml-6 p-2 bg-elevated rounded">
                  <div className="flex items-center gap-2">
                    <span className="text-xs">卖出价格：¥</span>
                    <input
                      type="number"
                      step="0.01"
                      value={specifiedPrice}
                      onChange={(e) => setSpecifiedPrice(e.target.value)}
                      className="input-terminal w-32 text-sm"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs text-secondary mb-2">平仓数量</label>
            <div className="space-y-2">
              <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-hover cursor-pointer">
                <input
                  type="radio"
                  name="quantityType"
                  checked={quantityType === 'all'}
                  onChange={() => setQuantityType('all')}
                  className="accent-cyan"
                />
                <span className="text-sm">全部平仓（{holding.shares}股）</span>
              </label>

              <label className="flex items-center gap-2 p-2 rounded-lg hover:bg-hover cursor-pointer">
                <input
                  type="radio"
                  name="quantityType"
                  checked={quantityType === 'partial'}
                  onChange={() => setQuantityType('partial')}
                  className="accent-cyan"
                />
                <span className="text-sm">部分平仓</span>
              </label>
              {quantityType === 'partial' && (
                <div className="ml-6 p-3 bg-elevated rounded space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs">数量：</span>
                    <input
                      type="number"
                      min={1}
                      max={holding.shares}
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      className="input-terminal w-24 text-sm"
                    />
                    <span className="text-xs text-muted">股</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={holding.shares ? (parseFloat(quantity || '0') / holding.shares) * 100 : 0}
                      onChange={(e) => setQuantity(String(Math.round((holding.shares || 0) * parseFloat(e.target.value) / 100)))}
                      className="flex-1 accent-cyan"
                    />
                    <span className="text-xs text-muted w-12 text-right">
                      {holding.shares ? ((parseFloat(quantity || '0') / holding.shares) * 100).toFixed(0) : 0}%
                    </span>
                  </div>
                  <div className="text-xs text-warning">
                    剩余：{remainingShares}股
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="glass-card p-4 border border-white/10">
            <div className="flex justify-between py-1">
              <span className="text-xs text-secondary">预计盈亏：</span>
              <span className={`text-sm font-mono font-semibold ${pnlAmount >= 0 ? 'text-success' : 'text-danger'}`}>
                {pnlAmount >= 0 ? '+' : ''}{formatCurrency(pnlAmount)} ({pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(2)}%)
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-xs text-secondary">平仓金额：</span>
              <span className="text-sm font-mono">{formatCurrency(closeAmount)}</span>
            </div>
            {quantityType === 'partial' && (
              <div className="flex justify-between py-1 text-warning">
                <span className="text-xs">剩余持仓：</span>
                <span className="text-xs">{remainingShares}股（占比需重新分配）</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 p-2 bg-warning/10 rounded text-xs text-warning">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            平仓操作不可撤销，请确认信息无误。
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              取消
            </Button>
            <Button type="submit" variant="danger" isLoading={isLoading}>
              确认平仓
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ClosePositionModal;
