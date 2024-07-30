export default function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-60">
      <div className="w-full bg-gray-400 rounded-full">
        <div
          className="bg-blue-600 text-xs font-medium text-blue-100 text-center p-0.5 leading-none rounded-full"
          style={{ width: progress === 0 ? undefined : `${Math.ceil(progress)}%` }}
        >
          {progress === 0 ? 'PENDING' : `${Math.ceil(progress)}%`}
        </div>
      </div>
    </div>
  );
}
