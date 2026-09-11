import { D1ResourceRepository } from "../resources/d1-resource.repository";
import { ResourceService } from "../resources/resource.service";
import { D1StudyPlanRepository } from "../study-plan/d1-study-plan.repository";
import { RuleBasedStudyPlanGenerator } from "../study-plan/study-plan-generator";
import { StudyPlanService } from "../study-plan/study-plan.service";
import { D1ReviewRepository } from "../review/d1-review.repository";
import { FixedIntervalReviewScheduler } from "../review/review-scheduler";
import { ReviewService } from "../review/review.service";
import { LearningArtifactService } from "../learning-artifacts/artifact.service";
import { NotebookService } from "../notebook/notebook.service";
import { ProgressService } from "../analytics/progress.service";
import { D1IeltsRepository } from "../ielts/d1-ielts.repository";
import { IeltsService } from "../ielts/ielts.service";

const resourceRepository = new D1ResourceRepository();
const studyPlanRepository = new D1StudyPlanRepository();
const reviewRepository = new D1ReviewRepository();

export const resourceService = new ResourceService(resourceRepository);
export const studyPlanService = new StudyPlanService(
  studyPlanRepository,
  resourceRepository,
  new RuleBasedStudyPlanGenerator(),
);
export const reviewService = new ReviewService(reviewRepository, new FixedIntervalReviewScheduler());
export const artifactService = new LearningArtifactService(reviewRepository);
export const notebookService = new NotebookService();
export const progressService = new ProgressService();
export const ieltsService = new IeltsService(new D1IeltsRepository());
