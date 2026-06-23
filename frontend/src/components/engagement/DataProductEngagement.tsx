import { DataProduct } from '../pages/workspace/projects/Project';
import EngagementInline from './EngagementInline';
import { useDataProductLike } from './useDataProductLike';

interface DataProductEngagementProps {
  dataProduct: DataProduct;
  projectId?: string;
  flightId?: string;
  interactive?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md';
  vertical?: boolean;
  className?: string;
}

// Connects a data product to the shared EngagementInline display. Used where a
// hook can't be called inline (e.g. inside a .map() in the table) and to keep
// wiring DRY across surfaces.
export default function DataProductEngagement({
  dataProduct,
  projectId,
  flightId,
  interactive = true,
  disabled = false,
  size = 'sm',
  vertical = false,
  className,
}: DataProductEngagementProps) {
  const { engagement, toggleLike } = useDataProductLike(
    dataProduct,
    projectId,
    flightId
  );

  return (
    <EngagementInline
      engagement={engagement}
      onToggleLike={toggleLike}
      size={size}
      interactive={interactive}
      disabled={disabled}
      vertical={vertical}
      className={className}
    />
  );
}
