import { create } from 'zustand';
import type {
  Portfolio,
  PortfolioListItem,
  Holding,
  ClosePositionRequest,
  ClosePositionResponse,
  RebalanceResponse,
  CalculateResponse,
  PortfolioHistoryItem,
  PerformanceResponse,
  CreatePortfolioRequest,
  UpdatePortfolioRequest,
  BatchHoldingsRequest,
  BatchHoldingsResponse,
} from '../api/portfolio';

interface PortfolioState {
  portfolios: PortfolioListItem[];
  currentPortfolio: Portfolio | null;
  history: PortfolioHistoryItem[];
  performance: PerformanceResponse | null;
  isLoading: boolean;
  error: string | null;

  fetchPortfolios: (params?: { includeDeleted?: boolean }) => Promise<void>;
  fetchPortfolio: (id: number) => Promise<void>;
  createPortfolio: (data: CreatePortfolioRequest) => Promise<Portfolio>;
  updatePortfolio: (id: number, data: UpdatePortfolioRequest) => Promise<void>;
  deletePortfolio: (id: number) => Promise<void>;
  restorePortfolio: (id: number) => Promise<void>;

  addHolding: (portfolioId: number, data: { code: string; entryPrice: number; weight: number }) => Promise<Holding>;
  updateHolding: (portfolioId: number, holdingId: number, data: { entryPrice?: number; weight?: number }) => Promise<Holding>;
  closePosition: (portfolioId: number, holdingId: number, data: ClosePositionRequest) => Promise<ClosePositionResponse>;
  batchAddHoldings: (portfolioId: number, data: BatchHoldingsRequest) => Promise<BatchHoldingsResponse>;
  rebalanceHoldings: (portfolioId: number) => Promise<RebalanceResponse>;

  calculatePortfolio: (portfolioId: number) => Promise<CalculateResponse>;
  fetchHistory: (portfolioId: number, params?: { startDate?: string; endDate?: string; page?: number; limit?: number }) => Promise<void>;
  fetchPerformance: (portfolioId: number, params?: { startDate?: string; endDate?: string; viewMode?: string }) => Promise<void>;

  clearError: () => void;
  clearCurrentPortfolio: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set, get) => ({
  portfolios: [],
  currentPortfolio: null,
  history: [],
  performance: null,
  isLoading: false,
  error: null,

  fetchPortfolios: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.list(params);
      set({ portfolios: response.items, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || '获取组合列表失败', isLoading: false });
    }
  },

  fetchPortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.get(id);
      set({ currentPortfolio: response, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || '获取组合详情失败', isLoading: false });
    }
  },

  createPortfolio: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.create(data);
      set(state => ({
        portfolios: [...state.portfolios, {
          id: response.id,
          name: response.name,
          description: response.description,
          holdingsCount: response.summary.holdingsCount,
          totalValue: response.summary.totalValue,
          totalPnlPct: response.summary.totalPnlPct,
          totalPnlAmount: response.summary.totalPnlAmount,
          isDeleted: response.isDeleted,
          createdAt: response.createdAt,
          updatedAt: response.updatedAt,
        }],
        currentPortfolio: response,
        isLoading: false,
      }));
      return response;
    } catch (error: any) {
      set({ error: error.message || '创建组合失败', isLoading: false });
      throw error;
    }
  },

  updatePortfolio: async (id, data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.update(id, data);
      set(state => ({
        portfolios: state.portfolios.map(p =>
          p.id === id
            ? { ...p, name: response.name, description: response.description, initialCapital: response.initialCapital }
            : p
        ),
        currentPortfolio: state.currentPortfolio?.id === id ? response : state.currentPortfolio,
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || '更新组合失败', isLoading: false });
      throw error;
    }
  },

  deletePortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      await portfolioApi.delete(id);
      set(state => ({
        portfolios: state.portfolios.filter(p => p.id !== id),
        currentPortfolio: state.currentPortfolio?.id === id ? null : state.currentPortfolio,
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || '删除组合失败', isLoading: false });
      throw error;
    }
  },

  restorePortfolio: async (id) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.restore(id);
      set(state => ({
        portfolios: [...state.portfolios, {
          id: response.id,
          name: response.name,
          description: response.description,
          holdingsCount: response.summary.holdingsCount,
          totalValue: response.summary.totalValue,
          totalPnlPct: response.summary.totalPnlPct,
          totalPnlAmount: response.summary.totalPnlAmount,
          isDeleted: response.isDeleted,
          createdAt: response.createdAt,
          updatedAt: response.updatedAt,
        }],
        isLoading: false,
      }));
    } catch (error: any) {
      set({ error: error.message || '恢复组合失败', isLoading: false });
      throw error;
    }
  },

  addHolding: async (portfolioId, data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.addHolding(portfolioId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: [...currentPortfolio.holdings, response],
            summary: {
              ...currentPortfolio.summary,
              holdingsCount: currentPortfolio.summary.holdingsCount + 1,
            },
          },
          isLoading: false,
        });
      }
      return response;
    } catch (error: any) {
      set({ error: error.message || '添加持仓失败', isLoading: false });
      throw error;
    }
  },

  updateHolding: async (portfolioId, holdingId, data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.updateHolding(portfolioId, holdingId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: currentPortfolio.holdings.map(h =>
              h.id === holdingId ? response : h
            ),
          },
          isLoading: false,
        });
      }
      return response;
    } catch (error: any) {
      set({ error: error.message || '更新持仓失败', isLoading: false });
      throw error;
    }
  },

  closePosition: async (portfolioId, holdingId, data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.closePosition(portfolioId, holdingId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        const updatedHoldings = currentPortfolio.holdings.map(h => {
          if (h.id === holdingId) {
            return {
              ...h,
              isClosed: response.isClosed,
              closePrice: response.closePrice,
              closeQuantity: response.closeQuantity,
              closeType: response.closeType,
            };
          }
          return h;
        });
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: updatedHoldings,
            summary: {
              ...currentPortfolio.summary,
              holdingsCount: response.isClosed
                ? currentPortfolio.summary.holdingsCount - 1
                : currentPortfolio.summary.holdingsCount,
            },
          },
          isLoading: false,
        });
      }
      return response;
    } catch (error: any) {
      set({ error: error.message || '平仓失败', isLoading: false });
      throw error;
    }
  },

  batchAddHoldings: async (portfolioId, data) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.batchAddHoldings(portfolioId, data);
      const { currentPortfolio } = get();
      if (currentPortfolio && currentPortfolio.id === portfolioId) {
        set({
          currentPortfolio: {
            ...currentPortfolio,
            holdings: [...currentPortfolio.holdings, ...response.holdings],
            summary: {
              ...currentPortfolio.summary,
              holdingsCount: currentPortfolio.summary.holdingsCount + response.addedCount,
            },
          },
          isLoading: false,
        });
      }
      return response;
    } catch (error: any) {
      set({ error: error.message || '批量添加持仓失败', isLoading: false });
      throw error;
    }
  },

  rebalanceHoldings: async (portfolioId) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.rebalance(portfolioId);
      await get().fetchPortfolio(portfolioId);
      return response;
    } catch (error: any) {
      set({ error: error.message || '仓位重平衡失败', isLoading: false });
      throw error;
    }
  },

  calculatePortfolio: async (portfolioId) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.calculate(portfolioId);
      set({ isLoading: false });
      return response;
    } catch (error: any) {
      set({ error: error.message || '计算失败', isLoading: false });
      throw error;
    }
  },

  fetchHistory: async (portfolioId, params) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.getHistory(portfolioId, params);
      set({ history: response.items, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || '获取历史记录失败', isLoading: false });
    }
  },

  fetchPerformance: async (portfolioId, params) => {
    set({ isLoading: true, error: null });
    try {
      const { portfolioApi } = await import('../api/portfolio');
      const response = await portfolioApi.getPerformance(portfolioId, params);
      set({ performance: response, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || '获取收益走势失败', isLoading: false });
    }
  },

  clearError: () => set({ error: null }),

  clearCurrentPortfolio: () => set({ currentPortfolio: null, history: [], performance: null }),
}));
