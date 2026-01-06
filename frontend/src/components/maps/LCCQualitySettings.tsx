interface LCCQualitySettingsProps {
  quality: 'very-low' | 'low' | 'medium' | 'high' | 'very-high';
  setQuality: (quality: 'very-low' | 'low' | 'medium' | 'high' | 'very-high') => void;
}

export default function LCCQualitySettings({
  quality,
  setQuality,
}: LCCQualitySettingsProps) {
  return (
    <div className="flex items-center gap-2 rounded-sm border border-white/30 bg-black/70 px-3 py-2">
      <span className="text-sm font-medium text-white">Quality:</span>
      <div className="flex overflow-hidden rounded-sm border border-white/30">
        <button
          onClick={() => setQuality('very-low')}
          className={`px-2 py-1 text-xs font-medium transition-colors ${
            quality === 'very-low'
              ? 'bg-white/30 text-white'
              : 'bg-black/40 text-white/70 hover:bg-white/10'
          }`}
        >
          Very Low
        </button>
        <button
          onClick={() => setQuality('low')}
          className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
            quality === 'low'
              ? 'bg-white/30 text-white'
              : 'bg-black/40 text-white/70 hover:bg-white/10'
          }`}
        >
          Low
        </button>
        <button
          onClick={() => setQuality('medium')}
          className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
            quality === 'medium'
              ? 'bg-white/30 text-white'
              : 'bg-black/40 text-white/70 hover:bg-white/10'
          }`}
        >
          Medium
        </button>
        <button
          onClick={() => setQuality('high')}
          className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
            quality === 'high'
              ? 'bg-white/30 text-white'
              : 'bg-black/40 text-white/70 hover:bg-white/10'
          }`}
        >
          High
        </button>
        <button
          onClick={() => setQuality('very-high')}
          className={`border-l border-white/30 px-2 py-1 text-xs font-medium transition-colors ${
            quality === 'very-high'
              ? 'bg-white/30 text-white'
              : 'bg-black/40 text-white/70 hover:bg-white/10'
          }`}
        >
          Very High
        </button>
      </div>
    </div>
  );
}
