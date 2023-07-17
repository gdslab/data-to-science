import * as Yup from "yup";

const validationSchema = Yup.object({
  title: Yup.string().max(255, "Must be 255 characters or less").required("Required"),
  description: Yup.string()
    .max(300, "Must be 300 characters or less")
    .required("Required"),
  location: Yup.object().shape({
    type: Yup.string(),
    geometry: Yup.object().shape({
      type: Yup.string(),
      coordinates: Yup.array(),
    }),
  }),
  plantingDate: Yup.date().required("Required"),
  harvestDate: Yup.date()
    .min(Yup.ref("plantingDate"), "Must be after planting date")
    .required("Required"),
});

export default validationSchema;
