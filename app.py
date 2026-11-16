"""
Entrada de la aplicación Flask.
Crea la app y registra el Blueprint de pólizas.
"""

from flask import Flask

from controllers.polizas_controller import polizas_bp

# variable tipo Flask: la aplicación
app = Flask(
    __name__,
    template_folder="views",
    static_folder="public/static",
    static_url_path="/static",
)

# registramos el Blueprint de rutas
app.register_blueprint(polizas_bp)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
