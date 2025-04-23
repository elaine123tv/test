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

# this function handles what happens when someone makes too many requests too quickly
async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"}
    )

app = FastAPI() # create the main application that will handle all the web requests
models.Base.metadata.create_all(bind=engine) # create all the database tables based on the models we defined

# set up rate limiting to prevent too many requests
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler) # tell the app what to do when rate limits are exceeded

# Pydantic Schemas: these classes define what information we expect when sending a request to the API (creating a new player or game data)
# they help make sure the data is in the right format before we save it

# defines what info is needed to create a new player
class PlayerCreate(BaseModel):
    first_name: str
    last_name: str
    passcode: int = Field(ge=1000, le=9999, description="4-digit passcode")
    
# defines what info is needed for the breathing technique game
class BreathingTechniqueCreate(BaseModel):
    play_or_pass: bool
    breaths: int

# similar classes for other games follow below...
# each one defines what data we store for that particular game

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

# this lets us easily use the database in our routes
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
# these routes handle creating and managing players

# route to create a new player account
@app.post("/create_player")
@limiter.limit("5/minute")
async def create_player(request: Request, player: PlayerCreate, db: db_dependency):
    try:
        # securely hash the passcode before storing it
        hashed = bcrypt.hashpw(str(player.passcode).encode('utf-8'), bcrypt.gensalt())
        # create a new player record
        db_player = models.Player(first_name=player.first_name,last_name=player.last_name,passcode=hashed.decode('utf-8'))
        # save to database
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return db_player.player_id # return the new player's ID
    except Exception as e: # undo changes if something went wrong
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# helper function to check if a passcode is correct. returns player_id if it is.
def verify_player_passcode(player_id: int, passcode: int, db: db_dependency):
    player = db.query(models.Player).filter(models.Player.player_id == player_id).first() # find the player in the database
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Player not found")
    # securely check if the passcode matches
    if not bcrypt.checkpw(str(passcode).encode('utf-8'), player.passcode.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect passcode")
    return player.player_id

# route to start a new game session
@app.post("/create_game_session")
@limiter.limit("10/minute") # limit to 10 requests per minute
async def create_game_session(request: Request, player_id: int, passcode: int, db: db_dependency):
    # verify if passcode is correct first
    verified_player_id = verify_player_passcode(player_id, passcode, db)
    try:
        # check if player has created too many sessions recently (20 per hour)
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
        # create new session
        new_session = models.GameSession(player_id=verified_player_id)
        db.add(new_session)
        db.commit()
        return new_session.session_id # return the new session ID
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# ----- Game Exercise Endpoints -----
# these routes save data for each type of game exercise
# they all work similarly - they take session_id and game data, and save it

# route to save breathing technique game results
@app.post("/game_sessions/{session_id}/create_breathing_techniques")
async def create_breathing_technique(session_id: int, data: BreathingTechniqueCreate, db:db_dependency):
    try:
        # first check the session exists
        if not db.query(models.GameSession).filter(models.GameSession.session_id == session_id).first():
            raise HTTPException(status_code=404, detail="Game session not found")
        # create new breathing technique record
        bt = models.BreathingTechnique(session_id=session_id, play_or_pass=data.play_or_pass, breaths=data.breaths)
        db.add(bt)
        db.commit()
        return {"message": "Breathing technique record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        
# similar routes for other game exercises follow...
# each one saves the results for a different game    

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

