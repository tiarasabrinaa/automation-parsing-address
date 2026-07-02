# AI Agent Backend

FastAPI backend scaffold for an AI agent service.

## Structure

- `app/main.py`: FastAPI application entrypoint
- `app/api/v1`: versioned API router and endpoints
- `app/core/config.py`: application settings
- `app/schemas`: request and response models
- `app/services`: business logic layer

## Run Locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the development server:

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Open the API docs:

   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## Run With Docker

1. Make sure `backend/.env` exists and includes `GEMINI_API_KEY`.

2. Build and start the container from the project root:

   ```bash
   docker compose up --build
   ```

3. The API will be available at `http://127.0.0.1:8000`.
