# 🛠️ DATABASE IMPLEMENTATION PROMPT

## Use this prompt to implement the premium video intelligence database schema

---

```
ROLE

You are a senior database architect implementing a premium video intelligence pipeline.

You need to create a complete PostgreSQL database schema for a 3-prompt video analysis system:

STRUCTURAL MECHANICS → PSYCHOLOGICAL LEVERAGE → PERFORMANCE MODELING

REQUIREMENTS:

1. Create all tables with exact specifications provided
2. Include proper constraints, indexes, and relationships
3. Add necessary PostgreSQL extensions
4. Include migration scripts for version control
5. Add sample data for testing
6. Create optimized views for dashboard queries

IMPLEMENTATION TASKS:

1. DATABASE SETUP
   - Create PostgreSQL database with UUID extension
   - Set up proper user permissions
   - Configure connection pooling settings

2. TABLE CREATION
   Execute the exact schema from the specification document:
   - videos (main video metadata + performance scores)
   - video_intervals (20-second segments with structural/psychological data)
   - structural_weaknesses (top 3 priority weaknesses per video)
   - analysis_sessions (prompt execution tracking)
   - prompt_responses (raw AI responses for debugging)
   - performance_benchmarks (industry benchmark data)
   - video_benchmark_comparisons (competitive positioning)

3. INDEXES & PERFORMANCE
   - Create all specified indexes for query optimization
   - Add composite indexes for common query patterns
   - Set up partial indexes where beneficial

4. MIGRATION SYSTEM
   - Create migration_001_initial_schema.sql
   - Create migration_002_add_benchmarks.sql
   - Create migration_003_add_indexes.sql
   - Include rollback scripts for each migration

5. VIEWS & FUNCTIONS
   - Create view: video_performance_summary (aggregated metrics)
   - Create view: interval_analysis_dashboard (interval-level insights)
   - Create function: calculate_video_percentile(benchmark_data)
   - Create function: get_optimization_recommendations(video_id)

6. SAMPLE DATA
   - Insert 3 sample videos with complete analysis data
   - Insert benchmark data for TikTok, Instagram, YouTube
   - Include edge cases (low performance, high performance)

7. SECURITY & BACKUP
   - Create read-only user for dashboard queries
   - Set up row-level security for multi-tenant scenarios
   - Create backup/restore procedures

DELIVERABLES:

1. Complete SQL schema file
2. Migration scripts (up/down)
3. Sample data insertion scripts
4. Performance optimization recommendations
5. Dashboard query examples

CONSTRAINTS:
- Use PostgreSQL 14+ features
- Follow naming conventions (snake_case)
- Include proper foreign key constraints
- Add check constraints for data validation
- Use UUID for primary keys
- Include created_at timestamps

Return the complete implementation ready for production deployment.
```

---

## 📁 EXPECTED OUTPUT STRUCTURE

```
database/
├── migrations/
│   ├── 001_initial_schema_up.sql
│   ├── 001_initial_schema_down.sql
│   ├── 002_add_benchmarks_up.sql
│   ├── 002_add_benchmarks_down.sql
│   └── 003_performance_indexes_up.sql
├── schema/
│   ├── tables.sql
│   ├── indexes.sql
│   ├── views.sql
│   └── functions.sql
├── data/
│   ├── sample_videos.sql
│   └── benchmark_data.sql
├── security/
│   ├── users.sql
│   └── permissions.sql
└── README.md (setup instructions)
```

---

## 🎯 SUCCESS CRITERIA

✅ All tables created with proper constraints
✅ Indexes optimized for dashboard queries  
✅ Migration system ready for version control
✅ Sample data demonstrates 3-prompt pipeline
✅ Views provide efficient dashboard access
✅ Security model supports multi-tenancy
✅ Performance queries under 100ms

This prompt will give you a production-ready database implementation for your premium video intelligence platform.
