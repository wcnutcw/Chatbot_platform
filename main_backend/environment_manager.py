import os
import logging
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv, set_key
from typing import Dict, Optional, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentManager:
    """
    Manages environment variables stored in MongoDB database
    and syncs them with the .env file
    """
    
    def __init__(self, mongo_url: str = None, db_name: str = "ENVIRONMENT"):
        """
        Initialize Environment Manager
        
        Args:
            mongo_url: MongoDB connection URL
            db_name: Database name for storing environment variables
        """
        # Get current directory and construct .env path
        current_directory = os.getcwd()
        self.env_path = Path(current_directory).parent / 'venv' / '.env'
        
        # Ensure .env file exists
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.env_path.exists():
            self.env_path.touch()
        
        # Load existing .env file
        load_dotenv(dotenv_path=self.env_path, override=True)
        
        # MongoDB connection
        self.mongo_url = mongo_url or os.getenv("MONGO_URL", "mongodb://localhost:27017/")
        self.db_name = db_name
        self.collection_name = "environment_variables"
        
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def save_to_database(self, env_vars: Dict[str, Any], description: str = None) -> bool:
        """
        Save environment variables to MongoDB database
        
        Args:
            env_vars: Dictionary of environment variables
            description: Optional description for this configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare document
            document = {
                "_id": "current_environment",  # Single document approach
                "variables": env_vars,
                "description": description or "Environment configuration",
                "updated_at": datetime.now(),
                "created_at": datetime.now()
            }
            
            # Check if document exists
            existing = self.collection.find_one({"_id": "current_environment"})
            if existing:
                document["created_at"] = existing.get("created_at", datetime.now())
                # Update existing document
                result = self.collection.replace_one(
                    {"_id": "current_environment"}, 
                    document
                )
                logger.info(f"Updated environment variables in database: {result.modified_count} document(s)")
            else:
                # Insert new document
                result = self.collection.insert_one(document)
                logger.info(f"Inserted environment variables in database: {result.inserted_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False
    
    def load_from_database(self) -> Optional[Dict[str, Any]]:
        """
        Load environment variables from MongoDB database
        
        Returns:
            Dict[str, Any]: Environment variables or None if not found
        """
        try:
            document = self.collection.find_one({"_id": "current_environment"})
            if document:
                logger.info("Loaded environment variables from database")
                return document.get("variables", {})
            else:
                logger.warning("No environment variables found in database")
                return None
                
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return None
    
    def sync_to_env_file(self, env_vars: Dict[str, Any]) -> bool:
        """
        Sync environment variables to .env file
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Backup existing .env file
            backup_path = self.env_path.with_suffix('.env.backup')
            if self.env_path.exists():
                import shutil
                shutil.copy2(self.env_path, backup_path)
                logger.info(f"Backed up existing .env file to {backup_path}")
            
            # Write new environment variables
            for key, value in env_vars.items():
                if value is not None:  # Only set non-None values
                    set_key(self.env_path, key, str(value))
                    logger.debug(f"Set {key} in .env file")
            
            logger.info(f"Successfully synced {len(env_vars)} variables to .env file")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing to .env file: {e}")
            return False
    
    def load_from_env_file(self) -> Dict[str, str]:
        """
        Load current environment variables from .env file
        
        Returns:
            Dict[str, str]: Current environment variables
        """
        try:
            # Reload .env file
            load_dotenv(dotenv_path=self.env_path, override=True)
            
            # Read .env file manually to get all variables
            env_vars = {}
            if self.env_path.exists():
                with open(self.env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip('"\'')
                            env_vars[key.strip()] = value
            
            logger.info(f"Loaded {len(env_vars)} variables from .env file")
            return env_vars
            
        except Exception as e:
            logger.error(f"Error loading from .env file: {e}")
            return {}
    
    def sync_database_to_env(self) -> bool:
        """
        Load environment variables from database and sync to .env file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load from database
            env_vars = self.load_from_database()
            if env_vars is None:
                logger.warning("No environment variables found in database to sync")
                return False
            
            # Sync to .env file
            success = self.sync_to_env_file(env_vars)
            if success:
                logger.info("Successfully synced database environment variables to .env file")
                # Reload environment variables
                load_dotenv(dotenv_path=self.env_path, override=True)
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing database to .env: {e}")
            return False
    
    def sync_env_to_database(self, description: str = None) -> bool:
        """
        Load environment variables from .env file and save to database
        
        Args:
            description: Optional description for this configuration
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load from .env file
            env_vars = self.load_from_env_file()
            if not env_vars:
                logger.warning("No environment variables found in .env file to sync")
                return False
            
            # Save to database
            success = self.save_to_database(env_vars, description)
            if success:
                logger.info("Successfully synced .env file to database")
            
            return success
            
        except Exception as e:
            logger.error(f"Error syncing .env to database: {e}")
            return False
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about current environment configuration
        
        Returns:
            Dict[str, Any]: Environment information
        """
        try:
            # Get database info
            db_document = self.collection.find_one({"_id": "current_environment"})
            db_vars = db_document.get("variables", {}) if db_document else {}
            
            # Get .env file info
            env_vars = self.load_from_env_file()
            
            return {
                "database": {
                    "exists": db_document is not None,
                    "variables_count": len(db_vars),
                    "last_updated": db_document.get("updated_at") if db_document else None,
                    "description": db_document.get("description") if db_document else None
                },
                "env_file": {
                    "path": str(self.env_path),
                    "exists": self.env_path.exists(),
                    "variables_count": len(env_vars)
                },
                "sync_status": {
                    "in_sync": db_vars == env_vars,
                    "db_only_keys": set(db_vars.keys()) - set(env_vars.keys()),
                    "env_only_keys": set(env_vars.keys()) - set(db_vars.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting environment info: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close MongoDB connection"""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("Closed MongoDB connection")

# Convenience functions
def get_env_manager() -> EnvironmentManager:
    """Get a configured EnvironmentManager instance"""
    return EnvironmentManager()

def sync_database_to_env() -> bool:
    """Quick function to sync database environment variables to .env file"""
    manager = get_env_manager()
    try:
        return manager.sync_database_to_env()
    finally:
        manager.close()

def sync_env_to_database(description: str = None) -> bool:
    """Quick function to sync .env file to database"""
    manager = get_env_manager()
    try:
        return manager.sync_env_to_database(description)
    finally:
        manager.close()

def save_environment_config(env_vars: Dict[str, Any], description: str = None) -> bool:
    """Quick function to save environment configuration"""
    manager = get_env_manager()
    try:
        # Save to database
        db_success = manager.save_to_database(env_vars, description)
        # Sync to .env file
        env_success = manager.sync_to_env_file(env_vars)
        return db_success and env_success
    finally:
        manager.close()

# Example usage and testing
if __name__ == "__main__":
    # Test the environment manager
    manager = EnvironmentManager()
    
    try:
        # Example environment variables
        test_env_vars = {
            "OPENAI_API_KEY": "sk-test-key-123",
            "MONGO_URL": "mongodb://localhost:27017/",
            "PINECONE_API_KEY": "test-pinecone-key",
            "PINECONE_ENV": "us-west1-gcp",
            "EMBEDDING_MODEL": "text-embedding-3-small",
            "FACEBOOK_ACCESS_TOKEN": "test-facebook-token",
            "EMAIL_ADMIN": "admin@example.com",
            "EMAIL_PASS": "test-password"
        }
        
        print("🧪 Testing Environment Manager")
        print("=" * 50)
        
        # Test saving to database
        print("1. Saving test environment variables to database...")
        success = manager.save_to_database(test_env_vars, "Test configuration")
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test loading from database
        print("\n2. Loading environment variables from database...")
        loaded_vars = manager.load_from_database()
        print(f"   Result: {'✅ Success' if loaded_vars else '❌ Failed'}")
        if loaded_vars:
            print(f"   Loaded {len(loaded_vars)} variables")
        
        # Test syncing to .env file
        print("\n3. Syncing database to .env file...")
        success = manager.sync_database_to_env()
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test environment info
        print("\n4. Getting environment information...")
        info = manager.get_environment_info()
        print(f"   Database variables: {info['database']['variables_count']}")
        print(f"   .env file variables: {info['env_file']['variables_count']}")
        print(f"   In sync: {'✅ Yes' if info['sync_status']['in_sync'] else '❌ No'}")
        
        print("\n🎉 Environment Manager test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    finally:
        manager.close()