import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';

const emptyForm = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  gender: 'Male',
  email: '',
  mobile: '',
  address: '',
  emergency_contact: '',
  language: 'English',
  national_id_number: '',
  tax_identification_number: '',
  nssf_number: '',
  job_title: '',
  department: '',
  position: '',
  grade: '',
  supervisor: '',
  employment_type: 'permanent',
  date_joined: '',
  probation_end_date: '',
  work_location: '',
  cost_center: '',
  account_number: '',
  bank: '',
  salary: '',
};

export default function EmployeeForm() {
  const { id } = useParams();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [departments, setDepartments] = useState([]);
  const [positions, setPositions] = useState([]);
  const [grades, setGrades] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getDepartments(),
      api.list('positions'),
      api.list('job-grades'),
      api.list('employees'),
    ]).then(([departmentData, positionData, gradeData, employeeData]) => {
      setDepartments(departmentData.results || departmentData);
      setPositions(positionData);
      setGrades(gradeData);
      setEmployees(employeeData);
    });
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    api.getEmployee(id)
      .then((emp) => {
        setForm({
          first_name: emp.first_name || '',
          last_name: emp.last_name || '',
          date_of_birth: emp.date_of_birth || '',
          gender: emp.gender || 'Male',
          email: emp.email || '',
          mobile: emp.mobile || '',
          address: emp.address || '',
          emergency_contact: emp.emergency_contact || '',
          language: emp.language || 'English',
          national_id_number: emp.national_id_number || '',
          tax_identification_number: emp.tax_identification_number || '',
          nssf_number: emp.nssf_number || '',
          job_title: emp.job_title || '',
          department: emp.department || '',
          position: emp.position || '',
          grade: emp.grade || '',
          supervisor: emp.supervisor || '',
          employment_type: emp.employment_type || 'permanent',
          date_joined: emp.date_joined || '',
          probation_end_date: emp.probation_end_date || '',
          work_location: emp.work_location || '',
          cost_center: emp.cost_center || '',
          account_number: emp.account_number || '',
          bank: emp.bank || '',
          salary: emp.salary || '',
        });
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id, isEdit]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const payload = {
      ...form,
      department: form.department ? Number(form.department) : null,
      position: form.position ? Number(form.position) : null,
      grade: form.grade ? Number(form.grade) : null,
      supervisor: form.supervisor ? Number(form.supervisor) : null,
      probation_end_date: form.probation_end_date || null,
      salary: form.salary,
    };

    try {
      if (isEdit) {
        await api.updateEmployee(id, payload);
        navigate(`/employees/${id}`);
      } else {
        const created = await api.createEmployee(payload);
        navigate(`/employees/${created.id}`);
      }
    } catch (err) {
      const messages = Object.entries(err.data || {})
        .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
        .join(' ');
      setError(messages || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4 className="page-heading mb-0">{isEdit ? 'Edit Employee' : 'Add Employee'}</h4>
        <Link to={isEdit ? `/employees/${id}` : '/employees'} className="btn btn-outline-secondary btn-sm">
          Cancel
        </Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} className="card">
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-6">
              <label className="form-label">First Name</label>
              <input name="first_name" className="form-control" value={form.first_name} onChange={handleChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Last Name</label>
              <input name="last_name" className="form-control" value={form.last_name} onChange={handleChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Email</label>
              <input type="email" name="email" className="form-control" value={form.email} onChange={handleChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Mobile</label>
              <input name="mobile" className="form-control" value={form.mobile} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">Date of Birth</label>
              <input type="date" name="date_of_birth" className="form-control" value={form.date_of_birth} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">Gender</label>
              <select name="gender" className="form-select" value={form.gender} onChange={handleChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Language</label>
              <input name="language" className="form-control" value={form.language} onChange={handleChange} />
            </div>
            <div className="col-md-12">
              <label className="form-label">Address</label>
              <input name="address" className="form-control" value={form.address} onChange={handleChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Emergency Contact</label>
              <input name="emergency_contact" className="form-control" value={form.emergency_contact} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">National ID Number (NIN)</label>
              <input name="national_id_number" className="form-control" value={form.national_id_number} onChange={handleChange} />
            </div>
            <div className="col-md-4">
              <label className="form-label">Tax Identification Number</label>
              <input name="tax_identification_number" className="form-control" value={form.tax_identification_number} onChange={handleChange} />
            </div>
            <div className="col-md-4">
              <label className="form-label">NSSF Number</label>
              <input name="nssf_number" className="form-control" value={form.nssf_number} onChange={handleChange} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Job Title</label>
              <input name="job_title" className="form-control" value={form.job_title} onChange={handleChange} required />
            </div>
            <div className="col-md-6">
              <label className="form-label">Department</label>
              <select name="department" className="form-select" value={form.department} onChange={handleChange}>
                <option value="">Select department</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Position</label>
              <select name="position" className="form-select" value={form.position} onChange={handleChange}>
                <option value="">Select position</option>
                {positions.map((position) => <option key={position.id} value={position.id}>{position.title}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Job Grade</label>
              <select name="grade" className="form-select" value={form.grade} onChange={handleChange}>
                <option value="">Select grade</option>
                {grades.map((grade) => <option key={grade.id} value={grade.id}>{grade.code} — {grade.name}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Supervisor</label>
              <select name="supervisor" className="form-select" value={form.supervisor} onChange={handleChange}>
                <option value="">Select supervisor</option>
                {employees.filter((employee) => String(employee.id) !== String(id)).map((employee) => (
                  <option key={employee.id} value={employee.id}>{employee.full_name}</option>
                ))}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label">Employment Type</label>
              <select name="employment_type" className="form-select" value={form.employment_type} onChange={handleChange}>
                <option value="permanent">Permanent</option>
                <option value="fixed_term">Fixed Term</option>
                <option value="temporary">Temporary</option>
                <option value="intern">Intern</option>
                <option value="consultant">Consultant</option>
              </select>
            </div>
            <div className="col-md-6">
              <label className="form-label">Date Joined</label>
              <input type="date" name="date_joined" className="form-control" value={form.date_joined} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">Probation End Date</label>
              <input type="date" name="probation_end_date" className="form-control" value={form.probation_end_date} onChange={handleChange} />
            </div>
            <div className="col-md-4">
              <label className="form-label">Work Location</label>
              <input name="work_location" className="form-control" value={form.work_location} onChange={handleChange} />
            </div>
            <div className="col-md-4">
              <label className="form-label">Cost Centre</label>
              <input name="cost_center" className="form-control" value={form.cost_center} onChange={handleChange} />
            </div>
            <div className="col-md-4">
              <label className="form-label">Account Number</label>
              <input name="account_number" className="form-control" value={form.account_number} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">Bank</label>
              <input name="bank" className="form-control" value={form.bank} onChange={handleChange} required />
            </div>
            <div className="col-md-4">
              <label className="form-label">Salary</label>
              <input type="number" step="0.01" name="salary" className="form-control" value={form.salary} onChange={handleChange} required />
            </div>
          </div>

          <div className="mt-4">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : isEdit ? 'Update Employee' : 'Create Employee'}
            </button>
          </div>
        </div>
      </form>
    </>
  );
}
