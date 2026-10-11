import { createClient } from '@supabase/supabase-js';

const url = process.env.REACT_APP_SUPABASE_URL;
const anonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;

// null when Supabase is not configured, which is the normal local setup:
// `npm start` then signs in as the dev user (see App.js).
export const supabase = url && anonKey ? createClient(url, anonKey) : null;
