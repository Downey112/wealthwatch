import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
import * as api from './api';
import { localDateISO, yearOptions } from './utils/dates';

jest.mock('./api', () => ({
  getSummary: jest.fn(),
  getTransactions: jest.fn(),
  addTransaction: jest.fn(),
  deleteTransaction: jest.fn(),
  errorMessage: (error, fallback) => error?.response?.data?.error || fallback,
}));

// Chart.js needs a real canvas, which jsdom does not provide.
jest.mock('react-chartjs-2', () => ({
  Pie: ({ data }) => <div data-testid="pie-chart">{data.labels.join(',')}</div>,
}));

const signedInAs = (clientPrincipal) => {
  global.fetch = jest.fn(() =>
    Promise.resolve({ json: () => Promise.resolve({ clientPrincipal }) })
  );
};

const SUMMARY = {
  total_income: 3000,
  total_expense: 750.5,
  net_savings: 2249.5,
  categories: [{ category: 'Housing', total: 450 }, { category: 'Food', total: 300.5 }],
};

const LUNCH = {
  id: 7, amount: 12.5, type: 'expense', category: 'Food', description: 'Lunch', date: '2026-03-15',
};

beforeEach(() => {
  jest.clearAllMocks();
  api.getSummary.mockResolvedValue(SUMMARY);
  api.getTransactions.mockResolvedValue([LUNCH]);
});

test('asks signed-out visitors to sign in', async () => {
  signedInAs(null);
  render(<App />);
  expect(await screen.findByText(/sign in with microsoft/i)).toBeInTheDocument();
  expect(api.getSummary).not.toHaveBeenCalled();
});

test('shows the summary, chart and transactions for a signed-in user', async () => {
  signedInAs({ userDetails: 'alice@example.com' });
  render(<App />);

  expect(await screen.findByText(/alice@example.com/)).toBeInTheDocument();
  expect(await screen.findByText('RM 3000.00')).toBeInTheDocument();
  expect(screen.getByText('RM 750.50')).toBeInTheDocument();
  expect(screen.getByText('RM 2249.50')).toBeInTheDocument();
  expect(screen.getByTestId('pie-chart')).toHaveTextContent('Housing,Food');
  expect(await screen.findByText('- RM 12.50')).toBeInTheDocument();

  const now = new Date();
  expect(api.getSummary).toHaveBeenCalledWith(now.getFullYear(), now.getMonth() + 1);
});

test('adding a transaction posts it and reloads the data', async () => {
  signedInAs({ userDetails: 'alice@example.com' });
  api.addTransaction.mockResolvedValue({ transaction_id: 8 });
  render(<App />);
  await screen.findByText('RM 3000.00');

  userEvent.type(screen.getByLabelText(/amount/i), '42.10');
  userEvent.type(screen.getByLabelText(/description/i), 'Groceries');
  userEvent.click(screen.getByRole('button', { name: /add transaction/i }));

  await waitFor(() => expect(api.addTransaction).toHaveBeenCalledWith({
    amount: 42.1,
    type: 'expense',
    category: 'Food',
    description: 'Groceries',
    transaction_date: localDateISO(),
  }));
  await waitFor(() => expect(api.getSummary).toHaveBeenCalledTimes(2));
  expect(api.getTransactions).toHaveBeenCalledTimes(2);
});

test('shows the API error when adding a transaction fails', async () => {
  signedInAs({ userDetails: 'alice@example.com' });
  api.addTransaction.mockRejectedValue({ response: { data: { error: 'amount must be a number' } } });
  render(<App />);
  await screen.findByText('RM 3000.00');

  userEvent.type(screen.getByLabelText(/amount/i), '5');
  userEvent.click(screen.getByRole('button', { name: /add transaction/i }));

  expect(await screen.findByText('amount must be a number')).toBeInTheDocument();
});

test('deleting a transaction reloads the list and the summary', async () => {
  signedInAs({ userDetails: 'alice@example.com' });
  api.deleteTransaction.mockResolvedValue({});
  jest.spyOn(window, 'confirm').mockReturnValue(true);
  render(<App />);

  userEvent.click(await screen.findByRole('button', { name: /delete food transaction/i }));

  await waitFor(() => expect(api.deleteTransaction).toHaveBeenCalledWith(7));
  await waitFor(() => expect(api.getSummary).toHaveBeenCalledTimes(2));
});

test('keeps the period selectors usable when the summary fails to load', async () => {
  signedInAs({ userDetails: 'alice@example.com' });
  api.getSummary.mockRejectedValue(new Error('network'));
  render(<App />);

  expect(await screen.findByText(/failed to load summary/i)).toBeInTheDocument();
  expect(screen.getAllByLabelText('Year')).toHaveLength(2);
});

test('year options always include the current year', () => {
  expect(yearOptions(new Date(2026, 9, 10))).toEqual([2026, 2025, 2024, 2023, 2022, 2021]);
});

test('localDateISO uses the local calendar date', () => {
  expect(localDateISO(new Date(2026, 0, 5, 1, 30))).toBe('2026-01-05');
});
