import sqlite3
from datetime import datetime, timedelta
import random

def setup_performance_db():
    # Creamos la base de datos en tu carpeta de database
    conn = sqlite3.connect('src/database/kinetic_guard.db')
    cursor = conn.cursor()

    # Tabla de métricas diarias del atleta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id TEXT,
            fecha DATE,
            carga_entrenamiento REAL, -- Volumen total (kg o km)
            hrv_ms INTEGER,             -- Variabilidad Cardíaca (mide recuperación)
            horas_sueno REAL,
            rpe_fatiga INTEGER          -- Esfuerzo percibido 1-10
        )
    ''')

    # Poblamos con datos ficticios
    atleta = "atleta_01"
    hoy = datetime.now()
    
    for i in range(30, -1, -1):
        fecha = (hoy - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Simulamos una tendencia: los últimos 5 días la carga sube mucho (Riesgo)
        if i < 5:
            carga = random.uniform(800, 1000) 
            hrv = random.randint(30, 45)       # HRV bajo = mala recuperación
            rpe = random.randint(8, 10)
        else:
            carga = random.uniform(400, 600)
            hrv = random.randint(55, 75)
            rpe = random.randint(4, 7)
            
        cursor.execute('''
            INSERT INTO daily_metrics (atleta_id, fecha, carga_entrenamiento, hrv_ms, horas_sueno, rpe_fatiga)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (atleta, fecha, carga, hrv, random.uniform(6, 8), rpe))

    conn.commit()
    conn.close()
    print("📊 Base de datos SQL 'kinetic_guard.db' creada con éxito.")

if __name__ == "__main__":
    setup_performance_db()