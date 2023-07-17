export const PLATFORM_OPTIONS = ["phantom_4", "m300", "m350", "other"];
export const SENSOR_OPTIONS = ["rgb", "multispectral", "lidar", "other"];

const initialValues = {
  acquisitionDate: "",
  altitude: 120,
  sideOverlap: 60,
  forwardOverlap: 75,
  sensor: SENSOR_OPTIONS[0],
  platform: PLATFORM_OPTIONS[0],
  //   pilot: "" // List of team members with access to the project?
  // If no team associated with the project, pilot = logged in user?
};

export default initialValues;
