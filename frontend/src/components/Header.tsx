export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-teal-950 px-6 py-4 text-white">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            Dengue-Aware Field Response System
          </h1>
          <p className="text-xs text-teal-300">
            A* route planning + rule-based clinical triage · Colombo &amp; Gampaha, Sri Lanka
          </p>
        </div>
      </div>
    </header>
  );
}
