from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import boto3

Base = declarative_base()
ssm = boto3.client('ssm', region_name='eu-west-2')
try:
    data = ssm.get_parameter(Name='/dev/api/db-url', WithDecryption=True)
    URL_DATABASE = data['Parameter']['Value']
except ssm.exceptions.ParameterNotFound:
    raise ValueError("SSM parameter not found")

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
