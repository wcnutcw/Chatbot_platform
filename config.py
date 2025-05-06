# from pydantic_settings import BaseSettings , SettingsConfigDict
# from pydantic import ValidationError


# class Settings(BaseSettings): 
    
#         model_config = SettingsConfigDict(
#              env_file=(
#         "./venv/dev.env"
#         )
#     )
        
  

# try:
#     config = Settings()
# except ValidationError as e:
#     print("Missing required settings:", e)
#     print(repr(e.errors()[0]['type']))
#     raise