/** Character-kind helpers for form inputs (letters / digits / alphanumeric). */

export const INPUT_KIND = {
  letters: 'letters',
  digits: 'digits',
  alphanumeric: 'alphanumeric',
  phone: 'phone',
};

const LETTERS_RE = /^[A-Za-z]+(?:[ '\-.][A-Za-z]+)*$/;
const DIGITS_RE = /^\d*$/;
const PHONE_RE = /^\+?\d*$/;
const ALPHANUMERIC_RE = /^[A-Za-z0-9]+(?:[ \-_/]+[A-Za-z0-9]+)*$/;
const ADDRESS_RE = /^[A-Za-z0-9]+(?:[ \-_/.,#]+[A-Za-z0-9]+)*$/;

/** Strip characters that are never allowed for the given kind (as-you-type). */
export function sanitizeByKind(value, kind) {
  const raw = value ?? '';
  switch (kind) {
    case INPUT_KIND.letters:
      return raw.replace(/[^A-Za-z '\-.]/g, '');
    case INPUT_KIND.digits:
      return raw.replace(/\D/g, '');
    case INPUT_KIND.phone:
      return raw.replace(/[^\d+]/g, '').replace(/(?!^)\+/g, '');
    case INPUT_KIND.alphanumeric:
      return raw.replace(/[^A-Za-z0-9 \-_/]/g, '');
    case 'address':
      return raw.replace(/[^A-Za-z0-9 \-_/.,#]/g, '');
    default:
      return raw;
  }
}

/** Final format check (empty is allowed; required is handled by the form). */
export function isValidByKind(value, kind) {
  if (value == null || value === '') return true;
  const v = String(value).trim();
  switch (kind) {
    case INPUT_KIND.letters:
      return LETTERS_RE.test(v);
    case INPUT_KIND.digits:
      return DIGITS_RE.test(v) && v.length > 0;
    case INPUT_KIND.phone: {
      const compact = v.replace(/[\s\-()]/g, '');
      return /^\+?\d{9,15}$/.test(compact);
    }
    case INPUT_KIND.alphanumeric:
      return ALPHANUMERIC_RE.test(v);
    case 'address':
      return ADDRESS_RE.test(v);
    default:
      return true;
  }
}

export function kindHint(kind) {
  switch (kind) {
    case INPUT_KIND.letters:
      return 'Letters only';
    case INPUT_KIND.digits:
      return 'Digits only';
    case INPUT_KIND.phone:
      return 'Digits only (9–15), optional +';
    case INPUT_KIND.alphanumeric:
      return 'Letters and numbers';
    case 'address':
      return 'Letters and numbers';
    default:
      return '';
  }
}

export function inputModeForKind(kind) {
  if (kind === INPUT_KIND.digits || kind === INPUT_KIND.phone) return 'numeric';
  if (kind === INPUT_KIND.letters) return 'text';
  return 'text';
}
