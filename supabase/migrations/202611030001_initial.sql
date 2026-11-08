-- ML Code Trainer / Supabase PostgreSQL. Apply once with Supabase migrations.
BEGIN;


CREATE TABLE profiles (
	id VARCHAR NOT NULL, 
	token_hash VARCHAR, 
	display_name VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (token_hash)
)

;


CREATE TABLE system_usage_daily (
	key VARCHAR NOT NULL, 
	count INTEGER NOT NULL, 
	PRIMARY KEY (key)
)

;


CREATE TABLE activity_progress (
	user_id VARCHAR NOT NULL, 
	activity_id VARCHAR NOT NULL, 
	question_id VARCHAR NOT NULL, 
	accepted BOOLEAN NOT NULL, 
	answer INTEGER NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id, activity_id, question_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;


CREATE TABLE review_schedules (
	user_id VARCHAR NOT NULL, 
	concept_id VARCHAR NOT NULL, 
	due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	interval_days INTEGER NOT NULL, 
	success_streak INTEGER NOT NULL, 
	last_reviewed_at TIMESTAMP WITH TIME ZONE, 
	last_problem_family_id VARCHAR NOT NULL, 
	algorithm_version VARCHAR NOT NULL, 
	PRIMARY KEY (user_id, concept_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;

CREATE INDEX ix_review_schedules_due_at ON review_schedules (due_at);


CREATE TABLE study_sessions (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	position INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;

CREATE INDEX ix_study_sessions_user_id ON study_sessions (user_id);


CREATE TABLE user_concept_progress (
	user_id VARCHAR NOT NULL, 
	concept_id VARCHAR NOT NULL, 
	mastery_level INTEGER NOT NULL, 
	mastery_score FLOAT NOT NULL, 
	current_stage VARCHAR NOT NULL, 
	stage_families JSON NOT NULL, 
	last_practiced_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_verified_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (user_id, concept_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;


CREATE TABLE user_problem_progress (
	user_id VARCHAR NOT NULL, 
	problem_version_id VARCHAR NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (user_id, problem_version_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;


CREATE TABLE user_settings (
	user_id VARCHAR NOT NULL, 
	data JSON NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id)
)

;


CREATE TABLE session_items (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	session_id VARCHAR NOT NULL, 
	problem_version_id VARCHAR NOT NULL, 
	variant_seed INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	hint_level INTEGER NOT NULL, 
	solution_viewed BOOLEAN NOT NULL, 
	completed BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (session_id, position), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(session_id) REFERENCES study_sessions (id)
)

;

CREATE INDEX ix_session_items_user_id ON session_items (user_id);

CREATE INDEX ix_session_items_session_id ON session_items (session_id);


CREATE TABLE execution_jobs (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	item_id VARCHAR NOT NULL, 
	problem_version_id VARCHAR NOT NULL, 
	code TEXT NOT NULL, 
	code_hash VARCHAR NOT NULL, 
	mode VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	request_id VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	lease_until TIMESTAMP WITH TIME ZONE, 
	provider_id VARCHAR, 
	limits JSON NOT NULL, 
	result JSON, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, request_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(item_id) REFERENCES session_items (id)
)

;

CREATE INDEX ix_execution_jobs_user_id ON execution_jobs (user_id);

CREATE UNIQUE INDEX one_active_job_per_user ON execution_jobs (user_id) WHERE status IN ('queued','running');


CREATE TABLE problem_drafts (
	user_id VARCHAR NOT NULL, 
	item_id VARCHAR NOT NULL, 
	code TEXT NOT NULL, 
	revision INTEGER NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (user_id, item_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(item_id) REFERENCES session_items (id)
)

;


CREATE TABLE submission_attempts (
	id VARCHAR NOT NULL, 
	user_id VARCHAR NOT NULL, 
	problem_version_id VARCHAR NOT NULL, 
	session_id VARCHAR NOT NULL, 
	item_id VARCHAR NOT NULL, 
	variant_seed INTEGER NOT NULL, 
	submitted_code TEXT NOT NULL, 
	verdict VARCHAR NOT NULL, 
	verification_level VARCHAR NOT NULL, 
	passed_tests INTEGER NOT NULL, 
	total_tests INTEGER NOT NULL, 
	run_count INTEGER NOT NULL, 
	hint_level_used INTEGER NOT NULL, 
	solution_viewed BOOLEAN NOT NULL, 
	submitted_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	client_request_id VARCHAR NOT NULL, 
	code_hash VARCHAR NOT NULL, 
	result JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, client_request_id), 
	FOREIGN KEY(user_id) REFERENCES profiles (id), 
	FOREIGN KEY(session_id) REFERENCES study_sessions (id), 
	FOREIGN KEY(item_id) REFERENCES session_items (id)
)

;

CREATE INDEX ix_submission_attempts_user_id ON submission_attempts (user_id);


CREATE TABLE curriculum_modules (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE concepts (id text PRIMARY KEY, module_id text NOT NULL REFERENCES curriculum_modules(id), data jsonb NOT NULL);
CREATE TABLE concept_prerequisites (concept_id text REFERENCES concepts(id), prerequisite_id text REFERENCES concepts(id), PRIMARY KEY(concept_id,prerequisite_id));
CREATE TABLE problem_families (id text PRIMARY KEY, concept_id text NOT NULL REFERENCES concepts(id), data jsonb NOT NULL);
CREATE TABLE problem_versions (id text PRIMARY KEY, family_id text NOT NULL REFERENCES problem_families(id), version integer NOT NULL, data jsonb NOT NULL, UNIQUE(family_id,version));
CREATE TABLE deep_dive_tasks (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE reading_projects (id text PRIMARY KEY, data jsonb NOT NULL);
CREATE TABLE reading_questions (id text PRIMARY KEY, project_id text NOT NULL REFERENCES reading_projects(id), data jsonb NOT NULL);
ALTER TABLE user_problem_progress ADD CONSTRAINT progress_version_fk FOREIGN KEY(problem_version_id) REFERENCES problem_versions(id);
CREATE SCHEMA IF NOT EXISTS private;
REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated;
CREATE TABLE private.grader_test_sets (problem_version_id text PRIMARY KEY REFERENCES problem_versions(id), data jsonb NOT NULL);
CREATE TABLE private.activity_answers (id text PRIMARY KEY, data jsonb NOT NULL);
REVOKE ALL ON ALL TABLES IN SCHEMA private FROM PUBLIC, anon, authenticated;
ALTER TABLE private.grader_test_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE private.activity_answers ENABLE ROW LEVEL SECURITY;
-- API/worker connect with a dedicated trusted DB role; browser roles cannot write certification.


ALTER TABLE curriculum_modules ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON curriculum_modules FROM anon, authenticated;

GRANT SELECT ON curriculum_modules TO anon, authenticated;

CREATE POLICY public_read ON curriculum_modules FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE concepts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON concepts FROM anon, authenticated;

GRANT SELECT ON concepts TO anon, authenticated;

CREATE POLICY public_read ON concepts FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE concept_prerequisites ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON concept_prerequisites FROM anon, authenticated;

GRANT SELECT ON concept_prerequisites TO anon, authenticated;

CREATE POLICY public_read ON concept_prerequisites FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE problem_families ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON problem_families FROM anon, authenticated;

GRANT SELECT ON problem_families TO anon, authenticated;

CREATE POLICY public_read ON problem_families FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE problem_versions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON problem_versions FROM anon, authenticated;

GRANT SELECT ON problem_versions TO anon, authenticated;

CREATE POLICY public_read ON problem_versions FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE deep_dive_tasks ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON deep_dive_tasks FROM anon, authenticated;

GRANT SELECT ON deep_dive_tasks TO anon, authenticated;

CREATE POLICY public_read ON deep_dive_tasks FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE reading_projects ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON reading_projects FROM anon, authenticated;

GRANT SELECT ON reading_projects TO anon, authenticated;

CREATE POLICY public_read ON reading_projects FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE reading_questions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON reading_questions FROM anon, authenticated;

GRANT SELECT ON reading_questions TO anon, authenticated;

CREATE POLICY public_read ON reading_questions FOR SELECT TO anon, authenticated USING (true);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON profiles FROM anon, authenticated;

GRANT SELECT ON profiles TO authenticated;

CREATE POLICY own_rows ON profiles FOR SELECT TO authenticated USING (id = (select auth.uid())::text);

ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON user_settings FROM anon, authenticated;

GRANT SELECT ON user_settings TO authenticated;

CREATE POLICY own_rows ON user_settings FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE study_sessions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON study_sessions FROM anon, authenticated;

GRANT SELECT ON study_sessions TO authenticated;

CREATE POLICY own_rows ON study_sessions FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE session_items ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON session_items FROM anon, authenticated;

GRANT SELECT ON session_items TO authenticated;

CREATE POLICY own_rows ON session_items FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE problem_drafts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON problem_drafts FROM anon, authenticated;

GRANT SELECT ON problem_drafts TO authenticated;

CREATE POLICY own_rows ON problem_drafts FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE submission_attempts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON submission_attempts FROM anon, authenticated;

GRANT SELECT ON submission_attempts TO authenticated;

CREATE POLICY own_rows ON submission_attempts FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE user_concept_progress ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON user_concept_progress FROM anon, authenticated;

GRANT SELECT ON user_concept_progress TO authenticated;

CREATE POLICY own_rows ON user_concept_progress FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE user_problem_progress ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON user_problem_progress FROM anon, authenticated;

GRANT SELECT ON user_problem_progress TO authenticated;

CREATE POLICY own_rows ON user_problem_progress FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE review_schedules ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON review_schedules FROM anon, authenticated;

GRANT SELECT ON review_schedules TO authenticated;

CREATE POLICY own_rows ON review_schedules FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE execution_jobs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON execution_jobs FROM anon, authenticated;

GRANT SELECT ON execution_jobs TO authenticated;

CREATE POLICY own_rows ON execution_jobs FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE activity_progress ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON activity_progress FROM anon, authenticated;

GRANT SELECT ON activity_progress TO authenticated;

CREATE POLICY own_rows ON activity_progress FOR SELECT TO authenticated USING (user_id = (select auth.uid())::text);

ALTER TABLE system_usage_daily ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON system_usage_daily FROM anon, authenticated;

CREATE INDEX attempts_user_date ON submission_attempts(user_id,submitted_at DESC);

CREATE INDEX jobs_claim ON execution_jobs(status,created_at);

CREATE INDEX session_resume ON study_sessions(user_id,updated_at DESC);

COMMIT;