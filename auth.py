from fastapi import FastAPI, Request

async def get_session_cookie_value(request: Request) -> str:
    return request.cookies.get("fast_vote_session", None)