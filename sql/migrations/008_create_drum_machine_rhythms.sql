CREATE TABLE IF NOT EXISTS drum_machine_rhythms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    drum_machine VARCHAR(2048) NOT NULL,
    created_by_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_drum_machine_rhythms_creator (created_by_id),
    CONSTRAINT fk_drum_machine_rhythms_user FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE CASCADE
);
