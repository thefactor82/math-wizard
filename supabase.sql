-- Math Wizard - classifica online delle Sfide
-- Eseguire questo file nel SQL Editor di Supabase (o con psql) una sola volta.

create table if not exists public.challenge_scores (
    id bigint generated always as identity primary key,
    created_at timestamptz not null default now(),
    name text not null,
    uuid text not null,
    character text not null default '',
    operation text not null,
    questions_total integer not null,
    correct integer not null,
    wrong integer not null,
    average_time numeric(8,2) not null,
    total_time numeric(10,2) not null,
    version text not null default ''
);

create index if not exists challenge_scores_operation_idx
    on public.challenge_scores (operation, created_at desc);

create index if not exists challenge_scores_uuid_idx
    on public.challenge_scores (uuid);

-- La chiave anonima del progetto e' pubblica per progetto: l'accesso e' limitato
-- dalle policy qui sotto, non dalla segretezza della chiave.
alter table public.challenge_scores enable row level security;

-- Lettura della classifica: consentita a tutti (anche anonimi).
drop policy if exists challenge_scores_select on public.challenge_scores;
create policy challenge_scores_select
    on public.challenge_scores
    for select
    to anon, authenticated
    using (true);

-- Inserimento: consentito a tutti, ma solo con dati plausibili.
-- La rate limiting e' consigliata lato server (Edge Function) per evitare abusi.
drop policy if exists challenge_scores_insert on public.challenge_scores;
create policy challenge_scores_insert
    on public.challenge_scores
    for insert
    to anon, authenticated
    with check (
        char_length(name) between 1 and 40
        and char_length(uuid) between 8 and 64
        and char_length(character) <= 2
        and operation in ('moltiplicazione','addizione','sottrazione','divisione')
        and questions_total between 1 and 500
        and correct >= 0
        and wrong >= 0
        and correct + wrong <= questions_total
        and average_time >= 0
        and total_time >= 0
        and char_length(version) <= 20
    );

-- Nessuna modifica e nessuna cancellazione pubblica: le policy di update/delete
-- non vengono create, quindi le operazioni anonime falliscono.
