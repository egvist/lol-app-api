-- LoLApp v2 - PostgreSQL 15+
-- 25 tables = 10 original + 15 selected-feature tables.
-- Data sources: HTML initial pro directory; Riot APIs for accounts/ranked/matches;
-- licensed/authorized esports source for pro events.
-- Do not expose historical Riot IDs or non-consented custom-match histories.
-- Run against an empty database: psql -v ON_ERROR_STOP=1 -d lolapp -f sql/schema.sql

BEGIN;

-- 01. Pro directory (HTML bootstrap)
CREATE TABLE players (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nickname             VARCHAR(100) NOT NULL,
    slug                 VARCHAR(150) NOT NULL UNIQUE,
    country_code         CHAR(2),
    main_role            VARCHAR(16),
    profile_image_url    TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT players_role_ck CHECK
        (main_role IS NULL OR main_role IN ('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'))
);

-- 02. Social links
CREATE TABLE player_socials (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id            BIGINT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    platform             VARCHAR(40) NOT NULL,
    url                  TEXT NOT NULL,
    UNIQUE (player_id, platform, url)
);

-- 03. Accounts known to belong to pro players, PUUID resolved after HTML import
CREATE TABLE riot_accounts (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id            BIGINT NOT NULL REFERENCES players(id) ON DELETE RESTRICT,
    puuid                VARCHAR(128) UNIQUE,
    game_name            VARCHAR(100) NOT NULL,
    tag_line             VARCHAR(32) NOT NULL,
    platform_id          VARCHAR(12), -- EUW1, TR1, KR etc.; nullable before resolution
    summoner_level       INTEGER CHECK (summoner_level IS NULL OR summoner_level >= 0),
    profile_icon_id      INTEGER,
    last_synced_at       TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 04. Ranked years (2026=S16, 2027=S17). NOT LoL esports tournaments.
CREATE TABLE ranked_seasons (
    id                   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    season_year          SMALLINT NOT NULL UNIQUE,
    label                VARCHAR(20) NOT NULL UNIQUE,
    starts_at            TIMESTAMPTZ NOT NULL,
    ends_at              TIMESTAMPTZ NOT NULL,
    status               VARCHAR(12) NOT NULL DEFAULT 'UPCOMING',
    CHECK (ends_at > starts_at),
    CHECK (status IN ('UPCOMING','ACTIVE','FINISHED'))
);

-- 05. Per-account, per-year, per-queue rollup (current on closed year = final observed)
CREATE TABLE account_season_ranks (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id           BIGINT NOT NULL REFERENCES riot_accounts(id) ON DELETE CASCADE,
    season_id            INTEGER NOT NULL REFERENCES ranked_seasons(id),
    queue_type           VARCHAR(32) NOT NULL,
    current_tier         VARCHAR(16),
    current_division     VARCHAR(3),
    current_lp           INTEGER CHECK (current_lp IS NULL OR current_lp >= 0),
    current_wins         INTEGER CHECK (current_wins IS NULL OR current_wins >= 0),
    current_losses       INTEGER CHECK (current_losses IS NULL OR current_losses >= 0),
    current_observed_at  TIMESTAMPTZ,
    peak_tier            VARCHAR(16),
    peak_division        VARCHAR(3),
    peak_lp              INTEGER CHECK (peak_lp IS NULL OR peak_lp >= 0),
    peak_observed_at     TIMESTAMPTZ,
    finalized_at         TIMESTAMPTZ,
    UNIQUE (account_id, season_id, queue_type),
    CHECK (queue_type IN ('RANKED_SOLO_5x5','RANKED_FLEX_SR')),
    CHECK (current_division IS NULL OR current_division IN ('I','II','III','IV')),
    CHECK (peak_division IS NULL OR peak_division IN ('I','II','III','IV')),
    CHECK (finalized_at IS NULL OR current_observed_at IS NOT NULL)
);

-- 06. Immutable observations used for LP trend, audit, and last-season observation
CREATE TABLE rank_snapshots (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_season_rank_id BIGINT NOT NULL REFERENCES account_season_ranks(id) ON DELETE CASCADE,
    tier                 VARCHAR(16),
    division             VARCHAR(3),
    lp                   INTEGER CHECK (lp IS NULL OR lp >= 0),
    wins                 INTEGER CHECK (wins IS NULL OR wins >= 0),
    losses               INTEGER CHECK (losses IS NULL OR losses >= 0),
    observed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (account_season_rank_id, observed_at),
    CHECK (division IS NULL OR division IN ('I','II','III','IV'))
);

-- 07. Unique Riot Match-V5 match, regardless of which pro account discovered it
CREATE TABLE matches (
    match_id             VARCHAR(80) PRIMARY KEY, -- e.g., EUW1_1234567890
    platform_id          VARCHAR(12) NOT NULL,
    queue_id             INTEGER NOT NULL,
    game_mode            VARCHAR(32),
    map_id               INTEGER,
    game_version         VARCHAR(50),
    started_at           TIMESTAMPTZ NOT NULL,
    duration_seconds     INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    raw_data             JSONB, -- optional; limit retention/storage as needed
    fetched_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 08. Static champion metadata from Data Dragon
CREATE TABLE champions (
    id                   INTEGER PRIMARY KEY, -- numeric champion ID used in Match-V5
    ddragon_key          VARCHAR(64) NOT NULL UNIQUE, -- e.g. 'MonkeyKing'
    name                 VARCHAR(100) NOT NULL,
    image_filename       VARCHAR(150),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 09. Selected feature D: per-team stats and objectives from Match-V5
-- This must be created before match_participants for their team FK.
CREATE TABLE match_teams (
    match_id             VARCHAR(80) NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    team_id              INTEGER NOT NULL,
    win                  BOOLEAN,
    champion_kills       INTEGER CHECK (champion_kills IS NULL OR champion_kills >= 0),
    baron_kills          INTEGER CHECK (baron_kills IS NULL OR baron_kills >= 0),
    dragon_kills         INTEGER CHECK (dragon_kills IS NULL OR dragon_kills >= 0),
    tower_kills          INTEGER CHECK (tower_kills IS NULL OR tower_kills >= 0),
    inhibitor_kills      INTEGER CHECK (inhibitor_kills IS NULL OR inhibitor_kills >= 0),
    objectives_json      JSONB NOT NULL DEFAULT '{}'::jsonb,
    bans_json            JSONB NOT NULL DEFAULT '[]'::jsonb,
    PRIMARY KEY (match_id, team_id)
);

-- 10. ALL participants, not just the profiles tracked in riot_accounts
CREATE TABLE match_participants (
    match_id             VARCHAR(80) NOT NULL,
    participant_id       SMALLINT NOT NULL CHECK (participant_id > 0),
    puuid                VARCHAR(128), -- may be absent in nonstandard games
    account_id           BIGINT REFERENCES riot_accounts(id) ON DELETE SET NULL,
    team_id              INTEGER NOT NULL,
    champion_id          INTEGER REFERENCES champions(id),
    team_position        VARCHAR(20),
    individual_position  VARCHAR(20),
    win                  BOOLEAN,
    kills                INTEGER CHECK (kills IS NULL OR kills >= 0),
    deaths               INTEGER CHECK (deaths IS NULL OR deaths >= 0),
    assists              INTEGER CHECK (assists IS NULL OR assists >= 0),
    total_minions_killed INTEGER,
    neutral_minions_killed INTEGER,
    cs                   INTEGER GENERATED ALWAYS AS
                         (COALESCE(total_minions_killed,0)+COALESCE(neutral_minions_killed,0)) STORED,
    gold_earned          INTEGER,
    damage_to_champions  INTEGER,
    damage_taken         INTEGER,
    vision_score         INTEGER,
    wards_placed         INTEGER,
    wards_killed         INTEGER,
    spell1_id            INTEGER,
    spell2_id            INTEGER,
    items_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
    perks_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    extra_stats          JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (match_id, participant_id),
    FOREIGN KEY (match_id, team_id)
        REFERENCES match_teams(match_id, team_id) ON DELETE CASCADE
);

-- 11. Poll scheduling, retry/backfill progress per account
CREATE TABLE account_sync_state (
    account_id           BIGINT PRIMARY KEY REFERENCES riot_accounts(id) ON DELETE CASCADE,
    last_account_sync_at TIMESTAMPTZ,
    last_rank_sync_at    TIMESTAMPTZ,
    last_mastery_sync_at TIMESTAMPTZ,
    last_match_sync_at   TIMESTAMPTZ,
    last_live_check_at   TIMESTAMPTZ,
    oldest_match_synced_at TIMESTAMPTZ,
    backfill_before_at   TIMESTAMPTZ,
    next_retry_at        TIMESTAMPTZ,
    sync_status          VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    last_error           TEXT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (sync_status IN ('PENDING','RUNNING','OK','FAILED','PAUSED'))
);

-- A. Pro teams and historical membership
-- 12.
CREATE TABLE teams (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                 VARCHAR(160) NOT NULL,
    slug                 VARCHAR(180) NOT NULL UNIQUE,
    short_name           VARCHAR(24),
    region_code          VARCHAR(32),
    logo_url             TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 13. Multiple rows allowed for distinct stints of same player with same team.
CREATE TABLE team_memberships (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    player_id            BIGINT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    team_id              BIGINT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    roster_role          VARCHAR(32) NOT NULL DEFAULT 'PLAYER',
    game_position        VARCHAR(16),
    joined_on            DATE,
    left_on              DATE,
    source_url           TEXT,
    CHECK (left_on IS NULL OR joined_on IS NULL OR left_on >= joined_on),
    CHECK (game_position IS NULL OR game_position IN
           ('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'))
);

-- B. Current champion mastery (per account, not per player)
-- 14.
CREATE TABLE champion_masteries (
    account_id           BIGINT NOT NULL REFERENCES riot_accounts(id) ON DELETE CASCADE,
    champion_id          INTEGER NOT NULL REFERENCES champions(id),
    mastery_level        INTEGER NOT NULL CHECK (mastery_level >= 0),
    mastery_points       BIGINT NOT NULL CHECK (mastery_points >= 0),
    points_since_last_level INTEGER,
    points_until_next_level INTEGER,
    marks_earned         INTEGER,
    last_play_at         TIMESTAMPTZ,
    observed_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    extra_data           JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (account_id, champion_id)
);

-- C. Historical Riot IDs are INTERNAL-ONLY: Riot policy bars exposing them publicly
-- 15.
CREATE TABLE riot_id_history (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id           BIGINT NOT NULL REFERENCES riot_accounts(id) ON DELETE CASCADE,
    game_name            VARCHAR(100) NOT NULL,
    tag_line             VARCHAR(32) NOT NULL,
    first_seen_at        TIMESTAMPTZ NOT NULL,
    last_seen_at         TIMESTAMPTZ NOT NULL,
    CHECK (last_seen_at >= first_seen_at),
    UNIQUE (account_id, first_seen_at)
);

-- G. Ephemeral, publicly allowed Spectator-V5 active-game cache
-- 16.
CREATE TABLE live_games (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_id          VARCHAR(12) NOT NULL,
    riot_game_id         BIGINT NOT NULL,
    queue_id             INTEGER,
    game_mode            VARCHAR(32),
    map_id               INTEGER,
    started_at           TIMESTAMPTZ,
    first_seen_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at           TIMESTAMPTZ NOT NULL,
    ended_at             TIMESTAMPTZ,
    bans_json            JSONB NOT NULL DEFAULT '[]'::jsonb,
    UNIQUE (platform_id, riot_game_id),
    CHECK (last_seen_at >= first_seen_at)
);

-- 17. A slot is locally assigned from a Spectator response; bot PUUID can be NULL
CREATE TABLE live_game_participants (
    live_game_id         BIGINT NOT NULL REFERENCES live_games(id) ON DELETE CASCADE,
    slot                 SMALLINT NOT NULL CHECK (slot > 0),
    puuid                VARCHAR(128),
    account_id           BIGINT REFERENCES riot_accounts(id) ON DELETE SET NULL,
    team_id              INTEGER NOT NULL,
    champion_id          INTEGER REFERENCES champions(id),
    spell1_id            INTEGER,
    spell2_id            INTEGER,
    profile_icon_id      INTEGER,
    is_bot               BOOLEAN NOT NULL DEFAULT FALSE,
    perks_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (live_game_id, slot)
);

-- J. Historical LEADERBOARDS, only among pro accounts tracked by LoLApp
-- 18.
CREATE TABLE leaderboard_snapshots (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    season_id            INTEGER NOT NULL REFERENCES ranked_seasons(id),
    platform_id          VARCHAR(12) NOT NULL,
    queue_type           VARCHAR(32) NOT NULL,
    scope                VARCHAR(32) NOT NULL DEFAULT 'TRACKED_PROS',
    captured_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (season_id, platform_id, queue_type, scope, captured_at),
    CHECK (scope = 'TRACKED_PROS'),
    CHECK (queue_type IN ('RANKED_SOLO_5x5','RANKED_FLEX_SR'))
);

-- 19.
CREATE TABLE leaderboard_entries (
    snapshot_id          BIGINT NOT NULL REFERENCES leaderboard_snapshots(id) ON DELETE CASCADE,
    rank_position        INTEGER NOT NULL CHECK (rank_position > 0),
    account_id           BIGINT NOT NULL REFERENCES riot_accounts(id),
    tier                 VARCHAR(16) NOT NULL,
    division             VARCHAR(3),
    lp                   INTEGER NOT NULL CHECK (lp >= 0),
    wins                 INTEGER,
    losses               INTEGER,
    PRIMARY KEY (snapshot_id, rank_position),
    UNIQUE (snapshot_id, account_id)
);

-- L. Pro-esports schedule, BO3/BO5 series, individual pro games and pro rosters.
-- IMPORTANT: not provided by ordinary Riot Tournament-V5 for all LEC/LCK matches.
-- Get data from a provider whose terms authorize this use.
-- 20.
CREATE TABLE esports_leagues (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                 VARCHAR(160) NOT NULL,
    slug                 VARCHAR(180) NOT NULL UNIQUE,
    region_code          VARCHAR(32),
    logo_url             TEXT
);

-- 21.
CREATE TABLE esports_tournaments (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    league_id            BIGINT NOT NULL REFERENCES esports_leagues(id),
    name                 VARCHAR(180) NOT NULL,
    slug                 VARCHAR(220) NOT NULL UNIQUE,
    season_year          SMALLINT NOT NULL,
    split_name           VARCHAR(80),
    starts_at            TIMESTAMPTZ,
    ends_at              TIMESTAMPTZ,
    CHECK (ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at)
);

-- 22. One best-of series. Score is in esports_series_teams.
CREATE TABLE esports_series (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tournament_id        BIGINT NOT NULL REFERENCES esports_tournaments(id),
    source_name          VARCHAR(80),
    external_series_id   VARCHAR(150),
    round_label          VARCHAR(100),
    best_of              SMALLINT CHECK (best_of IS NULL OR best_of IN (1,3,5,7)),
    status               VARCHAR(16) NOT NULL DEFAULT 'SCHEDULED',
    scheduled_at         TIMESTAMPTZ,
    started_at           TIMESTAMPTZ,
    finished_at          TIMESTAMPTZ,
    source_url           TEXT,
    UNIQUE (source_name, external_series_id),
    CHECK (status IN ('SCHEDULED','LIVE','FINISHED','CANCELLED'))
);

-- 23. Two competitors per series, with score / win status
CREATE TABLE esports_series_teams (
    series_id            BIGINT NOT NULL REFERENCES esports_series(id) ON DELETE CASCADE,
    slot                 SMALLINT NOT NULL CHECK (slot IN (1,2)),
    team_id              BIGINT NOT NULL REFERENCES teams(id),
    games_won            SMALLINT NOT NULL DEFAULT 0 CHECK (games_won >= 0),
    PRIMARY KEY (series_id, slot),
    UNIQUE (series_id, team_id)
);

-- 24. One individual map/game inside an esports best-of series
CREATE TABLE esports_games (
    id                   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id            BIGINT NOT NULL REFERENCES esports_series(id) ON DELETE CASCADE,
    game_number          SMALLINT NOT NULL CHECK (game_number > 0),
    blue_team_id         BIGINT REFERENCES teams(id),
    red_team_id          BIGINT REFERENCES teams(id),
    winner_team_id       BIGINT REFERENCES teams(id),
    riot_match_id        VARCHAR(80) UNIQUE REFERENCES matches(match_id),
    patch                VARCHAR(40),
    started_at           TIMESTAMPTZ,
    duration_seconds     INTEGER,
    draft_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_name          VARCHAR(80),
    external_game_id     VARCHAR(150),
    extra_data           JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (series_id, game_number),
    UNIQUE (source_name, external_game_id),
    FOREIGN KEY (series_id, blue_team_id) REFERENCES esports_series_teams(series_id, team_id),
    FOREIGN KEY (series_id, red_team_id) REFERENCES esports_series_teams(series_id, team_id),
    CHECK (blue_team_id IS NULL OR red_team_id IS NULL OR blue_team_id <> red_team_id),
    CHECK (winner_team_id IS NULL OR
           winner_team_id IN (blue_team_id, red_team_id)),
    CHECK (duration_seconds IS NULL OR duration_seconds >= 0)
);

-- 25. Tournament game statistics independent from SoloQ match_participants.
CREATE TABLE esports_game_participants (
    esports_game_id      BIGINT NOT NULL REFERENCES esports_games(id) ON DELETE CASCADE,
    slot                 SMALLINT NOT NULL CHECK (slot BETWEEN 1 AND 20),
    team_id              BIGINT NOT NULL REFERENCES teams(id),
    player_id            BIGINT REFERENCES players(id) ON DELETE SET NULL,
    player_name_snapshot VARCHAR(100), -- pro handle, not a historical Riot ID
    champion_id          INTEGER REFERENCES champions(id),
    game_position        VARCHAR(16),
    kills                INTEGER,
    deaths               INTEGER,
    assists              INTEGER,
    cs                   INTEGER,
    gold_earned          INTEGER,
    damage_to_champions  INTEGER,
    vision_score         INTEGER,
    extra_stats          JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (esports_game_id, slot),
    CHECK (game_position IS NULL OR game_position IN
           ('TOP','JUNGLE','MIDDLE','BOTTOM','UTILITY'))
);

-- -------------------------------------
-- Rank comparison + automatic PEAK update (on writing current rank).
-- Master/Grandmaster/Challenger compare tier first, LP second.
-- For Diamond and below: tier > division > LP.
-- -------------------------------------
CREATE FUNCTION lol_tier_priority(t TEXT) RETURNS INTEGER
LANGUAGE SQL IMMUTABLE AS $$
    SELECT CASE upper(coalesce(t,''))
        WHEN 'IRON' THEN 1 WHEN 'BRONZE' THEN 2 WHEN 'SILVER' THEN 3
        WHEN 'GOLD' THEN 4 WHEN 'PLATINUM' THEN 5 WHEN 'EMERALD' THEN 6
        WHEN 'DIAMOND' THEN 7 WHEN 'MASTER' THEN 8
        WHEN 'GRANDMASTER' THEN 9 WHEN 'CHALLENGER' THEN 10
        ELSE 0 END
$$;

CREATE FUNCTION lol_division_priority(d TEXT) RETURNS INTEGER
LANGUAGE SQL IMMUTABLE AS $$
    SELECT CASE upper(coalesce(d,''))
        WHEN 'IV' THEN 1 WHEN 'III' THEN 2 WHEN 'II' THEN 3
        WHEN 'I' THEN 4 ELSE 0 END
$$;

CREATE FUNCTION lol_rank_is_higher(
    next_tier TEXT, next_division TEXT, next_lp INTEGER,
    previous_tier TEXT, previous_division TEXT, previous_lp INTEGER
) RETURNS BOOLEAN LANGUAGE SQL IMMUTABLE AS $$
    SELECT (lol_tier_priority(next_tier), lol_division_priority(next_division),
            coalesce(next_lp,-1))
         > (lol_tier_priority(previous_tier), lol_division_priority(previous_division),
            coalesce(previous_lp,-1))
$$;

CREATE FUNCTION lol_update_peak_and_guard_finalized()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.finalized_at IS NOT NULL THEN
        RAISE EXCEPTION 'Finished ranked season row % cannot be changed', OLD.id;
    END IF;
    IF NEW.current_tier IS NOT NULL AND NEW.current_lp IS NOT NULL AND
       (NEW.peak_tier IS NULL OR lol_rank_is_higher(
            NEW.current_tier, NEW.current_division, NEW.current_lp,
            NEW.peak_tier, NEW.peak_division, NEW.peak_lp)) THEN
        NEW.peak_tier := NEW.current_tier;
        NEW.peak_division := NEW.current_division;
        NEW.peak_lp := NEW.current_lp;
        NEW.peak_observed_at := NEW.current_observed_at;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_account_rank_peak
BEFORE INSERT OR UPDATE ON account_season_ranks
FOR EACH ROW EXECUTE FUNCTION lol_update_peak_and_guard_finalized();

-- Dynamic current leaderboard among tracked pro accounts, never official global ladder.
CREATE VIEW v_current_pro_leaderboard AS
SELECT
    ROW_NUMBER() OVER (
        PARTITION BY r.season_id, a.platform_id, r.queue_type
        ORDER BY lol_tier_priority(r.current_tier) DESC,
                 lol_division_priority(r.current_division) DESC,
                 r.current_lp DESC, a.id ASC
    ) AS rank_position,
    r.season_id, s.label AS season_label,
    a.platform_id, r.queue_type,
    a.id AS account_id, a.player_id, p.nickname,
    a.game_name, a.tag_line,
    r.current_tier AS tier, r.current_division AS division,
    r.current_lp AS lp, r.current_wins AS wins, r.current_losses AS losses,
    r.current_observed_at
FROM account_season_ranks r
JOIN ranked_seasons s ON s.id = r.season_id
JOIN riot_accounts a ON a.id = r.account_id
JOIN players p ON p.id = a.player_id
WHERE s.status = 'ACTIVE'
  AND r.finalized_at IS NULL
  AND r.current_tier IS NOT NULL AND r.current_lp IS NOT NULL
  AND a.platform_id IS NOT NULL;

-- Indexes for key pages and workers
CREATE INDEX idx_socials_player ON player_socials(player_id);
CREATE INDEX idx_accounts_player ON riot_accounts(player_id);
CREATE INDEX idx_accounts_platform ON riot_accounts(platform_id);
CREATE INDEX idx_accounts_riot_id ON riot_accounts(lower(game_name), lower(tag_line));
CREATE INDEX idx_season_ranks_season_queue ON account_season_ranks(season_id, queue_type);
CREATE INDEX idx_season_ranks_account ON account_season_ranks(account_id);
CREATE INDEX idx_rank_snapshots_time ON rank_snapshots(account_season_rank_id, observed_at DESC);
CREATE INDEX idx_matches_time ON matches(started_at DESC);
CREATE INDEX idx_matches_queue_time ON matches(queue_id, started_at DESC);
CREATE INDEX idx_participants_puuid ON match_participants(puuid) WHERE puuid IS NOT NULL;
CREATE INDEX idx_participants_account ON match_participants(account_id, match_id);
CREATE INDEX idx_participants_champion_role ON match_participants(champion_id, team_position);
CREATE UNIQUE INDEX idx_participants_match_puuid ON match_participants(match_id, puuid)
    WHERE puuid IS NOT NULL;
CREATE INDEX idx_teams_membership_player ON team_memberships(player_id, joined_on DESC);
CREATE INDEX idx_teams_membership_team ON team_memberships(team_id, joined_on DESC);
CREATE INDEX idx_mastery_points ON champion_masteries(account_id, mastery_points DESC);
CREATE INDEX idx_riot_id_history_account ON riot_id_history(account_id, first_seen_at DESC);
CREATE INDEX idx_live_games_expiry ON live_games(expires_at) WHERE ended_at IS NULL;
CREATE INDEX idx_live_participants_puuid ON live_game_participants(puuid) WHERE puuid IS NOT NULL;
CREATE INDEX idx_live_participants_account ON live_game_participants(account_id);
CREATE INDEX idx_leaderboard_snapshots_latest ON leaderboard_snapshots(
    season_id, platform_id, queue_type, captured_at DESC);
CREATE INDEX idx_leaderboard_entries_account ON leaderboard_entries(account_id);
CREATE INDEX idx_esports_tournament_league ON esports_tournaments(league_id, season_year DESC);
CREATE INDEX idx_esports_series_tournament ON esports_series(tournament_id, scheduled_at DESC);
CREATE INDEX idx_esports_games_series ON esports_games(series_id, game_number);
CREATE INDEX idx_esports_game_participants_player ON esports_game_participants(player_id);
CREATE INDEX idx_esports_game_participants_champion ON esports_game_participants(champion_id);
CREATE INDEX idx_sync_retry ON account_sync_state(next_retry_at) WHERE sync_status = 'FAILED';

COMMENT ON TABLE riot_id_history IS 'Internal only: never publish prior Riot IDs (Riot policy).';
COMMENT ON TABLE leaderboard_snapshots IS 'Tracks ONLY the LoLApp pro-account subset; not an official or global Riot ladder.';
COMMENT ON TABLE esports_games IS 'Esports games require authorized third-party competition data; Riot Tournament-V5 does not enumerate all pro leagues.';
COMMENT ON COLUMN account_season_ranks.peak_lp IS 'Maximum OBSERVED LP within tracked season; no historical peak can be guaranteed.';
COMMENT ON COLUMN account_season_ranks.current_lp IS 'For finalized seasons this is the last observed (final) LP.';

COMMIT;
