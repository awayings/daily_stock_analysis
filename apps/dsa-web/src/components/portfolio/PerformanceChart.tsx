import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import type { PerformanceDataPoint } from '../../api/portfolio';

interface PerformanceChartProps {
  dataPoints: PerformanceDataPoint[];
  viewMode: 'portfolio' | 'holdings';
  holdings?: { code: string; name: string }[];
}

const CHART_COLORS = [
  '#00d4ff',
  '#00ff88',
  '#ffaa00',
  '#ff4466',
  '#a78bfa',
  '#f472b6',
  '#34d399',
  '#fbbf24',
];

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}月${date.getDate()}日`;
};

const formatPnl = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

const formatAmount = (value: number): string => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}¥${Math.abs(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  dataPoints,
  viewMode,
  holdings = [],
}) => {
  const formatXAxis = (dateStr: string): string => {
    return formatDate(dateStr);
  };

  const formatYAxis = (value: number): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) => {
    if (!active || !payload || payload.length === 0 || !label) {
      return null;
    }

    const dataPoint = dataPoints.find(d => d.date === label);
    if (!dataPoint) return null;

    return (
      <div className="bg-[#12121a] border border-white/10 rounded-lg p-3 shadow-xl backdrop-blur-sm">
        <div className="text-xs text-muted mb-2">{label}</div>
        <div className="space-y-1">
          {payload.map((entry) => (
            <div key={entry.name} className="flex items-center justify-between gap-4 text-xs">
              <span style={{ color: entry.color }}>{entry.name}</span>
              <span className="font-mono text-white">
                {entry.name.includes('盈亏') || entry.name.includes('收益率')
                  ? formatPnl(entry.value)
                  : formatAmount(entry.value)}
              </span>
            </div>
          ))}
        </div>
        {dataPoint.holdings && Object.keys(dataPoint.holdings).length > 0 && (
          <div className="border-t border-white/10 my-2 pt-2">
            <div className="text-xs text-muted mb-1">持仓明细</div>
            {Object.entries(dataPoint.holdings).map(([code, data]) => (
              <div key={code} className="flex items-center justify-between gap-4 text-xs">
                <span className="text-cyan">{code}</span>
                <span className={`font-mono ${(data as { pnlPct: number }).pnlPct >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatPnl((data as { pnlPct: number }).pnlPct)}
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="border-t border-white/10 mt-2 pt-2 text-xs">
          <div className="flex justify-between gap-4">
            <span className="text-muted">总市值</span>
            <span className="font-mono text-white">
              ¥{dataPoint.totalValue.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </div>
    );
  };

  if (!dataPoints || dataPoints.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[300px] text-muted">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p>暂无收益数据</p>
          <p className="text-xs mt-1">请先添加持仓并触发计算</p>
        </div>
      </div>
    );
  }

  const chartData = dataPoints.map(point => ({
    ...point,
    totalPnlPct: point.totalPnlPct,
    unrealizedPnlPct: point.unrealizedPnlPct,
    realizedPnlPct: point.totalPnlPct - point.unrealizedPnlPct,
  }));

  const hasMultipleHoldings = holdings.length > 1;
  const showHoldingsLines = viewMode === 'holdings' && hasMultipleHoldings;

  return (
    <div className="w-full">
      <div className="h-[350px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.06)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tickFormatter={formatXAxis}
              stroke="#606070"
              tick={{ fill: '#a0a0b0', fontSize: 11 }}
              axisLine={{ stroke: 'rgba(255, 255, 255, 0.1)' }}
              tickLine={false}
              interval="preserveStartEnd"
              minTickGap={50}
            />
            <YAxis
              tickFormatter={formatYAxis}
              stroke="#606070"
              tick={{ fill: '#a0a0b0', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={60}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: 20 }}
              formatter={(value: string) => (
                <span className="text-xs text-secondary">{value}</span>
              )}
            />
            <ReferenceLine
              y={0}
              stroke="rgba(255, 255, 255, 0.2)"
              strokeDasharray="3 3"
            />
            <Line
              type="monotone"
              dataKey="totalPnlPct"
              name="总盈亏"
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: CHART_COLORS[0], stroke: '#08080c', strokeWidth: 2 }}
              animationDuration={1500}
              animationEasing="ease-out"
            />
            <Line
              type="monotone"
              dataKey="unrealizedPnlPct"
              name="浮动盈亏"
              stroke={CHART_COLORS[1]}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="4 4"
              animationDuration={1500}
              animationEasing="ease-out"
            />
            <Line
              type="monotone"
              dataKey="realizedPnlPct"
              name="已实现盈亏"
              stroke={CHART_COLORS[2]}
              strokeWidth={1.5}
              dot={false}
              strokeDasharray="4 4"
              animationDuration={1500}
              animationEasing="ease-out"
            />
            {showHoldingsLines && holdings.slice(0, 5).map((holding, index) => {
              return (
                <Line
                  key={holding.code}
                  type="monotone"
                  dataKey={`holding_${holding.code}`}
                  name={holding.code}
                  stroke={CHART_COLORS[index + 3] || CHART_COLORS[index % CHART_COLORS.length]}
                  strokeWidth={1.5}
                  dot={false}
                  animationDuration={1500}
                  animationEasing="ease-out"
                />
              );
            })}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceChart;
