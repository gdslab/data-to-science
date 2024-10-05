import * as Yup from 'yup';

const validationSchema = Yup.object({
  name: Yup.string()
    .min(1, 'Name must have at least one character')
    .max(255, 'Name cannot exceed 255 characters'),
  acquisitionDate: Yup.date().required('Required'),
  altitude: Yup.number()
    .typeError('Enter a number using only digits (0-9)')
    .positive('Must be greater than 0')
    .required('Required'),
  sideOverlap: Yup.number()
    .typeError('Enter a number using only digits (0-9)')
    .min(0, 'Cannot be lower than 0%')
    .max(100, 'Cannot be higher than 100%')
    .required('Required'),
  forwardOverlap: Yup.number()
    .typeError('Enter a number using only digits (0-9)')
    .min(0, 'Cannot be lower than 0%')
    .max(100, 'Cannot be higher than 100%')
    .required('Required'),
  sensor: Yup.string().required('Required'),
  platform: Yup.string().required('Required'),
  platformOther: Yup.string().when('platform', {
    is: (val) => val === 'Other',
    then: (schema) =>
      schema
        .min(2, 'Must be at least 2 character')
        .required('Must provide platform name'),
    otherwise: (schema) => schema.min(0),
  }),
  pilotId: Yup.string().required('Requried'),
});

export default validationSchema;
