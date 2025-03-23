export default function Legend() {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full bg-black" />
        <span>Saturated</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-full border-8 border-black" />
        <span>Drydown</span>
      </div>
    </div>
  );
}
