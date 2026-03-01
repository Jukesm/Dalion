import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ceo_ia.db")

HOT_MEMORY_PATH = "memory_hot.txt"
WARM_MEMORY_PATH = "memory_warm.txt"
COLD_MEMORY_PATH = "memory_cold.txt"
