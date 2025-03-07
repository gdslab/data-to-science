import { confirmable, ConfirmDialog, createConfirmation } from 'react-confirm';
import {
  Description,
  Dialog,
  DialogPanel,
  DialogTitle,
} from '@headlessui/react';

interface Props {
  confirmation?: string;
  description?: string;
  title?: string;
}

const ConfirmationDialog: ConfirmDialog<Props, boolean> = ({
  show,
  proceed,
  description,
  confirmation,
  title,
}) => (
  <Dialog open={show} onClose={() => proceed(false)} className="relative z-50">
    <div className="fixed inset-0 flex w-screen items-center justify-center p-4">
      <DialogPanel className="max-w-lg space-y-4 border bg-white p-12">
        <DialogTitle className="font-bold">{title}</DialogTitle>
        <Description>{description}</Description>
        <p>{confirmation}</p>
        <div className="w-full flex justify-between gap-4">
          <button
            className="px-4 py-2 w-1/3 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition"
            onClick={() => proceed(false)}
          >
            CANCEL
          </button>
          <button
            className="px-4 py-2 w-1/3 text-white bg-blue-600 rounded-md hover:bg-blue-700 transition"
            onClick={() => proceed(true)}
          >
            OK
          </button>
        </div>
      </DialogPanel>
    </div>
  </Dialog>
);

export const confirm = createConfirmation(confirmable(ConfirmationDialog));
