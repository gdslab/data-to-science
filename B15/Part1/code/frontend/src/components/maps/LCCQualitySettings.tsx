type Quality = 'very-low' | 'low' | 'medium' | 'high' | 'very-high';

const QUALITY_OPTIONS: { value: Quality; label: string; shortLabel: string }[] = [
  { value: 'very-low', label: 'Very Low', shortLabel: 'V. Low' },
  { value: 'low', label: 'Low', shortLabel: 'Low' },
  { value: 'medium', label: 'Medium', shortLabel: 'Med' },
  { value: 'high', label: 'High', shortLabel: 'High' },
  { value: 'very-high', label: 'Very High', shortLabel: 'V. High' },
];

interface LCCQualitySettingsProps {
  quality: Quality;
  setQuality: (quality: Quality) => void;
}

export default function LCCQualitySettings({
  quality,
  setQuality,
}: LCCQualitySettingsProps) {
  return (
    <div className="w-fit flex items-center gap-2 rounded-sm border border-white/30 bg-black/70 px-3 py-2">
      <span className="text-sm font-medium text-white">Quality:</span>
      <div className="flex overflow-hidden rounded-sm border border-white/30">
        {QUALITY_OPTIONS.map((o, i) => (
          <button
            key={o.value}
            onClick={() => setQuality(o.value)}
            title={o.label}
            className={`px-2 py-1 text-xs font-medium transition-colors${i > 0 ? ' border-l border-white/30' : ''} ${
              quality === o.value
                ? 'bg-white/30 text-white'
                : 'bg-black/40 text-white/70 hover:bg-white/10'
            }`}
          >
            <span className="md:hidden">{o.shortLabel}</span>
            <span className="hidden md:inline">{o.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
