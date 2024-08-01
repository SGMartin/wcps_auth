from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    ## Database 
    database_name: str = "auth_test"
    database_user: str = "root"
    database_password: str = "root"
    database_port: int = 3306

    ## Networking
    server_ip: str = "127.0.0.1"

    class Config:
        env_file = ".env"


settings = Settings