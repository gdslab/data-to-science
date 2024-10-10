import axios, { isAxiosError } from 'axios';
import clsx from 'clsx';
import { useContext, useState } from 'react';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import Alert, { Status } from './Alert';
import { Button } from './Buttons';
import Card from './Card';
import { InputField, SelectField, styles, TextAreaField } from './FormFields';
import Modal from './Modal';
import AuthContext from '../AuthContext';

type ContactFormData = {
  topic: string;
  subject: string;
  message: string;
};

const defaultValues = {
  topic: '',
  subject: '',
  message: '',
};

const validationSchema = Yup.object({
  topic: Yup.string().required('Select a topic'),
  subject: Yup.string()
    .min(5, 'Subject must have at least 5 characters')
    .max(60, 'Subject cannot be more than 60 characters')
    .required('Enter a subject'),
  message: Yup.string()
    .min(30, 'Message must have at least 30 characters')
    .max(1000, 'Message cannot be more than 1,000 characters')
    .required('Enter a message'),
});

const TOPIC_OPTIONS = [
  { label: 'Select a topic', value: '' },
  { label: 'Bug Report', value: 'bug' },
  { label: 'Feature Request', value: 'feature' },
  { label: 'General Feedback', value: 'feedback' },
  { label: 'Other', value: 'other' },
];

function ContactForm() {
  const [status, setStatus] = useState<Status | null>(null);

  const { user } = useContext(AuthContext);

  const methods = useForm<ContactFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
    watch,
  } = methods;

  const onSubmit: SubmitHandler<ContactFormData> = async (values) => {
    setStatus(null);
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_V1_STR}/contact`, {
        ...values,
      });
      if (response) {
        setStatus({ type: 'success', msg: 'Message sent' });
      } else {
        setStatus({
          type: 'success',
          msg: 'Unable to send message',
        });
      }
    } catch (err) {
      if (isAxiosError(err)) {
        setStatus({ type: 'error', msg: err.response?.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to send message' });
      }
    }
  };

  const currentSubject = watch('subject');
  const currentMessage = watch('message');

  return (
    <Card>
      <h1>Contact Us</h1>
      <FormProvider {...methods}>
        <form className="grid grid-flow-row gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <SelectField label="Topic" name="topic" options={TOPIC_OPTIONS} />
          </div>
          <div className="border-b-2 border-slate-200"></div>
          <div>
            {user && (
              <span
                className={styles.label}
              >{`From: ${user.first_name} <${user.email}>`}</span>
            )}
            <InputField
              label="Subject"
              name="subject"
              placeholder="Briefly describe your inquiry"
            />
            <span
              className={clsx('text-sm text-gray-400', {
                'text-red-500': currentSubject.length > 60,
              })}
            >
              {currentSubject.length.toLocaleString()} of 60 characters
            </span>
          </div>
          <div>
            <span className={styles.label}>{`To: D2S Support <support@d2s.org>`}</span>
            <TextAreaField
              label="Message"
              name="message"
              placeholder="Tell us more about your inquiry..."
            />
            <span
              className={clsx('text-sm text-gray-400', {
                'text-red-500': currentMessage.length > 1000,
              })}
            >
              {currentMessage.length.toLocaleString()} of 1,000 characters
            </span>
          </div>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending...' : 'Send'}
          </Button>
          {status && status.type && status.msg && (
            <Alert alertType={status.type}>{status.msg}</Alert>
          )}
        </form>
      </FormProvider>
    </Card>
  );
}

export default function ContactFormModal() {
  const [open, setOpen] = useState(false);

  return (
    <div>
      <button
        className="rounded-md px-3 py-2 text-md text-white visited:text-white hover:[text-shadow:_0px_8px_16px_rgb(0_0_0_/_70%)]"
        onClick={() => setOpen(true)}
      >
        CONTACT US
      </button>
      <Modal open={open} setOpen={setOpen}>
        <ContactForm />
      </Modal>
    </div>
  );
}
