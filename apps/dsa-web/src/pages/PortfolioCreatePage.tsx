import type React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { StockSearchInput } from '../components/portfolio';
import type { StockSearchResult } from '../api/stocks';
import { usePortfolioStore } from '../stores';

interface HoldingFormData {
  code: string;
  name: string;
  entryPrice: string;
  weight: string;
}

const PortfolioCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { createPortfolio, isLoading, error } = usePortfolioStore();

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [initialCapital, setInitialCapital] = useState('');
  const [currency, setCurrency] = useState('CNY');
  const [holdings, setHoldings] = useState<HoldingFormData[]>([]);
  const [showAddHolding, setShowAddHolding] = useState(false);
  const [newHolding, setNewHolding] = useState<HoldingFormData>({ code: '', name: '', entryPrice: '', weight: '' });
  const [submitError, setSubmitError] = useState<string | null>(null);

  const totalWeight = holdings.reduce((sum, h) => sum + (parseFloat(h.weight) || 0), 0);
  const isWeightValid = totalWeight <= 100;

  const handleStockSelect = (code: string, stock?: StockSearchResult) => {
    setNewHolding({
      ...newHolding,
      code,
      name: stock?.name || '',
      entryPrice: stock?.close ? stock.close.toFixed(2) : newHolding.entryPrice,
    });
  };

  const handleAddHolding = () => {
    if (!newHolding.code || !newHolding.entryPrice || !newHolding.weight) return;

    setHoldings([...holdings, { ...newHolding }]);
    setNewHolding({ code: '', name: '', entryPrice: '', weight: '' });
    setShowAddHolding(false);
  };

  const handleRemoveHolding = (index: number) => {
    setHoldings(holdings.filter((_, i) => i !== index));
  };

  const handleAverage分配 = () => {
    if (holdings.length === 0) return;
    const avgWeight = (100 / holdings.length).toFixed(2);
    setHoldings(holdings.map(h => ({ ...h, weight: avgWeight })));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!name.trim()) {
      setSubmitError('请输入组合名称');
      return;
    }

    if (holdings.length === 0) {
      setSubmitError('请至少添加一个持仓');
      return;
    }

    if (!isWeightValid) {
      setSubmitError('仓位占比总和不能超过100%');
      return;
    }

    try {
      const portfolio = await createPortfolio({
        name: name.trim(),
        description: description.trim() || undefined,
        initialCapital: initialCapital ? parseFloat(initialCapital) : undefined,
        currency,
        holdings: holdings.map(h => ({
          code: h.code.toUpperCase(),
          name: h.name,
          entryPrice: parseFloat(h.entryPrice),
          weight: parseFloat(h.weight),
        })),
      });

      navigate(`/portfolios/${portfolio.id}`);
    } catch (err: any) {
      setSubmitError(err.message || '创建组合失败');
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex-shrink-0 px-4 py-3 border-b border-white/5">
        <button
          onClick={() => navigate('/portfolios')}
          className="flex items-center gap-2 text-muted hover:text-white transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          返回组合列表
        </button>
      </header>

      <main className="flex-1 overflow-auto p-4">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-xl font-semibold text-white mb-6">创建新组合</h1>

          {(error || submitError) && (
            <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">
              {error || submitError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="glass-card p-4 space-y-4">
              <h2 className="text-sm font-medium text-white">基本信息</h2>

              <div>
                <label className="block text-xs text-secondary mb-1.5">组合名称 *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="请输入组合名称..."
                  className="input-terminal w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-xs text-secondary mb-1.5">描述（可选）</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="添加组合描述..."
                  className="input-terminal w-full min-h-[80px] resize-none"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-xs text-secondary mb-1.5">初始资金（可选）</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(e.target.value)}
                    placeholder="1000000.00"
                    className="input-terminal flex-1 min-w-[180px]"
                  />
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="input-terminal w-24"
                  >
                    <option value="CNY">CNY</option>
                    <option value="USD">USD</option>
                    <option value="HKD">HKD</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="glass-card p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-white">添加持仓</h2>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setShowAddHolding(true)}
                  >
                    手动选择
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {}}
                    disabled
                  >
                    批量导入
                  </Button>
                </div>
              </div>

              {showAddHolding && (
                <div className="p-3 bg-elevated rounded-lg space-y-3">
                  <div>
                    <label className="block text-xs text-muted mb-1">股票代码</label>
                    <StockSearchInput
                      value={newHolding.code}
                      onChange={handleStockSelect}
                      placeholder="搜索股票代码或名称..."
                    />
                    {newHolding.name && (
                      <p className="mt-1 text-xs text-muted">{newHolding.name}</p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <label className="block text-xs text-muted mb-1">建仓价格</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newHolding.entryPrice}
                        onChange={(e) => setNewHolding({ ...newHolding, entryPrice: e.target.value })}
                        placeholder="0.00"
                        className="input-terminal w-full"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="block text-xs text-muted mb-1">仓位占比</label>
                      <input
                        type="number"
                        step="0.01"
                        value={newHolding.weight}
                        onChange={(e) => setNewHolding({ ...newHolding, weight: e.target.value })}
                        placeholder="0.00"
                        className="input-terminal w-full"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAddHolding(false)}
                    >
                      取消
                    </Button>
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={handleAddHolding}
                    >
                      添加
                    </Button>
                  </div>
                </div>
              )}

              {holdings.length > 0 ? (
                <div className="overflow-x-auto rounded-lg border border-white/5">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-elevated text-left">
                        <th className="px-3 py-2 text-xs font-medium text-secondary">代码</th>
                        <th className="px-3 py-2 text-xs font-medium text-secondary">名称</th>
                        <th className="px-3 py-2 text-xs font-medium text-secondary">建仓价格</th>
                        <th className="px-3 py-2 text-xs font-medium text-secondary text-right">仓位占比</th>
                        <th className="px-3 py-2 text-xs font-medium text-center">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {holdings.map((holding, index) => (
                        <tr key={index} className="border-t border-white/5">
                          <td className="px-3 py-2 font-mono text-cyan">{holding.code}</td>
                          <td className="px-3 py-2 text-secondary">{holding.name || '-'}</td>
                          <td className="px-3 py-2 font-mono text-secondary">¥{holding.entryPrice}</td>
                          <td className="px-3 py-2 font-mono text-right">{holding.weight}%</td>
                          <td className="px-3 py-2 text-center">
                            <button
                              type="button"
                              onClick={() => handleRemoveHolding(index)}
                              className="text-danger hover:text-danger/80"
                            >
                              ×
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-muted text-sm">
                  暂无持仓，请添加
                </div>
              )}
            </div>

            {holdings.length > 0 && (
              <div className="glass-card p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">
                    仓位占比总和：
                    <span className={`font-mono ml-2 ${isWeightValid ? 'text-success' : 'text-danger'}`}>
                      {totalWeight.toFixed(2)}%
                    </span>
                    {isWeightValid && totalWeight < 100 && (
                      <span className="text-muted ml-2">
                        (剩余 {(100 - totalWeight).toFixed(2)}% 未分配)
                      </span>
                    )}
                    {isWeightValid && (
                      <svg className="w-4 h-4 text-success inline ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleAverage分配}
                  >
                    平均分配
                  </Button>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/portfolios')}
              >
                取消
              </Button>
              <Button
                type="submit"
                variant="primary"
                isLoading={isLoading}
              >
                创建组合
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default PortfolioCreatePage;
