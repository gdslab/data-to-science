import { useState, useEffect } from 'react';
import { FaRuler } from 'react-icons/fa6';

import MeasureTerraDrawControl from './MeasureTerraDrawControl';

type MeasureUnitType = 'metric' | 'imperial';

export default function MeasureToolsToggle() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);
  const [unitType, setUnitType] = useState<MeasureUnitType>('metric');

  useEffect(() => {
    if (isExpanded) {
      setShouldRender(true);
    } else if (shouldRender) {
      // Add class to body to trigger animation
      document.body.classList.add('measure-tools-closing');
      // Wait for animation to complete before unmounting
      const timer = setTimeout(() => {
        setShouldRender(false);
        document.body.classList.remove('measure-tools-closing');
      }, 300); // Match animation duration
      return () => {
        clearTimeout(timer);
        document.body.classList.remove('measure-tools-closing');
      };
    }
  }, [isExpanded, shouldRender]);

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const toggleUnitType = () => {
    setUnitType(unitType === 'metric' ? 'imperial' : 'metric');
  };

  return (
    <>
      <div className="absolute bottom-9 right-2 m-2.5 flex flex-col items-end gap-2 z-10 pointer-events-none">
        {isExpanded && (
          <div className="bg-white rounded-md shadow-md px-3 py-2 flex items-center gap-2 relative z-10 pointer-events-auto">
            <span className="text-xs text-slate-500">Units:</span>
            <button
              type="button"
              className="h-6 px-2 bg-slate-100 rounded-sm border border-slate-300 text-xs font-medium text-slate-600 hover:text-slate-800 hover:bg-slate-200 focus:outline-hidden focus:ring-2 focus:ring-accent2 transition-colors"
              onClick={toggleUnitType}
              title={`Switch to ${
                unitType === 'metric' ? 'Imperial' : 'Metric'
              } units`}
            >
              {unitType === 'metric' ? 'Metric' : 'Imperial'}
            </button>
          </div>
        )}
        <div className="flex items-end gap-2">
          {shouldRender && <MeasureTerraDrawControl unitType={unitType} />}
          <button
            type="button"
            className="h-12 w-12 bg-white rounded-md shadow-md flex items-center justify-center text-slate-600 hover:text-slate-800 hover:bg-slate-50 focus:outline-hidden focus:ring-2 focus:ring-accent2 transition-colors relative z-10 pointer-events-auto"
            aria-label={
              isExpanded ? 'Hide measurement tools' : 'Show measurement tools'
            }
            aria-expanded={isExpanded}
            title="Measurement Tools"
            onClick={toggleExpanded}
          >
            <FaRuler className="h-5 w-5" />
          </button>
        </div>
      </div>
    </>
  );
}
