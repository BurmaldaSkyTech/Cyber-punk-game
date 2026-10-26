CREATE TABLE IF NOT EXISTS game_data (
  family   TEXT NOT NULL,
  key      TEXT NOT NULL,
  data     JSONB NOT NULL,
  source_page INT,
  validated BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (family, key)
);
CREATE INDEX IF NOT EXISTS game_data_gin ON game_data USING GIN (data);

CREATE TABLE IF NOT EXISTS lore_chunks (
  id TEXT PRIMARY KEY,
  crumb TEXT, page_start INT, page_end INT, kind TEXT, text TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  scenario JSONB, heat INT, flags JSONB, clocks JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS turns (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT REFERENCES sessions(id),
  turn_no INT, player TEXT, action_text TEXT,
  judge JSONB, mechanics JSONB,
  narration TEXT, edited_narration TEXT, rating SMALLINT,
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS turns_sess_idx ON turns (session_id, turn_no);