import React, { useState } from 'react';
import { Button } from '../common';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  title?: string;
  message: string;
  onClose: () => void;
  onConfirm: (deleteHistory: boolean) => void;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  title = '删除组合',
  message,
  onClose,
  onConfirm,
}) => {
  const [deleteHistory, setDeleteHistory] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      onConfirm(deleteHistory);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="modal-backdrop active" onClick={onClose}>
      <div className="modal-content max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header flex justify-between items-center p-4 border-b border-white/5">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-muted hover:text-white">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-danger/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-white">{message}</p>
              <p className="text-xs text-muted mt-1">此操作将从列表中隐藏该组合，但所有历史数据将被保留。</p>
            </div>
          </div>

          <label className="flex items-center gap-2 cursor-pointer hover:bg-hover p-2 rounded">
            <input
              type="checkbox"
              checked={deleteHistory}
              onChange={(e) => setDeleteHistory(e.target.checked)}
              className="accent-danger"
            />
            <span className="text-sm text-secondary">同时删除所有历史记录</span>
          </label>
          <p className="text-xs text-muted pl-6">（此操作不可恢复）</p>

          <p className="text-xs text-muted">您可以从设置中恢复已删除的组合。</p>
        </div>

        <div className="flex justify-end gap-3 p-4 border-t border-white/5">
          <Button type="button" variant="secondary" onClick={onClose}>
            取消
          </Button>
          <Button type="button" variant="danger" onClick={handleConfirm} isLoading={isLoading}>
            删除组合
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
