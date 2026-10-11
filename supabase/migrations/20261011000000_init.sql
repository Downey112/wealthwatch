-- WealthWatch schema for Supabase Postgres. Applied with `supabase db push`.
-- Local development needs none of this: the API creates a SQLite file itself.

create table public.users (
    user_id integer generated always as identity primary key,
    email text unique not null,
    display_name text,
    created_at timestamptz not null default now()
);

create table public.transactions (
    transaction_id integer generated always as identity primary key,
    user_id integer not null references public.users (user_id) on delete cascade,
    amount numeric(10, 2) not null check (amount > 0),
    type text not null check (type in ('income', 'expense')),
    category varchar(50) not null,
    description varchar(255),
    transaction_date date not null,
    created_at timestamptz not null default now()
);

-- Every query filters on user_id and a transaction_date range.
create index idx_user_date on public.transactions (user_id, transaction_date);

-- Supabase exposes the public schema through its auto-generated REST API, and
-- the key for that API ships in the frontend. Row level security with no
-- policies shuts that door: only the WealthWatch API, which connects as the
-- table owner, can read or write these tables.
alter table public.users enable row level security;
alter table public.transactions enable row level security;
revoke all on public.users, public.transactions from anon, authenticated;
