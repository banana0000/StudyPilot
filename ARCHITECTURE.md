# StudyPilot Architecture

## Overview

StudyPilot is a local-first Dash application for uploading study material, reviewing extracted text, managing learning goals, timing focused sessions, and generating lightweight practice content.

## Components

- `app.py` — Dash entry point, DMC layout, UI callbacks, and dashboard data.
- `services/document_service.py` — validates uploads, extracts text from PDF/DOCX/TXT files, stores uploads locally, and removes uploaded files.
- `ai/client.py` — generates answers to questions about uploaded material.
- `config.py` — application configuration, upload directory, file-size limit, and allowed extensions.
- `assets/styles.css` — pink/blue responsive visual styling, including dark-mode-aware surfaces.
- `data/uploads/` — local storage for uploaded source documents.

## Data flow

1. A user uploads a PDF, DOCX, or TXT file.
2. `document_service` validates, stores, and extracts its text.
3. The extracted text is kept in the Dash session store.
4. The Material preview, flashcard, question answering, and quiz builder use this stored text.
5. The remove action clears the session material and deletes the local uploaded file.

## UI and state

- Dash Mantine Components render the interface and charts.
- `dcc.Store` retains session material and browser-local learning goals.
- Dash callbacks coordinate sidebar navigation, theme behavior, uploads, goals, quiz generation, the timer, and help modal.