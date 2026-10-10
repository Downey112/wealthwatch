export const MONTHS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

export const monthName = (month, format = 'long') =>
  new Date(2024, month - 1).toLocaleString('default', { month: format });

// The current year and the five before it, newest first.
export const yearOptions = (now = new Date()) =>
  Array.from({ length: 6 }, (_, i) => now.getFullYear() - i);

// Today's date as YYYY-MM-DD in the user's own timezone (toISOString is UTC).
export const localDateISO = (now = new Date()) => {
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
};
