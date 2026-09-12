CREATE TABLE `ielts_question_responses` (
	`id` text PRIMARY KEY NOT NULL,
	`attempt_id` text NOT NULL,
	`user_id` text NOT NULL,
	`section_number` integer NOT NULL,
	`question_number` integer NOT NULL,
	`answer` text DEFAULT '' NOT NULL,
	`is_correct` integer,
	`correct_answer` text,
	`explanation_page` integer,
	`saved_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`graded_at` text,
	FOREIGN KEY (`attempt_id`) REFERENCES `ielts_attempts`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_ielts_responses_attempt_question` ON `ielts_question_responses` (`attempt_id`,`question_number`);--> statement-breakpoint
CREATE INDEX `idx_ielts_responses_user_saved` ON `ielts_question_responses` (`user_id`,`saved_at`);