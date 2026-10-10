import axios from 'axios';

// Same-origin /api by default: Azure Static Web Apps proxies it to the backend
// in production, and the CRA dev server proxies it to localhost:7071.
const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
});

export const getSummary = (year, month) =>
  client.get('/getsummary', { params: { year, month } }).then(res => res.data);

export const getTransactions = (year, month) =>
  client.get('/gettransactions', { params: { year, month } }).then(res => res.data);

export const addTransaction = (transaction) =>
  client.post('/addtransaction', transaction).then(res => res.data);

export const deleteTransaction = (id) =>
  client.delete(`/deletetransaction/${id}`).then(res => res.data);

// Message the API sent back, or the fallback when it sent none.
export const errorMessage = (error, fallback) =>
  error?.response?.data?.error || fallback;
