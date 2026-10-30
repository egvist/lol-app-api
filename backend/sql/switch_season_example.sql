-- EXAMPLE for the future, only after S16 has REALLY ended.
-- This does NOT call Riot API. The previous latest snapshot is retained
-- as the final observed rank; the exact season-end rank requires a timely poll.
-- Make a database backup before manually switching seasons.
BEGIN;

DO $$
BEGIN
    IF (SELECT COUNT(*) FROM ranked_seasons
        WHERE season_year = 2026 AND status = 'ACTIVE') <> 1 THEN
        RAISE EXCEPTION 'Expected S16 to be the active ranked season';
    END IF;
END $$;

-- Finalize all S16 rows that have at least one actual rank observation.
-- Rows that are still entirely NULL stay unfinalized because the existing
-- schema requires current_observed_at to be non-NULL if finalized_at is set.
UPDATE account_season_ranks
SET finalized_at = NOW()
WHERE season_id = (SELECT id FROM ranked_seasons WHERE season_year = 2026)
  AND finalized_at IS NULL
  AND current_observed_at IS NOT NULL;

UPDATE ranked_seasons
SET status = 'FINISHED'
WHERE season_year = 2026 AND status = 'ACTIVE';

-- S17 may have been pre-created as UPCOMING, or may not yet exist.
-- starts_at / ends_at are NOT NULL: adjust the dates to the real season.
INSERT INTO ranked_seasons (season_year, label, starts_at, ends_at, status)
VALUES (2027, 'S17', '2027-01-01', '2028-01-01', 'ACTIVE')
ON CONFLICT (season_year) DO UPDATE
SET status = 'ACTIVE';

COMMIT;

SELECT id, season_year, label, status FROM ranked_seasons ORDER BY season_year;
