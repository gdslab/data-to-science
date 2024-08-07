export default function ProgressBar({
  progress,
  initialCheck = false,
  completedMsg,
}: {
  progress: number;
  initialCheck?: boolean;
  completedMsg?: string;
}) {
  return (
    <div className="flex items-center gap-4">
      <div className="w-60">
        <div className="w-full bg-gray-400 rounded-full">
          <div
            className="bg-blue-600 text-xs font-medium text-blue-100 text-center p-0.5 leading-none rounded-full"
            style={{ width: progress === 0 ? undefined : `${Math.ceil(progress)}%` }}
          >
            {progress === 0 && !initialCheck
              ? 'PENDING'
              : progress === 0 && initialCheck
              ? 'CHECKING FOR PROGRESS'
              : `${Math.ceil(progress)}%`}
          </div>
        </div>
      </div>
      {progress >= 100 && <span className="text-sm">{completedMsg}</span>}
    </div>
  );
}
