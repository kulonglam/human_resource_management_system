export default function ExecutiveBrief({ text }) {
  if (!text) return null;

  return (
    <div className="dashboard-brief">
      <div className="dashboard-brief-label">
        <i className="bi bi-stars" /> Executive summary
      </div>
      <p className="dashboard-brief-text mb-0">{text}</p>
    </div>
  );
}
