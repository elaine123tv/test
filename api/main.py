from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field
import models
from typing import Annotated
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
import bcrypt
from fastapi.responses import JSONResponse 

async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"}
    )
    
app = FastAPI()
models.Base.metadata.create_all(bind=engine)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Pydantic Schemas: These define data validation rules for API requests & responses.
class PlayerCreate(BaseModel):
    first_name: str
    last_name: str
    passcode: int = Field(ge=1000, le=9999, description="4-digit passcode")
    
# schemas for game exercise tables (all fields except session_id)
class BreathingTechniqueCreate(BaseModel):
    play_or_pass: bool
    breaths: int

class StretchAndReachCreate(BaseModel):
    play_or_pass: bool
    total_stars: int
    highest_level: int
    missed_stars_location: str

class LightHandsCreate(BaseModel):
    play_or_pass: bool
    two_one_left_score: int
    two_one_right_score: int
    two_two_left_score: int
    two_two_right_score: int
    three_three_left_score: int
    three_three_right_score: int

class RhythmRecoveryCreate(BaseModel):
    play_or_pass: bool
    thumb_left_time: float
    index_left_time: float
    middle_left_time: float
    ring_left_time: float
    little_left_time: float
    thumb_right_time: float
    index_right_time: float
    middle_right_time: float
    ring_right_time: float
    little_right_time: float
    thumb_left_skipped: bool
    index_left_skipped: bool
    middle_left_skipped: bool
    ring_left_skipped: bool
    little_left_skipped: bool
    thumb_right_skipped: bool
    index_right_skipped: bool
    middle_right_skipped: bool
    ring_right_skipped: bool
    little_right_skipped: bool

class DrawShapesCreate(BaseModel):
    play_or_pass: bool
    small_left_time: int
    small_right_time: int
    medium_left_time: int
    medium_right_time: int
    large_left_time: int
    large_right_time: int

class LineWalkCreate(BaseModel):
    play_or_pass: bool
    forward_time: float
    backward_time: float
    crab_right_time: float
    crab_left_time: float
    out_of_line_count: int

class BalloonsCreate(BaseModel):
    play_or_pass: bool
    waist_left_score: int
    waist_right_score: int
    chest_left_score: int
    chest_right_score: int
    head_left_score: int
    head_right_score: int
    knees_left_score: int
    knees_right_score: int
    feet_left_score: int
    feet_right_score: int

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
@app.get("/")
async def read_root():
    return {"message": "Hello World"}
# ----- Players Endpoints -----
# create new player, returns player_id
@app.post("/create_player")
@limiter.limit("5/minute")
async def create_player(request: Request, player: PlayerCreate, db: db_dependency):
    try:
        hashed = bcrypt.hashpw(str(player.passcode).encode('utf-8'), bcrypt.gensalt())
        db_player = models.Player(
            first_name=player.first_name,
            last_name=player.last_name,
            passcode=hashed.decode('utf-8')
        )
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player.player_id
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# returns player_id
def verify_player_passcode(player_id: int, passcode: int, db: db_dependency):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Player not found")
    # check if the hashed passcode matches
    if not bcrypt.checkpw(str(passcode).encode('utf-8'), player.passcode.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect passcode")
    return player.player_id

# create session by player_id and return newly created session_id
@app.post("/create_game_session")
@limiter.limit("10/minute")
async def create_game_session(request: Request, player_id: int, passcode: int, db: db_dependency):
    #verify passcode first
    verified_player_id = verify_player_passcode(player_id, passcode, db)
    try:
        # Check player-based rate limit (20 sessions per hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        session_count = db.query(models.GameSession).filter(
            models.GameSession.player_id == player_id,
            models.GameSession.date_time >= hour_ago
        ).count()
        if session_count >= 20:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many sessions created in the last hour."
            )
        # Create new session
        new_session = models.GameSession(player_id=verified_player_id)
        db.add(new_session)
        db.commit()
        return new_session.session_id
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# ----- Game Exercise Endpoints -----
# Each endpoint uses the session_id from the URL and accepts all other fields in the request body.

@app.post("/game_sessions/{session_id}/create_breathing_techniques")
async def create_breathing_technique(session_id: int, data: BreathingTechniqueCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        bt = models.BreathingTechnique(session_id=session_id, play_or_pass=data.play_or_pass, breaths=data.breaths)
        db.add(bt)
        db.commit()
        return {"message": "Breathing technique record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        

@app.post("/game_sessions/{session_id}/create_stretch_and_reach")
async def create_stretch_and_reach(session_id: int, data: StretchAndReachCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        sar = models.StretchAndReach(session_id=session_id, **data.dict())
        db.add(sar)
        db.commit()
        return {"message": "Stretch and reach record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        
@app.post("/game_sessions/{session_id}/create_light_hands")
async def create_light_hands(session_id: int, data: LightHandsCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        lh = models.LightHands(session_id=session_id, **data.dict())
        db.add(lh)
        db.commit()
        return {"message": "Light hands record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        

@app.post("/game_sessions/{session_id}/create_rhythm_recovery")
async def create_rhythm_recovery(session_id: int, data: RhythmRecoveryCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        rr = models.RhythmRecovery(session_id=session_id, **data.dict())
        db.add(rr)
        db.commit()
        return {"message": "Rhythm recovery record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        

@app.post("/game_sessions/{session_id}/create_draw_shapes")
async def create_draw_shapes(session_id: int, data: DrawShapesCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        ds = models.DrawShapes(session_id=session_id, **data.dict())
        db.add(ds)
        db.commit()
        return {"message": "Draw shapes record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@app.post("/game_sessions/{session_id}/create_line_walk")
async def create_line_walk(session_id: int, data: LineWalkCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        lw = models.LineWalk(session_id=session_id, **data.dict())
        db.add(lw)
        db.commit()
        return {"message": "Line walk record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

@app.post("/game_sessions/{session_id}/create_balloons")
async def create_balloons(session_id: int, data: BalloonsCreate, db:db_dependency):
    try:
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        bl = models.Balloons(session_id=session_id, **data.dict())
        db.add(bl)
        db.commit()
        return {"message": "Balloons record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

