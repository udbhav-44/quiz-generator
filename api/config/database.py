from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Database:
    client = None
    db = None

    @classmethod
    async def connect_to_mongodb(cls):
        """Connect to MongoDB using the connection string from environment variables"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                logger.error("MONGODB_URI environment variable not set")
                raise ValueError("MONGODB_URI environment variable not set")

            logger.info(f"Connecting to MongoDB at {mongodb_uri}")
            cls.client = AsyncIOMotorClient(mongodb_uri)
            
            # Extract database name from URI
            parsed_uri = urlparse(mongodb_uri)
            db_name = parsed_uri.path.strip('/') or "quiz_generator"
            cls.db = cls.client[db_name]
            
            logger.info(f"Connected to MongoDB database: {db_name}")
            return cls.db
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def close_mongodb_connection(cls):
        """Close the MongoDB connection"""
        if cls.client:
            logger.info("Closing MongoDB connection")
            cls.client.close()
            logger.info("MongoDB connection closed")