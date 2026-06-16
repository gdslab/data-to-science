import { FaRegEye, FaRegThumbsUp, FaThumbsUp } from 'react-icons/fa6';

import { formatCount } from '../../utils/formatCount';

export interface Engagement {
  likeCount: number;
  viewCount: number;
  likedByMe: boolean;
}

interface EngagementInlineProps {
  engagement: Engagement;
  onToggleLike: () => void;
  size?: 'sm' | 'md'; // md bumps text-sm -> text-[15px], icons 16 -> 20
  interactive?: boolean; // when false, the like renders as a read-only count
  disabled?: boolean; // interactive button rendered but not yet clickable
  vertical?: boolean; // stack like over views (drops the dot separator)
  className?: string;
}

export default function EngagementInline({
  engagement,
  onToggleLike,
  size = 'sm',
  interactive = true,
  disabled = false,
  vertical = false,
  className = '',
}: EngagementInlineProps) {
  const { likeCount, viewCount, likedByMe } = engagement;

  const textSize = size === 'md' ? 'text-[15px]' : 'text-sm';
  const iconSize = size === 'md' ? 14 : 12;

  const likeClasses = `inline-flex items-center gap-1.5 ${textSize} ${
    likedByMe ? 'text-accent2' : 'text-slate-600'
  }`;

  const likeContent = (
    <>
      {likedByMe ? (
        <FaThumbsUp size={iconSize} />
      ) : (
        <FaRegThumbsUp size={iconSize} />
      )}
      <span className={`font-semibold ${likedByMe ? '' : 'text-slate-800'}`}>
        {formatCount(likeCount)}
      </span>
      <span>likes</span>
    </>
  );

  return (
    <div
      className={`inline-flex items-center whitespace-nowrap ${
        vertical ? 'flex-col gap-1.5' : 'gap-3'
      } ${className}`}
    >
      {interactive ? (
        <button
          type="button"
          onClick={(e) => {
            // Don't let a like bubble up to a clickable parent card.
            e.stopPropagation();
            onToggleLike();
          }}
          disabled={disabled}
          aria-pressed={likedByMe}
          aria-label={
            likedByMe ? 'Unlike this data product' : 'Like this data product'
          }
          title={
            disabled ? 'Activate this data product to like it' : undefined
          }
          className={`${likeClasses} disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {likeContent}
        </button>
      ) : (
        <span className={likeClasses}>{likeContent}</span>
      )}

      {!vertical && (
        <span
          className="h-1 w-1 rounded-full bg-slate-300"
          aria-hidden="true"
        />
      )}

      <span
        className={`inline-flex items-center gap-1.5 ${textSize} text-slate-400`}
      >
        <FaRegEye size={iconSize} />
        <span className="font-semibold text-slate-500">
          {formatCount(viewCount)}
        </span>
        <span>views</span>
      </span>
    </div>
  );
}
