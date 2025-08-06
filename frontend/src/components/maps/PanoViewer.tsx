import { useEffect, useRef } from 'react';

declare global {
  interface Window {
    pannellum: any;
  }
}

interface PanoViewerProps {
  imageUrl: string;
}

export default function PanoViewer({ imageUrl }: PanoViewerProps) {
  const viewerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!viewerRef.current) return;

    // Load script dynamically
    const script = document.createElement('script');
    script.src = '/lib/pannellum/pannellum.js';
    script.async = true;
    script.onload = () => {
      if (window.pannellum) {
        window.pannellum.viewer(viewerRef.current, {
          type: 'equirectangular',
          panorama: imageUrl,
          autoLoad: true,
        });
      }
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [imageUrl]);

  return <div ref={viewerRef} style={{ width: '100%', height: '100%' }} />;
}
