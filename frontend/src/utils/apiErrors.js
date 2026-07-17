/** Flatten DRF / Django REST validation payloads into a readable string. */

export function formatApiErrors(data, fallback = 'Request failed') {
  if (data == null) return fallback;
  if (typeof data === 'string') {
    return data.trimStart().startsWith('<') ? fallback : data;
  }
  if (typeof data !== 'object') return fallback;

  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => (typeof item === 'string' ? item : JSON.stringify(item))).join(' ');
  }

  if (Array.isArray(data.non_field_errors)) {
    return data.non_field_errors.join(' ');
  }

  const parts = [];
  for (const [field, msgs] of Object.entries(data)) {
    if (field === 'detail' || field === 'non_field_errors') continue;
    if (Array.isArray(msgs)) {
      parts.push(`${field}: ${msgs.join(', ')}`);
    } else if (msgs && typeof msgs === 'object') {
      parts.push(`${field}: ${formatApiErrors(msgs, '')}`);
    } else if (msgs != null && msgs !== '') {
      parts.push(`${field}: ${msgs}`);
    }
  }
  return parts.filter(Boolean).join(' ') || fallback;
}

export function errorMessage(err, fallback = 'Request failed') {
  if (!err) return fallback;
  return formatApiErrors(err.data, err.message || fallback);
}
