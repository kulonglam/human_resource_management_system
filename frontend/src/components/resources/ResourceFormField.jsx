export function defaultLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ResourceFormField({ field, value, onChange, options = {}, existingUrl }) {
  const { name, label, type = 'text', required, choices, step, accept } = field;
  const fieldId = `field-${name}`;
  const common = {
    name,
    id: fieldId,
    className: 'form-control form-control-sm',
    value: type === 'file' ? undefined : (value ?? ''),
    onChange,
    required: type === 'file' ? required && !existingUrl : required,
  };

  if (type === 'file') {
    return (
      <div className="mb-3">
        <label className="form-label" htmlFor={fieldId}>{label || defaultLabel(name)}</label>
        {existingUrl && (
          <div className="mb-1">
            <a href={existingUrl} target="_blank" rel="noreferrer">View current file</a>
          </div>
        )}
        <input type="file" accept={accept} className="form-control form-control-sm" name={name} id={fieldId} onChange={onChange} />
      </div>
    );
  }

  if (type === 'select') {
    const opts = choices || options[name] || [];
    return (
      <div className="mb-3">
        <label className="form-label" htmlFor={fieldId}>{label || defaultLabel(name)}</label>
        <select {...common} className="form-select form-select-sm">
          <option value="">Select...</option>
          {opts.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (type === 'textarea') {
    return (
      <div className="mb-3">
        <label className="form-label" htmlFor={fieldId}>{label || defaultLabel(name)}</label>
        <textarea {...common} className="form-control form-control-sm" rows={3} />
      </div>
    );
  }

  if (type === 'checkbox') {
    return (
      <div className="form-check mb-3">
        <input
          type="checkbox"
          className="form-check-input"
          name={name}
          id={fieldId}
          checked={!!value}
          onChange={(e) => onChange({ target: { name, value: e.target.checked, type: 'checkbox' } })}
        />
        <label className="form-check-label" htmlFor={fieldId}>
          {label || defaultLabel(name)}
        </label>
      </div>
    );
  }

  return (
    <div className="mb-3">
      <label className="form-label" htmlFor={fieldId}>{label || defaultLabel(name)}</label>
      <input type={type} step={step} {...common} />
    </div>
  );
}
