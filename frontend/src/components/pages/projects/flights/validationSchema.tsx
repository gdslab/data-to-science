import * as Yup from 'yup';

const validationSchema = Yup.object({
  acquisitionDate: Yup.date().required('Required'),
  altitude: Yup.number().positive('Must be greater than 0').required('Required'),
  sideOverlap: Yup.number().positive('Must be greater than 0').required('Required'),
  forwardOverlap: Yup.number().positive('Must be greater than 0').required('Required'),
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
