ALTER TABLE chord_sheets
  ADD COLUMN is_private BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN share_token VARCHAR(64) NOT NULL DEFAULT '';

CREATE INDEX idx_chord_sheets_share_token ON chord_sheets(share_token);
CREATE INDEX idx_chord_sheets_is_private ON chord_sheets(is_private);
