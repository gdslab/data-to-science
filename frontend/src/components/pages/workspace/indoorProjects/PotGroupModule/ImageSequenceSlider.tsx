import { useEffect, useMemo, useState } from 'react';

interface ImageSequenceSliderProps {
  images: string[];
  interval?: number;
  title?: string;
}

/**
 * Extract rotation angle from filename (number after SideBottom- or SideFull-).
 * @param filename The filename to extract the angle from.
 * @returns The rotation angle as an integer, or Infinity if no angle is found.
 */
const getAngle = (filename: string) => {
  const match = filename.match(/(?:SideBottom|SideFull)-(\d+)/);
  return match ? parseInt(match[1], 10) : Infinity;
};

export default function ImageSequenceSlider({
  images,
  interval = 1000,
  title,
}: ImageSequenceSliderProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Sort images based on rotation angle in filename
  const sortedImages = useMemo(() => {
    return [...images].sort((a, b) => getAngle(a) - getAngle(b));
  }, [images]);

  // Auto-play effect
  useEffect(() => {
    if (!isPlaying) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % sortedImages.length);
    }, interval);

    return () => clearInterval(timer);
  }, [isPlaying, interval, sortedImages.length]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative">
        <img
          src={sortedImages[currentIndex]}
          alt={title || `Rotation view ${currentIndex + 1}`}
          className="w-[32rem] h-[32rem] object-cover rounded"
          title={title}
        />
        <div className="absolute top-2 left-2 w-12 h-12 rounded-full bg-black/50 flex items-center justify-center text-white font-bold text-lg">
          {getAngle(sortedImages[currentIndex])}°
        </div>
      </div>
      <div className="flex items-center gap-4">
        <input
          type="range"
          min="0"
          max={sortedImages.length - 1}
          value={currentIndex}
          onChange={(e) => setCurrentIndex(Number(e.target.value))}
          className="w-32"
        />
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 transition-colors w-16"
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
      </div>
    </div>
  );
}
