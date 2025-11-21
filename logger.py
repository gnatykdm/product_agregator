from logging import Logger, getLogger, StreamHandler, Formatter, DEBUG

def get_logger(__name__: str) -> Logger:
    logger: Logger = getLogger(__name__)
    if not logger.handlers:
        handler: StreamHandler = StreamHandler()
        fmt: Formatter = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(Formatter(fmt))
        logger.addHandler(handler)
        logger.setLevel(DEBUG)
        logger.propagate = False
    return logger