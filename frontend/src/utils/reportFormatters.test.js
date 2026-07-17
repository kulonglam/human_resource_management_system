import { describe, expect, it } from 'vitest';
import { formatDate, formatLabel, formatUGX, REPORT_TABS } from './reportFormatters';

describe('formatUGX', () => {
  it('formats whole numbers with separators', () => {
    expect(formatUGX(1500000)).toBe('UGX 1,500,000');
  });

  it('coerces numeric strings', () => {
    expect(formatUGX('2500')).toBe('UGX 2,500');
  });

  it('treats invalid values as zero', () => {
    expect(formatUGX(null)).toBe('UGX 0');
    expect(formatUGX('abc')).toBe('UGX 0');
    expect(formatUGX(undefined)).toBe('UGX 0');
  });

  it('rounds fractions away', () => {
    expect(formatUGX(1999.6)).toBe('UGX 2,000');
  });
});

describe('formatDate', () => {
  it('renders an em dash for empty values', () => {
    expect(formatDate('')).toBe('—');
    expect(formatDate(null)).toBe('—');
  });

  it('formats ISO dates', () => {
    expect(formatDate('2026-07-17')).toMatch(/17 Jul 2026/);
  });

  it('returns the raw value for unparseable dates', () => {
    expect(formatDate('not-a-date')).toBe('not-a-date');
  });
});

describe('formatLabel', () => {
  it('renders an em dash for empty values', () => {
    expect(formatLabel('')).toBe('—');
    expect(formatLabel(null)).toBe('—');
  });

  it('converts snake_case to Title Case', () => {
    expect(formatLabel('annual_leave')).toBe('Annual Leave');
    expect(formatLabel('paid')).toBe('Paid');
  });

  it('stringifies non-string input', () => {
    expect(formatLabel(42)).toBe('42');
  });
});

describe('REPORT_TABS', () => {
  it('exposes stable tab ids', () => {
    expect(REPORT_TABS.map((tab) => tab.id)).toEqual([
      'overview', 'attendance', 'leave', 'payroll', 'performance', 'recruitment',
    ]);
  });
});
