# Clínica MVP Plus
MVP académico con Flask, SQLite, SQLAlchemy, Jinja2, HTML5, CSS y JavaScript vanilla.

## Inicio
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
La base y los datos demo se crean automáticamente.

## Usuarios
- admin@clinica.demo / demo123
- recepcion@clinica.demo / demo123
- medico@clinica.demo / demo123

## Plus
- Calendario mensual
- Tipos de reservación
- Pago ficticio
- Email por SMTP o bandeja demo `instance/outbox.log`
- Tasa BCV configurable, caché y contingencia manual
- Precios de exámenes USD/Bs
- Centro QA por módulos
- Modo oscuro
- Auditoría clínica

> Datos ficticios. No es un sistema clínico certificado. La API de tasa externa puede requerir API Key; el sistema conserva fallback manual.
