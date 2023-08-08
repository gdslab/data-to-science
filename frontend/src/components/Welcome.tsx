export default function Welcome({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 items-center jusitfy-center m-4">
      <div className="h-16 w-16 bg-accent2 text-white flex items-center justify-center">
        Logo
      </div>
      <div className="text-center">
        <h1 className="text-white mb-0">Welcome!</h1>
        <span className="text-sm text-white">{children}</span>
      </div>
    </div>
  );
}
