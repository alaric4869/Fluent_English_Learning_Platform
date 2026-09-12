import type { IeltsSkill } from "../shared/contracts";
import type { IeltsAnswerKey, IeltsAnswerKeyEntry } from "./ielts-question-bank";
import { sectionForQuestion } from "./ielts-question-bank";
import generatedRawKeys from "./ielts-answer-keys.generated.json";
import { getIeltsExplanationRange } from "./ielts-explanation-manifest";

interface RawAnswerKey {
  bookNumber: number;
  testNumber: number;
  skill: Extract<IeltsSkill, "listening" | "reading">;
  answers: Record<number, string>;
  groups?: Array<{ questions: number[]; answers: string[] }>;
}

const RAW_KEYS: RawAnswerKey[] = [
  ...(generatedRawKeys as RawAnswerKey[]),
  raw(20, 1, "listening", [
    "fish", "roof", "Spanish", "vegetarian", "Audley", "hotel", "reviews", "local", "(£)30/(£)thirty", "average",
    "A", "B", "C", "A", "B", "C", "A", "E", "C", "E", "C", "E", "A", "C", "A", "B", "A", "B", "A", "C",
    "factories", "dead", "whale", "apartments", "park", "art", "beaches", "ferry", "bikes", "drone",
  ], [{ questions: [17, 18], answers: ["A", "E"] }, { questions: [19, 20], answers: ["C", "E"] }, { questions: [21, 22], answers: ["C", "E"] }, { questions: [23, 24], answers: ["A", "C"] }, { questions: [25, 26], answers: ["A", "B"] }]),
  raw(20, 1, "reading", [
    "D", "B", "C", "F", "E", "TRUE", "FALSE", "FALSE", "NOT GIVEN", "TRUE", "TRUE", "NOT GIVEN", "TRUE", "NOT GIVEN",
    "behaviour/behavior", "conflict", "environment", "friend", "solutions", "workload", "skills", "half", "reviews", "employees", "dates", "rights", "competitors",
    "B", "F", "C", "D", "G", "C", "D", "B", "A", "university", "game", "workshop", "C",
  ]),
  raw(20, 2, "listening", [
    "break", "time", "shower", "money", "memory", "lifting", "fall", "taxi", "insurance", "stress",
    "D", "C", "H", "E", "A", "B", "B", "A", "B", "A", "D", "G", "B", "A", "E", "C", "A", "A", "B", "C",
    "photos/photographs/pictures", "vegan", "chefs/cooks", "journalists/reporters", "health", "coffee", "environment", "reputation", "price/cost", "soil",
  ]),
  raw(20, 2, "reading", [
    "D", "C", "E", "C", "E", "B", "A", "accessories", "fit", "expense", "profile", "agencies", "training", "contacts",
    "hours", "orders", "marketing", "phone", "needs", "price", "listening", "opinions", "mistakes", "confused", "recruitment", "quality", "leader",
    "D", "B", "D", "C", "A", "D", "E", "B", "classroom", "shoes", "games", "circus", "socialise/socialize",
  ]),
  raw(20, 3, "listening", [
    "($)239/($)two hundred (and) thirty-nine", "modern", "lamp", "Aaron", "damage", "electronic", "insurance", "Space", "app", "Exchanges",
    "B", "A", "A", "C", "B", "C", "B", "A", "G", "E", "B", "A", "C", "A", "C", "B", "F", "E", "B", "D",
    "adaptation", "cognitive", "desks", "taps", "blue", "voice", "pregnant", "shoulders", "police", "temperature",
  ]),
  raw(20, 3, "reading", [
    "D", "E", "C", "A", "D", "B", "B", "TRUE", "FALSE", "TRUE", "NOT GIVEN", "TRUE", "NOT GIVEN", "FALSE",
    "NOT GIVEN", "TRUE", "FALSE", "TRUE", "FALSE", "FALSE", "TRUE", "Current Vacancies", "First Time Applicant", "(small) sections", "name", "one sitting/1 sitting", "recruitment office",
    "C", "F", "B", "H", "I", "E", "D", "E", "A", "C", "D", "D", "A",
  ]),
  raw(20, 4, "listening", [
    "Kings/King's", "125/one hundred (and) twenty-five", "walking", "boat", "Tuesday", "space", "vegetarian", "2.30/two thirty", "75/seventy-five", "port",
    "B", "C", "A", "C", "D", "F", "B", "H", "C", "G", "C", "E", "A", "C", "C", "A", "A", "B", "B", "C",
    "rats", "snakes", "tourism", "traffic", "rain", "poison", "building", "60p", "noise", "combination",
  ], [{ questions: [11, 12], answers: ["B", "C"] }, { questions: [13, 14], answers: ["A", "C"] }, { questions: [21, 22], answers: ["C", "E"] }, { questions: [23, 24], answers: ["A", "C"] }]),
  raw(20, 4, "reading", [
    "F", "B", "A", "E", "F", "A", "C", "FALSE", "FALSE", "NOT GIVEN", "NOT GIVEN", "FALSE", "TRUE", "TRUE",
    "genuine", "pitches", "workload", "flexibility", "job", "payment", "motivation", "sections", "interest", "skills", "budget", "achievements", "mistakes",
    "vii", "v", "iv", "viii", "i", "iii", "mosaics", "tokens", "records", "barley", "A", "B", "D",
  ]),
];

export const IELTS_ANSWER_KEYS = new Map(RAW_KEYS.map((key) => {
  const groups = new Map<number, { id: string; answers: string[] }>();
  for (const group of key.groups ?? []) {
    const id = group.questions.join("-");
    for (const question of group.questions) groups.set(question, { id, answers: group.answers });
  }
  const answers: IeltsAnswerKeyEntry[] = Object.entries(key.answers).map(([number, answer]) => {
    const questionNumber = Number(number);
    const group = groups.get(questionNumber);
    const sectionNumber = sectionForQuestion(key.skill, questionNumber);
    return {
      questionNumber,
      sectionNumber,
      acceptedAnswers: group?.answers ?? [answer],
      groupId: group?.id,
      acceptedSet: group?.answers,
      explanationPage: getIeltsExplanationRange(key.bookNumber, key.testNumber, key.skill, sectionNumber)?.startPage,
    };
  });
  const value: IeltsAnswerKey = { bookNumber: key.bookNumber, testNumber: key.testNumber, skill: key.skill, answers };
  return [`${key.bookNumber}-${key.testNumber}-${key.skill}`, value] as const;
}));

function raw(
  bookNumber: number,
  testNumber: number,
  skill: RawAnswerKey["skill"],
  answers: string[],
  groups?: RawAnswerKey["groups"],
): RawAnswerKey {
  if (answers.length !== 40) throw new Error(`IELTS ${bookNumber}-${testNumber}-${skill} must contain 40 answers.`);
  return { bookNumber, testNumber, skill, answers: Object.fromEntries(answers.map((answer, index) => [index + 1, answer])), groups };
}
