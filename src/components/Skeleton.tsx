interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`bg-gray-100 rounded-lg animate-pulse ${className}`}
    />
  )
}

export function StatCardSkeleton() {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 flex items-start justify-between flex-1">
      <div className="space-y-2 flex-1">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-3 w-28" />
      </div>
      <Skeleton className="w-6 h-6 rounded-md" />
    </div>
  )
}

export function ChartSkeleton({ height = 200 }: { height?: number }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-6">
      <Skeleton className="h-4 w-32 mb-1" />
      <Skeleton className="h-3 w-48 mb-5" />
      <div
        className="bg-gray-50 rounded-xl flex items-end gap-2 px-4 pb-4 pt-8"
        style={{ height }}
      >
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex-1 flex flex-col justify-end">
            <div
              className="bg-gray-200 rounded-t animate-pulse"
              style={{ height: `${30 + Math.random() * 70}%` }}
            />
          </div>
        ))}
      </div>
    </div>
  )
}
