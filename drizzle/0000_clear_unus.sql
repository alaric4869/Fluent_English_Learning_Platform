CREATE TABLE `app_meta` (
	`key` text PRIMARY KEY NOT NULL,
	`value` text NOT NULL
);
--> statement-breakpoint
CREATE TABLE `notebook_entries` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`type` text NOT NULL,
	`title` text NOT NULL,
	`content` text NOT NULL,
	`source_resource_id` text,
	`is_favorite` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`source_resource_id`) REFERENCES `learning_resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_notebook_user_created` ON `notebook_entries` (`user_id`,`created_at`);--> statement-breakpoint
CREATE TABLE `performance_signals` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`module` text NOT NULL,
	`signal_type` text NOT NULL,
	`numeric_value` integer NOT NULL,
	`plan_item_id` text,
	`observed_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`plan_item_id`) REFERENCES `study_plan_items`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_performance_user_module` ON `performance_signals` (`user_id`,`module`);--> statement-breakpoint
CREATE TABLE `resource_user_states` (
	`user_id` text NOT NULL,
	`resource_id` text NOT NULL,
	`is_favorite` integer DEFAULT false NOT NULL,
	`saved_for_later` integer DEFAULT false NOT NULL,
	FOREIGN KEY (`resource_id`) REFERENCES `learning_resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_resource_states_user_resource` ON `resource_user_states` (`user_id`,`resource_id`);--> statement-breakpoint
CREATE TABLE `learning_resources` (
	`id` text PRIMARY KEY NOT NULL,
	`owner_user_id` text,
	`type` text NOT NULL,
	`module` text NOT NULL,
	`title` text NOT NULL,
	`source` text NOT NULL,
	`url` text,
	`topic` text NOT NULL,
	`difficulty` text NOT NULL,
	`duration_minutes` integer NOT NULL,
	`priority` integer DEFAULT 50 NOT NULL,
	`tags_json` text DEFAULT '[]' NOT NULL,
	`content_json` text DEFAULT '{}' NOT NULL,
	`is_favorite` integer DEFAULT false NOT NULL,
	`is_archived` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`last_studied_at` text
);
--> statement-breakpoint
CREATE INDEX `idx_resources_module_archived` ON `learning_resources` (`module`,`is_archived`);--> statement-breakpoint
CREATE INDEX `idx_resources_topic` ON `learning_resources` (`topic`);--> statement-breakpoint
CREATE TABLE `review_attempts` (
	`id` text PRIMARY KEY NOT NULL,
	`review_item_id` text NOT NULL,
	`user_id` text NOT NULL,
	`rating` text NOT NULL,
	`previous_due_date` text NOT NULL,
	`next_due_date` text NOT NULL,
	`attempted_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`review_item_id`) REFERENCES `review_items`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_review_attempts_user_date` ON `review_attempts` (`user_id`,`attempted_at`);--> statement-breakpoint
CREATE TABLE `review_items` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`target_type` text NOT NULL,
	`target_id` text NOT NULL,
	`prompt` text NOT NULL,
	`answer` text NOT NULL,
	`stage` integer DEFAULT 0 NOT NULL,
	`due_date` text NOT NULL,
	`mastery` text DEFAULT 'new' NOT NULL,
	`lapse_count` integer DEFAULT 0 NOT NULL,
	`scheduler_version` text DEFAULT 'fixed-v1' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_review_items_user_due` ON `review_items` (`user_id`,`due_date`);--> statement-breakpoint
CREATE UNIQUE INDEX `idx_review_items_user_target` ON `review_items` (`user_id`,`target_type`,`target_id`);--> statement-breakpoint
CREATE TABLE `saved_sentences` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`resource_id` text NOT NULL,
	`sentence_index` integer NOT NULL,
	`sentence` text NOT NULL,
	`status` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`resource_id`) REFERENCES `learning_resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_saved_sentences_user` ON `saved_sentences` (`user_id`);--> statement-breakpoint
CREATE UNIQUE INDEX `idx_saved_sentences_user_resource_index` ON `saved_sentences` (`user_id`,`resource_id`,`sentence_index`);--> statement-breakpoint
CREATE TABLE `study_days` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`study_date` text NOT NULL,
	`theme` text NOT NULL,
	`target_minutes` integer NOT NULL,
	`adaptation_reasons_json` text DEFAULT '[]' NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_study_days_user_date` ON `study_days` (`user_id`,`study_date`);--> statement-breakpoint
CREATE TABLE `study_plan_items` (
	`id` text PRIMARY KEY NOT NULL,
	`study_day_id` text NOT NULL,
	`resource_id` text NOT NULL,
	`module` text NOT NULL,
	`position` integer NOT NULL,
	`target_minutes` integer NOT NULL,
	`instructions_json` text DEFAULT '[]' NOT NULL,
	`objectives_json` text DEFAULT '[]' NOT NULL,
	`resource_snapshot_json` text NOT NULL,
	`assignment_source` text DEFAULT 'rule_based' NOT NULL,
	`status` text DEFAULT 'not_started' NOT NULL,
	`notes` text DEFAULT '' NOT NULL,
	`difficulty_rating` integer,
	`confidence_rating` integer,
	`completed_at` text,
	FOREIGN KEY (`study_day_id`) REFERENCES `study_days`(`id`) ON UPDATE no action ON DELETE no action,
	FOREIGN KEY (`resource_id`) REFERENCES `learning_resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_plan_items_study_day` ON `study_plan_items` (`study_day_id`);--> statement-breakpoint
CREATE TABLE `study_sessions` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`plan_item_id` text NOT NULL,
	`started_at` text NOT NULL,
	`completed_at` text,
	`active_seconds` integer DEFAULT 0 NOT NULL,
	FOREIGN KEY (`plan_item_id`) REFERENCES `study_plan_items`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_sessions_user_started` ON `study_sessions` (`user_id`,`started_at`);--> statement-breakpoint
CREATE TABLE `vocabulary_items` (
	`id` text PRIMARY KEY NOT NULL,
	`user_id` text NOT NULL,
	`phrase` text NOT NULL,
	`meaning` text NOT NULL,
	`example` text NOT NULL,
	`source_resource_id` text,
	`date_learned` text NOT NULL,
	`personal_note` text DEFAULT '' NOT NULL,
	`difficulty` text DEFAULT 'medium' NOT NULL,
	`mastery` text DEFAULT 'new' NOT NULL,
	`is_favorite` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`source_resource_id`) REFERENCES `learning_resources`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE INDEX `idx_vocabulary_user_date` ON `vocabulary_items` (`user_id`,`date_learned`);