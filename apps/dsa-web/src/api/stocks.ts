import apiClient from './index';
import { toCamelCase } from './utils';

export interface StockSearchResult {
  code: string;
  name: string | null;
  close: number | null;
  date: string | null;
}

export interface StockSearchResponse {
  total: number;
  items: StockSearchResult[];
}

export const stocksApi = {
  search: async (keyword: string, limit: number = 20): Promise<StockSearchResponse> => {
    const response = await apiClient.get<Record<string, unknown>>(
      '/api/v1/stocks/search',
      {
        params: {
          keyword,
          limit,
        },
      },
    );
    return toCamelCase<StockSearchResponse>(response.data);
  },

  getQuote: async (stockCode: string): Promise<{
    stockCode: string;
    stockName: string | null;
    currentPrice: number;
    change: number | null;
    changePercent: number | null;
  }> => {
    const response = await apiClient.get<Record<string, unknown>>(
      `/api/v1/stocks/${stockCode}/quote`,
    );
    return toCamelCase<{
      stockCode: string;
      stockName: string | null;
      currentPrice: number;
      change: number | null;
      changePercent: number | null;
    }>(response.data);
  },
};
