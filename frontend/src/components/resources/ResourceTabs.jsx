export default function ResourceTabs({ tabs, activeTab, onChange, ariaLabel = 'Resource sections' }) {
  if (tabs.length <= 1) return null;

  return (
    <ul className="nav nav-tabs mb-3" role="tablist" aria-label={ariaLabel}>
      {tabs.map((tab) => (
        <li className="nav-item" role="presentation" key={tab.id}>
          <button
            type="button"
            className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
            role="tab"
            id={`resource-tab-${tab.id}`}
            aria-selected={activeTab === tab.id}
            aria-controls={`resource-panel-${tab.id}`}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        </li>
      ))}
    </ul>
  );
}
