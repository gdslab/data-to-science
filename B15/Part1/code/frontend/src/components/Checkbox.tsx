import React from 'react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id: string;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export default function Checkbox({
  id,
  checked,
  onChange,
  className = '',
  ...rest
}: CheckboxProps) {
  return (
    <input
      type="checkbox"
      id={id}
      checked={checked}
      onChange={onChange}
      className={
        'rounded-sm cursor-pointer border-slate-300 ' +
        'focus:ring-0 focus-visible:ring-accent3 focus-visible:ring-2 ' +
        'checked:bg-accent2 checked:border-slate-600 ' +
        className
      }
      {...rest}
    />
  );
}
