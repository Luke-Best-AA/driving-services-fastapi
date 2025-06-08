from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import RequestValidationError

from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv
import os
from http import HTTPStatus

from .utils.debug import Debug
from .utils.config import ENV
from .utils.messages import Messages

from app.controllers.user_controller import router as user_router
from app.controllers.optional_extra_controller import router as optional_extra_router
from app.controllers.car_insurance_policy_controller import router as car_insurance_policy_router
from app.controllers.auth_controller import router as auth_router

app = FastAPI()

# Mount static files
app.mount("/app/static", StaticFiles(directory="app/static"), name="static")

# Set Debug.enabled based on environment
Debug.enabled = ENV != "prod"

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Load environment variables from .env file
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  # Load SECRET_KEY from .env

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in the environment variables")

ALGORITHM = "HS256"  # JWT signing algorithm

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={
            "message": Messages.INVALID_REQUEST_DATA,
            "errors": exc.errors(),
        },
    )

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        accept = request.headers.get("accept", "")
        if "text/html" in accept:
            return RedirectResponse(url="/")
    # fallback to default behavior
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.get("/healthcheck")
async def healthcheck():
    return JSONResponse(
        content={
            "message": Messages.API_IS_RUNNNG
        },
        status_code=HTTPStatus.OK
    )

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(optional_extra_router)
app.include_router(car_insurance_policy_router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.get("/admin_dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse(request, "admin-dashboard.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse(request, "profile.html", {"request": request})