import * as Yup from "yup";

const validationSchema = Yup.object({
  acquisitionDate: Yup.date().required("Required"),
  altitude: Yup.number().positive("Must be greater than 0").required("Required"),
  sideOverlap: Yup.number().positive("Must be greater than 0").required("Required"),
  forwardOverlap: Yup.number().positive("Must be greater than 0").required("Required"),
  sensor: Yup.string().required("Required"),
  platform: Yup.string().required("Required"),
});

export default validationSchema;
