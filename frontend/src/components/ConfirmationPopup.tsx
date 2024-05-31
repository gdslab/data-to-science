import { Button } from './Buttons';

type ConfirmationPopup = {
  confirmText: string;
  content: string;
  onConfirm: () => void;
  rejectText: string;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  title: string;
};

export function ConfirmationPopup({
  onConfirm,
  title,
  content,
  confirmText,
  rejectText,
  setOpen,
}: ConfirmationPopup) {
  return (
    <div className="rounded-lg bg-white p-8 shadow-2xl">
      <h2>{title}</h2>
      <p className="mt-2 text-sm text-gray-500">{content}</p>
      <div className="mt-8 flex justify-center gap-8">
        <div className="w-1/3">
          <Button type="button" size="sm" onClick={() => setOpen(false)}>
            {rejectText}
          </Button>
        </div>
        <div className="w-1/3">
          <Button
            type="submit"
            size="sm"
            icon="trash"
            onClick={() => {
              onConfirm();
              setOpen(false);
            }}
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
