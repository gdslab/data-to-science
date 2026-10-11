import { useCallback, useEffect, useState } from 'react';

interface SwipeSliderProps {
  position: number; // 0-100
  onPositionChange: (newPosition: number) => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export default function SwipeSlider({
  position,
  onPositionChange,
  containerRef,
}: SwipeSliderProps) {
  const [isDragging, setIsDragging] = useState(false);

  // Mouse event handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = (x / rect.width) * 100;
      onPositionChange(Math.max(0, Math.min(100, percentage)));
    },
    [isDragging, containerRef, onPositionChange]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Touch event handlers for mobile
  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isDragging || !containerRef.current) return;
      const touch = e.touches[0];
      const rect = containerRef.current.getBoundingClientRect();
      const x = touch.clientX - rect.left;
      const percentage = (x / rect.width) * 100;
      onPositionChange(Math.max(0, Math.min(100, percentage)));
    },
    [isDragging, containerRef, onPositionChange]
  );

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  // Effect for global event listeners
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('touchmove', handleTouchMove);
      document.addEventListener('touchend', handleMouseUp);

      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.removeEventListener('touchmove', handleTouchMove);
        document.removeEventListener('touchend', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove]);

  return (
    <div
      style={{
        position: 'absolute',
        left: `${position}%`,
        top: 0,
        bottom: 0,
        width: 4,
        backgroundColor: 'white',
        cursor: 'ew-resize',
        zIndex: 1000,
        boxShadow: '0 0 10px rgba(0,0,0,0.5)',
      }}
      onMouseDown={handleMouseDown}
      onTouchStart={handleTouchStart}
    >
      {/* Slider handle/grip */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 40,
          height: 40,
          backgroundColor: 'white',
          borderRadius: '50%',
          border: '3px solid #ee6c4d',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        }}
      >
        {/* Left/Right arrows icon */}
        <svg width="20" height="20" viewBox="0 0 20 20">
          <path d="M7 10l-4-4v8l4-4zm6 0l4-4v8l-4-4z" fill="#ee6c4d" />
        </svg>
      </div>
    </div>
  );
}
