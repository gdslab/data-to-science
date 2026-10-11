import { useMemo, useState } from 'react';
import { Popup } from 'react-map-gl/maplibre';
import centroid from '@turf/centroid';

import AttachmentViewerModal from './AttachmentViewerModal';
import {
  AnnotationAttachment,
  useAnnotationContext,
} from './contexts/AnnotationContext';
import { useMapContext } from './MapContext';

export default function AnnotationPopup() {
  const { annotations, selectedAnnotationId, setSelectedAnnotationId } =
    useAnnotationContext();
  const { activeProject, activeDataProduct } = useMapContext();
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerAttachment, setViewerAttachment] =
    useState<AnnotationAttachment | null>(null);

  const annotation = useMemo(
    () => annotations.find((a) => a.id === selectedAnnotationId) ?? null,
    [annotations, selectedAnnotationId]
  );

  const coordinates = useMemo(() => {
    if (!annotation) return null;
    const geom = annotation.geom;
    const geomType = geom.geometry?.type;
    if (geomType === 'Point') {
      const coords = (geom.geometry as GeoJSON.Point).coordinates;
      return { longitude: coords[0], latitude: coords[1] };
    }
    const center = centroid(geom);
    const coords = center.geometry.coordinates;
    return { longitude: coords[0], latitude: coords[1] };
  }, [annotation]);

  if (!annotation || !coordinates) return null;

  const tags = annotation.tag_rows
    .map((tr) => tr.tag?.name)
    .filter(Boolean);

  const downloadUrlBase =
    activeProject && activeDataProduct
      ? `${import.meta.env.VITE_API_V1_STR}/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${annotation.id}/attachments`
      : null;

  return (
    <>
      <Popup
        anchor="bottom"
        longitude={coordinates.longitude}
        latitude={coordinates.latitude}
        onClose={() => setSelectedAnnotationId(null)}
        maxWidth="320px"
      >
        <article className="p-2 flex flex-col gap-2">
          <p className="text-sm font-medium">{annotation.description}</p>

          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="text-xs bg-slate-200 text-slate-600 rounded-full px-2 py-0.5"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}

          {annotation.attachments?.length > 0 && (
            <div className="flex gap-1.5 overflow-x-auto">
              {annotation.attachments.map((att) => (
                <div
                  key={att.id}
                  className="relative rounded overflow-hidden bg-slate-200 cursor-pointer shrink-0 w-24"
                  onClick={() => {
                    setViewerAttachment(att);
                    setViewerOpen(true);
                  }}
                >
                  {att.content_type.startsWith('video/') ? (
                    <video
                      src={att.filepath}
                      className="w-full h-16 object-cover"
                      muted
                      preload="metadata"
                    />
                  ) : (
                    <img
                      src={att.filepath}
                      alt={att.original_filename}
                      className="w-full h-16 object-cover"
                    />
                  )}
                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 px-1 py-0.5">
                    <span className="text-[10px] text-white truncate block">
                      {att.original_filename}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </Popup>
      <AttachmentViewerModal
        open={viewerOpen}
        setOpen={setViewerOpen}
        attachment={viewerAttachment}
        downloadUrl={
          viewerAttachment && downloadUrlBase
            ? `${downloadUrlBase}/${viewerAttachment.id}/download`
            : null
        }
      />
    </>
  );
}
