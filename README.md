# BDSA Protocols Platform

A centralized web application for reviewing and creating protocols for stains and regions in the BDSA (Big Data Slide Archive) platform.

## Features

- **Protocol Management**: Create, view, and edit staining and region protocols
- **Schema viewer**: Explore the BDSA JSON schema (clinical, region, stain, flattened view, CDE reference)—migrated from BDSA-Schema-Wrangler `apps/schema-viewer-app`
- **Documentation**: Access background information, methods, and references from the manuscript
- **Modern UI**: Built with React, TypeScript, and Vite for a fast, responsive experience
- **Component Library**: Integrated with `bdsa-react-components` for consistent UI elements

## Running the stack (Docker)

**Production build** (frontend built and served with nginx):

```bash
docker compose up -d
```

**Dev mode** (source mounted, frontend and backend reload on change):

```bash
./run-dev.sh
```

Optional: `./run-dev.sh -d` to run in background, or `./run-dev.sh --build` to rebuild images.

- **Frontend**: http://localhost:3001 in dev (port 3001 avoids conflict with other apps on 3000)
- **Admin panel**: http://localhost:3002 (inspect MongoDB data per resource/tab)
- **Backend API**: http://localhost:8000 (uvicorn `--reload` in dev)
- **API docs**: http://localhost:8000/docs
- **MongoDB**: port 27017

See `backend/README.md` for API details and wrangler compatibility.

## Prerequisites

- Node.js 18+ and npm (for local frontend development)
- Docker and Docker Compose (for the full stack)
- Access to the `bdsa-react-components` library (either published or via npm link)

## Frontend development (local)

The web app lives in `frontend/`. To run it locally (without Docker):

### 1. Install dependencies

```bash
cd frontend && npm install
```

### 2. Link bdsa-react-components (if using local development version)

**In the bdsa-react-components library directory:**
```bash
npm link
```

**In the frontend directory:**
```bash
npm link bdsa-react-components
```

### 3. Start dev server

```bash
npm run dev
```

The app will be at http://localhost:3000

## Project structure

```
frontend/                 # Vite + React web app
├── src/
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── protocols/     # ProtocolList, ProtocolEditor
│   │   ├── schema/        # SchemaViewer, FlattenedDataView, CdeReferenceView
│   │   └── documentation/
│   ├── pages/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── Dockerfile             # Production image (nginx)
└── package.json

backend/                   # FastAPI + MongoDB API
├── app/
└── Dockerfile

docs/                      # Project docs — see docs/README.md
docker-compose.yml         # frontend, backend, mongodb
```

## Integration with bdsa-react-components

This project uses the following components from `bdsa-react-components`:

- `Card` - For displaying protocol cards and content containers
- `Button` - For actions throughout the application

See `docs/API.md` for REST API usage and **API key auth from external servers**. See `docs/CURSOR_INTEGRATION.md` for bdsa-react-components integration.

## Manuscript content integration

The documentation section is designed to load content from `manuscript-first-submission.docx`. 

**Current status**: Placeholder content is displayed. To integrate actual content:

1. Place `manuscript-first-submission.docx` in the `frontend/` directory (or wire a path in the app).
2. Implement DOCX parsing in `frontend/src/utils/manuscriptLoader.ts`
3. Consider using libraries like:
   - `mammoth` - Convert DOCX to HTML
   - `docx` - Parse DOCX files
   - Or a backend service to handle conversion

## Building for production

From the `frontend/` directory:

```bash
npm run build
```

The built files will be in `frontend/dist/`. The Docker image builds this and serves it with nginx.

## Development Notes

- All source files are kept under 1000 lines per project rules
- TypeScript is used for type safety
- CSS modules are used for component styling
- React Router is used for navigation

## Future Enhancements

- [ ] Implement actual API integration for protocol CRUD operations
- [ ] Add DOCX parsing for manuscript content
- [ ] Add protocol validation and versioning
- [ ] Add search and filtering for protocols
- [ ] Add protocol templates
- [ ] Add export functionality for protocols

