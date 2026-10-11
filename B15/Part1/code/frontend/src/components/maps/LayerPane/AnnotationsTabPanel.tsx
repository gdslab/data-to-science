import { useCallback, useContext, useState } from 'react';
import {
  FaChevronDown,
  FaChevronRight,
  FaDownload,
  FaDrawPolygon,
  FaPaperclip,
  FaPenToSquare,
  FaTrashCan,
  FaXmark,
} from 'react-icons/fa6';

import api from '../../../api';
import AuthContext from '../../../AuthContext';
import Checkbox from '../../Checkbox';
import AnnotationAttachmentUpload from './AnnotationAttachmentUpload';
import AttachmentViewerModal from '../AttachmentViewerModal';
import AnnotationEditModal from '../AnnotationEditModal';
import AnnotationsPane from './AnnotationsPane';
import OpacitySlider from '../OpacitySlider';
import { formatArea, formatLength, getGeomTypeIcon } from './utils';
import {
  Annotation,
  AnnotationAttachment,
  useAnnotationContext,
  defaultAnnotationStyle,
} from '../contexts/AnnotationContext';
import { useMapContext } from '../MapContext';

function getGeometryLabel(geomType: string | undefined): string {
  switch (geomType) {
    case 'Point':
      return 'Point';
    case 'LineString':
      return 'Line';
    case 'Polygon':
      return 'Polygon';
    default:
      return geomType || 'Unknown';
  }
}

export default function AnnotationsTabPanel() {
  const {
    annotations,
    checkedIds,
    styles,
    loading,
    error,
    activate,
    setEditingAnnotation,
    setHoveredAnnotationId,
    toggleChecked,
    updateStyle,
    refetch,
  } = useAnnotationContext();
  const { activeProject, activeDataProduct } = useMapContext();
  const { user } = useContext(AuthContext);
  const projectRole = activeProject?.role;
  const [editOpen, setEditOpen] = useState(false);
  const [editModalAnnotation, setEditModalAnnotation] =
    useState<Annotation | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerAttachment, setViewerAttachment] =
    useState<AnnotationAttachment | null>(null);

  const toggleExpanded = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleEdit = (annotation: Annotation) => {
    setEditModalAnnotation(annotation);
    setEditOpen(true);
  };

  const handleRedrawGeometry = (annotation: Annotation) => {
    setEditingAnnotation(annotation);
    activate();
  };

  const handleUploadComplete = useCallback(
    (annotationId: string) => {
      setProcessingIds((prev) => new Set(prev).add(annotationId));
      // Delay refetch to allow the backend post-finish hook to complete
      setTimeout(() => {
        refetch();
        setProcessingIds((prev) => {
          const next = new Set(prev);
          next.delete(annotationId);
          return next;
        });
      }, 2000);
    },
    [refetch],
  );

  const handleDeleteAttachment = useCallback(
    async (attachment: AnnotationAttachment) => {
      if (!activeProject || !activeDataProduct) return;
      try {
        await api.delete(
          `/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${attachment.annotation_id}/attachments/${attachment.id}`,
        );
        refetch();
      } catch (err) {
        console.error('Failed to delete attachment', err);
      }
    },
    [activeProject, activeDataProduct, refetch],
  );

  const canEdit = projectRole === 'owner' || projectRole === 'manager';

  const canDelete = useCallback(
    (annotation: Annotation) => {
      const isCreator = user?.id === annotation.created_by?.id;
      const isProjectOwner = projectRole === 'owner';
      if (annotation.visibility === 'OWNER') return isCreator;
      return isCreator || isProjectOwner;
    },
    [user, projectRole],
  );

  const handleDeleteAnnotation = useCallback(
    async (annotation: Annotation) => {
      if (!activeProject || !activeDataProduct) return;
      if (!window.confirm('Are you sure you want to delete this annotation?'))
        return;
      try {
        await api.delete(
          `/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${annotation.id}`,
        );
        refetch();
      } catch (err) {
        console.error('Failed to delete annotation', err);
      }
    },
    [activeProject, activeDataProduct, refetch],
  );

  const handleRemoveTag = useCallback(
    async (annotation: Annotation, tagToRemove: string) => {
      if (!activeProject || !activeDataProduct) return;
      const remainingTags = annotation.tag_rows
        .map((tr) => tr.tag?.name)
        .filter((t): t is string => Boolean(t) && t !== tagToRemove);
      try {
        await api.put(
          `/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${annotation.id}`,
          { tags: remainingTags },
        );
        refetch();
      } catch (err) {
        console.error('Failed to remove tag', err);
      }
    },
    [activeProject, activeDataProduct, refetch],
  );

  return (
    <>
      <div className="h-full flex flex-col gap-3">
        <AnnotationsPane />
        <div className="flex-1 overflow-y-auto pb-16">
          {loading && (
            <p className="text-sm text-slate-500 italic p-2">
              Loading annotations...
            </p>
          )}
          {error && <p className="text-sm text-red-600 p-2">{error}</p>}
          {!loading && !error && annotations.length === 0 && (
            <p className="text-sm text-slate-500 italic p-2">
              No annotations for this data product.
            </p>
          )}
          {!loading && !error && annotations.length > 0 && (
            <div className="flex flex-col gap-3">
              {annotations.map((annotation) => {
                const checked = checkedIds.has(annotation.id);
                const geomType = annotation.geom.geometry?.type;
                const geomLabel = getGeometryLabel(geomType);
                const isPolygon = geomType === 'Polygon';
                const style = styles[annotation.id] || defaultAnnotationStyle;
                const tags = annotation.tag_rows
                  .map((tr) => tr.tag?.name)
                  .filter((t): t is string => Boolean(t));

                return (
                  <div
                    key={annotation.id}
                    className="flex flex-col p-2 rounded-sm bg-slate-50"
                    onMouseEnter={() => setHoveredAnnotationId(annotation.id)}
                    onMouseLeave={() => setHoveredAnnotationId(null)}
                  >
                    {/* Description and checkbox */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <div className="pt-0.5">
                          <Checkbox
                            id={`annotation-${annotation.id}`}
                            checked={checked}
                            onChange={() => toggleChecked(annotation.id)}
                          />
                        </div>
                        <label
                          htmlFor={`annotation-${annotation.id}`}
                          className="text-sm font-medium flex-1 min-w-0 cursor-pointer"
                          title={annotation.description}
                        >
                          <span className="line-clamp-2">
                            {annotation.description}
                          </span>
                        </label>
                      </div>
                      {canEdit && (
                        <button
                          type="button"
                          onClick={() => handleEdit(annotation)}
                          className="p-1 text-slate-400 hover:text-slate-600 shrink-0"
                          title="Edit annotation"
                        >
                          <FaPenToSquare className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {canEdit && (
                        <button
                          type="button"
                          onClick={() => handleRedrawGeometry(annotation)}
                          className="p-1 text-slate-400 hover:text-slate-600 shrink-0"
                          title="Redraw geometry"
                        >
                          <FaDrawPolygon className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {canDelete(annotation) && (
                        <button
                          type="button"
                          onClick={() => handleDeleteAnnotation(annotation)}
                          className="p-1 text-slate-400 hover:text-red-500 shrink-0"
                          title="Delete annotation"
                        >
                          <FaTrashCan className="h-3.5 w-3.5" />
                        </button>
                      )}
                      {/* Color controls */}
                      {isPolygon ? (
                        <div className="flex items-center gap-2">
                          <div className="flex flex-col items-center">
                            <span className="text-xs text-slate-500 mb-0.5">
                              Fill
                            </span>
                            <input
                              type="color"
                              value={style.fill}
                              disabled={!checked}
                              onChange={(e) =>
                                updateStyle(
                                  annotation.id,
                                  'fill',
                                  e.target.value,
                                )
                              }
                              className="h-7 w-10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                            />
                          </div>
                          <div className="flex flex-col items-center">
                            <span className="text-xs text-slate-500 mb-0.5">
                              Border
                            </span>
                            <input
                              type="color"
                              value={style.color}
                              disabled={!checked}
                              onChange={(e) =>
                                updateStyle(
                                  annotation.id,
                                  'color',
                                  e.target.value,
                                )
                              }
                              className="h-7 w-10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                            />
                          </div>
                        </div>
                      ) : (
                        <input
                          type="color"
                          value={style.color}
                          disabled={!checked}
                          onChange={(e) =>
                            updateStyle(annotation.id, 'color', e.target.value)
                          }
                          className="h-7 w-10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                        />
                      )}
                    </div>

                    {/* Geometry type and measurement */}
                    <div className="flex items-center gap-1.5 pl-6 pt-1">
                      <img
                        src={getGeomTypeIcon(geomLabel)}
                        alt=""
                        className="h-3 w-3"
                      />
                      <span className="text-xs font-light text-slate-500">
                        {geomLabel}
                        {geomType === 'LineString' &&
                          ` · ${formatLength(annotation.geom)}`}
                        {geomType === 'Polygon' &&
                          ` · ${formatArea(annotation.geom)}`}
                      </span>
                    </div>

                    {/* Tags */}
                    {tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 pl-6 pt-1.5">
                        {tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-0.5 text-xs bg-slate-200 text-slate-600 rounded-full px-2 py-0.5"
                          >
                            {tag}
                            {canEdit && (
                              <button
                                type="button"
                                onClick={() => handleRemoveTag(annotation, tag)}
                                className="text-slate-400 hover:text-red-500"
                                title={`Remove tag "${tag}"`}
                              >
                                <FaXmark className="h-3 w-3" />
                              </button>
                            )}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Opacity slider */}
                    <div className="pl-1 pr-4 py-2">
                      <OpacitySlider
                        disabled={!checked}
                        currentValue={style.opacity}
                        onChange={(_, newValue: number | number[]) => {
                          if (typeof newValue === 'number') {
                            updateStyle(annotation.id, 'opacity', newValue);
                          }
                        }}
                      />
                    </div>

                    {/* Attachments */}
                    <div className="pl-2 pr-2">
                      <button
                        type="button"
                        onClick={() => toggleExpanded(annotation.id)}
                        className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
                      >
                        {expandedIds.has(annotation.id) ? (
                          <FaChevronDown className="h-3 w-3" />
                        ) : (
                          <FaChevronRight className="h-3 w-3" />
                        )}
                        <FaPaperclip className="h-3 w-3" />
                        <span>
                          Attachments
                          {annotation.attachments?.length > 0 &&
                            ` (${annotation.attachments.length})`}
                        </span>
                      </button>

                      {expandedIds.has(annotation.id) && (
                        <div className="mt-2 flex flex-col gap-2">
                          {annotation.attachments?.length > 0 && (
                            <div className="flex gap-2 overflow-x-auto">
                              {annotation.attachments.map((att) => (
                                <div
                                  key={att.id}
                                  className="relative group rounded overflow-hidden bg-slate-200 cursor-pointer shrink-0 w-24"
                                  onClick={() => {
                                    setViewerAttachment(att);
                                    setViewerOpen(true);
                                  }}
                                >
                                  {att.content_type.startsWith('video/') ? (
                                    <video
                                      src={att.filepath}
                                      className="h-20 w-full object-cover"
                                      muted
                                      preload="metadata"
                                    />
                                  ) : (
                                    <img
                                      src={att.filepath}
                                      alt={att.original_filename}
                                      className="h-20 w-full object-cover"
                                    />
                                  )}
                                  <div className="absolute top-0.5 right-0.5 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <a
                                      href={`${
                                        import.meta.env.VITE_API_V1_STR
                                      }/projects/${activeProject?.id}/flights/${activeDataProduct?.flight_id}/data_products/${activeDataProduct?.id}/annotations/${att.annotation_id}/attachments/${att.id}/download`}
                                      download
                                      onClick={(e) => e.stopPropagation()}
                                      className="p-0.5 bg-slate-600 text-white rounded"
                                      title="Download attachment"
                                    >
                                      <FaDownload className="h-3 w-3" />
                                    </a>
                                    {(canEdit ||
                                      user?.id ===
                                        annotation.created_by?.id) && (
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleDeleteAttachment(att);
                                        }}
                                        className="p-0.5 bg-red-500 text-white rounded"
                                        title="Delete attachment"
                                      >
                                        <FaTrashCan className="h-3 w-3" />
                                      </button>
                                    )}
                                  </div>
                                  <div className="absolute bottom-0 left-0 right-0 bg-black/50 px-1 py-0.5">
                                    <span className="text-[10px] text-white truncate block">
                                      {att.original_filename}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {processingIds.has(annotation.id) && (
                            <p className="text-xs text-amber-600 italic px-1">
                              Processing upload...
                            </p>
                          )}

                          {activeProject &&
                            activeDataProduct &&
                            (canEdit ||
                              user?.id === annotation.created_by?.id) && (
                              <AnnotationAttachmentUpload
                                projectId={activeProject.id}
                                flightId={activeDataProduct.flight_id}
                                dataProductId={activeDataProduct.id}
                                annotationId={annotation.id}
                                onUploadComplete={() =>
                                  handleUploadComplete(annotation.id)
                                }
                              />
                            )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      {editModalAnnotation && activeProject && activeDataProduct && (
        <AnnotationEditModal
          open={editOpen}
          setOpen={setEditOpen}
          annotation={editModalAnnotation}
          projectId={activeProject.id}
          flightId={activeDataProduct.flight_id}
          dataProductId={activeDataProduct.id}
          onSuccess={() => {
            setEditOpen(false);
            setEditModalAnnotation(null);
            refetch();
          }}
        />
      )}
      <AttachmentViewerModal
        open={viewerOpen}
        setOpen={setViewerOpen}
        attachment={viewerAttachment}
        downloadUrl={
          viewerAttachment && activeProject && activeDataProduct
            ? `${
                import.meta.env.VITE_API_V1_STR
              }/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${viewerAttachment.annotation_id}/attachments/${viewerAttachment.id}/download`
            : null
        }
      />
    </>
  );
}
