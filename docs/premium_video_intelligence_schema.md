# 🧠 PREMIUM VIDEO INTELLIGENCE - DATABASE SCHEMA

## Overview
3-prompt pipeline architecture for premium video analysis: Structural Mechanics → Psychological Leverage → Performance Modeling

---

## 📊 CORE TABLES

### 1. `videos`
```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500),
    url TEXT,
    duration_seconds INTEGER,
    file_path TEXT,
    platform VARCHAR(50), -- 'tiktok', 'instagram', 'youtube'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    analysis_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    
    -- Performance Index (Final Output)
    total_performance_index INTEGER CHECK (total_performance_index >= 0 AND total_performance_index <= 100),
    retention_strength INTEGER CHECK (retention_strength >= 0 AND retention_strength <= 100),
    competitive_density_rating INTEGER CHECK (competitive_density_rating >= 0 AND competitive_density_rating <= 10),
    
    -- Platform Readiness Scores
    tiktok_readiness INTEGER CHECK (tiktok_readiness >= 0 AND tiktok_readiness <= 10),
    instagram_readiness INTEGER CHECK (instagram_readiness >= 0 AND instagram_readiness <= 10),
    youtube_readiness INTEGER CHECK (youtube_readiness >= 0 AND youtube_readiness <= 10),
    
    conversion_leverage_score INTEGER CHECK (conversion_leverage_score >= 0 AND conversion_leverage_score <= 10),
    
    -- Optimization Targets
    highest_leverage_optimization VARCHAR(200),
    analysis_completed_at TIMESTAMP
);
```

### 2. `video_intervals` (20-second segments)
```sql
CREATE TABLE video_intervals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    start_time INTEGER, -- seconds from start
    end_time INTEGER, -- seconds from start
    interval_duration INTEGER DEFAULT 20,
    
    -- PROMPT 1: Structural Mechanics
    hook_strength INTEGER CHECK (hook_strength >= 0 AND hook_strength <= 10),
    stimulation_density_cuts INTEGER,
    stimulation_density_camera_variation VARCHAR(10), -- 'Low', 'Medium', 'High'
    stimulation_density_motion_intensity VARCHAR(10), -- 'Low', 'Medium', 'High'
    escalation_signal_intensity_increase BOOLEAN,
    escalation_signal_new_information BOOLEAN,
    cognitive_load_information_rate VARCHAR(10), -- 'Low', 'Medium', 'High'
    cognitive_load_over_explanation_risk BOOLEAN,
    drop_risk_probability INTEGER CHECK (drop_risk_probability >= 0 AND drop_risk_probability <= 100),
    
    -- PROMPT 2: Psychological Leverage
    primary_trigger_type VARCHAR(20), -- 'Curiosity', 'Fear', 'Aspiration', 'Identity', 'Authority', 'Transformation', 'Controversy', 'None'
    trigger_intensity INTEGER CHECK (trigger_intensity >= 0 AND trigger_intensity <= 10),
    emotional_arc_pattern VARCHAR(15), -- 'Escalating', 'Flat', 'Declining', 'Inconsistent'
    attention_sustainability_model VARCHAR(30), -- 'Early spike then drop', 'Gradual build', 'Strong throughout', 'Weak start'
    viewer_momentum_score INTEGER CHECK (viewer_momentum_score >= 0 AND viewer_momentum_score <= 100),
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, start_time)
);
```

### 3. `structural_weaknesses` (Top 3 priority weaknesses)
```sql
CREATE TABLE structural_weaknesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    weakness_rank INTEGER CHECK (weakness_rank >= 1 AND weakness_rank <= 3),
    weakness_description TEXT,
    impact_score INTEGER CHECK (impact_score >= 0 AND impact_score <= 10),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(video_id, weakness_rank)
);
```

---

## 🔧 ANALYSIS METADATA TABLES

### 4. `analysis_sessions`
```sql
CREATE TABLE analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    
    -- Prompt execution tracking
    prompt1_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    prompt2_status VARCHAR(20) DEFAULT 'pending',
    prompt3_status VARCHAR(20) DEFAULT 'pending',
    
    prompt1_completed_at TIMESTAMP,
    prompt2_completed_at TIMESTAMP,
    prompt3_completed_at TIMESTAMP,
    
    -- AI model metadata
    model_version VARCHAR(50),
    total_tokens_used INTEGER,
    analysis_cost DECIMAL(10, 4),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5. `prompt_responses` (Raw AI responses for debugging/improvement)
```sql
CREATE TABLE prompt_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    prompt_number INTEGER CHECK (prompt_number >= 1 AND prompt_number <= 3),
    interval_id UUID REFERENCES video_intervals(id) ON DELETE NULL, -- null for prompt 3 (video-level)
    
    -- Input/Output tracking
    prompt_text TEXT,
    raw_response TEXT,
    parsed_data JSONB,
    response_time_ms INTEGER,
    
    -- Quality metrics
    response_quality_score INTEGER CHECK (response_quality_score >= 0 AND response_quality_score <= 10),
    parsing_success BOOLEAN,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 📈 BENCHMARK & COMPARISON TABLES

### 6. `performance_benchmarks`
```sql
CREATE TABLE performance_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform VARCHAR(50),
    content_category VARCHAR(100),
    benchmark_date DATE DEFAULT CURRENT_DATE,
    
    -- Industry averages for comparison
    avg_retention_strength INTEGER,
    avg_competitive_density DECIMAL(3, 1),
    avg_total_performance_index INTEGER,
    
    -- Percentile rankings
    p25_retention INTEGER,
    p50_retention INTEGER,
    p75_retention INTEGER,
    p90_retention INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 7. `video_benchmark_comparisons`
```sql
CREATE TABLE video_benchmark_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    benchmark_id UUID REFERENCES performance_benchmarks(id) ON DELETE CASCADE,
    
    -- Percentile rankings
    retention_percentile INTEGER CHECK (retention_percentile >= 0 AND retention_percentile <= 100),
    performance_index_percentile INTEGER CHECK (performance_index_percentile >= 0 AND performance_index_percentile <= 100),
    competitive_density_percentile INTEGER CHECK (competitive_density_percentile >= 0 AND competitive_density_percentile <= 100),
    
    -- Competitive positioning
    market_position VARCHAR(20), -- 'Bottom Quartile', 'Lower Half', 'Upper Half', 'Top Quartile'
    competitive_advantage_score INTEGER CHECK (competitive_advantage_score >= 0 AND competitive_advantage_score <= 10),
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎯 INDEXES FOR PERFORMANCE

```sql
-- Video lookups
CREATE INDEX idx_videos_project_id ON videos(project_id);
CREATE INDEX idx_videos_analysis_status ON videos(analysis_status);
CREATE INDEX idx_videos_performance_index ON videos(total_performance_index);

-- Interval queries
CREATE INDEX idx_intervals_video_id ON video_intervals(video_id);
CREATE INDEX idx_intervals_drop_risk ON video_intervals(drop_risk_probability);
CREATE INDEX idx_intervals_momentum ON video_intervals(viewer_momentum_score);

-- Analysis tracking
CREATE INDEX idx_sessions_video_id ON analysis_sessions(video_id);
CREATE INDEX idx_sessions_status ON analysis_sessions(prompt3_status);

-- Benchmark comparisons
CREATE INDEX idx_comparisons_video_id ON video_benchmark_comparisons(video_id);
CREATE INDEX idx_comparisons_percentile ON video_benchmark_comparisons(performance_index_percentile);
```

---

## 📊 SAMPLE DATA FLOW

### Video Analysis Pipeline:
1. **Video Upload** → `videos` table (status: 'pending')
2. **Create Intervals** → `video_intervals` (20-second segments)
3. **Prompt 1** → Update `video_intervals` structural fields
4. **Prompt 2** → Update `video_intervals` psychological fields  
5. **Prompt 3** → Update `videos` performance scores + `structural_weaknesses`
6. **Benchmark Comparison** → `video_benchmark_comparisons`

### Query Examples:
```sql
-- Get high-performing videos
SELECT title, total_performance_index, retention_strength 
FROM videos 
WHERE total_performance_index >= 80 
ORDER BY total_performance_index DESC;

-- Find riskiest intervals in a video
SELECT start_time, end_time, drop_risk_probability, hook_strength
FROM video_intervals 
WHERE video_id = $1 
ORDER BY drop_risk_probability DESC 
LIMIT 3;

-- Get psychological trigger patterns
SELECT primary_trigger_type, AVG(trigger_intensity) as avg_intensity, COUNT(*)
FROM video_intervals 
GROUP BY primary_trigger_type 
ORDER BY avg_intensity DESC;
```

---

## 🚀 SCALABILITY CONSIDERATIONS

- **Partitioning**: Consider partitioning `video_intervals` by video_id for large datasets
- **Caching**: Cache benchmark data and frequently accessed video analyses
- **JSON Storage**: Use JSONB for flexible prompt response storage
- **Time-series**: Add time-based partitioning for benchmark data
- **Read Replicas**: Use read replicas for dashboard/analytics queries

This schema supports your 3-prompt premium architecture while being enterprise-ready and scalable.
