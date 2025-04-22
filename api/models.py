from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base

class Player(Base):
    __tablename__ = "players"
    player_id = Column(Integer, primary_key=True, index=True)
    passcode = Column(Integer, nullable=False) 
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

class GameSession(Base):
    __tablename__ = "game_sessions"
    session_id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    date_time = Column(DateTime, default=func.now())

class BreathingTechnique(Base):
    __tablename__ = "breathing_techniques"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    breaths = Column(Integer)

class StretchAndReach(Base):
    __tablename__ = "stretch_and_reach"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    total_stars = Column(Integer)
    highest_level = Column(Integer)
    missed_stars_location = Column(Text)

class LightHands(Base):
    __tablename__ = "light_hands"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    two_one_left_score = Column(Integer)
    two_one_right_score = Column(Integer)
    two_two_left_score = Column(Integer)
    two_two_right_score = Column(Integer)
    three_three_left_score = Column(Integer)
    three_three_right_score = Column(Integer)

class RhythmRecovery(Base):
    __tablename__ = "rhythm_recovery"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    thumb_left_time = Column(Float)
    index_left_time = Column(Float)
    middle_left_time = Column(Float)
    ring_left_time = Column(Float)
    little_left_time = Column(Float)
    thumb_right_time = Column(Float)
    index_right_time = Column(Float)
    middle_right_time = Column(Float)
    ring_right_time = Column(Float)
    little_right_time = Column(Float)
    thumb_left_skipped = Column(Boolean)
    index_left_skipped = Column(Boolean)
    middle_left_skipped = Column(Boolean)
    ring_left_skipped = Column(Boolean)
    little_left_skipped = Column(Boolean)
    thumb_right_skipped = Column(Boolean)
    index_right_skipped = Column(Boolean)
    middle_right_skipped = Column(Boolean)
    ring_right_skipped = Column(Boolean)
    little_right_skipped = Column(Boolean, default=False)

class DrawShapes(Base):
    __tablename__ = "draw_shapes"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    small_left_time = Column(Integer)
    small_right_time = Column(Integer)
    medium_left_time = Column(Integer)
    medium_right_time = Column(Integer)
    large_left_time = Column(Integer)
    large_right_time = Column(Integer)

class LineWalk(Base):
    __tablename__ = "line_walk"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    forward_time = Column(Float)
    backward_time = Column(Float)
    crab_right_time = Column(Float)
    crab_left_time = Column(Float)
    out_of_line_count = Column(Integer)

class Balloons(Base):
    __tablename__ = "balloons"
    session_id = Column(Integer, ForeignKey("game_sessions.session_id"), primary_key=True)
    play_or_pass = Column(Boolean)
    waist_left_score = Column(Integer)
    waist_right_score = Column(Integer)
    chest_left_score = Column(Integer)
    chest_right_score = Column(Integer)
    head_left_score = Column(Integer)
    head_right_score = Column(Integer)
    knees_left_score = Column(Integer)
    knees_right_score = Column(Integer)
    feet_left_score = Column(Integer)
    feet_right_score = Column(Integer)

