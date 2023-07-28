import * as Yup from "yup";

const validationSchema = Yup.object({
  title: Yup.string().max(255, "Must be 255 characters or less").required("Required"),
  description: Yup.string()
    .max(300, "Must be 300 characters or less")
    .required("Required"),
});

export default validationSchema;
