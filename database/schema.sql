-- Life Optimization AI Database Schema
-- PostgreSQL 12+

-- Extension for vector support (for RAG/embeddings later)
-- TODO: Install pgvector extension when implementing RAG
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Health Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS health_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'garmin', 'strava', etc.

    -- Sleep metrics
    sleep_duration_hours DECIMAL(4,2),
    sleep_quality_score INTEGER CHECK (sleep_quality_score >= 0 AND sleep_quality_score <= 100),
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    awake_time_minutes INTEGER,

    -- Heart metrics
    resting_heart_rate INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    hrv_score DECIMAL(5,2),

    -- Stress & Recovery
    stress_level INTEGER CHECK (stress_level >= 0 AND stress_level <= 100),
    body_battery INTEGER CHECK (body_battery >= 0 AND body_battery <= 100),
    recovery_score DECIMAL(5,2),

    -- Activity
    steps INTEGER,
    active_calories INTEGER,
    intensity_minutes INTEGER,

    -- Other vitals
    spo2_avg DECIMAL(4,1),
    respiration_rate DECIMAL(4,1),

    -- Metadata
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_health_metric UNIQUE (timestamp, source)
);

CREATE INDEX idx_health_timestamp ON health_metrics(timestamp DESC);
CREATE INDEX idx_health_source ON health_metrics(source);
CREATE INDEX idx_health_created ON health_metrics(created_at DESC);

-- ============================================
-- Activity Data Table
-- ============================================
CREATE TABLE IF NOT EXISTS activity_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    source VARCHAR(50) NOT NULL,

    activity_type VARCHAR(50),  -- 'run', 'cycle', 'swim', 'workout', etc.
    duration_minutes INTEGER,
    distance_km DECIMAL(6,2),
    elevation_gain_m INTEGER,

    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    avg_power INTEGER,

    training_load INTEGER,
    perceived_exertion INTEGER CHECK (perceived_exertion >= 1 AND perceived_exertion <= 10),

    calories_burned INTEGER,

    -- Metadata
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activity_timestamp ON activity_data(timestamp DESC);
CREATE INDEX idx_activity_type ON activity_data(activity_type);
CREATE INDEX idx_activity_source ON activity_data(source);

-- ============================================
-- Calendar Events Table
-- ============================================
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,

    -- Event details
    summary VARCHAR(500),
    description TEXT,
    location VARCHAR(500),

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time)) / 60
    ) STORED,

    -- Recurrence
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule TEXT,
    is_exception_to_series BOOLEAN DEFAULT FALSE,

    -- Metadata
    priority VARCHAR(20) DEFAULT 'normal',  -- 'critical', 'high', 'normal', 'low'
    flexibility_score INTEGER DEFAULT 50 CHECK (flexibility_score >= 0 AND flexibility_score <= 100),

    -- Participants
    has_external_participants BOOLEAN DEFAULT FALSE,
    participant_count INTEGER DEFAULT 0,
    organizer_email VARCHAR(255),
    attendees JSONB,

    -- Tags and constraints
    tags JSONB,
    constraints JSONB,

    -- Agent learning
    user_modifications JSONB,
    user_feedback VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    last_modified TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP
);

CREATE INDEX idx_calendar_start ON calendar_events(start_time DESC);
CREATE INDEX idx_calendar_end ON calendar_events(end_time);
CREATE INDEX idx_calendar_event_id ON calendar_events(event_id);
CREATE INDEX idx_calendar_tags ON calendar_events USING GIN (tags);

-- ============================================
-- Productivity Metrics Table
-- ============================================
CREATE TABLE IF NOT EXISTS productivity_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Meeting metrics (from calendar)
    total_meetings INTEGER DEFAULT 0,
    meeting_duration_minutes INTEGER DEFAULT 0,
    back_to_back_meetings INTEGER DEFAULT 0,

    -- Focus time
    focus_blocks_count INTEGER DEFAULT 0,
    total_focus_minutes INTEGER DEFAULT 0,
    longest_focus_block_minutes INTEGER DEFAULT 0,

    -- Calculated scores
    meeting_density_score DECIMAL(5,2),  -- 0-100
    focus_time_score DECIMAL(5,2),  -- 0-100
    productivity_score DECIMAL(5,2),  -- 0-100

    -- Metadata
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_productivity_date ON productivity_metrics(date DESC);

-- ============================================
-- Learned Patterns Table
-- ============================================
CREATE TABLE IF NOT EXISTS learned_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,
    pattern_description TEXT NOT NULL,
    confidence_score DECIMAL(5,2) CHECK (confidence_score >= 0 AND confidence_score <= 100),

    -- Pattern data
    triggers JSONB,
    outcomes JSONB,

    -- Statistics
    occurrences_count INTEGER DEFAULT 1,
    last_seen TIMESTAMP,

    -- For RAG (will use ChromaDB but keep reference here)
    embedding_id VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_patterns_type ON learned_patterns(pattern_type);
CREATE INDEX idx_patterns_confidence ON learned_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_last_seen ON learned_patterns(last_seen DESC);

-- ============================================
-- Agent Actions Table (Audit Log)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_actions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    agent_name VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'reschedule', 'block_time', 'suggest', etc.
    confidence_score DECIMAL(5,2),

    -- What changed
    before_state JSONB,
    after_state JSONB,

    -- Why
    reasoning TEXT,
    data_sources JSONB,

    -- Outcome
    executed BOOLEAN DEFAULT FALSE,
    user_feedback VARCHAR(20),  -- 'approved', 'rejected', 'modified', 'undone'

    -- Metadata
    edge_case_flags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_actions_timestamp ON agent_actions(timestamp DESC);
CREATE INDEX idx_actions_agent ON agent_actions(agent_name);
CREATE INDEX idx_actions_type ON agent_actions(action_type);
CREATE INDEX idx_actions_feedback ON agent_actions(user_feedback);

-- ============================================
-- User Preferences Table
-- ============================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,

    description TEXT,
    category VARCHAR(50),  -- 'scheduling', 'health', 'notifications', etc.

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_preferences_key ON user_preferences(key);
CREATE INDEX idx_preferences_category ON user_preferences(category);

-- ============================================
-- Insert Default Preferences
-- ============================================
INSERT INTO user_preferences (key, value, description, category) VALUES
('working_hours_start', '"09:00"', 'Start of working day', 'scheduling'),
('working_hours_end', '"17:00"', 'End of working day', 'scheduling'),
('max_meetings_per_day', '5', 'Maximum number of meetings per day', 'scheduling'),
('min_focus_block_minutes', '120', 'Minimum duration for focus blocks', 'scheduling'),
('protected_keywords', '["interview", "demo", "presentation", "CEO"]', 'Events with these keywords cannot be rescheduled', 'scheduling'),
('max_agent_changes_per_day', '3', 'Maximum calendar changes agent can make per day', 'safety'),
('min_notice_hours', '24', 'Minimum notice before rescheduling (hours)', 'safety'),
('target_sleep_hours', '7.5', 'Target sleep duration', 'health'),
('recovery_threshold', '60', 'Minimum recovery score (below triggers optimization)', 'health')
ON CONFLICT (key) DO NOTHING;

-- ============================================
-- Mood Tracking Table
-- ============================================
CREATE TABLE IF NOT EXISTS mood_tracking (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    mood_score INTEGER CHECK (mood_score >= 1 AND mood_score <= 10),
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    stress_perception INTEGER CHECK (stress_perception >= 1 AND stress_perception <= 10),

    notes TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mood_date ON mood_tracking(date DESC);

-- ============================================
-- System Metadata Table
-- ============================================
CREATE TABLE IF NOT EXISTS system_metadata (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO system_metadata (key, value) VALUES
('schema_version', '1.0'),
('last_migration', NOW()::TEXT),
('database_initialized', NOW()::TEXT)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

-- ============================================
-- Helper Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_productivity_metrics_updated_at
    BEFORE UPDATE ON productivity_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learned_patterns_updated_at
    BEFORE UPDATE ON learned_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Views for Common Queries
-- ============================================

-- Recent health summary
CREATE OR REPLACE VIEW recent_health_summary AS
SELECT
    DATE(timestamp) as date,
    AVG(sleep_duration_hours) as avg_sleep,
    AVG(sleep_quality_score) as avg_sleep_quality,
    AVG(resting_heart_rate) as avg_rhr,
    AVG(stress_level) as avg_stress,
    AVG(recovery_score) as avg_recovery,
    SUM(steps) as total_steps
FROM health_metrics
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Daily productivity summary
CREATE OR REPLACE VIEW daily_productivity AS
SELECT
    DATE(start_time) as date,
    COUNT(*) as total_events,
    SUM(duration_minutes) as total_meeting_minutes,
    AVG(duration_minutes) as avg_meeting_duration
FROM calendar_events
WHERE start_time >= NOW() - INTERVAL '30 days'
GROUP BY DATE(start_time)
ORDER BY date DESC;

-- Agent performance metrics
CREATE OR REPLACE VIEW agent_performance AS
SELECT
    agent_name,
    COUNT(*) as total_actions,
    SUM(CASE WHEN executed = TRUE THEN 1 ELSE 0 END) as executed_count,
    SUM(CASE WHEN user_feedback = 'approved' THEN 1 ELSE 0 END) as approved_count,
    SUM(CASE WHEN user_feedback = 'rejected' THEN 1 ELSE 0 END) as rejected_count,
    AVG(confidence_score) as avg_confidence,
    MAX(timestamp) as last_action
FROM agent_actions
GROUP BY agent_name
ORDER BY total_actions DESC;

-- ============================================
-- Completion
-- ============================================
SELECT 'Database schema created successfully!' as status;
