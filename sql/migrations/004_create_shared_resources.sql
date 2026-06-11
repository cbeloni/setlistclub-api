CREATE TABLE IF NOT EXISTS shared_resources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    resource_type VARCHAR(20) NOT NULL,
    resource_id INT NOT NULL,
    shared_with_user_id INT NOT NULL,
    shared_by_user_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_shared_resource (resource_type, resource_id, shared_with_user_id),
    INDEX idx_shared_user (shared_with_user_id),
    INDEX idx_shared_resource (resource_type, resource_id),
    CONSTRAINT fk_shared_with_user FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_shared_by_user FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);