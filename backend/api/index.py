from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response
from .langgraph.course_eval.agent import assistant_ui_graph as ce_graph
from .routes.add_langgraph_route import add_langgraph_route as add_ce_route
from .langgraph.virtual_ta.agent import ta_ui_graph  as ta_graph
from .routes.add_langgraph_route_ta import add_langgraph_route as add_ta_route
from .database.mongodb import MongoDB
from .routes.file_routes import router as file_router
from .routes.auth_routes import router as auth_router
from .routes.feedback_routes import router as feedback_router
from .routes.logging_routes import router as logging_router
from .utils.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager








@asynccontextmanager
async def lifespan(app: FastAPI):
   # Code to run before the app starts
   MongoDB.connect_db()
   # Initialize the scheduler
   scheduler = BackgroundScheduler()
   # Start after 1 minute from now
   start_time = datetime.now() + timedelta(minutes=5)
   scheduler.add_job(sync_health_check, 'interval', minutes=1, next_run_time=start_time)
   scheduler.start()
   yield
   # Code to run after the app shuts down
   MongoDB.close_db()




app = FastAPI(lifespan=lifespan)




# Get environment
ENVIRONMENT = os.getenv("DEPLOYMENT_ENV", "development")
BASE_URL = "https://comment-sense-1.onrender.com" if ENVIRONMENT == "production" else "http://localhost:8000"


# CORS configuration - Must be added before any routes
app.add_middleware(
   CORSMiddleware,
   allow_origins=[
       "http://localhost:3000",
       "http://127.0.0.1:3000"
       "https://comment-sense-delta.vercel.app",
       BASE_URL,
   ],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
   expose_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
   return {"status": "healthy", "message": "Service is running"}


def sync_health_check():
   try:
       health_url = f"{BASE_URL}/health"
       response = requests.get(health_url)
       if response.status_code == 200:
           logger.info(f"Health check passed for {health_url}")
       else:
           logger.error(f"Health check failed for {health_url} with status code: {response.status_code}")
   except Exception as e:
       logger.error(f"Health check failed with error: {str(e)}")


# Add routes
# Course Eval bot
add_ce_route(app, ce_graph, "/api/course-eval/chat")


# Virtual TA bot
add_ta_route(app, ta_graph, "/api/virtual-ta/chat")
app.include_router(file_router, prefix="/api/files", tags=["files"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["feedback"])
app.include_router(logging_router)  # No prefix needed as it's defined in the router




if __name__ == "__main__":
   import uvicorn
   uvicorn.run(app, host="0.0.0.0", port=8000)
