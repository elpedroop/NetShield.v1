import os
import stripe
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# ── RUTA PRINCIPAL ─────────────────────────────────────────────────
@app.route("/")
def index():
    pub_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    return render_template("index.html", stripe_pub_key=pub_key)


# ── API: FORMULARIO DE CONTACTO ────────────────────────────────────
@app.route("/api/contacto", methods=["POST"])
def contacto():
    data    = request.get_json(silent=True) or {}
    nombre  = data.get("nombre", "").strip()
    email   = data.get("email", "").strip()
    tipo    = data.get("tipo", "")
    mensaje = data.get("mensaje", "")

    if not nombre or not email:
        return jsonify({"error": "Nombre y correo son requeridos."}), 400

    # Aquí puedes guardar en DB, enviar email, etc.
    print(f"[CONTACTO] {nombre} <{email}> | {tipo}: {mensaje}")

    return jsonify({"mensaje": "¡Mensaje recibido! Te contactaremos en menos de 24 horas."})


# ── API: CREAR SESIÓN DE PAGO STRIPE ──────────────────────────────
@app.route("/api/crear-sesion", methods=["POST"])
def crear_sesion():
    data = request.get_json(silent=True) or {}
    plan = data.get("plan")  # "basico", "pro", "empresarial"

    precios = {
        "basico":      {"amount": 49900,  "name": "Plan Básico"},
        "pro":         {"amount": 129900, "name": "Plan Pro"},
        "empresarial": {"amount": 299900, "name": "Plan Empresarial"},
    }

    if plan not in precios:
        return jsonify({"error": "Plan inválido"}), 400

    # Detectar dominio base dinámicamente (local o producción)
    base_url = os.getenv("BASE_URL", "http://localhost:5000")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "mxn",
                    "recurring": {"interval": "month"},
                    "product_data": {"name": precios[plan]["name"]},
                    "unit_amount": precios[plan]["amount"],
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{base_url}/gracias",
            cancel_url=f"{base_url}/#planes",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── PÁGINA DE ÉXITO ────────────────────────────────────────────────
@app.route("/gracias")
def gracias():
    return render_template("gracias.html")


if __name__ == "__main__":
    app.run(debug=True)