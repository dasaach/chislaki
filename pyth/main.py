import sqlite3
from contextlib import contextmanager
from typing import List, Optional
from xml.dom import minidom

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel, Field
import jinja2

DB_PATH = "excursion.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# =========================
# Pydantic модели
# =========================

class GuideBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150)
    experience_years: int = Field(..., ge=0, le=50)

class Guide(GuideBase):
    id: int


class ExcursionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    city: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., ge=0)
    guide_id: int

class Excursion(ExcursionBase):
    id: int
    guide_name: Optional[str] = None


class ClientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150)
    phone: str = Field(..., min_length=1, max_length=30)
    email: str = Field(..., min_length=1, max_length=100)

class Client(ClientBase):
    id: int


class BookingBase(BaseModel):
    client_id: int
    excursion_id: int
    booking_date: str
    people_count: int = Field(..., ge=1)

class Booking(BookingBase):
    id: int
    client_name: Optional[str] = None
    excursion_title: Optional[str] = None

# =========================
# FastAPI
# =========================

app = FastAPI(title="Excursion Bureau API")

TEMPLATES_DIR = "templates"

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    autoescape=True
)

# =========================
# Вспомогательные функции
# =========================

def _check_foreign_key(conn: sqlite3.Connection, table: str, id: int) -> bool:
    cursor = conn.cursor()
    cursor.execute(f"SELECT 1 FROM {table} WHERE id = ?", (id,))
    return cursor.fetchone() is not None

# =========================
# Создание записей
# =========================

def _create_guide_in_db(full_name: str, experience_years: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO guides (full_name, experience_years)
            VALUES (?, ?)
            """,
            (full_name, experience_years)
        )

        conn.commit()
        return cursor.lastrowid


def _create_excursion_in_db(title: str, city: str, price: float, guide_id: int):
    with get_db_connection() as conn:

        if not _check_foreign_key(conn, "guides", guide_id):
            raise ValueError("Гид не найден")

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO excursions (title, city, price, guide_id)
            VALUES (?, ?, ?, ?)
            """,
            (title, city, price, guide_id)
        )

        conn.commit()
        return cursor.lastrowid


def _create_client_in_db(full_name: str, phone: str, email: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO clients (full_name, phone, email)
            VALUES (?, ?, ?)
            """,
            (full_name, phone, email)
        )

        conn.commit()
        return cursor.lastrowid


def _create_booking_in_db(client_id: int, excursion_id: int,
                           booking_date: str, people_count: int):

    with get_db_connection() as conn:

        if not _check_foreign_key(conn, "clients", client_id):
            raise ValueError("Клиент не найден")

        if not _check_foreign_key(conn, "excursions", excursion_id):
            raise ValueError("Экскурсия не найдена")

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO bookings
            (client_id, excursion_id, booking_date, people_count)
            VALUES (?, ?, ?, ?)
            """,
            (client_id, excursion_id, booking_date, people_count)
        )

        conn.commit()
        return cursor.lastrowid

# =========================
# API endpoints
# =========================

# ---------- GUIDES ----------

@app.get("/guides", response_model=List[Guide])
def get_guides():

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, full_name, experience_years
            FROM guides
            ORDER BY id
        """)

        return [dict(row) for row in cursor.fetchall()]


@app.post("/guides", response_model=Guide, status_code=201)
def create_guide(guide: GuideBase):

    new_id = _create_guide_in_db(
        guide.full_name,
        guide.experience_years
    )

    return {
        "id": new_id,
        "full_name": guide.full_name,
        "experience_years": guide.experience_years
    }

# ---------- EXCURSIONS ----------

@app.get("/excursions", response_model=List[Excursion])
def get_excursions():

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.id,
                   e.title,
                   e.city,
                   e.price,
                   e.guide_id,
                   g.full_name AS guide_name
            FROM excursions e
            JOIN guides g ON e.guide_id = g.id
            ORDER BY e.id
        """)

        return [dict(row) for row in cursor.fetchall()]


@app.post("/excursions", response_model=Excursion, status_code=201)
def create_excursion(excursion: ExcursionBase):

    try:
        new_id = _create_excursion_in_db(
            excursion.title,
            excursion.city,
            excursion.price,
            excursion.guide_id
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT e.id,
                   e.title,
                   e.city,
                   e.price,
                   e.guide_id,
                   g.full_name AS guide_name
            FROM excursions e
            JOIN guides g ON e.guide_id = g.id
            WHERE e.id = ?
        """, (new_id,))

        return dict(cursor.fetchone())

# ---------- CLIENTS ----------

@app.get("/clients", response_model=List[Client])
def get_clients():

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, full_name, phone, email
            FROM clients
            ORDER BY id
        """)

        return [dict(row) for row in cursor.fetchall()]


@app.post("/clients", response_model=Client, status_code=201)
def create_client(client: ClientBase):

    new_id = _create_client_in_db(
        client.full_name,
        client.phone,
        client.email
    )

    return {
        "id": new_id,
        "full_name": client.full_name,
        "phone": client.phone,
        "email": client.email
    }

# ---------- BOOKINGS ----------

@app.get("/bookings", response_model=List[Booking])
def get_bookings():

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.id,
                   b.client_id,
                   b.excursion_id,
                   b.booking_date,
                   b.people_count,
                   c.full_name AS client_name,
                   e.title AS excursion_title
            FROM bookings b
            JOIN clients c ON b.client_id = c.id
            JOIN excursions e ON b.excursion_id = e.id
            ORDER BY b.id
        """)

        return [dict(row) for row in cursor.fetchall()]


@app.post("/bookings", response_model=Booking, status_code=201)
def create_booking(booking: BookingBase):

    try:
        new_id = _create_booking_in_db(
            booking.client_id,
            booking.excursion_id,
            booking.booking_date,
            booking.people_count
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.id,
                   b.client_id,
                   b.excursion_id,
                   b.booking_date,
                   b.people_count,
                   c.full_name AS client_name,
                   e.title AS excursion_title
            FROM bookings b
            JOIN clients c ON b.client_id = c.id
            JOIN excursions e ON b.excursion_id = e.id
            WHERE b.id = ?
        """, (new_id,))

        return dict(cursor.fetchone())

# =========================
# HTML форма
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin_form(request: Request):

    with get_db_connection() as conn:
        cursor = conn.cursor()

        guides = cursor.execute("""
            SELECT id, full_name
            FROM guides
        """).fetchall()

        clients = cursor.execute("""
            SELECT id, full_name
            FROM clients
        """).fetchall()

        excursions = cursor.execute("""
            SELECT id, title
            FROM excursions
        """).fetchall()

    template = jinja_env.get_template("admin.html")

    html_content = template.render(
        request=request,
        guides=guides,
        clients=clients,
        excursions=excursions
    )

    return HTMLResponse(content=html_content)

# =========================
# Формы
# =========================

@app.post("/add-guide")
def add_guide(
    full_name: str = Form(...),
    experience_years: int = Form(...)
):

    _create_guide_in_db(full_name, experience_years)

    return RedirectResponse(
        url="/admin",
        status_code=303
    )


@app.post("/add-client")
def add_client(
    full_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...)
):

    _create_client_in_db(full_name, phone, email)

    return RedirectResponse(
        url="/admin",
        status_code=303
    )


@app.post("/add-excursion")
def add_excursion(
    title: str = Form(...),
    city: str = Form(...),
    price: float = Form(...),
    guide_id: int = Form(...)
):

    try:
        _create_excursion_in_db(
            title,
            city,
            price,
            guide_id
        )

    except ValueError as e:
        return RedirectResponse(
            url=f"/admin?error={str(e)}",
            status_code=303
        )

    return RedirectResponse(
        url="/admin",
        status_code=303
    )


@app.post("/add-booking")
def add_booking(
    client_id: int = Form(...),
    excursion_id: int = Form(...),
    booking_date: str = Form(...),
    people_count: int = Form(...)
):

    try:
        _create_booking_in_db(
            client_id,
            excursion_id,
            booking_date,
            people_count
        )

    except ValueError as e:
        return RedirectResponse(
            url=f"/admin?error={str(e)}",
            status_code=303
        )

    return RedirectResponse(
        url="/admin",
        status_code=303
    )
@app.get("/")
def home():
    return {"message": "Экскурсионное бюро"}

# =========================
# XML EXPORT
# =========================

@app.get("/export/bookings/xml")
def export_bookings_xml():

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT b.id,
                   c.full_name AS client_name,
                   e.title AS excursion_title,
                   b.booking_date,
                   b.people_count
            FROM bookings b
            JOIN clients c ON b.client_id = c.id
            JOIN excursions e ON b.excursion_id = e.id
        """)

        rows = cursor.fetchall()

    impl = minidom.getDOMImplementation()
    doc = impl.createDocument(None, "bookings", None)

    root = doc.documentElement

    for row in rows:

        booking_elem = doc.createElement("booking")
        booking_elem.setAttribute("id", str(row["id"]))

        client_elem = doc.createElement("client_name")
        client_elem.appendChild(
            doc.createTextNode(row["client_name"])
        )
        booking_elem.appendChild(client_elem)

        excursion_elem = doc.createElement("excursion_title")
        excursion_elem.appendChild(
            doc.createTextNode(row["excursion_title"])
        )
        booking_elem.appendChild(excursion_elem)

        date_elem = doc.createElement("booking_date")
        date_elem.appendChild(
            doc.createTextNode(row["booking_date"])
        )
        booking_elem.appendChild(date_elem)

        people_elem = doc.createElement("people_count")
        people_elem.appendChild(
            doc.createTextNode(str(row["people_count"]))
        )
        booking_elem.appendChild(people_elem)

        root.appendChild(booking_elem)

    pretty_xml = doc.toprettyxml(
        indent="  ",
        encoding="utf-8"
    )

    return Response(
        content=pretty_xml,
        media_type="application/xml",
        headers={
            "Content-Disposition":
            "attachment; filename=bookings.xml"
        }
    )