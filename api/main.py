from fastapi import FastAPI, HTTPException, status
import psycopg2
from psycopg2.extras import RealDictCursor
from config import config

app = FastAPI()

def get_db():
    params = config()
    conn = psycopg2.connect(**params, cursor_factory=RealDictCursor)
    return conn

@app.get("/titles")
def get_titles():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM game ORDER BY id;")
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

@app.get("/titles/{id}")
def get_title(id: int):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM game WHERE id = %s;", (id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося знайти гру")
        return row
    finally:
        conn.close()

@app.get("/prices/{id}")
def get_prices(id: int):
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT name FROM site")
        site_names = [row['name'] for row in cur.fetchall()]

        columns = ', '.join([f'{name}_id' for name in site_names])
        cur.execute(f"SELECT {columns} FROM game WHERE id = %s", (id,))
        ids = cur.fetchone()

        if not ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося знайти гру")

        result = {}
        for site, site_id in zip(site_names, ids.values()):
            if site_id is None:
                continue

            cur.execute(f"""SELECT id, title, price, in_stock, url, lastchecked
                        FROM {site} 
                        WHERE id = %s""", (site_id,))

            shop = cur.fetchone()
            if shop:
                result[site] = shop

        return result

    finally:
        conn.close()

@app.get('/history/{id}')
def get_history(id: int):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""SELECT site.name, history.price, history.checkdate 
                        FROM history
                        JOIN site
                        ON history.site_id = site.id
                        WHERE history.game_id = %s
                        ORDER BY history.checkdate;""", (id,))
        
        rows = cur.fetchall()
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не вдалося знайти гру")
        
        result = {}
        for row in rows:
            site_name = row['name']
            price = row['price']
            date = row['checkdate']

            if result.get(site_name) is None:
                result[site_name] = {date: price}
            else:
                result[site_name].update({date: price})
                
        return result
    finally:
        conn.close()
