import { describe, it, expect } from 'vitest';
import { formatFirstName } from '../utils/name';

describe('formatFirstName utility', () => {
  it('capitalizes all-lowercase first names properly (e.g. divya -> Divya)', () => {
    expect(formatFirstName('divya')).toBe('Divya');
    expect(formatFirstName('divya sharma')).toBe('Divya');
    expect(formatFirstName('alex')).toBe('Alex');
    expect(formatFirstName('sarah connor')).toBe('Sarah');
  });

  it('preserves existing mixed-case and camel-case names (e.g. McGregor, McDonald, O\'Connor)', () => {
    expect(formatFirstName('McGregor')).toBe('McGregor');
    expect(formatFirstName('McDonald')).toBe('McDonald');
    expect(formatFirstName("O'Connor")).toBe("O'Connor");
    expect(formatFirstName('vanDyke')).toBe('vanDyke');
  });

  it('preserves already-capitalized names', () => {
    expect(formatFirstName('Divya')).toBe('Divya');
    expect(formatFirstName('John Doe')).toBe('John');
    expect(formatFirstName('Jane Candidate')).toBe('Jane');
  });

  it('handles edge cases, extra whitespace, empty strings and null/undefined gracefully', () => {
    expect(formatFirstName('')).toBe('User');
    expect(formatFirstName('   ')).toBe('User');
    expect(formatFirstName(null, 'Candidate')).toBe('Candidate');
    expect(formatFirstName(undefined, 'Recruiter')).toBe('Recruiter');
    expect(formatFirstName('   divya   ')).toBe('Divya');
  });
});
