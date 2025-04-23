from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import boto3

# base (foundational) class that allows us to define database models by mapping Python classes to database tables.
Base = declarative_base()
ssm = boto3.client('ssm', region_name='eu-west-2')  # set up connection to AWS Parameter Store for getting database password
try:
    data = ssm.get_parameter(Name='/dev/api/db-url', WithDecryption=True) 
    URL_DATABASE = data['Parameter']['Value'] # get the database connection string from AWS Parameter Store
except ssm.exceptions.ParameterNotFound:
    raise ValueError("SSM parameter not found")

engine = create_engine(URL_DATABASE)  # create engine that connects to database 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # create factory for making database sessions (safe temporary connections)
