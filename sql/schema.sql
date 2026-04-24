CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NULL,
    google_sub VARCHAR(255) NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email)
);

CREATE TABLE IF NOT EXISTS chord_sheets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    key_signature VARCHAR(16) NULL,
    content TEXT NOT NULL,
    youtube_url VARCHAR(1024) NULL,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_chord_sheets_title (title),
    INDEX idx_chord_sheets_artist (artist),
    INDEX idx_chord_sheets_creator (created_by_id),
    CONSTRAINT fk_chord_sheets_user FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS setlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_setlists_name (name),
    INDEX idx_setlists_creator (created_by_id),
    CONSTRAINT fk_setlists_user FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS setlist_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setlist_id INT NOT NULL,
    chord_sheet_id INT NOT NULL,
    position INT NOT NULL,
    UNIQUE KEY uq_setlist_position (setlist_id, position),
    INDEX idx_setlist_items_setlist (setlist_id),
    INDEX idx_setlist_items_chord_sheet (chord_sheet_id),
    CONSTRAINT fk_setlist_items_setlist FOREIGN KEY (setlist_id) REFERENCES setlists(id) ON DELETE CASCADE,
    CONSTRAINT fk_setlist_items_chord_sheet FOREIGN KEY (chord_sheet_id) REFERENCES chord_sheets(id) ON DELETE CASCADE
);
