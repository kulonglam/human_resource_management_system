import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ResourceManager from '../components/ResourceManager';

export default function ModulePage({ title, icon, tabs, headerExtra, passUser = false }) {
  const { user } = useAuth();
  const [lookupOptions, setLookupOptions] = useState({});

  useEffect(() => {
    async function loadLookups() {
      try {
        const [employees, departments, jobs, courses, skills, assets, shifts, categories, benefits, exitProcesses, certifications, policies, disciplineRecords, positions, grades] =
          await Promise.all([
            api.list('employees'),
            api.list('departments'),
            api.list('jobs').catch(() => []),
            api.list('training-courses').catch(() => []),
            api.list('skills').catch(() => []),
            api.list('assets').catch(() => []),
            api.list('shifts').catch(() => []),
            api.list('expense-categories').catch(() => []),
            api.list('benefits').catch(() => []),
            api.list('exit-processes').catch(() => []),
            api.list('certifications').catch(() => []),
            api.list('leave-policies').catch(() => []),
            api.list('discipline-records').catch(() => []),
            api.list('positions').catch(() => []),
            api.list('job-grades').catch(() => []),
          ]);

        setLookupOptions({
          employee: employees.map((e) => ({ value: e.id, label: e.full_name })),
          department: departments.map((d) => ({ value: d.id, label: d.name })),
          previous_department: departments.map((d) => ({ value: d.id, label: d.name })),
          new_department: departments.map((d) => ({ value: d.id, label: d.name })),
          job: jobs.map((j) => ({ value: j.id, label: j.title })),
          course: courses.map((c) => ({ value: c.id, label: c.title })),
          skill: skills.map((s) => ({ value: s.id, label: s.name })),
          asset: assets.map((a) => ({ value: a.id, label: a.name })),
          shift: shifts.map((s) => ({ value: s.id, label: s.shift_name })),
          category: categories.map((c) => ({ value: c.id, label: c.name })),
          benefit: benefits.map((b) => ({ value: b.id, label: b.name })),
          exit_process: exitProcesses.map((e) => ({ value: e.id, label: e.employee_name })),
          certification: certifications.map((c) => ({ value: c.id, label: c.name })),
          policy: policies.map((p) => ({ value: p.id, label: p.name })),
          discipline: disciplineRecords.map((d) => ({ value: d.id, label: `${d.employee_name} — ${d.reason}` })),
          position: positions.map((p) => ({ value: p.id, label: p.title })),
          previous_position: positions.map((p) => ({ value: p.id, label: p.title })),
          new_position: positions.map((p) => ({ value: p.id, label: p.title })),
          reports_to: positions.map((p) => ({ value: p.id, label: p.title })),
          grade: grades.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
          previous_grade: grades.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
          new_grade: grades.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
          survey: [],
        });
      } catch {
        /* lookups optional */
      }
    }
    loadLookups();
  }, []);

  return (
    <ResourceManager
      title={title}
      icon={icon}
      tabs={tabs}
      lookupOptions={lookupOptions}
      user={passUser ? user : undefined}
      headerExtra={headerExtra}
    />
  );
}
