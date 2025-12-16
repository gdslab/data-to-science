import * as Yup from 'yup';
import YupPassword from 'yup-password';

YupPassword(Yup);

const nameRules = Yup.object({
  firstName: Yup.string()
    .min(2, 'First name must have at least 2 characters')
    .max(64, 'First name cannot be more than 64 characters')
    .required('Enter your first name'),
  lastName: Yup.string()
    .min(2, 'Last name must have at least 2 characters')
    .max(64, 'Last name cannot be more than 64 characters')
    .required('Enter your last name'),
});

const passwordRules = Yup.string()
  .min(12, 'Use 12 or more characters for your password')
  .max(128, 'Password cannot be more than 128 characters')
  .minRepeating(
    2,
    'Password cannot have more than two repeating characters in a row'
  )
  .required('Enter your password');

const passwordRetypeRules = (passwordField: string) =>
  Yup.string()
    .oneOf([Yup.ref(passwordField), ''], 'Passwords do not match')
    .required('Retype your password');

export const loginValidationSchema = Yup.object({
  email: Yup.string()
    .max(254, 'Email address cannot be more than 254 characters')
    .email('Invalid email address')
    .required('Enter your email'),
  password: Yup.string().required('Enter your password'),
});

export const registrationValidationSchema = nameRules.concat(
  Yup.object({
    email: Yup.string()
      .email('Invalid email address')
      .required('Enter your email'),
    password: passwordRules,
    passwordRetype: passwordRetypeRules('password'),
    registrationIntent: Yup.string()
      .transform((value) => value || undefined)
      .min(20, 'Minimum 20 characters')
      .max(500, 'Maximum 500 characters')
      .optional(),
  })
);

export const passwordChangeValidationSchema = Yup.object({
  passwordCurrent: Yup.string().required('Enter your current password'),
  passwordNew: passwordRules,
  passwordNewRetype: passwordRetypeRules('passwordNew'),
});

export const profileValidationSchema = nameRules;

export const recoveryValidationSchema = Yup.object({
  email: Yup.string()
    .email('Invalid email address')
    .required('Enter your email'),
});

export const resetValidationSchema = Yup.object({
  password: passwordRules,
  passwordRetype: passwordRetypeRules('password'),
});
