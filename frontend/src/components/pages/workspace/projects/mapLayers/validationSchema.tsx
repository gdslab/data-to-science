import * as Yup from 'yup';

export const validationSchema = Yup.object({
  layerName: Yup.string()
    .max(128, 'Must be 128 characters or less')
    .required('Must enter layer name'),
  geojson: Yup.string().required('Must provide GeoJSON file or zipped shapefile'),
});
