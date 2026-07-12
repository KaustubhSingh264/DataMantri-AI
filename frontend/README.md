# Data Mantri Frontend

React frontend for Data Mantri.

## Local Development

```bash
cp .env.example .env
npm install
npm start
```

The frontend uses `REACT_APP_API_BASE` for the FastAPI backend URL.

## Verification

```bash
npm test -- --watchAll=false
npm run build
```
