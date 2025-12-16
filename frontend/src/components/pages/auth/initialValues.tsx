export type LoginFormData = {
  email: string;
  password: string;
};

export const loginInitialValues = {
  email: '',
  password: '',
};

export type RegistrationFormData = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  passwordRetype: string;
  registrationIntent?: string;
};

export const registrationInitialValues = {
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  passwordRetype: '',
  registrationIntent: '',
};

export type RecoveryFormData = {
  email: string;
};

export const recoveryInitialValues = {
  email: '',
};

export type ResetFormData = {
  password: string;
  passwordRetype: string;
};

export const resetInitialValues = { password: '', passwordRetype: '' };
