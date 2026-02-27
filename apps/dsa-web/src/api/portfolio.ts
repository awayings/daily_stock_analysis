import apiClient from './index';
import { toCamelCase } from './utils';

export interface Holding {
  id: number;
  portfolioId: number;
  code: string;
  name: string;
  entryPrice: number;
  lastPrice: number;
  currentPrice: number;
  weight: number;
  shares?: number;
  pnlPct: number;
  weightedPnl: number;
  isClosed: boolean;
  addedAt?: string;
  updatedAt?: string;
  closePrice?: number;
  closeQuantity?: number;
  closeType?: string;
  closedAt?: string;
}

export interface PortfolioSummary {
  totalValue: number;
  totalPnlPct: number;
  totalPnlAmount: number;
  holdingsCount: number;
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  initialCapital?: number;
  currency: string;
  isDeleted: boolean;
  createdAt?: string;
  updatedAt?: string;
  holdings: Holding[];
  summary: PortfolioSummary;
}

export interface PortfolioListItem {
  id: number;
  name: string;
  description?: string;
  holdingsCount: number;
  totalValue: number;
  totalPnlPct: number;
  totalPnlAmount: number;
  isDeleted: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  initialCapital?: number;
  currency?: string;
  holdings?: {
    code: string;
    name?: string;
    entryPrice: number;
    lastPrice?: number;
    weight: number;
  }[];
}

export interface UpdatePortfolioRequest {
  name?: string;
  description?: string;
  initialCapital?: number;
}

export interface ClosePositionRequest {
  priceType: 'current' | 'specified';
  specifiedPrice?: number;
  quantityType: 'all' | 'partial';
  quantity?: number;
  ratio?: number;
}

export interface ClosePositionResponse {
  id: number;
  portfolioId: number;
  code: string;
  name: string;
  entryPrice: number;
  closePrice: number;
  closeQuantity: number;
  closeType: string;
  isClosed: boolean;
  closedAt?: string;
  pnl: {
    amount: number;
    percentage: number;
    realized: boolean;
  };
  remaining: {
    shares: number;
    weight: number;
  };
  weightRebalanceRequired: boolean;
}

export interface BatchHoldingsRequest {
  holdings: {
    code: string;
    entryPrice: number;
    lastPrice?: number;
    weight: number;
  }[];
  rebalanceMode?: 'none' | 'equal' | 'keep_existing';
}

export interface BatchHoldingsResponse {
  addedCount: number;
  skippedCount: number;
  holdings: Holding[];
  weightSummary: Record<string, unknown>;
}

export interface RebalanceResponse {
  portfolioId: number;
  holdingsCount: number;
  newWeightEach: number;
  holdings: {
    id: number;
    code: string;
    weight: number;
  }[];
}

export interface CalculateResponse {
  portfolioId: number;
  calculatedAt: string;
  snapshotDate: string;
  totalValue: number;
  totalPnlPct: number;
  holdingsUpdated: number;
  status: string;
}

export interface PortfolioHistoryItem {
  id: number;
  portfolioId: number;
  snapshotDate: string;
  totalValue: number;
  unrealizedPnlPct: number;
  unrealizedPnlAmount: number;
  realizedPnlAmount: number;
  cumulativeRealizedPnl: number;
  totalPnlPct: number;
  totalPnlAmount: number;
  activeHoldingsCount: number;
  closedHoldingsCount: number;
  calculationStatus: string;
  errorMessage?: string;
  calculatedAt: string;
  holdings: Holding[];
}

export interface PerformanceDataPoint {
  date: string;
  totalValue: number;
  unrealizedPnlPct: number;
  unrealizedPnlAmount: number;
  realizedPnlAmount: number;
  cumulativeRealizedPnl: number;
  totalPnlPct: number;
  holdings?: Record<string, { pnlPct: number; weightedPnl: number }>;
}

export interface PerformanceStatistics {
  totalReturnPct: number;
  unrealizedReturnPct: number;
  realizedReturnPct: number;
  maxDrawdownPct: number;
  bestDay: { date: string; pnlPct: number };
  worstDay: { date: string; pnlPct: number };
}

export interface PerformanceResponse {
  portfolioId: number;
  viewMode: string;
  dateRange: {
    start: string;
    end: string;
  };
  dataPoints: PerformanceDataPoint[];
  statistics: PerformanceStatistics;
}

export const portfolioApi = {
  create: async (data: CreatePortfolioRequest): Promise<Portfolio> => {
    const requestData: Record<string, unknown> = {
      name: data.name,
    };
    if (data.description) requestData.description = data.description;
    if (data.initialCapital) requestData.initial_capital = data.initialCapital;
    if (data.currency) requestData.currency = data.currency;
    if (data.holdings) {
      requestData.holdings = data.holdings.map(h => ({
        code: h.code,
        name: h.name,
        entry_price: h.entryPrice,
        weight: h.weight,
      }));
    }

    const response = await apiClient.post<Record<string, unknown>>(
      '/api/v1/portfolios',
      requestData,
    );
    return toCamelCase<Portfolio>(response.data);
  },

  list: async (params?: {
    includeDeleted?: boolean;
    page?: number;
    limit?: number;
  }): Promise<{ items: PortfolioListItem[]; total: number; page: number; limit: number }> => {
    const queryParams: Record<string, string | number> = {};
    if (params?.includeDeleted) queryParams.include_deleted = String(params.includeDeleted);
    if (params?.page) queryParams.page = params.page;
    if (params?.limit) queryParams.limit = params.limit;

    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/portfolios',
      { params: queryParams },
    );

    const data = toCamelCase<{
      items: PortfolioListItem[];
      total: number;
      page: number;
      limit: number;
    }>(response.data);

    return {
      items: (data.items || []).map(item => toCamelCase<PortfolioListItem>(item)),
      total: data.total,
      page: data.page,
      limit: data.limit,
    };
  },

  get: async (id: number): Promise<Portfolio> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/portfolios/${id}`,
    );
    return toCamelCase<Portfolio>(response.data);
  },

  update: async (id: number, data: UpdatePortfolioRequest): Promise<Portfolio> => {
    const requestData: Record<string, unknown> = {};
    if (data.name !== undefined) requestData.name = data.name;
    if (data.description !== undefined) requestData.description = data.description;
    if (data.initialCapital !== undefined) requestData.initial_capital = data.initialCapital;

    const response = await apiClient.put<Record<string, unknown>>(
      `/api/v1/portfolios/${id}`,
      requestData,
    );
    return toCamelCase<Portfolio>(response.data);
  },

  delete: async (id: number): Promise<{ id: number; isDeleted: boolean }> => {
    const response = await apiClient.delete<Record<string, unknown>>(
      `/api/v1/portfolios/${id}`,
    );
    return toCamelCase<{ id: number; isDeleted: boolean }>(response.data);
  },

  restore: async (id: number): Promise<Portfolio> => {
    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${id}/restore`,
    );
    return toCamelCase<Portfolio>(response.data);
  },

  addHolding: async (
    portfolioId: number,
    data: { code: string; entryPrice: number; weight: number; lastPrice?: number },
  ): Promise<Holding> => {
    const requestData = {
      code: data.code,
      entry_price: data.entryPrice,
      last_price: data.lastPrice,
      weight: data.weight,
    };

    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/holdings`,
      requestData,
    );
    return toCamelCase<Holding>(response.data);
  },

  updateHolding: async (
    portfolioId: number,
    holdingId: number,
    data: { entryPrice?: number; weight?: number },
  ): Promise<Holding> => {
    const requestData: Record<string, unknown> = {};
    if (data.entryPrice !== undefined) requestData.entry_price = data.entryPrice;
    if (data.weight !== undefined) requestData.weight = data.weight;

    const response = await apiClient.put<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/holdings/${holdingId}`,
      requestData,
    );
    return toCamelCase<Holding>(response.data);
  },

  closePosition: async (
    portfolioId: number,
    holdingId: number,
    data: ClosePositionRequest,
  ): Promise<ClosePositionResponse> => {
    const requestData: Record<string, unknown> = {
      price_type: data.priceType,
      quantity_type: data.quantityType,
    };
    if (data.specifiedPrice) requestData.specified_price = data.specifiedPrice;
    if (data.quantity) requestData.quantity = data.quantity;
    if (data.ratio) requestData.ratio = data.ratio;

    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/holdings/${holdingId}/closePosition`,
      requestData,
    );
    return toCamelCase<ClosePositionResponse>(response.data);
  },

  batchAddHoldings: async (
    portfolioId: number,
    data: BatchHoldingsRequest,
  ): Promise<BatchHoldingsResponse> => {
    const requestData: Record<string, unknown> = {
      holdings: data.holdings.map(h => ({
        code: h.code,
        entry_price: h.entryPrice,
        weight: h.weight,
      })),
    };
    if (data.rebalanceMode) requestData.rebalance_mode = data.rebalanceMode;

    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/holdings/batch`,
      requestData,
    );
    return toCamelCase<BatchHoldingsResponse>(response.data);
  },

  rebalance: async (portfolioId: number): Promise<RebalanceResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/holdings/rebalance`,
    );
    return toCamelCase<RebalanceResponse>(response.data);
  },

  calculate: async (portfolioId: number): Promise<CalculateResponse> => {
    const response = await apiClient.post<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/calculate`,
    );
    return toCamelCase<CalculateResponse>(response.data);
  },

  getHistory: async (
    portfolioId: number,
    params?: {
      startDate?: string;
      endDate?: string;
      page?: number;
      limit?: number;
    },
  ): Promise<{ portfolioId: number; items: PortfolioHistoryItem[]; total: number; page: number; limit: number }> => {
    const queryParams: Record<string, string | number> = {};
    if (params?.startDate) queryParams.start_date = params.startDate;
    if (params?.endDate) queryParams.end_date = params.endDate;
    if (params?.page) queryParams.page = params.page;
    if (params?.limit) queryParams.limit = params.limit;

    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/history`,
      { params: queryParams },
    );

    const data = response.data as {
      portfolio_id: number;
      items: Record<string, unknown>[];
      total: number;
      page: number;
      limit: number;
    };

    return {
      portfolioId: data.portfolio_id || portfolioId,
      items: (data.items || []).map(item => toCamelCase<PortfolioHistoryItem>(item)),
      total: data.total,
      page: data.page,
      limit: data.limit,
    };
  },

  getPerformance: async (
    portfolioId: number,
    params?: {
      startDate?: string;
      endDate?: string;
      viewMode?: string;
    },
  ): Promise<PerformanceResponse> => {
    const queryParams: Record<string, string> = {};
    if (params?.startDate) queryParams.start_date = params.startDate;
    if (params?.endDate) queryParams.end_date = params.endDate;
    if (params?.viewMode) queryParams.view_mode = params.viewMode;

    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/portfolios/${portfolioId}/performance`,
      { params: queryParams },
    );
    return toCamelCase<PerformanceResponse>(response.data);
  },

  export: async (
    portfolioId: number,
    params?: {
      format?: 'csv' | 'json';
      scope?: 'summary' | 'detailed';
      startDate?: string;
      endDate?: string;
    },
  ): Promise<Blob> => {
    const queryParams: Record<string, string> = {};
    if (params?.format) queryParams.format = params.format;
    if (params?.scope) queryParams.scope = params.scope;
    if (params?.startDate) queryParams.start_date = params.startDate;
    if (params?.endDate) queryParams.end_date = params.endDate;

    const response = await apiClient.get(
      `/api/v1/portfolios/${portfolioId}/export`,
      {
        params: queryParams,
        responseType: 'blob' as const,
      },
    );
    return response.data;
  },
};
