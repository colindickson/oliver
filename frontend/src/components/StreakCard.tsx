interface Props {
  current: number
  longest: number
}

export function StreakCard({ current, longest }: Props) {
  return (
    <div className="bg-white rounded-2xl border border-stone-100 p-6 shadow-soft">
      <h3 className="text-xs font-medium text-stone-400 uppercase tracking-wider mb-4">Streaks</h3>
      <div className="flex gap-8">
        <div className="text-center">
          <p className="text-4xl font-bold text-terracotta-600 tabular-nums">{current}</p>
          <p className="text-xs text-stone-400 mt-1">Current streak</p>
          {current === longest && current > 0 && (
            <span className="inline-block mt-1 px-2 py-0.5 text-[10px] font-medium bg-terracotta-100 text-terracotta-600 rounded-full">
              Best!
            </span>
          )}
        </div>
        <div className="text-center">
          <p className="text-4xl font-bold text-stone-500 tabular-nums">{longest}</p>
          <p className="text-xs text-stone-400 mt-1">Longest streak</p>
        </div>
      </div>
    </div>
  )
}
