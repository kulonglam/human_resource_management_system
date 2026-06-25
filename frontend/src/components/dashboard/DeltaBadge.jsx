function DeltaBadge({ delta, invert = false }) {
  if (!delta || delta.direction === 'flat') {
    return <span className="dashboard-kpi-delta dashboard-kpi-delta--flat">—</span>;
  }

  const isPositive = delta.direction === 'up';
  const isGood = invert ? !isPositive : isPositive;
  const sign = isPositive ? '+' : '';
  const pct = delta.change_pct != null ? `${sign}${delta.change_pct}%` : `${sign}${delta.change}`;

  return (
    <span className={`dashboard-kpi-delta dashboard-kpi-delta--${isGood ? 'good' : 'bad'}`}>
      <i className={`bi bi-arrow-${isPositive ? 'up' : 'down'}-short`} />
      {pct}
      <span className="dashboard-kpi-delta-period">vs prior</span>
    </span>
  );
}

export default DeltaBadge;
