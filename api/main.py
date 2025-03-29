from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
import models
from typing import Annotated
from database import engine, SessionLocal
from sqlalchemy.orm import Session

# Replace with your AWS RDS connection string

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class PlayerCreate(BaseModel):
    username: str

class PlayerResponse(BaseModel):
    player_id: int
    class Config:
        from_attributes = True

class GameSessionCreate(BaseModel):
    player_id: int

class GameSessionResponse(BaseModel):
    session_id: int
    player_id: int
    date_time: str
    class Config:
        from_attributes = True

# Schemas for game exercise tables (all fields except session_id)
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
# create new player
@app.post("/create_player")
async def create_player(player: PlayerCreate, db: db_dependency):
    try:
        db_player = models.Player(username=player.username)
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
        return {"message": "New player record created"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")

# get id from existing username
@app.get("/get_player_id/{username}")
async def get_player_id(username:str, db:db_dependency):
    try:
        db_player = db.query(models.Player).filter(models.Player.username == username).first()
        if not db_player:
            raise HTTPException(status_code=404, detail="Player not found")
        return {"player_id":db_player.player_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
        

# create session by player_id and return newly created session_id
@app.post("/create_game_session/{response_player_id}")
async def create_game_session(response_player_id:int, db:db_dependency):
    # Ensure the player exists
    try:
        player = db.query(models.Player).filter(models.Player.player_id == response_player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        new_session = models.GameSession(player_id=response_player_id)
        db.add(new_session)
        db.commit()
        return new_session.session_id
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
