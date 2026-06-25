import { useEffect, useState } from 'react';
import { api } from '../api/client';
import FeedbackWorkflow from '../components/FeedbackWorkflow';
import ResourceManager from '../components/ResourceManager';
import { performanceTabs } from '../config/opsModules';

export default function Performance() {
  const [activeTab, setActiveTab] = useState('goals');
  const [lookupOptions, setLookupOptions] = useState({});
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.getMe().then(setUser).catch(() => {});
    async function loadLookups() {
      try {
        const [employees, departments] = await Promise.all([
          api.list('employees'),
          api.list('departments'),
        ]);
        setLookupOptions({
          employee: employees.map((e) => ({ value: e.id, label: e.full_name })),
          department: departments.map((d) => ({ value: d.id, label: d.name })),
        });
      } catch {
        /* optional */
      }
    }
    loadLookups();
  }, []);

  const navTabs = [
    ...performanceTabs.map((t) => ({ id: t.id, label: t.label })),
    { id: 'feedback360', label: '360° Feedback' },
  ];

  const currentTab = performanceTabs.find((t) => t.id === activeTab);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-graph-up-arrow" style={{ color: 'var(--fca-lime)' }} /> Performance
        </h4>
      </div>

      <ul className="nav nav-tabs mb-3">
        {navTabs.map((t) => (
          <li className="nav-item" key={t.id}>
            <button
              type="button"
              className={`nav-link ${activeTab === t.id ? 'active' : ''}`}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          </li>
        ))}
      </ul>

      {activeTab === 'feedback360' ? (
        <FeedbackWorkflow
          lookupOptions={lookupOptions}
          isManager={Boolean(user?.is_admin || user?.is_manager)}
        />
      ) : (
        <ResourceManager
          title=""
          tabs={[currentTab]}
          lookupOptions={lookupOptions}
        />
      )}
    </>
  );
}
