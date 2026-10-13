from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sig_alfa_clave_secreta_admin')

DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:DMR007@localhost:5432/sig_alfa'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluaciones_sensoriales (
                id SERIAL PRIMARY KEY,
                nombre_estudiante VARCHAR(100) NOT NULL,
                identificacion VARCHAR(50),
                edad INT NOT NULL,
                condicion VARCHAR(50) NOT NULL,
                kit_utilizado VARCHAR(100) NOT NULL,
                nivel_atencion VARCHAR(20) NOT NULL,
                adulto_responsable VARCHAR(100),
                telefono VARCHAR(20),
                contacto_emergencia VARCHAR(100),
                email VARCHAR(100),
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")

init_db()

def calcular_diagnostico(kit, atencion, condicion):
    niveles = {"Alto": 90, "Medio": 65, "Bajo": 40}
    score = niveles.get(atencion, 50)
    recomendaciones = {
        "TDAH": "Se recomienda sesiones cortas de 10-15 min utilizando kits táctiles de alta textura para mantener el foco.",
        "Autismo": "Utilizar estímulos auditivos y visuales de baja intensidad para evitar sobrecarga sensorial.",
        "Desarrollo Típico": "Implementar dinámicas integrales que combinen estimulación visual y motriz fina.",
        "Síndrome de Down": "Reforzar actividades de coordinación oculo-manual mediante kits de formas geométricas."
    }
    rec = recomendaciones.get(condicion, "Mantener seguimiento continuo con los kits de apoyo sensorial.")
    return score, rec

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/guardar', methods=['POST'])
def guardar():
    if request.method == 'POST':
        nombre = request.form.get('nombre_estudiante') or request.form.get('nombre_paciente') or request.form.get('nombre')
        identificacion = request.form.get('identificacion')
        edad = request.form.get('edad')
        condicion = request.form.get('condicion')
        kit = request.form.get('kit_utilizado') or request.form.get('kit')
        atencion = request.form.get('nivel_atencion') or request.form.get('atencion')
        adulto = request.form.get('adulto_responsable')
        telefono = request.form.get('telefono')
        emergencia = request.form.get('contacto_emergencia')
        email = request.form.get('email')
        observaciones = request.form.get('observaciones')
        
        score, recomendacion = calcular_diagnostico(kit, atencion, condicion)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO evaluaciones_sensoriales 
                (nombre_estudiante, identificacion, edad, condicion, kit_utilizado, nivel_atencion, adulto_responsable, telefono, contacto_emergencia, email, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nombre, identificacion, edad, condicion, kit, atencion, adulto, telefono, emergencia, email, observaciones))
            conn.commit()
            cur.close()
            conn.close()
            
            return render_template('exito.html', 
                                   nombre=nombre, 
                                   kit=kit, 
                                   score=score, 
                                   atencion=atencion, 
                                   recomendacion=recomendacion)
        except Exception as e:
            flash(f"Error al guardar: {e}", "danger")
            return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "DKD":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Contraseña incorrecta", "danger")
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM evaluaciones_sensoriales ORDER BY id DESC;")
        evaluaciones = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('admin.html', evaluaciones=evaluaciones)
    except Exception as e:
        return f"Error en la base de datos: {e}"

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)