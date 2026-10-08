from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="MES Cart Tracking System",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).parent.parent

DATABASE_PATH = (
    ROOT
    / "database"
    / "mes_demo.db"
)

FRONTEND_PATH = (
    ROOT
    / "frontend"
    / "index.html"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATA MODEL
# ============================================================

class ScanRequest(BaseModel):

    tag_id: str

    station_id: int = 1


# ============================================================
# WEB DASHBOARD
# ============================================================

@app.get("/")
def dashboard():

    return FileResponse(
        FRONTEND_PATH
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.get("/api/status")
def system_status():

    return {
        "system": "MES Cart Tracking System",
        "status": "ONLINE",
        "reader": "KEYENCE SR-X300",
        "database": "SQLite MES Demo Database"
    }


# ============================================================
# GET STATIONS
# ============================================================

@app.get("/api/stations")
def get_stations():

    db = get_db()

    stations = db.execute("""
        SELECT
            station_id,
            station_name,
            status
        FROM Stations
        ORDER BY station_id
    """).fetchall()

    db.close()

    return [
        dict(station)
        for station in stations
    ]


# ============================================================
# GET ALL CARTS
# ============================================================

@app.get("/api/carts")
def get_carts():

    db = get_db()

    carts = db.execute("""
        SELECT
            c.cart_id,
            c.tag_id,
            c.status,
            c.current_station,
            s.station_name,
            c.created_at

        FROM Carts c

        LEFT JOIN Stations s
            ON c.current_station = s.station_id

        ORDER BY c.cart_id DESC
    """).fetchall()

    db.close()

    return [
        dict(cart)
        for cart in carts
    ]


# ============================================================
# GET SCAN HISTORY
# ============================================================

@app.get("/api/scans")
def get_scans():

    db = get_db()

    scans = db.execute("""
        SELECT
            cs.scan_id,
            cs.tag_id,
            cs.station_id,
            s.station_name,
            cs.scan_time,
            cs.scan_result

        FROM CartScans cs

        LEFT JOIN Stations s
            ON cs.station_id = s.station_id

        ORDER BY cs.scan_id DESC

        LIMIT 100
    """).fetchall()

    db.close()

    return [
        dict(scan)
        for scan in scans
    ]


# ============================================================
# SCAN CART
# ============================================================

@app.post("/api/scan")
def scan_cart(scan: ScanRequest):

    db = get_db()

    # --------------------------------------------------------
    # Check whether TAG_ID already exists
    # --------------------------------------------------------

    cart = db.execute(
        """
        SELECT *
        FROM Carts
        WHERE tag_id = ?
        """,
        (scan.tag_id,)
    ).fetchone()


    # --------------------------------------------------------
    # Existing cart
    # --------------------------------------------------------

    if cart:

        db.execute(
            """
            UPDATE Carts

            SET
                current_station = ?,
                status = 'ACTIVE'

            WHERE tag_id = ?
            """,
            (
                scan.station_id,
                scan.tag_id
            )
        )

        result = "EXISTING_CART"


    # --------------------------------------------------------
    # New cart
    # --------------------------------------------------------

    else:

        db.execute(
            """
            INSERT INTO Carts
            (
                tag_id,
                status,
                current_station
            )

            VALUES
            (
                ?,
                'ACTIVE',
                ?
            )
            """,
            (
                scan.tag_id,
                scan.station_id
            )
        )

        result = "NEW_CART"


    # --------------------------------------------------------
    # Record the scan
    # --------------------------------------------------------

    scan_time = datetime.now().isoformat(
        timespec="seconds"
    )


    db.execute(
        """
        INSERT INTO CartScans
        (
            tag_id,
            station_id,
            scan_time,
            scan_result
        )

        VALUES
        (
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            scan.tag_id,
            scan.station_id,
            scan_time,
            "SUCCESS"
        )
    )


    # --------------------------------------------------------
    # Save changes
    # --------------------------------------------------------

    db.commit()

    db.close()


    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {

        "success": True,

        "tag_id": scan.tag_id,

        "station_id": scan.station_id,

        "result": result,

        "message":
            "Cart scan recorded successfully"

    }