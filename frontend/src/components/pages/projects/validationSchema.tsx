import * as Yup from 'yup';

const validationSchema = Yup.object({
  title: Yup.string()
    .max(255, 'Must be 255 characters or less')
    .required('Must enter project title'),
  description: Yup.string()
    .max(300, 'Must be 300 characters or less')
    .required('Must enter project description'),
  location: Yup.object()
    .shape({
      center_x: Yup.number().min(-180).max(180).required(),
      center_y: Yup.number().min(-90).max(90).required(),
      geom: Yup.string().required('Must save a field boundary'),
    })
    .required('Must save a field boundary'),
  plantingDate: Yup.date(),
  harvestDate: Yup.date().min(Yup.ref('plantingDate'), 'Must be after planting date'),
  teamID: Yup.string(),
});

export default validationSchema;
