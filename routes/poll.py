from typing import Any, List, Optional

from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from models.Option import Option
from models.Poll import Poll, PollCreateBody
from sqlmodel import Session, select
from config.database import engine
from auth import get_session_cookie_value
from ws import ws_manager

from models.Vote import Vote

router = APIRouter(prefix="/poll")

@router.get("/assign-session", response_model=Any, status_code=status.HTTP_200_OK)
async def assign_session(session_id: str = Depends(get_session_cookie_value)) -> Any:
    if not session_id:
        return JSONResponse(content={"status": "session not found"}, status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(content={"status": "ok", "session_id": session_id})

@router.post("/create_poll/", response_model=Any, status_code=status.HTTP_201_CREATED)
async def create_poll(
    data: PollCreateBody,
    sid: str = Depends(get_session_cookie_value),
) -> Any:
    options = [Option(option_text=text) for text in data.options]
    poll = Poll(
        poll_text=data.poll_text, 
        user_id=sid, 
        options=options
    )
    with Session(engine) as session:     
        session.add(poll)
        session.commit()
        session.refresh(poll)
        session.close()
        
    response = {
        "status": "ok",
        "poll_id": poll.id,
    }
    return JSONResponse(content=response, status_code=status.HTTP_201_CREATED)

@router.get("/get-user-polls/", response_model=Any, status_code=status.HTTP_200_OK)
async def get_user_polls(
    sid: str = Depends(get_session_cookie_value),
) -> Any:
    with Session(engine) as session:
        statement = select(Poll).where(Poll.user_id == sid)
        result = session.exec(statement)
        polls = result.all()
        res = []
        
        for poll in polls:  
            res.append({
                **poll.model_dump(exclude={"options", "pub_date"}),
                "pub_date": poll.pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "options": [
                    {
                        **option.model_dump(exclude={"votes", "poll_id"}),
                        "votes": len(option.votes) if option.votes else 0
                    } for option in poll.options
                ]
            })
        
        session.close()
        return JSONResponse(content=res, status_code=status.HTTP_200_OK)

@router.get("/get-poll/{poll_id}", status_code=status.HTTP_200_OK)
async def get_poll(
    poll_id: str,
    sid: str = Depends(get_session_cookie_value),
) -> Any:
    with Session(engine) as session:
        statement = select(Poll).where(Poll.id == poll_id)
        result = session.exec(statement)
        poll = result.first()
        if not poll:
            return JSONResponse(content={"status": "not found"}, status_code=status.HTTP_404_NOT_FOUND)
        vote_statement = select(Vote).where(Vote.user_id == sid)\
            .select_from(Vote)\
            .where(Vote.option_id == Option.id)\
            .where(Option.poll_id == poll_id)
        vote = session.exec(vote_statement).first()
        res = {
            **poll.model_dump(exclude={"options", "pub_date"}),
            "pub_date": poll.pub_date.strftime("%Y-%m-%d %H:%M:%S"),
            "options": [
                {
                    **option.model_dump(exclude={"votes", "poll_id"}),
                    "votes": len(option.votes) if option.votes else 0
                } for option in poll.options
            ],
            "has_voted": vote is not None,
            "votes": vote.option_id if vote else "",
        }
        session.close()
        return JSONResponse(content=res, status_code=status.HTTP_200_OK)
    
@router.post("/vote/", response_model=Any, status_code=status.HTTP_201_CREATED)
async def vote(
    option_id: str,
    sid: str = Depends(get_session_cookie_value),
) -> Any:
    print(f"User ID (sid): {sid}")
    if sid is None:
        raise HTTPException(status_code=400, detail="User ID is missing")
    with Session(engine) as session:
        statement = select(Vote)\
            .where(
                Vote.user_id == sid,
                Vote.option_id == option_id
                )
        vote = session.exec(statement).first()
        if vote:
            return JSONResponse(content={"status": "already voted"}, status_code=status.HTTP_400_BAD_REQUEST)
        vote = Vote(user_id=sid, option_id=option_id)
        session.add(vote)
        session.commit()
        session.refresh(vote)
        updated_options_statement = select(Option).where(Option.poll_id == vote.option.poll_id)
        res = [
            {
                **option.model_dump(exclude={"votes", "poll_id"}),
                "votes": len(option.votes) if option.votes else 0
            } for option in session.exec(updated_options_statement).all()
        ]
        session.close()
        await ws_manager.send_message(
            vote.option.poll_id, {"type": "poll_vote", "payload": res}
        )
    # return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_201_CREATED)
    return True


@router.delete("/{poll_id}", status_code=status.HTTP_200_OK)
async def delete_item(
    sid: str = Depends(get_session_cookie_value),
    poll_id: str = None,
) -> Any:
    with Session(engine) as session:
        statement = select(Poll).where(Poll.id == poll_id, Poll.user_id == sid)
        poll = session.exec(statement).first()
        if not poll:
            return JSONResponse(content={"status": "not found"}, status_code=status.HTTP_404_NOT_FOUND)
        if poll.user_id != sid:
            return JSONResponse(content={"status": "forbidden"}, status_code=status.HTTP_403_FORBIDDEN)
        session.delete(poll)
        session.commit()
        session.close()
        return True
        # return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)