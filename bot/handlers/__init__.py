from .commands import router as commands_router
from .messages import router as message_router

handlers_routers = [commands_router, message_router]