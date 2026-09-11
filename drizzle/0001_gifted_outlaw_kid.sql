CREATE TABLE `ielts_attempts` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`book_number` integer NOT NULL,
	`test_number` integer NOT NULL,
	`skill` text NOT NULL,
	`status` text DEFAULT 'in_progress' NOT NULL,
	`raw_score` integer,
	`estimated_band` real,
	`notes` text DEFAULT '' NOT NULL,
	`started_at` text NOT NULL,
	`completed_at` text,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_ielts_attempts_user_started` ON `ielts_attempts` (`user_id`,`started_at`);--> statement-breakpoint
CREATE INDEX `idx_ielts_attempts_material` ON `ielts_attempts` (`user_id`,`book_number`,`test_number`,`skill`);--> statement-breakpoint
CREATE TABLE `ielts_goals` (
	`user_id` text PRIMARY KEY NOT NULL,
	`test_type` text DEFAULT 'general' NOT NULL,
	`target_band` real DEFAULT 6.5 NOT NULL,
	`exam_date` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
