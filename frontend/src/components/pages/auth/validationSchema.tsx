import * as Yup from 'yup';
import YupPassword from 'yup-password';

YupPassword(Yup);

const nameRules = Yup.object({
  firstName: Yup.string()
    .max(64, 'First name cannot be more than 64 characters')
    .required('Enter your first name'),
  lastName: Yup.string()
    .max(64, 'Last name cannot be more than 64 characters')
    .required('Enter your last name'),
});

const passwordRules = Yup.string()
  .min(10, 'Use 10 or more characters for your password')
  .max(128, 'Password cannot be more than 128 characters')
  .minLowercase(1, 'Password must contain at least one lowercase character')
  .minUppercase(1, 'Password must contain at least one uppercase character')
  .minNumbers(1, 'Password must contain at least one number')
  .minRepeating(2, 'Password cannot have more than two repeating characters in a row')
  .required('Enter your password');

export const loginValidationSchema = Yup.object({
  email: Yup.string()
    .max(254, 'Email address cannot be more than 254 characters')
    .email('Invalid email address')
    .required('Enter your email'),
  password: Yup.string().required('Enter your password'),
});

export const registrationValidationSchema = nameRules.concat(
  Yup.object({
    email: Yup.string().email('Invalid email address').required('Enter your email'),
    password: passwordRules,
    passwordRetype: Yup.string()
      .oneOf([Yup.ref('password'), ''], 'Passwords do not match')
      .required('Retype your password'),
  })
);

export const passwordChangeValidationSchema = Yup.object({
  passwordCurrent: Yup.string().required('Enter your current password'),
  passwordNew: passwordRules,
  passwordNewRetype: Yup.string()
    .oneOf([Yup.ref('passwordNew'), ''], 'Passwords do not match')
    .required('Retype your new password'),
});

export const profileValidationSchema = nameRules;
