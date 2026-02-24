import React, { useState, useEffect, useRef, useCallback } from 'react';
import { stocksApi } from '../../api/stocks';
import type { StockSearchResult } from '../../api/stocks';

interface StockSearchInputProps {
  value: string;
  onChange: (code: string, stock?: StockSearchResult) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const StockSearchInput: React.FC<StockSearchInputProps> = ({
  value,
  onChange,
  placeholder = '搜索股票代码或名称...',
  className = '',
  disabled = false,
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const searchStocks = useCallback(async (keyword: string) => {
    if (!keyword || keyword.length < 1) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await stocksApi.search(keyword, 10);
      setResults(response.items);
      setIsOpen(response.items.length > 0);
      setHighlightedIndex(-1);
    } catch (error) {
      console.error('搜索股票失败:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value.toUpperCase();
    setInputValue(newValue);
    onChange(newValue);

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      searchStocks(newValue);
    }, 300);
  };

  const handleSelect = (stock: StockSearchResult) => {
    setInputValue(stock.code);
    onChange(stock.code, stock);
    setIsOpen(false);
    setResults([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev < results.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) =>
          prev > 0 ? prev - 1 : results.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < results.length) {
          handleSelect(results[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  const handleFocus = () => {
    if (inputValue.length >= 1 && results.length > 0) {
      setIsOpen(true);
    }
  };

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="input-terminal w-full pr-8"
          autoComplete="off"
        />
        {isLoading && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <svg
              className="w-4 h-4 text-muted animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          </div>
        )}
        {!isLoading && (
          <div className="absolute right-2 top-1/2 -translate-y-1/2 text-muted">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-elevated border border-white/10 rounded-lg shadow-lg max-h-60 overflow-y-auto"
        >
          {results.map((stock, index) => (
            <div
              key={stock.code}
              onClick={() => handleSelect(stock)}
              className={`px-3 py-2 cursor-pointer flex justify-between items-center ${
                index === highlightedIndex
                  ? 'bg-cyan/10 text-cyan'
                  : 'hover:bg-white/5 text-secondary hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium">{stock.code}</span>
                {stock.name && (
                  <span className="text-sm text-muted">{stock.name}</span>
                )}
              </div>
              {stock.close && (
                <span className="text-sm font-mono text-muted">
                  ¥{stock.close.toFixed(2)}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearchInput;
