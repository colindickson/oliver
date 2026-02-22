interface Props {
  current: number
  longest: number
}

export function StreakCard({ current, longest }: Props) {
  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm">
      <h3 className="text-sm font-medium text-gray-500 mb-4">Streaks</h3>
      <div className="flex gap-8">
        <div className="text-center">
          <p className="text-4xl font-bold text-blue-600">{current}</p>
          <p className="text-xs text-gray-400 mt-1">Current streak</p>
        </div>
        <div className="text-center">
          <p className="text-4xl font-bold text-gray-700">{longest}</p>
          <p className="text-xs text-gray-400 mt-1">Longest streak</p>
        </div>
      </div>
    </div>
  )
}
