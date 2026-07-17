import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from './client';

function jsonResponse(body, { status = 200 } = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: () => 'application/json' },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

function htmlResponse(html, { status = 500 } = {}) {
  return {
    ok: false,
    status,
    headers: { get: () => 'text/html' },
    json: async () => { throw new Error('not json'); },
    text: async () => html,
  };
}

describe('api client', () => {
  beforeEach(() => {
    globalThis.document = { cookie: 'csrftoken=test-csrf-token' };
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    delete globalThis.document;
    delete globalThis.fetch;
  });

  it('GET requests hit /api/v1 and skip the CSRF header', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ status: 'ok' }));
    const data = await api.getHealth();
    expect(data).toEqual({ status: 'ok' });

    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/v1/health/');
    expect(options.credentials).toBe('include');
    expect(options.headers['X-CSRFToken']).toBeUndefined();
  });

  it('POST requests serialize JSON and attach the CSRF token', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ id: 1 }));
    await api.login('alice', 'secret');

    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/v1/auth/login/');
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(options.headers['X-CSRFToken']).toBe('test-csrf-token');
    expect(JSON.parse(options.body)).toEqual({ username: 'alice', password: 'secret' });
  });

  it('throws with detail message and attaches response data on error', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ detail: 'Permission denied.' }, { status: 403 }));
    const err = await api.getDashboard().catch((e) => e);
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toBe('Permission denied.');
    expect(err.status).toBe(403);
    expect(err.data).toEqual({ detail: 'Permission denied.' });
  });

  it('replaces HTML error pages with a friendly message', async () => {
    fetch.mockResolvedValueOnce(htmlResponse('<!DOCTYPE html><html>boom</html>'));
    const err = await api.getDashboard().catch((e) => e);
    expect(err.message).toMatch(/Server error \(500\)/);
    expect(err.data).toBeNull();
  });

  it('unwraps paginated list results', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ count: 1, results: [{ id: 7 }] }));
    const rows = await api.list('employees');
    expect(rows).toEqual([{ id: 7 }]);
  });

  it('passes plain arrays through list unwrapping', async () => {
    fetch.mockResolvedValueOnce(jsonResponse([{ id: 1 }, { id: 2 }]));
    const rows = await api.list('departments');
    expect(rows).toHaveLength(2);
  });

  it('encodes employee search queries', async () => {
    fetch.mockResolvedValueOnce(jsonResponse([]));
    await api.getEmployees('jane doe');
    expect(fetch.mock.calls[0][0]).toBe('/api/v1/employees/?q=jane%20doe');
  });

  it('PATCH updates go to the resource detail route', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ id: 3 }));
    await api.update('leaves', 3, { status: 'approved' });
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/v1/leaves/3/');
    expect(options.method).toBe('PATCH');
    expect(options.headers['X-CSRFToken']).toBe('test-csrf-token');
  });

  it('sends collection actions as POST when payload is provided', async () => {
    fetch.mockResolvedValueOnce(jsonResponse({ synced: 2 }));
    await api.collectionAction('leave-policy-allocations', 'sync', { year: 2026 });
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/v1/leave-policy-allocations/sync/');
    expect(options.method).toBe('POST');
  });
});
