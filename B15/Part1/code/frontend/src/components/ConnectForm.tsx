import { useFormContext } from 'react-hook-form';

export default function ConnectForm({ children }) {
  const methods = useFormContext();

  return children({ ...methods });
}
