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
      <div className="mt-8 flex justify-between">
        <Button type="button" size="sm" onClick={() => setOpen(false)}>
          {rejectText}
        </Button>
        <Button type="submit" size="sm" icon="trash" onClick={() => action()}>
          {confirmText}
        </Button>
      </div>
    </div>
  );
}
