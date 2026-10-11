export default function LCCControlsOverlay() {
  return (
    <div className="absolute top-[110px] left-3 z-10 max-w-[300px] rounded-sm border border-white/30 bg-black/85 p-4 text-[13px] leading-relaxed text-white">
      <div className="mb-3 text-[15px] font-semibold">Controls</div>
      <div className="flex flex-col gap-2">
        <div>
          <div className="mb-1 font-medium">Camera</div>
          <div className="pl-2 opacity-90">
            <div>Left Click + Drag - Rotate view</div>
            <div>Mouse Wheel - Zoom in/out on drone</div>
          </div>
        </div>
        <div>
          <div className="mb-1 font-medium">Movement</div>
          <div className="pl-2 opacity-90">
            <div>W / ↑ - Move forward</div>
            <div>S / ↓ - Move backward</div>
            <div>A / ← - Move left</div>
            <div>D / → - Move right</div>
            <div>Space - Move up</div>
            <div>Ctrl / F - Move down</div>
            <div>Shift - Sprint (1.5x speed)</div>
          </div>
        </div>
        <div>
          <div className="mb-1 font-medium">Toggle</div>
          <div className="pl-2 opacity-90">
            <div>H - Show/hide drone</div>
            <div>C - Show/hide controls</div>
            <div>R - Reset position</div>
          </div>
        </div>
      </div>
    </div>
  );
}
