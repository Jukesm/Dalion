from config import HOT_MEMORY_PATH, WARM_MEMORY_PATH, COLD_MEMORY_PATH

def save_memory(content, level="hot"):
    path_map = {
        "hot": HOT_MEMORY_PATH,
        "warm": WARM_MEMORY_PATH,
        "cold": COLD_MEMORY_PATH
    }

    with open(path_map[level], "a", encoding="utf-8") as f:
        f.write(content + "\n")
