// Types for Uppy upload error handling

export type ValidationError = {
  loc: (string | number)[];
  msg: string;
  type: string;
};

export type ErrorResponseBody = {
  detail?: string | ValidationError[];
};