export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-16">
      <section className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-10 shadow-sm">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
          Under development
        </p>
        <h1 className="text-4xl font-semibold tracking-tight text-slate-950">
          PitchGuard
        </h1>
        <p className="mt-4 text-xl leading-8 text-slate-700">
          AI-assisted preflight review for PR pitches
        </p>
        <p className="mt-6 text-base leading-7 text-slate-600">
          The project scaffold is ready. Product functionality is currently
          under development.
        </p>
      </section>
    </main>
  );
}
