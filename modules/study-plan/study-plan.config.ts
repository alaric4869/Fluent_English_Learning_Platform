import type { StudyModule } from "../shared/contracts";

export const STUDY_PLAN_CONFIG = {
  baseMinutes: {
    listening: 30,
    speaking: 25,
    reading: 30,
    vocabulary: 25,
  } satisfies Record<StudyModule, number>,
  minimumMinutes: {
    listening: 20,
    speaking: 15,
    reading: 15,
    vocabulary: 15,
  } satisfies Record<StudyModule, number>,
  maximumMinutes: {
    listening: 45,
    speaking: 40,
    reading: 40,
    vocabulary: 35,
  } satisfies Record<StudyModule, number>,
  maximumDailyAdjustment: 5,
  recentResourceCooldown: 6,
  themes: [
    "Ordering food and coffee",
    "Small talk",
    "Making and changing appointments",
    "Renting and housing",
    "Healthcare",
    "Asking for help",
    "Workplace English",
    "Explaining problems",
    "Australian everyday English",
    "IELTS / PTE",
  ],
} as const;

export const MODULE_COPY: Record<StudyModule, { instructions: string[]; objectives: string[] }> = {
  listening: {
    instructions: [
      "Listen once with the transcript hidden.",
      "Listen again while reading the transcript.",
      "Mark unclear sentences and replay them one by one.",
      "Finish with one transcript-free listen.",
    ],
    objectives: ["Understand the main idea", "Notice reduced and connected speech", "Recover difficult sentences"],
  },
  speaking: {
    instructions: [
      "Listen, pause and repeat each line.",
      "Imitate the speaker's rhythm and stress.",
      "Hide the text and retell the idea in your own words.",
    ],
    objectives: ["Build automatic responses", "Use complete chunks", "Speak with smoother rhythm"],
  },
  reading: {
    instructions: [
      "Read once without looking up every word.",
      "Answer the comprehension questions.",
      "Save only high-value words or chunks.",
    ],
    objectives: ["Understand 70–90% from context", "Read for meaning", "Collect reusable expressions"],
  },
  vocabulary: {
    instructions: [
      "Review due items before learning new ones.",
      "Say each chunk in a complete sentence.",
      "Create one personal example for difficult chunks.",
    ],
    objectives: ["Recall phrases, not isolated words", "Use chunks productively", "Strengthen long-term retention"],
  },
};
