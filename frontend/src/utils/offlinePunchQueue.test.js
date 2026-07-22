import { beforeEach, describe, expect, it, vi } from 'vitest';
import { makeClientPunchId } from './offlinePunchQueue';

describe('offlinePunchQueue helpers', () => {
  beforeEach(() => {
    vi.stubGlobal('crypto', {
      randomUUID: () => 'uuid-test-1',
    });
  });

  it('uses crypto.randomUUID when available', () => {
    expect(makeClientPunchId()).toBe('uuid-test-1');
  });

  it('falls back without crypto.randomUUID', () => {
    vi.stubGlobal('crypto', {});
    const id = makeClientPunchId();
    expect(id.startsWith('punch-')).toBe(true);
  });
});
