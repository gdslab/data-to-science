import { useCallback } from 'react';

export type Mode = 'side-by-side' | 'split-screen';

export default function CompareModeControl(props: {
  mode: Mode;
  onModeChange: (newMode: Mode) => void;
}) {
  const onModeChange = useCallback(
    (evt) => {
      props.onModeChange(evt.target.value as Mode);
    },
    [props.onModeChange]
  );

  return (
    <div className="absolute bottom-12 left-2.5 font-semibold text-gray-600 border-2 border-gray-300 rounded-md">
      <select className="rounded-md" value={props.mode} onChange={onModeChange}>
        <option value="side-by-side">Side by side</option>
        <option value="split-screen">Split screen</option>
      </select>
    </div>
  );
}
