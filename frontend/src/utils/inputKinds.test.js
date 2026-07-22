import { describe, expect, it } from 'vitest';
import {
  INPUT_KIND,
  isValidByKind,
  sanitizeByKind,
} from './inputKinds';

describe('inputKinds', () => {
  it('sanitizes letters-only fields', () => {
    expect(sanitizeByKind('John2!', INPUT_KIND.letters)).toBe('John');
    expect(isValidByKind("O'Neil", INPUT_KIND.letters)).toBe(true);
    expect(isValidByKind('Mary-Jane', INPUT_KIND.letters)).toBe(true);
    expect(isValidByKind('John2', INPUT_KIND.letters)).toBe(false);
  });

  it('sanitizes digits-only fields', () => {
    expect(sanitizeByKind('12a34', INPUT_KIND.digits)).toBe('1234');
    expect(isValidByKind('1234', INPUT_KIND.digits)).toBe(true);
    expect(isValidByKind('12a', INPUT_KIND.digits)).toBe(false);
  });

  it('sanitizes alphanumeric fields', () => {
    expect(sanitizeByKind('EMP-001!', INPUT_KIND.alphanumeric)).toBe('EMP-001');
    expect(isValidByKind('Engineer II', INPUT_KIND.alphanumeric)).toBe(true);
    expect(isValidByKind('Bad@Title', INPUT_KIND.alphanumeric)).toBe(false);
  });
});
