from glob import glob
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from configparser import ConfigParser

def get_url(filename='database.ini', section='heroku-pgsql'):
    parser = ConfigParser()
    parser.read(filename)
 
    if parser.has_section(section):
        _, url = parser.items(section)[0]

    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
 
    return url

def get_engine():
    engine = None
    try:
        engine = create_engine(get_url(), poolclass=NullPool)
    except:
        print("An error occured creating the engine to PostgreSQL DB")
    return engine

def get_session():
    engine = get_engine()
    base = automap_base()
    base.prepare(engine, reflect = True)
    modules = base.classes.modules
    scans = base.classes.scans
    session = Session(engine)
    return session, modules, scans