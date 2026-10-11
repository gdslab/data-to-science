import Modal from '../Modal';
import { AnnotationAttachment } from './contexts/AnnotationContext';

interface AttachmentViewerModalProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  attachment: AnnotationAttachment | null;
  downloadUrl: string | null;
}

export default function AttachmentViewerModal({
  open,
  setOpen,
  attachment,
  downloadUrl,
}: AttachmentViewerModalProps) {
  return (
    <Modal open={open} setOpen={setOpen}>
      {attachment && (
        <div className="flex flex-col items-center p-4">
          {attachment.content_type.startsWith('video/') ? (
            <video
              key={attachment.id}
              controls
              preload="auto"
              playsInline
              className="w-full max-h-[80vh] aspect-video bg-black"
            >
              <source
                src={downloadUrl || attachment.filepath}
                type={attachment.content_type}
              />
            </video>
          ) : (
            <img
              src={attachment.filepath}
              alt={attachment.original_filename}
              className="w-full max-h-[80vh] object-contain"
            />
          )}
          <p className="mt-2 text-sm text-slate-500 truncate max-w-full">
            {attachment.original_filename}
          </p>
        </div>
      )}
    </Modal>
  );
}
