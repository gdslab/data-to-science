import { useCallback, ChangeEvent } from 'react';

export type Mode = 'side-by-side' | 'split-screen';

export default function CompareModeControl({
  mode,
  onModeChange: onModeChangeProp,
}: {
  mode: Mode;
  onModeChange: (newMode: Mode) => void;
}) {
  const onModeChange = useCallback(
    (evt: ChangeEvent<HTMLSelectElement>) => {
      onModeChangeProp(evt.target.value as Mode);
    },
    [onModeChangeProp]
  );

  return (
    <div className="absolute bottom-2 left-32 font-semibold text-gray-600 border-2 border-gray-300 rounded-md">
      <select className="rounded-md" value={mode} onChange={onModeChange}>
        <option value="side-by-side">Side by side</option>
        <option value="split-screen">Split screen</option>
      </select>
    </div>
  );
}
