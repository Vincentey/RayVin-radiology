from pydantic_settings import BaseSettings

class MySettings(BaseSettings):
    approved_modality: list = ["CR","DX","CT","MR"]


settings = MySettings()