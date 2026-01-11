CREATE TABLE IF NOT EXISTS default.logs
(
    timestamp DateTime64(3),
    level String DEFAULT 'info',
    event String,
    container_name String,
    data String DEFAULT '{}',
)
ENGINE = MergeTree()
ORDER BY (timestamp, container_name);