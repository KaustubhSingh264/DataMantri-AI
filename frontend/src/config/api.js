export const API_BASE = (process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000").replace(/\/$/, "");

export const API_BASE_CANDIDATES = [
  API_BASE,
  "http://127.0.0.1:8000",
  "http://localhost:8000",
].filter((value, index, values) => values.indexOf(value) === index);
