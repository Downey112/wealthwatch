import axios from 'axios';
import { supabase } from './supabase';

// Same-origin /api by default: Vercel routes it to the Python function in
// production, and the CRA dev server proxies it to localhost:8000.
const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '/api',
});

// The API identifies the user from their Supabase access token. getSession
// refreshes an expired token before returning it.
client.interceptors.request.use(async (config) => {
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session) {
      config.headers.Authorization = `Bearer ${data.session.access_token}`;
    }
  }
  return config;
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
