CREATE TABLE IF NOT EXISTS ship_class (
  id INTEGER PRIMARY KEY,
  country TEXT NOT NULL,          -- CN RU US JP GB FR KR IN TR
  navy TEXT,
  name TEXT NOT NULL,             -- class name
  type TEXT,                      -- carrier/destroyer/frigate/submarine/amphibious/corvette/patrol/mcm
  page TEXT NOT NULL,             -- wikipedia page title
  revid INTEGER,                  -- page revision id at fetch time
  displacement_full_t REAL,       -- full load, tonnes (submarines: submerged)
  displacement_raw TEXT,
  displacement_basis TEXT,        -- full | submerged | standard | other
  service_start TEXT,             -- first in-service year(s)
  service_raw TEXT,
  active_count INTEGER,           -- from list page, may be null
  note TEXT
);
CREATE TABLE IF NOT EXISTS radar (
  class_id INTEGER REFERENCES ship_class(id),
  model TEXT NOT NULL,
  role TEXT,
  raw TEXT
);
CREATE TABLE IF NOT EXISTS vls (
  class_id INTEGER REFERENCES ship_class(id),
  model TEXT,
  cells INTEGER,
  raw TEXT
);
CREATE TABLE IF NOT EXISTS weapon (
  class_id INTEGER REFERENCES ship_class(id),
  name TEXT NOT NULL,
  qty INTEGER,
  category TEXT,                  -- gun/missile/torpedo/ciws/aircraft/other
  raw TEXT
);

CREATE TABLE IF NOT EXISTS ship (
  id INTEGER PRIMARY KEY,
  class_id INTEGER REFERENCES ship_class(id),
  country TEXT NOT NULL,
  name TEXT NOT NULL,
  pennant TEXT,                   -- hull / pennant number
  commissioned TEXT,              -- ISO date or partial (YYYY-MM / YYYY)
  commissioned_raw TEXT,
  status TEXT,                    -- active / inactive / unknown
  status_raw TEXT,                -- original wording from the source
  status_basis TEXT,              -- table | us-list | inferred (class count matches)
  source_page TEXT,               -- wikipedia page the row came from
  source_rev INTEGER
);
CREATE INDEX IF NOT EXISTS ship_class_idx ON ship(class_id);
