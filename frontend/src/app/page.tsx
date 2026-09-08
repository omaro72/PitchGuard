import { PitchReviewWorkspace } from "@/components/pitch-review-workspace";
import { env } from "@/lib/env";

export default function Home() {
  return (
    <main className="min-h-screen px-3 py-3 sm:px-6 sm:py-6 lg:px-8 lg:py-8">
      <div className="mx-auto max-w-[92rem]">
        <header className="relative mb-6 overflow-hidden rounded-[1.75rem] bg-[#102a2d] px-5 py-6 text-white shadow-[0_24px_70px_-40px_rgba(15,23,42,0.8)] sm:px-8 sm:py-9 lg:mb-8 lg:px-11 lg:py-10">
          <div
            aria-hidden="true"
            className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[3rem] border-teal-300/10"
          />
          <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1fr)_18rem] lg:items-end">
            <div className="max-w-4xl">
              <div className="mb-5 flex items-center gap-3">
                <span
                  aria-hidden="true"
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-teal-200/30 bg-teal-300 text-base font-black text-[#102a2d]"
                >
                  P
                </span>
                <span className="text-xs font-bold uppercase tracking-[0.22em] text-teal-100">
                  PitchGuard · Review desk
                </span>
              </div>
              <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-teal-300">
                AI-assisted preflight review
              </p>
              <h1 className="max-w-3xl text-4xl leading-[1.05] font-semibold tracking-[-0.035em] text-balance sm:text-5xl lg:text-6xl">
                Review the pitch. Protect the relationship.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg sm:leading-8">
                Check claim support, journalist fit, and reputational risk before a draft reaches an inbox.
              </p>
            </div>

            <aside className="rounded-2xl border border-white/12 bg-white/6 p-5 backdrop-blur-sm" aria-label="Review process summary">
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-300">
                Review process
              </p>
              <ol className="mt-4 space-y-3 text-sm text-slate-200">
                <li className="flex items-center gap-3">
                  <span className="font-mono text-xs text-teal-300">01</span>
                  Evidence check
                </li>
                <li className="flex items-center gap-3">
                  <span className="font-mono text-xs text-teal-300">02</span>
                  Journalist relevance
                </li>
                <li className="flex items-center gap-3">
                  <span className="font-mono text-xs text-teal-300">03</span>
                  PR risk review
                </li>
              </ol>
              <p className="mt-5 border-t border-white/10 pt-4 text-xs leading-5 text-slate-400">
                Decision support only. A human makes the final call.
              </p>
            </aside>
          </div>
        </header>
        <PitchReviewWorkspace apiBaseUrl={env.apiBaseUrl} />
        <footer className="px-2 py-8 text-center text-xs leading-5 text-slate-500">
          PitchGuard reviews only the information you provide. It does not send pitches or guarantee factual accuracy.
        </footer>
      </div>
    </main>
  );
}
