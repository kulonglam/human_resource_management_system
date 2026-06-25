export default function ResumePreview({ url }) {
  if (!url) return null;

  const isPdf = url.toLowerCase().includes('.pdf') || url.includes('application/pdf');

  return (
    <div className="recruitment-resume-preview">
      {isPdf ? (
        <iframe title="Resume preview" src={url} className="recruitment-resume-frame" />
      ) : (
        <div className="recruitment-resume-fallback">
          <i className="bi bi-file-earmark-text display-6 text-muted" />
          <p className="text-muted mb-2">Inline preview is available for PDF resumes.</p>
          <a href={url} target="_blank" rel="noreferrer" className="btn btn-outline-primary btn-sm">
            Download / open resume
          </a>
        </div>
      )}
    </div>
  );
}
