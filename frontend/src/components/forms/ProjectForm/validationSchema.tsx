import * as Yup from "yup";

const validationSchema = Yup.object({
  title: Yup.string().max(255, "Must be 255 characters or less").required("Required"),
  description: Yup.string()
    .max(300, "Must be 300 characters or less")
    .required("Required"),
  locationID: Yup.string().required("Required"),
  plantingDate: Yup.date().required("Required"),
  harvestDate: Yup.date()
    .min(Yup.ref("plantingDate"), "Must be after planting date")
    .required("Required"),
  teamID: Yup.string(),
});

export default validationSchema;
