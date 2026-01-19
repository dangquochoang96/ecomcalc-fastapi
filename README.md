# FastAPI Application

A well-structured FastAPI application with modular architecture.

## Project Structure

```
.
├── app/                    # Main application package
│   ├── main.py            # FastAPI application entry point
│   ├── dependencies.py    # Shared dependencies
│   ├── routers/           # API route handlers
│   ├── services/          # Business logic layer
│   ├── schemas/           # Pydantic models for validation
│   ├── models/            # Database models
│   ├── external_services/ # External service integrations
│   └── utils/             # Utility functions
├── tests/                 # Test modules
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Setup

1. **Create a virtual environment:**

   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment:**

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative API docs (ReDoc)**: http://localhost:8000/redoc

## Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=app tests/
```

## API Endpoints

### Users

- `POST /api/users/` - Create a new user
- `GET /api/users/` - Get all users
- `GET /api/users/{user_id}` - Get a specific user
- `PUT /api/users/{user_id}` - Update a user
- `DELETE /api/users/{user_id}` - Delete a user

### Items

- `POST /api/items/` - Create a new item
- `GET /api/items/` - Get all items
- `GET /api/items/{item_id}` - Get a specific item
- `PUT /api/items/{item_id}` - Update an item
- `DELETE /api/items/{item_id}` - Delete an item

## Architecture

### Layers

1. **Routers** (`app/routers/`): Handle HTTP requests and responses
2. **Services** (`app/services/`): Contain business logic and CRUD operations
3. **Schemas** (`app/schemas/`): Define data validation and serialization
4. **Models** (`app/models/`): Define database models (ORM)
5. **External Services** (`app/external_services/`): Integrate with external APIs
6. **Utils** (`app/utils/`): Provide utility functions

### Key Features

- ✅ Modular structure for scalability
- ✅ Separation of concerns
- ✅ Pydantic validation
- ✅ JWT authentication utilities
- ✅ Email and notification services
- ✅ Comprehensive testing setup
- ✅ CORS middleware configured
- ✅ API documentation auto-generated

## Database Configuration

The application is now configured to work with MySQL database:

1. **Prerequisites**: Ensure MySQL Server is installed and running
2. **Setup**: Create a database (e.g., `fastapi_app`) and update the `.env` file with your MySQL connection details
3. **Default Connection**: The default connection string in `.env` is:
   ```
   DATABASE_URL=mysql+mysqlconnector://root:@localhost/fastapi_app
   ```
   Adjust the username, password, and database name as needed.

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

The database tables will be automatically created when the application starts.

## Next Steps

1. **Authentication**: Implement full authentication flow
2. **External Services**: Configure email and notification services
3. **Production**: Set up production deployment with proper security

## Development Notes

- The current implementation uses in-memory storage for demonstration
- Replace service layer logic with actual database operations
- Update authentication dependencies with your auth system
- Configure external services (email, SMS, etc.) with your providers
- Update SECRET_KEY in `app/utils/authentication.py` with a secure key

## License

MIT
