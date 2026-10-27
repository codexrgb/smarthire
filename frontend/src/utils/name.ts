/**
 * Utility functions for user name presentation.
 */

/**
 * Formats the user's first name for greetings and labels.
 * Extracts the first word. If the name is entered in all lowercase
 * (e.g. "divya", "alex smith"), it capitalizes the initial letter ("Divya", "Alex").
 * If the name already has uppercase or mixed casing (e.g. "McGregor", "O'Connor", "Jane"),
 * it preserves the exact casing.
 */
export function formatFirstName(fullName?: string | null, fallback: string = 'User'): string {
  if (!fullName || typeof fullName !== 'string') {
    return fallback;
  }

  const trimmed = fullName.trim();
  if (!trimmed) {
    return fallback;
  }

  const firstWord = trimmed.split(/\s+/)[0];
  if (!firstWord) {
    return fallback;
  }

  // Check if string has at least one letter and is completely in lowercase
  const hasLetters = /[a-zA-Z]/.test(firstWord);
  if (hasLetters && firstWord === firstWord.toLowerCase()) {
    return firstWord.charAt(0).toUpperCase() + firstWord.slice(1);
  }

  return firstWord;
}
