import * as Yup from 'yup';

export const loginValidationSchema = Yup.object({
  email: Yup.string().email('Invalid email address').required('Required'),
  password: Yup.string().required('Required'),
});

export const registrationValidationSchema = Yup.object({
  firstName: Yup.string().max(50, 'Must be 50 characters or less').required('Required'),
  lastName: Yup.string().max(50, 'Must be 50 characters or less').required('Required'),
  email: Yup.string().email('Invalid email address').required('Required'),
  password: Yup.string().required('Required'),
  passwordRetype: Yup.string()
    .oneOf([Yup.ref('password'), ''], 'Passwords do not match')
    .required('Required'),
});
