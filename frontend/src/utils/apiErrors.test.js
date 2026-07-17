import { describe, expect, it } from 'vitest';
import { errorMessage, formatApiErrors } from './apiErrors';

describe('formatApiErrors', () => {
  it('returns fallback for null/undefined', () => {
    expect(formatApiErrors(null)).toBe('Request failed');
    expect(formatApiErrors(undefined, 'Oops')).toBe('Oops');
  });

  it('returns plain string errors as-is', () => {
    expect(formatApiErrors('Something broke')).toBe('Something broke');
  });

  it('replaces HTML error pages with the fallback', () => {
    expect(formatApiErrors('<!DOCTYPE html><html>500</html>', 'Server error')).toBe('Server error');
    expect(formatApiErrors('  <html>oops</html>', 'Server error')).toBe('Server error');
  });

  it('returns fallback for non-object primitives', () => {
    expect(formatApiErrors(42)).toBe('Request failed');
    expect(formatApiErrors(true, 'Nope')).toBe('Nope');
  });

  it('prefers the detail string', () => {
    expect(formatApiErrors({ detail: 'Not found.' })).toBe('Not found.');
  });

  it('joins detail arrays', () => {
    expect(formatApiErrors({ detail: ['A', 'B'] })).toBe('A B');
    expect(formatApiErrors({ detail: ['A', { code: 'x' }] })).toBe('A {"code":"x"}');
  });

  it('joins non_field_errors', () => {
    expect(formatApiErrors({ non_field_errors: ['Bad combo', 'Try again'] })).toBe(
      'Bad combo Try again',
    );
  });

  it('formats field errors with array messages', () => {
    expect(formatApiErrors({ email: ['Required.', 'Invalid.'] })).toBe(
      'email: Required., Invalid.',
    );
  });

  it('formats nested object errors recursively', () => {
    expect(formatApiErrors({ profile: { phone: ['Too short.'] } })).toBe(
      'profile: phone: Too short.',
    );
  });

  it('formats scalar field errors', () => {
    expect(formatApiErrors({ amount: 'Must be positive' })).toBe('amount: Must be positive');
  });

  it('returns fallback when object has no usable messages', () => {
    expect(formatApiErrors({})).toBe('Request failed');
    expect(formatApiErrors({ field: '' }, 'Nothing')).toBe('Nothing');
  });
});

describe('errorMessage', () => {
  it('returns fallback when error is missing', () => {
    expect(errorMessage(null)).toBe('Request failed');
    expect(errorMessage(undefined, 'Custom')).toBe('Custom');
  });

  it('uses structured data when present', () => {
    const err = new Error('Request failed');
    err.data = { detail: 'Permission denied.' };
    expect(errorMessage(err)).toBe('Permission denied.');
  });

  it('falls back to the error message when no data', () => {
    const err = new Error('Network down');
    expect(errorMessage(err)).toBe('Network down');
  });
});
