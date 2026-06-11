ALTER TABLE setlists
  ADD COLUMN is_private BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN share_token VARCHAR(64) NOT NULL DEFAULT '';

CREATE INDEX idx_setlists_share_token ON setlists(share_token);
CREATE INDEX idx_setlists_is_private ON setlists(is_private);
