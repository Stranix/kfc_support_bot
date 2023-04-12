"""App configuration."""
from os import environ, path
from dotenv import load_dotenv

# Find .env file
basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

# General Config
BOT_TOKEN = environ.get('BOT_TOKEN')
MAIL_LOGIN = environ.get('MAIL_LOGIN')
MAIL_PASSWORD = environ.get('MAIL_PASSWORD')
XML_LINK = environ.get('XML_LINK')
TEST_LOGIN = environ.get('XML_LOGIN')
XML_PASSWORD = environ.get('XML_PASSWORD')
MAIL_IMAP_SERVER = environ.get('MAIL_IMAP_SERVER')
