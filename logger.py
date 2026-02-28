import logging
import os
from logging.handlers import RotatingFileHandler

# Criar pasta de logs se não existir
os.makedirs("logs", exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    """Configura um logger que escreve em arquivo e console."""
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler para arquivo com rotação (5MB por arquivo, mantém 5 backups)
    file_handler = RotatingFileHandler(f"logs/{log_file}", maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)

    # Handler para console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

# Logger principal da aplicação
logger = setup_logger("CEO_IA", "app.log")
# Logger específico para o pipeline autônomo
pipeline_logger = setup_logger("AutoPipeline", "pipeline.log")
