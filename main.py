import os
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from fastapi import FastAPI, Body, Header, Depends, HTTPException , Response
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from supabase import create_client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
print("Server running and connected to Supabase")

app = FastAPI()


@app.post("/auth/signup")
async def signup(body: dict = Body(default={})):
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})

    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

    return JSONResponse(status_code=201, content=jsonable_encoder(res.user))

@app.post("/auth/login")
async def login(body: dict = Body(default={})):
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:

        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

    return JSONResponse(status_code=200, content={
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
    })
@app.get("/public/info")
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):

    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    # The guard: runs before any route that uses it
    if not credentials or not credentials.credentials.strip():
        raise HTTPException(status_code=401, detail="Access token required")

    token = credentials.credentials.strip()

    try:
        user = supabase.auth.get_user(token).user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user  # handed to the route as "user"


@app.get("/protected/profile")
async def profile(user=Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "created_at": str(user.created_at)}


@app.get("/protected/dashboard")
async def dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}"}
@app.post("/auth/logout")
async def logout(user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    return Response(status_code=204)  # 204 = success, no body