import { PitchReviewWorkspace } from "@/components/pitch-review-workspace";
import { env } from "@/lib/env";

export default function Home() {
  return (
    <main className="min-h-screen px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
      <div className="mx-auto max-w-7xl">
        <header className="mb-10 max-w-3xl">
          <div className="mb-5 flex items-center gap-3">
            <span
              aria-hidden="true"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-800 text-lg font-black text-white shadow-sm"
            >
              P
            </span>
            <span className="text-sm font-bold uppercase tracking-[0.18em] text-cyan-800">
              PitchGuard
            </span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-950 sm:text-5xl">
            Review a PR pitch before it reaches a journalist.
          </h1>
          <p className="mt-5 text-lg leading-8 text-slate-600">
            Compare the draft with supplied evidence and journalist context. PitchGuard combines three focused AI reviews with deterministic decision rules.
          </p>
        </header>
        <PitchReviewWorkspace apiBaseUrl={env.apiBaseUrl} />
      </div>
    </main>
  );
}
