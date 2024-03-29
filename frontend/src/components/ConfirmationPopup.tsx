import { Button } from './Buttons';

export function ConfirmationPopup({
  action,
  title,
  content,
  confirmText,
  rejectText,
  setOpen,
}: {
  action: () => void;
  title: string;
  content: string;
  confirmText: string;
  rejectText: string;
  setOpen;
}) {
  return (
    <div className="rounded-lg bg-white p-8 shadow-2xl">
      <h2>{title}</h2>
      <p className="mt-2 text-sm text-gray-500">{content}</p>
      <div className="mt-8 flex justify-center gap-8">
        <div className="w-48">
          <Button type="button" size="sm" onClick={() => setOpen(false)}>
            {rejectText}
          </Button>
        </div>
        <div className="w-48">
          <Button type="submit" size="sm" icon="trash" onClick={() => action()}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
