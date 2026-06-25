import { useEffect, useState } from 'react';
import { api } from '../api/client';
import ResourceManager from '../components/ResourceManager';
import { trainingTabs } from '../config/opsModules';

export default function Training() {
  const [activeTab, setActiveTab] = useState('courses');
  const [lookupOptions, setLookupOptions] = useState({});

  useEffect(() => {
    async function loadLookups() {
      try {
        const [employees, skills, certifications] = await Promise.all([
          api.list('employees'),
          api.list('skills'),
          api.list('certifications').catch(() => []),
        ]);
        setLookupOptions({
          employee: employees.map((e) => ({ value: e.id, label: e.full_name })),
          skill: skills.map((s) => ({ value: s.id, label: s.name })),
          certification: certifications.map((c) => ({ value: c.id, label: c.name })),
        });
      } catch {
        /* optional */
      }
    }
    loadLookups();
  }, []);

  const currentTab = trainingTabs.find((t) => t.id === activeTab);

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">
          <i className="bi bi-book" style={{ color: 'var(--fca-lime)' }} /> Training
        </h4>
      </div>

      <ul className="nav nav-tabs mb-3">
        {trainingTabs.map((t) => (
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

      <ResourceManager title="" tabs={[currentTab]} lookupOptions={lookupOptions} />
    </>
  );
}
