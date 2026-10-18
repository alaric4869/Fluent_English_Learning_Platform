import { DashboardPage } from "./pages/DashboardPage";
import { HistoryDetailPage } from "./pages/HistoryDetailPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LibraryPage } from "./pages/LibraryPage";
import { NotebookPage } from "./pages/NotebookPage";
import { ProgressPage } from "./pages/ProgressPage";
import { ResourceDetailPage } from "./pages/ResourceDetailPage";
import { ReviewPage } from "./pages/ReviewPage";
import { TodayPage } from "./pages/TodayPage";
import { WeeklyReviewPage } from "./pages/WeeklyReviewPage";
import { IeltsPage } from "./pages/IeltsPage";
import { IeltsPracticePage } from "./pages/IeltsPracticePage";
import { WritingPage } from "./pages/WritingPage";
import { SpeakingPage } from "./pages/SpeakingPage";
import { ListeningPage } from "./pages/ListeningPage";


export default function App() {
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  const resourceMatch = path.match(/^\/library\/(\d+)$/);
  const historyMatch = path.match(/^\/history\/(\d{4}-\d{2}-\d{2})$/);
  const ieltsMatch = path.match(/^\/ielts\/(g\d+-test-\d+-(?:listening|reading))$/);
  const writingMatch = path.match(/^\/writing\/(\d+)$/);
  const speakingMatch = path.match(/^\/speaking\/(\d+)$/);
  const listeningMatch = path.match(/^\/listening\/(\d+)$/);
  if (resourceMatch) return <ResourceDetailPage resourceId={Number(resourceMatch[1])} />;
  if (historyMatch) return <HistoryDetailPage studyDate={historyMatch[1]} />;
  if (ieltsMatch) return <IeltsPracticePage slug={ieltsMatch[1]} />;
  if (writingMatch) return <WritingPage resourceId={Number(writingMatch[1])} />;
  if (speakingMatch) return <SpeakingPage resourceId={Number(speakingMatch[1])} />;
  if (listeningMatch) return <ListeningPage resourceId={Number(listeningMatch[1])} />;
  if (path === "/today") return <TodayPage />;
  if (path === "/library") return <LibraryPage />;
  if (path === "/review") return <ReviewPage />;
  if (path === "/history") return <HistoryPage />;
  if (path === "/progress") return <ProgressPage />;
  if (path === "/weekly-review") return <WeeklyReviewPage />;
  if (path === "/notebook") return <NotebookPage />;
  if (path === "/ielts") return <IeltsPage />;
  return <DashboardPage />;
}
