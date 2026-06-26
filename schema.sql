CREATE TABLE IF NOT EXISTS channels (
  id TEXT PRIMARY KEY,
  name TEXT,
  handle TEXT,
  last_updated_time DATETIME,
  score REAL,
  neutrality_label TEXT
);

CREATE TABLE IF NOT EXISTS video_ratings (
  yt_video_id TEXT PRIMARY KEY,
  channel_id TEXT,
  title TEXT,
  thumbnail_url TEXT,
  published_at DATETIME,
  quality INTEGER,
  credibility INTEGER,
  rationality INTEGER,
  neutrality INTEGER,
  neutrality_label TEXT,
  composite REAL,
  summary TEXT,
  rated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
