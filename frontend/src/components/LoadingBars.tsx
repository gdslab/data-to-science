import clsx from 'clsx';
import { useState } from 'react';
import { useInterval } from './hooks';

export default function LoadingBars() {
  const [animateFrame, setAnimateFrame] = useState(0);
  const [direction, setDirection] = useState(0);

  useInterval(() => {
    if (direction === 0) {
      // left-to-right
      if (animateFrame < 7) {
        setAnimateFrame(animateFrame + 1);
      } else {
        setDirection(1);
        setAnimateFrame(6);
      }
    } else {
      // right-to-left
      if (animateFrame > 0) {
        setAnimateFrame(animateFrame - 1);
      } else {
        setDirection(0);
        setAnimateFrame(1);
      }
    }
  }, 350);

  return (
    <div className="w-48 flex items-center justify-between gap-1 p-1.5">
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 0,
          'bg-white': animateFrame !== 0,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 1,
          'bg-white': animateFrame !== 1,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 2,
          'bg-white': animateFrame !== 2,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 3,
          'bg-white': animateFrame !== 3,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 4,
          'bg-white': animateFrame !== 4,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 5,
          'bg-white': animateFrame !== 5,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 6,
          'bg-white': animateFrame !== 6,
        })}
      ></div>
      <div
        className={clsx('h-8 w-4 rounded-xs transition ease-in-out duration-300', {
          'bg-accent2 scale-125': animateFrame === 7,
          'bg-white': animateFrame !== 7,
        })}
      ></div>
    </div>
  );
}
