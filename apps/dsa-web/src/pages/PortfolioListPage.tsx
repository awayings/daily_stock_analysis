import type React from 'react';
import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/common';
import { PortfolioList, DeleteConfirmModal } from '../components/portfolio';
import { usePortfolioStore } from '../stores';

const PortfolioListPage: React.FC = () => {
  const navigate = useNavigate();
  const { portfolios, isLoading, error, fetchPortfolios, deletePortfolio, clearError } = usePortfolioStore();
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [portfolioToDelete, setPortfolioToDelete] = useState<number | null>(null);

  const loadPortfolios = useCallback(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

  useEffect(() => {
    loadPortfolios();
  }, [loadPortfolios]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  const handleDelete = async (id: number) => {
    setPortfolioToDelete(id);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async (_deleteHistory: boolean) => {
    if (portfolioToDelete) {
      try {
        await deletePortfolio(portfolioToDelete);
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
    setDeleteModalOpen(false);
    setPortfolioToDelete(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex-shrink-0 px-4 py-3 border-b border-white/5">
        <div className="flex items-center justify-between max-w-7xl">
          <h1 className="text-xl font-semibold text-white">组合管理</h1>
          <Button
            variant="primary"
            onClick={() => navigate('/portfolios/create')}
            className="flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新建组合
          </Button>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-4">
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-danger/10 border border-danger/30 text-danger text-sm">
            {error}
          </div>
        )}

        <PortfolioList
          portfolios={portfolios}
          isLoading={isLoading}
          onDelete={handleDelete}
        />
      </main>

      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        message={`确定要删除该组合吗？`}
        onClose={() => {
          setDeleteModalOpen(false);
          setPortfolioToDelete(null);
        }}
        onConfirm={confirmDelete}
      />
    </div>
  );
};

export default PortfolioListPage;
