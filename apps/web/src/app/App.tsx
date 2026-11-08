import { lazy, Suspense } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../lib/api";
import { Layout } from "./Layout";
import { Home } from "../pages/Home";
import { Landing } from "../pages/Landing";
import { Curriculum, ConceptDetail } from "../pages/Curriculum";
import { DrillStart } from "../pages/DrillStart";
import { Analytics, History } from "../pages/Analytics";
import { Settings, AuthCallback } from "../pages/Settings";
import { Loading } from "../components/ui";
const Drill = lazy(() =>
  import("../pages/Drill").then((m) => ({ default: m.DrillPage })),
);
const ReadingList = lazy(() =>
  import("../pages/Activities").then((m) => ({ default: m.ReadingList })),
);
const ReadingProject = lazy(() =>
  import("../pages/Activities").then((m) => ({ default: m.ReadingProject })),
);
const DeepDive = lazy(() =>
  import("../pages/Activities").then((m) => ({ default: m.DeepDive })),
);
export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route element={<Layout />}>
              <Route path="/home" element={<Home />} />
              <Route path="/curriculum" element={<Curriculum />} />
              <Route path="/curriculum/:moduleId" element={<Curriculum />} />
              <Route path="/concepts/:conceptId" element={<ConceptDetail />} />
              <Route path="/drill" element={<DrillStart />} />
              <Route path="/drill/s/:sessionId/:itemId" element={<Drill />} />
              <Route path="/deep-dive/:taskId" element={<DeepDive />} />
              <Route path="/reading" element={<ReadingList />} />
              <Route path="/reading/:projectId" element={<ReadingProject />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/history" element={<History />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
              <Route
                path="*"
                element={
                  <div className="empty">
                    <h1>ページが見つかりません</h1>
                    <Link className="btn primary" to="/home">
                      ホームに戻る
                    </Link>
                  </div>
                }
              />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
