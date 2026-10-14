-- ==============================================================================
-- FANTASY FOOTBALL SCHEMA REPLICATION FOR SUPABASE
-- Extracted and structured for clean replication in new Supabase project
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. PROFILES (Users linked to Supabase Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    role TEXT DEFAULT 'coach',
    bio TEXT,
    motto TEXT,
    preferred_color TEXT,
    avatar_url TEXT,
    title TEXT,
    stripe_customer_id TEXT UNIQUE,
    subscription_tier TEXT,
    override_tier TEXT,
    subscription_status TEXT,
    subscription_period_end TIMESTAMPTZ,
    naf_number TEXT,
    naf_name TEXT,
    naf_stats JSONB,
    last_naf_sync TIMESTAMPTZ
);

-- 2. LEAGUES
CREATE TABLE IF NOT EXISTS public.leagues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    creator_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    invite_code TEXT UNIQUE NOT NULL,
    format TEXT NOT NULL DEFAULT 'standard',
    is_double_round BOOLEAN NOT NULL DEFAULT false,
    number_of_groups INTEGER,
    is_public BOOLEAN DEFAULT true,
    tier_rules JSONB,
    star_players_banned BOOLEAN NOT NULL DEFAULT false,
    max_star_player_cost INTEGER,
    banned_inducements JSONB,
    custom_rules TEXT,
    draft_budget INTEGER,
    team_tiers JSONB,
    max_primary_skills_per_player INTEGER NOT NULL DEFAULT 1,
    max_secondary_skills_per_player INTEGER NOT NULL DEFAULT 1,
    max_combos_per_player INTEGER NOT NULL DEFAULT 0,
    max_players_with_combo INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    current_phase INTEGER NOT NULL DEFAULT 1,
    logo_url TEXT,
    mvps_per_match INTEGER DEFAULT 1,
    game_mode TEXT DEFAULT 'standard',
    allow_free_lineman_skill BOOLEAN DEFAULT false,
    commissioner_ids UUID[] NOT NULL DEFAULT '{}'::uuid[]
);

-- 3. SEASONS
CREATE TABLE IF NOT EXISTS public.seasons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id UUID REFERENCES public.leagues(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'active'
);

-- 4. LEAGUE ROUNDS
CREATE TABLE IF NOT EXISTS public.league_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id UUID NOT NULL REFERENCES public.leagues(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    phase INTEGER NOT NULL DEFAULT 1,
    start_date DATE,
    end_date DATE,
    extension_days INTEGER NOT NULL DEFAULT 0
);

-- 5. LEAGUE MEMBERS
CREATE TABLE IF NOT EXISTS public.league_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id UUID NOT NULL REFERENCES public.leagues(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'coach',
    joined_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_league_member UNIQUE (league_id, user_id)
);

-- 6. TEAMS
CREATE TABLE IF NOT EXISTS public.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    league_id UUID REFERENCES public.leagues(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    race TEXT NOT NULL,
    treasury INTEGER DEFAULT 1000000,
    team_value INTEGER DEFAULT 0,
    rerolls INTEGER NOT NULL DEFAULT 0,
    assistant_coaches INTEGER NOT NULL DEFAULT 0,
    cheerleaders INTEGER NOT NULL DEFAULT 0,
    apothecary BOOLEAN NOT NULL DEFAULT false,
    dedicated_fans INTEGER NOT NULL DEFAULT 1,
    roster_closed BOOLEAN NOT NULL DEFAULT false,
    wins INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    played INTEGER NOT NULL DEFAULT 0,
    group_name TEXT,
    td_for INTEGER NOT NULL DEFAULT 0,
    td_against INTEGER NOT NULL DEFAULT 0,
    cas_for INTEGER NOT NULL DEFAULT 0,
    cas_against INTEGER NOT NULL DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    expensive_mistakes_pending BOOLEAN DEFAULT false,
    inducements JSONB NOT NULL DEFAULT '{}',
    conference_name TEXT,
    logo_url TEXT,
    allow_free_lineman_skill BOOLEAN DEFAULT false,
    sprint_falls INTEGER NOT NULL DEFAULT 0,
    dismissed_positionals JSONB DEFAULT '[]'
);

-- 7. PLAYERS
CREATE TABLE IF NOT EXISTS public.players (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    number INTEGER NOT NULL,
    position TEXT NOT NULL,
    spp INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    ma INTEGER,
    st INTEGER,
    ag TEXT,
    pa TEXT,
    av TEXT,
    cost INTEGER NOT NULL,
    ma_mod INTEGER NOT NULL DEFAULT 0,
    st_mod INTEGER NOT NULL DEFAULT 0,
    ag_mod INTEGER NOT NULL DEFAULT 0,
    pa_mod INTEGER NOT NULL DEFAULT 0,
    av_mod INTEGER NOT NULL DEFAULT 0,
    niggling INTEGER NOT NULL DEFAULT 0,
    spp_spent INTEGER NOT NULL DEFAULT 0,
    advancements JSONB NOT NULL DEFAULT '[]',
    tv_added INTEGER NOT NULL DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    hired_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    pending_advancement JSONB,
    is_captain BOOLEAN DEFAULT false,
    sprint_falls INTEGER NOT NULL DEFAULT 0,
    is_veteran BOOLEAN DEFAULT false
);

-- 8. TOURNAMENTS
CREATE TABLE IF NOT EXISTS public.tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    creator_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    format TEXT NOT NULL DEFAULT 'single_elimination',
    status TEXT NOT NULL DEFAULT 'draft',
    draft_budget INTEGER NOT NULL DEFAULT 1150000,
    max_teams INTEGER,
    bonus_t1 INTEGER NOT NULL DEFAULT 0,
    bonus_t2 INTEGER NOT NULL DEFAULT 0,
    bonus_t3 INTEGER NOT NULL DEFAULT 0,
    bonus_t4 INTEGER NOT NULL DEFAULT 0,
    star_players_banned BOOLEAN NOT NULL DEFAULT false,
    max_star_player_cost INTEGER,
    banned_inducements TEXT[] DEFAULT '{}'::text[],
    custom_rules TEXT,
    invite_code TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    tier_rules JSONB,
    team_tiers JSONB,
    max_primary_skills_per_player INTEGER NOT NULL DEFAULT 1,
    max_secondary_skills_per_player INTEGER NOT NULL DEFAULT 1,
    max_combos_per_player INTEGER NOT NULL DEFAULT 0,
    max_players_with_combo INTEGER NOT NULL DEFAULT 0,
    winner_team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    logo_url TEXT,
    game_mode TEXT DEFAULT 'standard'
);

-- 9. TOURNAMENT PARTICIPANTS
CREATE TABLE IF NOT EXISTS public.tournament_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES public.tournaments(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    CONSTRAINT unique_tournament_participant UNIQUE (tournament_id, team_id)
);

-- 10. TOURNAMENT ROUNDS
CREATE TABLE IF NOT EXISTS public.tournament_rounds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES public.tournaments(id) ON DELETE CASCADE,
    round_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- 11. TOURNAMENT MATCHES
CREATE TABLE IF NOT EXISTS public.tournament_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID NOT NULL REFERENCES public.tournaments(id) ON DELETE CASCADE,
    round_id UUID NOT NULL REFERENCES public.tournament_rounds(id) ON DELETE CASCADE,
    home_team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    away_team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    home_score INTEGER,
    away_score INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled',
    played_at TIMESTAMPTZ,
    bracket_index INTEGER,
    home_cas INTEGER,
    away_cas INTEGER
);

-- 12. MATCHES (LEAGUE & GENERAL)
CREATE TABLE IF NOT EXISTS public.matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id UUID REFERENCES public.leagues(id) ON DELETE SET NULL,
    home_team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    away_team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    home_score INTEGER NOT NULL DEFAULT 0,
    away_score INTEGER NOT NULL DEFAULT 0,
    weather TEXT,
    kickoff_event TEXT,
    home_fame INTEGER NOT NULL DEFAULT 0,
    away_fame INTEGER NOT NULL DEFAULT 0,
    home_winnings INTEGER NOT NULL DEFAULT 0,
    away_winnings INTEGER NOT NULL DEFAULT 0,
    played_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    status TEXT NOT NULL DEFAULT 'scheduled',
    round_id UUID REFERENCES public.league_rounds(id) ON DELETE SET NULL,
    home_mistake_loss INTEGER NOT NULL DEFAULT 0,
    away_mistake_loss INTEGER NOT NULL DEFAULT 0,
    home_inducement_treasury INTEGER NOT NULL DEFAULT 0,
    away_inducement_treasury INTEGER NOT NULL DEFAULT 0,
    home_inducements JSONB NOT NULL DEFAULT '{}',
    away_inducements JSONB NOT NULL DEFAULT '{}',
    tournament_id UUID REFERENCES public.tournaments(id) ON DELETE SET NULL,
    away_tv INTEGER,
    home_tv INTEGER,
    creator_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    wizard_step INTEGER DEFAULT 1,
    wizard_data JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    home_initial_treasury INTEGER,
    away_initial_treasury INTEGER,
    home_no_stall BOOLEAN DEFAULT false,
    away_no_stall BOOLEAN DEFAULT false
);

-- 13. MATCH PLAYER EVENTS
CREATE TABLE IF NOT EXISTS public.match_player_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES public.matches(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES public.players(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    touchdowns INTEGER NOT NULL DEFAULT 0,
    completions INTEGER NOT NULL DEFAULT 0,
    casualties_caused INTEGER NOT NULL DEFAULT 0,
    interceptions INTEGER NOT NULL DEFAULT 0,
    is_mvp BOOLEAN NOT NULL DEFAULT false,
    injury_result TEXT,
    fouls_committed INTEGER DEFAULT 0,
    superb_passes INTEGER NOT NULL DEFAULT 0,
    sprint_falls INTEGER NOT NULL DEFAULT 0
);

-- 14. MATCH EVENTS
CREATE TABLE IF NOT EXISTS public.match_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id UUID NOT NULL REFERENCES public.matches(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES public.teams(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES public.players(id) ON DELETE CASCADE,
    fouls_committed INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 15. LEAGUE BOUNTIES
CREATE TABLE IF NOT EXISTS public.league_bounties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_id UUID NOT NULL REFERENCES public.leagues(id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES public.players(id) ON DELETE CASCADE,
    bounty_amount INTEGER NOT NULL DEFAULT 0,
    reward_description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- 16. SUBSCRIPTIONS
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT NOT NULL,
    stripe_price_id TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    billing_interval TEXT NOT NULL DEFAULT 'month',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- ==============================================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ==============================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.seasons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_rounds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.players ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tournaments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tournament_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tournament_rounds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tournament_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_player_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_bounties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- ==============================================================================
-- BASIC PERMISSIVE RLS POLICIES FOR SUPABASE
-- ==============================================================================

-- Profiles: Public read, owner insert & update
DROP POLICY IF EXISTS "Public profiles read" ON public.profiles;
CREATE POLICY "Public profiles read" ON public.profiles FOR SELECT USING (true);
DROP POLICY IF EXISTS "Owner profile insert" ON public.profiles;
CREATE POLICY "Owner profile insert" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
DROP POLICY IF EXISTS "Owner profile update" ON public.profiles;
CREATE POLICY "Owner profile update" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Teams: Public read, owner manage
DROP POLICY IF EXISTS "Teams read all" ON public.teams;
CREATE POLICY "Teams read all" ON public.teams FOR SELECT USING (true);
DROP POLICY IF EXISTS "Owner team insert" ON public.teams;
CREATE POLICY "Owner team insert" ON public.teams FOR INSERT WITH CHECK (auth.uid() = owner_id);
DROP POLICY IF EXISTS "Owner team update" ON public.teams;
CREATE POLICY "Owner team update" ON public.teams FOR UPDATE USING (auth.uid() = owner_id);
DROP POLICY IF EXISTS "Owner team delete" ON public.teams;
CREATE POLICY "Owner team delete" ON public.teams FOR DELETE USING (auth.uid() = owner_id);

-- Players: Public read, team owner manage
DROP POLICY IF EXISTS "Players read all" ON public.players;
CREATE POLICY "Players read all" ON public.players FOR SELECT USING (true);
DROP POLICY IF EXISTS "Team owner player insert" ON public.players;
CREATE POLICY "Team owner player insert" ON public.players FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM public.teams WHERE id = team_id AND owner_id = auth.uid())
);
DROP POLICY IF EXISTS "Team owner player update" ON public.players;
CREATE POLICY "Team owner player update" ON public.players FOR UPDATE USING (
    EXISTS (SELECT 1 FROM public.teams WHERE id = team_id AND owner_id = auth.uid())
);
DROP POLICY IF EXISTS "Team owner player delete" ON public.players;
CREATE POLICY "Team owner player delete" ON public.players FOR DELETE USING (
    EXISTS (SELECT 1 FROM public.teams WHERE id = team_id AND owner_id = auth.uid())
);

-- Leagues: Public read, creator manage
DROP POLICY IF EXISTS "Leagues read all" ON public.leagues;
CREATE POLICY "Leagues read all" ON public.leagues FOR SELECT USING (true);
DROP POLICY IF EXISTS "Creator league insert" ON public.leagues;
CREATE POLICY "Creator league insert" ON public.leagues FOR INSERT WITH CHECK (auth.uid() = creator_id);
DROP POLICY IF EXISTS "Creator league update" ON public.leagues;
CREATE POLICY "Creator league update" ON public.leagues FOR UPDATE USING (auth.uid() = creator_id);
DROP POLICY IF EXISTS "Creator league delete" ON public.leagues;
CREATE POLICY "Creator league delete" ON public.leagues FOR DELETE USING (auth.uid() = creator_id);

-- Matches: Public read
DROP POLICY IF EXISTS "Matches read all" ON public.matches;
CREATE POLICY "Matches read all" ON public.matches FOR SELECT USING (true);

-- Match Events: Public read
DROP POLICY IF EXISTS "Match events read all" ON public.match_player_events;
CREATE POLICY "Match events read all" ON public.match_player_events FOR SELECT USING (true);
