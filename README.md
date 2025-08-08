Afiliados App (Flask)
Flask-Babel

Este proyecto es una aplicación web de afiliados construida con Python y el microframework Flask. Su objetivo es mostrar productos destacados, guías de compra y comparativas confiables para ayudar a los usuarios a tomar decisiones de compra informadas.

🧩 Características Principales
✅ Página de Inicio: Muestra productos destacados y secciones relevantes.

🛠️ Gestión de Productos: CRUD completo con enlaces de afiliado, descripciones, precios e imágenes.

🗂️ Categorías y Subcategorías: Organización jerárquica de productos.

📚 Guías y Artículos: Publicación de contenido especializado.

🔐 Panel de Administración: Protegido con autenticación.

📄 Páginas Informativas: Contacto, Política de Privacidad, Términos y Condiciones, Cookies.

📈 SEO Amigable: sitemap.xml y robots.txt generados dinámicamente.

📱 Diseño Responsivo: Con Bootstrap 5.3.

🎨 Modo Oscuro: Alternancia de temas claro/oscuro.

🌍 Traductor de Google: Widget de traducción automático.

⭐ Iconografía: Usa Font Awesome 6.5.

🔄 Sincronización API (Opcional): Posibilidad de sincronizar productos desde una API externa (configurable desde el panel de administración).

⚙️ Instalación y Ejecución Local
Sigue estos pasos para configurar y ejecutar la aplicación en tu entorno local.

1. Clona el Repositorio
git clone <URL_DEL_REPOSITORIO>
cd afiliados_app

2. Crea y Activa el Entorno Virtual
python -m venv venv
# En macOS/Linux
source venv/bin/activate
# En Windows
venv\Scripts\activate

3. Instala las Dependencias
pip install -r requirements.txt

4. Configura las Variables de Entorno
Copia el archivo .env.example a un nuevo archivo llamado .env y edita las variables.

cp .env.example .env
# Luego edita el archivo .env con tus credenciales

5. Ejecuta las Migraciones de Base de Datos y Semillas
flask db upgrade
flask seed-db

6. Ejecuta la Aplicación
flask run

La aplicación estará disponible en http://127.0.0.1:5000.

🚀 Despliegue
Para desplegar en Render, usa estos comandos:

Build Command: pip install -r requirements.txt && flask db upgrade && flask seed-db

Start Command: gunicorn --bind 0.0.0.0:$PORT --timeout 120 app:create_app