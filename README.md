# BDSA Protocols Platform

A centralized web application for reviewing and creating protocols for stains and regions in the BDSA (Big Data Slide Archive) platform.

## Features

- **Protocol Management**: Create, view, and edit staining and region protocols
- **Documentation**: Access background information, methods, and references from the manuscript
- **Modern UI**: Built with React, TypeScript, and Vite for a fast, responsive experience
- **Component Library**: Integrated with `bdsa-react-components` for consistent UI elements

## Prerequisites

- Node.js 18+ and npm
- Access to the `bdsa-react-components` library (either published or via npm link)

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Link bdsa-react-components (if using local development version)

If you're using a local development version of `bdsa-react-components`:

**In the bdsa-react-components library directory:**
```bash
npm link
```

**In this project directory:**
```bash
npm link bdsa-react-components
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Project Structure

```
src/
├── components/
│   ├── Layout.tsx              # Main layout with navigation
│   ├── protocols/
│   │   ├── ProtocolList.tsx    # List view of all protocols
│   │   └── ProtocolEditor.tsx  # Create/edit protocol form
│   └── documentation/
│       └── DocumentationTabs.tsx # Tabbed documentation viewer
├── pages/
│   ├── ProtocolsPage.tsx       # Protocols page container
│   └── DocumentationPage.tsx   # Documentation page container
├── utils/
│   └── manuscriptLoader.ts     # Utility for loading manuscript content
├── App.tsx                      # Main app component with routing
└── main.tsx                    # Application entry point
```

## Integration with bdsa-react-components

This project uses the following components from `bdsa-react-components`:

- `Card` - For displaying protocol cards and content containers
- `Button` - For actions throughout the application

See `docs/CURSOR_INTEGRATION.md` for complete API documentation.

## Manuscript Content Integration

The documentation section is designed to load content from `manuscript-first-submission.docx`. 

**Current Status**: Placeholder content is displayed. To integrate actual content:

1. Place `manuscript-first-submission.docx` in the project root
2. Implement DOCX parsing in `src/utils/manuscriptLoader.ts`
3. Consider using libraries like:
   - `mammoth` - Convert DOCX to HTML
   - `docx` - Parse DOCX files
   - Or a backend service to handle conversion

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

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

