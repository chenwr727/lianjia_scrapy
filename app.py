import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.database import database
from src.utils import get_house_data

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def get_db():
    db = database.Session()
    try:
        yield db
    finally:
        db.close()


@app.get("/{date_str}", response_class=HTMLResponse)
async def read_item(date_str: str, request: Request, db: Session = Depends(get_db)):
    house_data = get_house_data(db, date_str)
    return templates.TemplateResponse(
        "house_xm_base.html",
        {"request": request, "house_date": date_str, "house_data": eval(house_data)},
    )


if __name__ == "__main__":
    uvicorn.run(app="app:app", host="0.0.0.0", port=5000)
