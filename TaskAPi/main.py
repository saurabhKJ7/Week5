from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

tasks = []
task_counter = 1

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

@app.get("/api/tasks")
def get_tasks():
    return tasks

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    global task_counter
    new_task = {
        "id": task_counter,
        "title": task.title,
        "completed": False
    }
    tasks.append(new_task)
    task_counter += 1
    return new_task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title is not None:
                task["title"] = task_update.title
            if task_update.completed is not None:
                task["completed"] = task_update.completed
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "tasks": tasks}
    )

@app.post("/tasks")
def create_task_form(title: str = Form(...)):
    global task_counter
    new_task = {
        "id": task_counter,
        "title": title,
        "completed": False
    }
    tasks.append(new_task)
    task_counter += 1
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/{task_id}/toggle")
def toggle_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = not task["completed"]
            break
    return RedirectResponse(url="/", status_code=303)

@app.post("/tasks/{task_id}/delete")
def delete_task_form(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            break
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 