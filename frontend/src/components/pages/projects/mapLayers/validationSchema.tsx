import * as Yup from 'yup';

export const validationSchema = Yup.object({
  layerName: Yup.string()
    .max(128, 'Must be 128 characters or less')
    .required('Must enter layer name'),
  geojson: Yup.object()
    .shape({
      type: Yup.string().required(),
      features: Yup.array(
        Yup.object().shape({
          geometry: Yup.object()
            .shape({
              coordinates: Yup.array(Yup.number()).required(),
              type: Yup.string().required(),
            })
            .required(),
          properties: Yup.object(),
          type: Yup.string().required(),
        })
      ),
    })
    .required('Must upload GeoJSON or zipped shapefile'),
});
