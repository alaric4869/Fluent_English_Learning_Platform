import { useCallback } from "react";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/LoadingState";
import { PageIntro } from "../components/PageIntro";
import { frontendApi } from "../lib/api";
import { useApiQuery } from "../lib/useApiQuery";


const SKILL_CODES = { listening: "LI", reading: "RE", writing: "WR", speaking: "SP" } as const;


export function IeltsPage() {
  const loader = useCallback((signal: AbortSignal) => frontendApi.ieltsCatalog(signal), []);
  const { data, error } = useApiQuery(loader);
  return (
    <AppShell activePage="ielts">
      <div className="page-container ielts-catalog-page">
        <PageIntro
          eyebrow="IELTS General Training"
          title="Practice with purpose."
          description="听力与阅读直接在网页作答并查看错题精解；写作和口语继续保留独立练习工作区。"
          actions={data && (
            <div className="ielts-target-card"><span>EXAM TARGET</span><strong>Band {data.target_band}</strong><small>{data.exam_timing}</small></div>
          )}
        />
        {error && <ErrorState message={error} />}
        {!data && !error && <LoadingState />}
        {data && (
          <section className="surface-panel ielts-catalog-panel">
            <div className="section-heading">
              <div><p className="eyebrow">Cambridge 20 · Tests 1–4</p><h2>选择练习模块</h2></div>
              <p>{data.module_count} modules available</p>
            </div>
            <div className="ielts-module-grid">
              {data.modules.map((module) => (
                <article className={`ielts-module-card skill-${module.skill}`} key={module.key}>
                  <div className="ielts-module-top"><span>{SKILL_CODES[module.skill]}</span><small>{module.duration_minutes} min</small></div>
                  <p className="card-kicker">GENERAL TRAINING · TEST {module.test_number}</p>
                  <h3>{module.title}</h3>
                  <p>{module.description}</p>
                  <dl>
                    <div><dt>{module.question_count ? "Questions" : "Practice"}</dt><dd>{module.question_count ?? module.detail_label}</dd></div>
                    <div><dt>{module.section_count ? "Sections" : "Format"}</dt><dd>{module.section_count ?? "Interactive"}</dd></div>
                    <div><dt>Status</dt><dd>{module.migrated ? "React" : "Available"}</dd></div>
                  </dl>
                  <a className="primary-button" href={module.workspace_href}>开始 / 继续练习</a>
                </article>
              ))}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  );
}
