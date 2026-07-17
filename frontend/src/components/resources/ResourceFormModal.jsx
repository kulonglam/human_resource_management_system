import ResourceFormField from './ResourceFormField';

export default function ResourceFormModal({
  tab,
  editing,
  form,
  visibleFormFields,
  lookupOptions,
  isEmployeeUser,
  user,
  submitting,
  onClose,
  onSubmit,
  onChange,
}) {
  return (
    <>
      <div className="modal show d-block" tabIndex="-1" role="dialog" aria-modal="true" aria-labelledby="resource-form-title">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <form onSubmit={onSubmit}>
              <div className="modal-header">
                <h5 className="modal-title" id="resource-form-title">{editing ? 'Edit' : 'Add'} {tab.label}</h5>
                <button type="button" className="btn-close" onClick={onClose} aria-label="Close" />
              </div>
              <div className="modal-body">
                {tab.selfServiceEmployee && isEmployeeUser && user?.linked_employee_name && (
                  <div className="alert alert-light border mb-3">
                    Applying as <strong>{user.linked_employee_name}</strong>
                  </div>
                )}
                <div className="row">
                  {visibleFormFields.map((field) => (
                    <div className={field.fullWidth ? 'col-12' : 'col-md-6'} key={field.name}>
                      <ResourceFormField
                        field={field}
                        value={form[field.name]}
                        onChange={onChange}
                        options={lookupOptions}
                        existingUrl={
                          field.type === 'file' && editing
                            ? editing[`${field.name}_url`] || editing[field.name]
                            : null
                        }
                      />
                    </div>
                  ))}
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}
