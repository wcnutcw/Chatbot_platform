import os
import logging
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv, set_key
from typing import Dict, Optional, Any, List
import json
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedEnvironmentManager:
    """
    Enhanced Environment Manager that supports multiple named configurations
    Each configuration is stored as a separate document in MongoDB
    """
    
    def __init__(self, mongo_url: str = None, db_name: str = "ENVIRONMENT"):
        """
        Initialize Enhanced Environment Manager
        
        Args:
            mongo_url: MongoDB connection URL
            db_name: Database name for storing environment configurations
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
        self.collection_name = "configurations"
        
        try:
            self.client = MongoClient(self.mongo_url)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better performance
            self.collection.create_index("name", unique=True)
            self.collection.create_index("is_active")
            
            logger.info(f"Connected to MongoDB: {self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def create_configuration(self, name: str, description: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new environment configuration
        
        Args:
            name: Configuration name (must be unique)
            description: Configuration description
            variables: Environment variables dictionary
            
        Returns:
            Dict containing the created configuration
        """
        try:
            # Check if name already exists
            existing = self.collection.find_one({"name": name})
            if existing:
                raise ValueError(f"Configuration with name '{name}' already exists")
            
            # Generate unique ID
            config_id = str(uuid.uuid4())
            
            # Prepare document
            document = {
                "_id": config_id,
                "name": name,
                "description": description,
                "variables": variables,
                "is_active": False,  # New configurations are not active by default
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Insert document
            result = self.collection.insert_one(document)
            logger.info(f"Created configuration '{name}' with ID: {config_id}")
            
            return {
                "id": config_id,
                "name": name,
                "description": description,
                "variables": variables,
                "is_active": False,
                "created_at": document["created_at"].isoformat(),
                "updated_at": document["updated_at"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating configuration: {e}")
            raise
    
    def get_all_configurations(self) -> List[Dict[str, Any]]:
        """
        Get all environment configurations
        
        Returns:
            List of configuration dictionaries
        """
        try:
            configurations = []
            cursor = self.collection.find().sort("created_at", -1)
            
            for doc in cursor:
                configurations.append({
                    "id": doc["_id"],
                    "name": doc["name"],
                    "description": doc["description"],
                    "variables": doc["variables"],
                    "is_active": doc.get("is_active", False),
                    "created_at": doc["created_at"].isoformat(),
                    "updated_at": doc["updated_at"].isoformat()
                })
            
            logger.info(f"Retrieved {len(configurations)} configurations")
            return configurations
            
        except Exception as e:
            logger.error(f"Error getting configurations: {e}")
            return []
    
    def get_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific configuration by ID
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Configuration dictionary or None if not found
        """
        try:
            doc = self.collection.find_one({"_id": config_id})
            if doc:
                return {
                    "id": doc["_id"],
                    "name": doc["name"],
                    "description": doc["description"],
                    "variables": doc["variables"],
                    "is_active": doc.get("is_active", False),
                    "created_at": doc["created_at"].isoformat(),
                    "updated_at": doc["updated_at"].isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting configuration {config_id}: {e}")
            return None
    
    def get_active_configuration(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently active configuration
        
        Returns:
            Active configuration dictionary or None if no active configuration
        """
        try:
            doc = self.collection.find_one({"is_active": True})
            if doc:
                return {
                    "id": doc["_id"],
                    "name": doc["name"],
                    "description": doc["description"],
                    "variables": doc["variables"],
                    "is_active": True,
                    "created_at": doc["created_at"].isoformat(),
                    "updated_at": doc["updated_at"].isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting active configuration: {e}")
            return None
    
    def update_configuration(self, config_id: str, variables: Dict[str, Any], 
                           name: str = None, description: str = None) -> bool:
        """
        Update an existing configuration
        
        Args:
            config_id: Configuration ID
            variables: Updated environment variables
            name: Optional new name
            description: Optional new description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare update document
            update_doc = {
                "variables": variables,
                "updated_at": datetime.now()
            }
            
            if name is not None:
                # Check if new name conflicts with existing configurations
                existing = self.collection.find_one({"name": name, "_id": {"$ne": config_id}})
                if existing:
                    raise ValueError(f"Configuration with name '{name}' already exists")
                update_doc["name"] = name
            
            if description is not None:
                update_doc["description"] = description
            
            # Update document
            result = self.collection.update_one(
                {"_id": config_id},
                {"$set": update_doc}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated configuration {config_id}")
                
                # If this is the active configuration, sync to .env file
                config = self.get_configuration(config_id)
                if config and config["is_active"]:
                    self.sync_to_env_file(variables)
                
                return True
            else:
                logger.warning(f"No configuration found with ID {config_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating configuration {config_id}: {e}")
            return False
    
    def activate_configuration(self, config_id: str) -> bool:
        """
        Activate a configuration (deactivates all others and syncs to .env)
        
        Args:
            config_id: Configuration ID to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, deactivate all configurations
            self.collection.update_many(
                {},
                {"$set": {"is_active": False}}
            )
            
            # Get the configuration to activate
            config = self.get_configuration(config_id)
            if not config:
                logger.error(f"Configuration {config_id} not found")
                return False
            
            # Activate the specified configuration
            result = self.collection.update_one(
                {"_id": config_id},
                {"$set": {"is_active": True, "updated_at": datetime.now()}}
            )
            
            if result.modified_count > 0:
                # Sync to .env file
                success = self.sync_to_env_file(config["variables"])
                if success:
                    logger.info(f"Activated configuration '{config['name']}' and synced to .env")
                    # Reload environment variables
                    load_dotenv(dotenv_path=self.env_path, override=True)
                    return True
                else:
                    logger.error(f"Failed to sync configuration to .env file")
                    return False
            else:
                logger.error(f"Failed to activate configuration {config_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error activating configuration {config_id}: {e}")
            return False
    
    def delete_configuration(self, config_id: str) -> bool:
        """
        Delete a configuration (cannot delete active configuration)
        
        Args:
            config_id: Configuration ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if configuration is active
            config = self.get_configuration(config_id)
            if not config:
                logger.error(f"Configuration {config_id} not found")
                return False
            
            if config["is_active"]:
                logger.error(f"Cannot delete active configuration '{config['name']}'")
                return False
            
            # Delete configuration
            result = self.collection.delete_one({"_id": config_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted configuration '{config['name']}'")
                return True
            else:
                logger.error(f"Failed to delete configuration {config_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting configuration {config_id}: {e}")
            return False
    
    def sync_to_env_file(self, env_vars: Dict[str, Any]) -> bool:
        """
        Sync environment variables to .env file
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Backup existing .env file
            backup_path = self.env_path.with_suffix('.env.backup')
            if self.env_path.exists():
                import shutil
                shutil.copy2(self.env_path, backup_path)
                logger.info(f"Backed up existing .env file to {backup_path}")
            
            # Clear existing .env file
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write("# Environment variables managed by Configuration System\n")
                f.write(f"# Last updated: {datetime.now().isoformat()}\n\n")
            
            # Write new environment variables
            for key, value in env_vars.items():
                if value is not None and str(value).strip():  # Only set non-empty values
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
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about current environment configuration
        
        Returns:
            Dict[str, Any]: Environment information
        """
        try:
            # Get active configuration
            active_config = self.get_active_configuration()
            
            # Get .env file info
            env_vars = self.load_from_env_file()
            
            # Get all configurations count
            total_configs = self.collection.count_documents({})
            
            return {
                "active_configuration": active_config,
                "total_configurations": total_configs,
                "env_file": {
                    "path": str(self.env_path),
                    "exists": self.env_path.exists(),
                    "variables_count": len(env_vars)
                },
                "sync_status": {
                    "in_sync": (active_config and 
                               active_config["variables"] == env_vars) if active_config else False,
                    "active_config_vars": len(active_config["variables"]) if active_config else 0,
                    "env_file_vars": len(env_vars)
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
def get_enhanced_env_manager() -> EnhancedEnvironmentManager:
    """Get a configured EnhancedEnvironmentManager instance"""
    return EnhancedEnvironmentManager()

def create_environment_configuration(name: str, description: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to create a new environment configuration"""
    manager = get_enhanced_env_manager()
    try:
        return manager.create_configuration(name, description, variables)
    finally:
        manager.close()

def activate_environment_configuration(config_id: str) -> bool:
    """Quick function to activate an environment configuration"""
    manager = get_enhanced_env_manager()
    try:
        return manager.activate_configuration(config_id)
    finally:
        manager.close()

def get_all_environment_configurations() -> List[Dict[str, Any]]:
    """Quick function to get all environment configurations"""
    manager = get_enhanced_env_manager()
    try:
        return manager.get_all_configurations()
    finally:
        manager.close()

# Example usage and testing
if __name__ == "__main__":
    # Test the enhanced environment manager
    manager = EnhancedEnvironmentManager()
    
    try:
        print("🧪 Testing Enhanced Environment Manager")
        print("=" * 60)
        
        # Test creating configurations
        print("1. Creating test configurations...")
        
        # Production configuration
        prod_vars = {
            "OPENAI_API_KEY": "sk-prod-key-123",
            "MONGO_URL": "mongodb://prod-server:27017/",
            "PINECONE_API_KEY": "prod-pinecone-key",
            "PINECONE_ENV": "us-west1-gcp",
            "EMBEDDING_MODEL": "text-embedding-3-small",
            "FACEBOOK_ACCESS_TOKEN": "prod-facebook-token",
            "EMAIL_ADMIN": "admin@production.com"
        }
        
        prod_config = manager.create_configuration(
            "Production",
            "Production environment configuration",
            prod_vars
        )
        print(f"   ✅ Created Production config: {prod_config['id']}")
        
        # Development configuration
        dev_vars = {
            "OPENAI_API_KEY": "sk-dev-key-123",
            "MONGO_URL": "mongodb://localhost:27017/",
            "PINECONE_API_KEY": "dev-pinecone-key",
            "PINECONE_ENV": "us-west1-gcp",
            "EMBEDDING_MODEL": "text-embedding-3-small",
            "FACEBOOK_ACCESS_TOKEN": "dev-facebook-token",
            "EMAIL_ADMIN": "admin@development.com"
        }
        
        dev_config = manager.create_configuration(
            "Development",
            "Development environment configuration",
            dev_vars
        )
        print(f"   ✅ Created Development config: {dev_config['id']}")
        
        # Test getting all configurations
        print("\n2. Getting all configurations...")
        all_configs = manager.get_all_configurations()
        print(f"   ✅ Found {len(all_configs)} configurations")
        for config in all_configs:
            print(f"      - {config['name']}: {config['description']}")
        
        # Test activating configuration
        print("\n3. Activating Development configuration...")
        success = manager.activate_configuration(dev_config['id'])
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        # Test getting active configuration
        print("\n4. Getting active configuration...")
        active_config = manager.get_active_configuration()
        if active_config:
            print(f"   ✅ Active: {active_config['name']}")
        else:
            print("   ❌ No active configuration")
        
        # Test environment info
        print("\n5. Getting environment information...")
        info = manager.get_environment_info()
        print(f"   Total configurations: {info['total_configurations']}")
        print(f"   .env file variables: {info['env_file']['variables_count']}")
        print(f"   In sync: {'✅ Yes' if info['sync_status']['in_sync'] else '❌ No'}")
        
        # Test updating configuration
        print("\n6. Updating Development configuration...")
        updated_vars = dev_vars.copy()
        updated_vars["NEW_VARIABLE"] = "test-value"
        success = manager.update_configuration(dev_config['id'], updated_vars)
        print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
        
        print("\n🎉 Enhanced Environment Manager test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.close()