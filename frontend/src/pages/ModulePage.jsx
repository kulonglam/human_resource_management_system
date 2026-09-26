import { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ResourceManager from '../components/ResourceManager';

function asRows(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.results)) return data.results;
  return [];
}

export default function ModulePage({ title, icon, tabs, headerExtra, passUser = false }) {
  const { user } = useAuth();
  const [lookupOptions, setLookupOptions] = useState({});

  const loadLookups = useCallback(async () => {
    try {
      const [employees, departments, jobs, courses, skills, assets, shifts, categories, benefits, exitProcesses, certifications, policies, disciplineRecords, positions, grades] =
        await Promise.all([
          api.list('employees').catch(() => []),
          api.list('departments').catch(() => []),
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

      const employeeRows = asRows(employees);
      const departmentRows = asRows(departments);
      const jobRows = asRows(jobs);
      const courseRows = asRows(courses);
      const skillRows = asRows(skills);
      const assetRows = asRows(assets);
      const shiftRows = asRows(shifts);
      const categoryRows = asRows(categories);
      const benefitRows = asRows(benefits);
      const exitRows = asRows(exitProcesses);
      const certificationRows = asRows(certifications);
      const policyRows = asRows(policies);
      const disciplineRows = asRows(disciplineRecords);
      const positionRows = asRows(positions);
      const gradeRows = asRows(grades);

      const nextOptions = {
        employee: employeeRows.map((e) => ({ value: e.id, label: e.full_name })),
        department: departmentRows.map((d) => ({ value: d.id, label: d.name })),
        previous_department: departmentRows.map((d) => ({ value: d.id, label: d.name })),
        new_department: departmentRows.map((d) => ({ value: d.id, label: d.name })),
        job: jobRows.map((j) => ({ value: j.id, label: j.title })),
        course: courseRows.map((c) => ({ value: c.id, label: c.title })),
        skill: skillRows.map((s) => ({ value: s.id, label: s.name })),
        asset: assetRows.map((a) => ({ value: a.id, label: a.name })),
        shift: shiftRows.map((s) => ({ value: s.id, label: s.shift_name })),
        category: categoryRows.map((c) => ({ value: c.id, label: c.name })),
        benefit: benefitRows.map((b) => ({ value: b.id, label: b.name })),
        exit_process: exitRows.map((e) => ({ value: e.id, label: e.employee_name })),
        certification: certificationRows.map((c) => ({ value: c.id, label: c.name })),
        policy: policyRows.map((p) => ({ value: p.id, label: p.name })),
        discipline: disciplineRows.map((d) => ({ value: d.id, label: `${d.employee_name} — ${d.reason}` })),
        position: positionRows.map((p) => ({ value: p.id, label: p.title })),
        previous_position: positionRows.map((p) => ({ value: p.id, label: p.title })),
        new_position: positionRows.map((p) => ({ value: p.id, label: p.title })),
        reports_to: positionRows.map((p) => ({ value: p.id, label: p.title })),
        grade: gradeRows.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
        previous_grade: gradeRows.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
        new_grade: gradeRows.map((g) => ({ value: g.id, label: `${g.code} — ${g.name}` })),
        survey: [],
      };
      setLookupOptions(nextOptions);
      return nextOptions;
    } catch {
      /* lookups optional */
      return null;
    }
  }, []);

  useEffect(() => {
    loadLookups();
  }, [loadLookups]);

  return (
    <ResourceManager
      title={title}
      icon={icon}
      tabs={tabs}
      lookupOptions={lookupOptions}
      onLookupsRefresh={loadLookups}
      user={passUser ? user : undefined}
      headerExtra={headerExtra}
    />
  );
}
