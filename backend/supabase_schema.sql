-- Generated from SQLAlchemy models for PostgreSQL/Supabase
-- Source: backend/models.py


CREATE TABLE gemini_caches (
	id SERIAL NOT NULL, 
	video_hash VARCHAR(64) NOT NULL, 
	prompt_template_key VARCHAR(255) NOT NULL, 
	model VARCHAR(255) NOT NULL, 
	gemini_file_name VARCHAR(255), 
	gemini_file_uri VARCHAR(500), 
	cached_content_name VARCHAR(255) NOT NULL, 
	ttl_seconds INTEGER NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_gemini_cache_video_prompt_model UNIQUE (video_hash, prompt_template_key, model)
)

;


CREATE TABLE oauth_states (
	id SERIAL NOT NULL, 
	state VARCHAR(255) NOT NULL, 
	provider VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255), 
	name VARCHAR(255), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE oauth_connections (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	provider VARCHAR(50) NOT NULL, 
	provider_account_id VARCHAR(255), 
	display_name VARCHAR(255), 
	access_token TEXT NOT NULL, 
	refresh_token TEXT, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	scopes TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_provider UNIQUE (user_id, provider), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE videos (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	platform VARCHAR(50) NOT NULL, 
	channel_title VARCHAR(255), 
	channel_id VARCHAR(255), 
	channel_url VARCHAR(255), 
	thumbnail_url VARCHAR(500), 
	url VARCHAR(500), 
	duration_seconds INTEGER, 
	view_count INTEGER, 
	like_count INTEGER, 
	comment_count INTEGER, 
	categories TEXT, 
	tags TEXT, 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	cached_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE platform_videos (
	id SERIAL NOT NULL, 
	video_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	platform VARCHAR(50) NOT NULL, 
	platform_video_id VARCHAR(255) NOT NULL, 
	etag VARCHAR(255), 
	extra TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_platform_video UNIQUE (user_id, platform, platform_video_id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE projects (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	category VARCHAR(100), 
	description TEXT, 
	video_url VARCHAR(500), 
	video_id INTEGER, 
	priority VARCHAR(50), 
	progress INTEGER NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	job_id VARCHAR(255), 
	analysis_file_path VARCHAR(1000), 
	gemini_file_uri VARCHAR(500), 
	gemini_cached_content_name VARCHAR(255), 
	video_duration_seconds INTEGER, 
	start_date DATE, 
	end_date DATE, 
	vector_generation_status VARCHAR(20) NOT NULL, 
	vector_generation_started_at TIMESTAMP WITHOUT TIME ZONE, 
	vector_generation_completed_at TIMESTAMP WITHOUT TIME ZONE, 
	vector_generation_error TEXT, 
	premium_analysis_status VARCHAR(20) NOT NULL, 
	premium_analysis_started_at TIMESTAMP WITHOUT TIME ZONE, 
	premium_analysis_completed_at TIMESTAMP WITHOUT TIME ZONE, 
	premium_analysis_error TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id)
)

;


CREATE TABLE video_intervals (
	id SERIAL NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_video_interval_index UNIQUE (video_id, interval_index), 
	FOREIGN KEY(video_id) REFERENCES videos (id)
)

;


CREATE TABLE analysis_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	parent_interval_id INTEGER, 
	granularity VARCHAR(32) NOT NULL, 
	interval_index INTEGER NOT NULL, 
	sub_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_analysis_interval_slot UNIQUE (project_id, granularity, interval_index, sub_index), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(parent_interval_id) REFERENCES analysis_intervals (id)
)

;


CREATE TABLE analysis_runs (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	run_type VARCHAR(32) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	error TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE chats (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	platform VARCHAR(50), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE interval_embeddings (
	id SERIAL NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	combined_interval_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_interval_analyses (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	pass_1_json TEXT, 
	pass_2_json TEXT, 
	pass_3_json TEXT, 
	pass_4_json TEXT, 
	pass_5_json TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_interval_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_performance_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	retention_strength_score INTEGER, 
	retention_strength_justification TEXT, 
	competitive_density_score INTEGER, 
	competitive_density_justification TEXT, 
	platform_tiktok_score INTEGER, 
	platform_tiktok_justification TEXT, 
	platform_instagram_reels_score INTEGER, 
	platform_instagram_reels_justification TEXT, 
	platform_youtube_shorts_score INTEGER, 
	platform_youtube_shorts_justification TEXT, 
	conversion_leverage_score INTEGER, 
	conversion_leverage_justification TEXT, 
	total_performance_index_score INTEGER, 
	total_performance_index_justification TEXT, 
	structural_weakness_priority_json TEXT, 
	highest_leverage_target TEXT, 
	highest_leverage_justification TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_perf_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_psychological_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	primary_trigger_type VARCHAR(50), 
	primary_trigger_justification TEXT, 
	trigger_intensity_score INTEGER, 
	trigger_intensity_justification TEXT, 
	emotional_arc_pattern_type VARCHAR(50), 
	emotional_arc_justification TEXT, 
	attention_sustainability_type VARCHAR(50), 
	attention_sustainability_justification TEXT, 
	viewer_momentum_score INTEGER, 
	viewer_momentum_justification TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_psych_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_structural_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	hook_strength_score INTEGER, 
	hook_strength_justification TEXT, 
	stimulation_cuts_per_20s INTEGER, 
	stimulation_camera_variation VARCHAR(20), 
	stimulation_motion_intensity VARCHAR(20), 
	stimulation_justification TEXT, 
	escalation_intensity_increase INTEGER, 
	escalation_stakes_raised INTEGER, 
	escalation_justification TEXT, 
	cognitive_information_rate VARCHAR(20), 
	cognitive_over_explanation_risk INTEGER, 
	cognitive_justification TEXT, 
	drop_risk_score_percent INTEGER, 
	drop_risk_justification TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_structural_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_transcript_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	transcript_text TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_transcript_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE premium_verification_intervals (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	interval_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	question_type VARCHAR(100), 
	timestamp_reference VARCHAR(50), 
	visual_evidence_summary TEXT, 
	verification_status VARCHAR(50), 
	answer TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_premium_verification_project_interval UNIQUE (project_id, interval_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id)
)

;


CREATE TABLE project_content_features (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	error TEXT, 
	clips_status VARCHAR(20) NOT NULL, 
	clips_progress INTEGER NOT NULL, 
	clips_json TEXT NOT NULL, 
	clips_error TEXT, 
	subtitles_status VARCHAR(20) NOT NULL, 
	subtitles_progress INTEGER NOT NULL, 
	subtitles_json TEXT NOT NULL, 
	subtitles_error TEXT, 
	chapters_status VARCHAR(20) NOT NULL, 
	chapters_progress INTEGER NOT NULL, 
	chapters_json TEXT NOT NULL, 
	chapters_error TEXT, 
	moments_status VARCHAR(20) NOT NULL, 
	moments_progress INTEGER NOT NULL, 
	moments_json TEXT NOT NULL, 
	moments_error TEXT, 
	version INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_content_features_project UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE project_overviews (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	blog_markdown TEXT NOT NULL, 
	summary TEXT NOT NULL, 
	insights_json TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	version INTEGER NOT NULL, 
	error TEXT, 
	generated_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_overview_project UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE project_premium_analyses (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	pass_1_output TEXT, 
	pass_2_output TEXT, 
	pass_3_output TEXT, 
	pass_4_output TEXT, 
	pass_5_output TEXT, 
	status VARCHAR(20) NOT NULL, 
	version INTEGER NOT NULL, 
	error TEXT, 
	generated_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_premium_analysis_project UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE project_statistics (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	stats_json TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	version INTEGER NOT NULL, 
	error TEXT, 
	generated_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_statistics_project UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)

;


CREATE TABLE video_sub_intervals (
	id SERIAL NOT NULL, 
	interval_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	sub_index INTEGER NOT NULL, 
	start_time_seconds INTEGER NOT NULL, 
	end_time_seconds INTEGER NOT NULL, 
	camera_frame TEXT, 
	environment_background TEXT, 
	people_figures TEXT, 
	objects_props TEXT, 
	text_symbols TEXT, 
	motion_changes TEXT, 
	lighting_color TEXT, 
	audio_visible_indicators TEXT, 
	occlusions_limits TEXT, 
	raw_combined_text TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_video_sub_interval_time UNIQUE (video_id, start_time_seconds), 
	FOREIGN KEY(interval_id) REFERENCES video_intervals (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id)
)

;


CREATE TABLE analysis_records (
	id SERIAL NOT NULL, 
	project_id INTEGER NOT NULL, 
	video_id INTEGER NOT NULL, 
	interval_id INTEGER NOT NULL, 
	analysis_type VARCHAR(64) NOT NULL, 
	source_pass INTEGER, 
	status VARCHAR(20) NOT NULL, 
	summary_text TEXT, 
	payload_json TEXT, 
	confidence FLOAT, 
	schema_version INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_analysis_record_scope UNIQUE (project_id, interval_id, analysis_type), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(video_id) REFERENCES videos (id), 
	FOREIGN KEY(interval_id) REFERENCES analysis_intervals (id)
)

;


CREATE TABLE chat_messages (
	id SERIAL NOT NULL, 
	chat_id INTEGER NOT NULL, 
	role VARCHAR(50) NOT NULL, 
	content TEXT NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chat_id) REFERENCES chats (id)
)

;


CREATE TABLE premium_performance_interval_embeddings (
	performance_interval_id INTEGER NOT NULL, 
	combined_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (performance_interval_id), 
	FOREIGN KEY(performance_interval_id) REFERENCES premium_performance_intervals (id)
)

;


CREATE TABLE premium_psychological_interval_embeddings (
	psychological_interval_id INTEGER NOT NULL, 
	combined_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (psychological_interval_id), 
	FOREIGN KEY(psychological_interval_id) REFERENCES premium_psychological_intervals (id)
)

;


CREATE TABLE premium_structural_interval_embeddings (
	structural_interval_id INTEGER NOT NULL, 
	combined_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (structural_interval_id), 
	FOREIGN KEY(structural_interval_id) REFERENCES premium_structural_intervals (id)
)

;


CREATE TABLE premium_transcript_interval_embeddings (
	transcript_interval_id INTEGER NOT NULL, 
	combined_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (transcript_interval_id), 
	FOREIGN KEY(transcript_interval_id) REFERENCES premium_transcript_intervals (id)
)

;


CREATE TABLE premium_verification_interval_embeddings (
	verification_interval_id INTEGER NOT NULL, 
	combined_text TEXT, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (verification_interval_id), 
	FOREIGN KEY(verification_interval_id) REFERENCES premium_verification_intervals (id)
)

;


CREATE TABLE sub_video_interval_embeddings (
	sub_interval_id INTEGER NOT NULL, 
	embedding TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (sub_interval_id), 
	FOREIGN KEY(sub_interval_id) REFERENCES video_sub_intervals (id)
)

;


CREATE TABLE analysis_embeddings (
	analysis_record_id INTEGER NOT NULL, 
	embedding TEXT, 
	embedding_model VARCHAR(64) NOT NULL, 
	embedding_dim INTEGER NOT NULL, 
	embedded_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (analysis_record_id), 
	FOREIGN KEY(analysis_record_id) REFERENCES analysis_records (id)
)

;

CREATE INDEX ix_gemini_caches_prompt_template_key ON gemini_caches (prompt_template_key);
CREATE INDEX ix_gemini_caches_expires_at ON gemini_caches (expires_at);
CREATE INDEX ix_gemini_caches_model ON gemini_caches (model);
CREATE INDEX ix_gemini_caches_id ON gemini_caches (id);
CREATE INDEX ix_gemini_caches_video_hash ON gemini_caches (video_hash);
CREATE INDEX ix_oauth_states_provider ON oauth_states (provider);
CREATE INDEX ix_oauth_states_id ON oauth_states (id);
CREATE UNIQUE INDEX ix_oauth_states_state ON oauth_states (state);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_oauth_connections_id ON oauth_connections (id);
CREATE INDEX ix_oauth_connections_user_id ON oauth_connections (user_id);
CREATE INDEX ix_oauth_connections_provider ON oauth_connections (provider);
CREATE INDEX ix_videos_platform ON videos (platform);
CREATE INDEX ix_videos_id ON videos (id);
CREATE INDEX ix_videos_user_id ON videos (user_id);
CREATE INDEX ix_videos_published_at ON videos (published_at);
CREATE INDEX ix_platform_videos_platform ON platform_videos (platform);
CREATE INDEX ix_platform_videos_user_id ON platform_videos (user_id);
CREATE INDEX ix_platform_videos_id ON platform_videos (id);
CREATE INDEX ix_platform_videos_video_id ON platform_videos (video_id);
CREATE INDEX ix_projects_id ON projects (id);
CREATE INDEX ix_projects_user_id ON projects (user_id);
CREATE INDEX ix_projects_job_id ON projects (job_id);
CREATE INDEX ix_projects_video_id ON projects (video_id);
CREATE INDEX ix_video_intervals_id ON video_intervals (id);
CREATE INDEX ix_video_intervals_video_id ON video_intervals (video_id);
CREATE INDEX ix_analysis_intervals_project_id ON analysis_intervals (project_id);
CREATE INDEX ix_analysis_intervals_end_time_seconds ON analysis_intervals (end_time_seconds);
CREATE INDEX ix_analysis_intervals_granularity ON analysis_intervals (granularity);
CREATE INDEX ix_analysis_intervals_parent_interval_id ON analysis_intervals (parent_interval_id);
CREATE INDEX ix_analysis_intervals_start_time_seconds ON analysis_intervals (start_time_seconds);
CREATE INDEX ix_analysis_intervals_id ON analysis_intervals (id);
CREATE INDEX ix_analysis_intervals_video_id ON analysis_intervals (video_id);
CREATE INDEX ix_analysis_runs_project_id ON analysis_runs (project_id);
CREATE INDEX ix_analysis_runs_status ON analysis_runs (status);
CREATE INDEX ix_analysis_runs_run_type ON analysis_runs (run_type);
CREATE INDEX ix_analysis_runs_id ON analysis_runs (id);
CREATE INDEX ix_chats_project_id ON chats (project_id);
CREATE INDEX ix_chats_id ON chats (id);
CREATE INDEX ix_interval_embeddings_video_id ON interval_embeddings (video_id);
CREATE INDEX ix_interval_embeddings_interval_id ON interval_embeddings (interval_id);
CREATE INDEX ix_interval_embeddings_id ON interval_embeddings (id);
CREATE INDEX ix_premium_interval_analyses_interval_id ON premium_interval_analyses (interval_id);
CREATE INDEX ix_premium_interval_analyses_video_id ON premium_interval_analyses (video_id);
CREATE INDEX ix_premium_interval_analyses_id ON premium_interval_analyses (id);
CREATE INDEX ix_premium_interval_analyses_project_id ON premium_interval_analyses (project_id);
CREATE INDEX ix_premium_performance_intervals_id ON premium_performance_intervals (id);
CREATE INDEX ix_premium_performance_intervals_interval_id ON premium_performance_intervals (interval_id);
CREATE INDEX ix_premium_performance_intervals_project_id ON premium_performance_intervals (project_id);
CREATE INDEX ix_premium_performance_intervals_video_id ON premium_performance_intervals (video_id);
CREATE INDEX ix_premium_psychological_intervals_id ON premium_psychological_intervals (id);
CREATE INDEX ix_premium_psychological_intervals_project_id ON premium_psychological_intervals (project_id);
CREATE INDEX ix_premium_psychological_intervals_video_id ON premium_psychological_intervals (video_id);
CREATE INDEX ix_premium_psychological_intervals_interval_id ON premium_psychological_intervals (interval_id);
CREATE INDEX ix_premium_structural_intervals_interval_id ON premium_structural_intervals (interval_id);
CREATE INDEX ix_premium_structural_intervals_id ON premium_structural_intervals (id);
CREATE INDEX ix_premium_structural_intervals_project_id ON premium_structural_intervals (project_id);
CREATE INDEX ix_premium_structural_intervals_video_id ON premium_structural_intervals (video_id);
CREATE INDEX ix_premium_transcript_intervals_project_id ON premium_transcript_intervals (project_id);
CREATE INDEX ix_premium_transcript_intervals_video_id ON premium_transcript_intervals (video_id);
CREATE INDEX ix_premium_transcript_intervals_interval_id ON premium_transcript_intervals (interval_id);
CREATE INDEX ix_premium_transcript_intervals_id ON premium_transcript_intervals (id);
CREATE INDEX ix_premium_verification_intervals_video_id ON premium_verification_intervals (video_id);
CREATE INDEX ix_premium_verification_intervals_id ON premium_verification_intervals (id);
CREATE INDEX ix_premium_verification_intervals_interval_id ON premium_verification_intervals (interval_id);
CREATE INDEX ix_premium_verification_intervals_project_id ON premium_verification_intervals (project_id);
CREATE INDEX ix_project_content_features_id ON project_content_features (id);
CREATE UNIQUE INDEX ix_project_content_features_project_id ON project_content_features (project_id);
CREATE INDEX ix_project_overviews_id ON project_overviews (id);
CREATE UNIQUE INDEX ix_project_overviews_project_id ON project_overviews (project_id);
CREATE INDEX ix_project_premium_analyses_id ON project_premium_analyses (id);
CREATE UNIQUE INDEX ix_project_premium_analyses_project_id ON project_premium_analyses (project_id);
CREATE INDEX ix_project_statistics_id ON project_statistics (id);
CREATE UNIQUE INDEX ix_project_statistics_project_id ON project_statistics (project_id);
CREATE INDEX ix_video_sub_intervals_video_id ON video_sub_intervals (video_id);
CREATE INDEX ix_video_sub_intervals_id ON video_sub_intervals (id);
CREATE INDEX ix_video_sub_intervals_interval_id ON video_sub_intervals (interval_id);
CREATE INDEX ix_analysis_records_interval_id ON analysis_records (interval_id);
CREATE INDEX ix_analysis_records_analysis_type ON analysis_records (analysis_type);
CREATE INDEX ix_analysis_records_status ON analysis_records (status);
CREATE INDEX ix_analysis_records_id ON analysis_records (id);
CREATE INDEX ix_analysis_records_video_id ON analysis_records (video_id);
CREATE INDEX ix_analysis_records_project_id ON analysis_records (project_id);
CREATE INDEX ix_chat_messages_id ON chat_messages (id);
CREATE INDEX ix_chat_messages_chat_id ON chat_messages (chat_id);
