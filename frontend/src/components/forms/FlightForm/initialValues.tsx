export const PLATFORM_OPTIONS = [
  { label: "Phantom 4", value: "phantom_4" },
  { label: "m300", value: "M300" },
  { label: "m350", value: "M350" },
  { label: "other", value: "Other" },
];
export const SENSOR_OPTIONS = [
  { label: "RGB", value: "rgb" },
  { label: "Multispectral", value: "multispectral" },
  { label: "LiDAR", value: "lidar" },
  { label: "Other", value: "other" },
];

const initialValues = {
  acquisitionDate: "",
  altitude: 120,
  sideOverlap: 60,
  forwardOverlap: 75,
  sensor: SENSOR_OPTIONS[0].value,
  platform: PLATFORM_OPTIONS[0].value,
  //   pilot: "" // List of team members with access to the project?
  // If no team associated with the project, pilot = logged in user?
};

export default initialValues;
