import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

function formatTooltipValue(value, isCurrency) {
  if (isCurrency) return `KES ${Number(value).toLocaleString()}`;
  return Number(value).toLocaleString();
}

export default function TrendLineChart({ series, isCurrency = false, color = '#004924' }) {
  if (!series?.points?.length) {
    return (
      <div className="dashboard-empty-chart text-muted text-center py-5">
        <i className="bi bi-graph-up fs-2 d-block mb-2" />
        No trend data yet.
      </div>
    );
  }

  const data = series.points.map((p) => ({
    name: p.label,
    fullLabel: p.full_label || p.label,
    value: p.value,
  }));

  return (
    <div className="dashboard-trend-chart">
      <div className="dashboard-chart-header mb-3">
        <h5 className="mb-1">{series.title}</h5>
        {series.subtitle && <p className="text-muted small mb-0">{series.subtitle}</p>}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.35} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e6edea" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#404040' }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fontSize: 11, fill: '#404040' }}
            axisLine={false}
            tickLine={false}
            width={isCurrency ? 72 : 40}
            tickFormatter={(v) => (isCurrency ? `${Math.round(v / 1000)}k` : v)}
          />
          <Tooltip
            formatter={(value) => [formatTooltipValue(value, isCurrency), series.title]}
            labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel || ''}
            contentStyle={{ borderRadius: 0, border: '1px solid #d4e3de' }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2.5}
            fill={`url(#grad-${color.replace('#', '')})`}
            dot={{ r: 3, fill: color, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
