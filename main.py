import os
from dotenv import load_dotenv
from fastapi import FastAPI, Body, Header
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
        print("LOGIN ERROR:", e)
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})

    return JSONResponse(status_code=200, content={
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
    })
@app.get("/public/info")
async def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
async def profile(authorization: str | None = Header(default=None)):
    # 1. Extract the token from "Authorization: Bearer <token>"
    if not authorization or not authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"error": "Access token required"})

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return JSONResponse(status_code=401, content={"error": "Access token required"})

    try:
        user = supabase.auth.get_user(token).user
    except Exception:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired token"})

    return {"id": user.id, "email": user.email, "created_at": str(user.created_at)}