"""
Visor de Base de Datos — Servicio independiente de cita.me

Contenedor separado, puerto separado, sin relación con la app principal.
Se conecta directamente al archivo SQLite compartido por volumen.

Para acceder: http://localhost:8080
NO existe link desde cita.me.
"""
import logging
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DB Viewer — cita.me",
    description="Visor de base de datos (servicio aislado)",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


# ════════════════════════════════════════
# HTML embebido — interfaz completa
# ════════════════════════════════════════

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DB Viewer — cita.me</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Segoe UI',system-ui,sans-serif;background:#f4f6f4;color:#1a2e1a}
  .header{background:#1a2e1a;color:#fff;padding:16px 24px;display:flex;align-items:center;gap:12px}
  .header h1{font-size:16px;font-weight:700;letter-spacing:-0.3px}
  .header .tag{background:#16a34a;color:#fff;font-size:10px;font-weight:700;padding:2px 8px;border-radius:4px;letter-spacing:0.5px}
  .layout{display:flex;height:calc(100vh - 53px)}
  .sidebar{width:260px;background:#fff;border-right:1px solid #d4e4d4;overflow-y:auto;flex-shrink:0}
  .sidebar-title{font-size:11px;font-weight:700;color:#888;text-transform:uppercase;padding:14px 16px 8px;letter-spacing:0.5px}
  .tbl-btn{display:block;width:100%;text-align:left;padding:10px 16px;border:none;background:none;cursor:pointer;font-size:13px;color:#333;transition:background 0.15s}
  .tbl-btn:hover{background:#f0fdf4}
  .tbl-btn.active{background:#dcfce7;color:#15803d;font-weight:600}
  .tbl-btn .meta{font-size:11px;color:#999;margin-top:1px}
  .main{flex:1;overflow-y:auto;padding:20px 24px}
  .sql-box{margin-bottom:20px}
  .sql-box textarea{width:100%;padding:10px 14px;border:1px solid #d4e4d4;border-radius:8px;font-family:'Courier New',monospace;font-size:12px;resize:vertical;min-height:60px;outline:none;transition:border 0.2s}
  .sql-box textarea:focus{border-color:#16a34a}
  .sql-box button{margin-top:6px;padding:7px 18px;background:#1a2e1a;color:#fff;border:none;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;transition:background 0.15s}
  .sql-box button:hover{background:#166534}
  .info-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .info-bar h2{font-size:16px;font-weight:700}
  .info-bar .stats{font-size:12px;color:#888}
  .badges{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
  .badge{display:inline-flex;align-items:center;gap:4px;padding:3px 8px;border-radius:4px;font-size:11px;font-weight:600;border:1px solid}
  .badge.pk{background:#fef3c7;color:#92400e;border-color:#fcd34d}
  .badge.nn{background:#f1f5f9;color:#475569;border-color:#cbd5e1}
  .badge.normal{background:#f8fafc;color:#94a3b8;border-color:#e2e8f0}
  .badge .type{font-size:9px;opacity:0.6}
  table{width:100%;border-collapse:collapse;font-size:12px;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #d4e4d4}
  thead{background:#f8faf8}
  th{text-align:left;padding:10px 14px;font-weight:600;color:#666;border-bottom:2px solid #d4e4d4;white-space:nowrap}
  td{padding:8px 14px;border-bottom:1px solid #f0f4f0;white-space:nowrap;max-width:300px;overflow:hidden;text-overflow:ellipsis}
  tr:hover td{background:#f0fdf4}
  td.null{color:#ccc;font-style:italic}
  .pager{display:flex;align-items:center;gap:8px;margin-top:14px}
  .pager button{padding:6px 14px;border:1px solid #d4e4d4;border-radius:6px;background:#fff;font-size:12px;cursor:pointer;transition:all 0.15s}
  .pager button:hover:not(:disabled){background:#f0fdf4;border-color:#16a34a}
  .pager button:disabled{opacity:0.3;cursor:not-allowed}
  .pager span{font-size:12px;color:#888}
  .empty{text-align:center;padding:48px;color:#aaa}
  .error{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:14px}
</style>
</head>
<body>
<div class="header">
  <h1>DB Viewer</h1>
  <span class="tag">CITAME</span>
  <span style="flex:1"></span>
  <span style="font-size:11px;color:#999">Servicio aislado · Puerto 8080</span>
</div>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-title">Tablas</div>
    <div id="table-list">Cargando...</div>
    <div style="padding:12px 16px;border-top:1px solid #eee;margin-top:8px">
      <div class="sidebar-title" style="padding:0 0 8px">SQL</div>
      <textarea id="sql-input" rows="3" placeholder="SELECT * FROM ..." style="width:100%;padding:8px;border:1px solid #d4e4d4;border-radius:6px;font-size:11px;font-family:monospace;resize:vertical;outline:none"></textarea>
      <button onclick="runSQL()" style="width:100%;margin-top:6px;padding:6px;background:#1a2e1a;color:#fff;border:none;border-radius:6px;font-size:11px;font-weight:600;cursor:pointer">Ejecutar</button>
    </div>
  </div>

  <div class="main" id="main-content">
    <div class="empty">Seleccione una tabla para ver sus datos</div>
  </div>
</div>

<script>
let currentPage = 1;
let currentTable = '';

async function loadTables() {
  try {
    const r = await fetch('/api/tables');
    const d = await r.json();
    const el = document.getElementById('table-list');
    el.innerHTML = d.tables.map(t =>
      '<button class="tbl-btn" onclick="selectTable(\\'' + t.name + '\\')">' +
      '<div>' + t.name + '</div>' +
      '<div class="meta">' + t.rows + ' filas · ' + t.columns + ' cols</div>' +
      '</button>'
    ).join('');
  } catch(e) {
    document.getElementById('table-list').innerHTML = '<span style="color:red;font-size:12px;padding:8px 16px">Error cargando tablas</span>';
  }
}

async function selectTable(name) {
  currentTable = name;
  currentPage = 1;
  document.querySelectorAll('.tbl-btn').forEach(b => b.classList.remove('active'));
  event.currentTarget.classList.add('active');
  await loadTableData(name, 1);
}

async function loadTableData(name, page) {
  currentPage = page;
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="empty">Cargando...</div>';
  try {
    const r = await fetch('/api/table/' + name + '?page=' + page);
    const d = await r.json();

    let html = '<div class="info-bar"><h2>' + d.table + '</h2><div class="stats">' +
      d.total_rows + ' filas · Página ' + d.page + ' de ' + d.total_pages + '</div></div>';

    html += '<div class="badges">' + d.columns.map(c => {
      const cls = c.pk ? 'pk' : c.not_null ? 'nn' : 'normal';
      return '<span class="badge ' + cls + '">' + c.name + ' <span class="type">' + c.type + '</span>' +
        (c.pk ? ' PK' : '') + '</span>';
    }).join('') + '</div>';

    if (d.data.length === 0) {
      html += '<div class="empty">Tabla vacía</div>';
    } else {
      html += '<table><thead><tr>' + d.columns.map(c =>
        '<th>' + c.name + '</th>').join('') + '</tr></thead><tbody>';
      d.data.forEach(row => {
        html += '<tr>' + d.columns.map(c => {
          const v = row[c.name];
          return '<td' + (v === null ? ' class="null"' : '') + '>' + (v === null ? 'null' : escHtml(String(v))) + '</td>';
        }).join('') + '</tr>';
      });
      html += '</tbody></table>';

      html += '<div class="pager">' +
        '<button onclick="loadTableData(\\'' + name + '\\',' + (page-1) + ')"' + (page <= 1 ? ' disabled' : '') + '>← Anterior</button>' +
        '<span>' + page + ' / ' + d.total_pages + '</span>' +
        '<button onclick="loadTableData(\\'' + name + '\\',' + (page+1) + ')"' + (page >= d.total_pages ? ' disabled' : '') + '>Siguiente →</button>' +
        '</div>';
    }

    main.innerHTML = html;
  } catch(e) {
    main.innerHTML = '<div class="error">Error cargando tabla: ' + e.message + '</div>';
  }
}

async function runSQL() {
  const sql = document.getElementById('sql-input').value.trim();
  if (!sql) return;
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="empty">Ejecutando...</div>';
  try {
    const r = await fetch('/api/query?sql=' + encodeURIComponent(sql));
    if (!r.ok) {
      const err = await r.json();
      throw new Error(err.detail);
    }
    const d = await r.json();

    let html = '<div class="info-bar"><h2>Resultado</h2><div class="stats">' +
      d.rows + ' filas</div></div>';
    html += '<p style="font-size:12px;color:#666;margin-bottom:12px;font-family:monospace;background:#f8faf8;padding:8px;border-radius:6px">' +
      escHtml(d.query) + '</p>';

    if (d.data.length === 0) {
      html += '<div class="empty">Sin resultados</div>';
    } else {
      html += '<table><thead><tr>' + d.columns.map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>';
      d.data.forEach(row => {
        html += '<tr>' + d.columns.map(c => {
          const v = row[c];
          return '<td' + (v === null ? ' class="null"' : '') + '>' + (v === null ? 'null' : escHtml(String(v))) + '</td>';
        }).join('') + '</tr>';
      });
      html += '</tbody></table>';
    }
    main.innerHTML = html;
  } catch(e) {
    main.innerHTML = '<div class="error">Error: ' + escHtml(e.message) + '</div>';
  }
}

function escHtml(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

loadTables();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    """Página principal del visor."""
    return HTML_PAGE


@app.get("/api/tables")
async def api_tables(session: AsyncSession = Depends(get_session)):
    """Listar todas las tablas con metadatos."""
    try:
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ))
        tablas_raw = [row[0] for row in result.all()]
        tablas = [t for t in tablas_raw if t != "alembic_version"]

        info = []
        for tabla in tablas:
            try:
                cnt = await session.execute(text(f'SELECT COUNT(*) FROM "{tabla}"'))
                rows = cnt.scalar()
            except Exception:
                rows = -1
            try:
                cols = await session.execute(text(f'PRAGMA table_info("{tabla}")'))
                columnas = len(cols.all())
            except Exception:
                columnas = 0
            info.append({"name": tabla, "rows": rows, "columns": columnas})

        return {"tables": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/table/{nombre}")
async def api_table(
    nombre: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Datos de una tabla con paginación."""
    if not nombre.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Nombre inválido")

    try:
        check = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:n"
        ), {"n": nombre})
        if not check.fetchone():
            raise HTTPException(status_code=404, detail="Tabla no existe")

        total = await session.execute(text(f'SELECT COUNT(*) FROM "{nombre}"'))
        total_rows = total.scalar()

        cols = await session.execute(text(f'PRAGMA table_info("{nombre}")'))
        columns = [{"name": r[1], "type": r[2], "not_null": bool(r[3]), "pk": bool(r[5])} for r in cols.all()]
        col_names = [c["name"] for c in columns]

        offset = (page - 1) * per_page
        data_r = await session.execute(
            text(f'SELECT * FROM "{nombre}" ORDER BY rowid LIMIT :l OFFSET :o'),
            {"l": per_page, "o": offset}
        )
        data = [dict(zip(col_names, row)) for row in data_r.all()]
        total_pages = max(1, (total_rows + per_page - 1) // per_page)

        return {
            "table": nombre,
            "columns": columns,
            "total_rows": total_rows,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query")
async def api_query(
    sql: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    """Ejecutar SQL SELECT (solo lectura)."""
    upper = sql.strip().upper()
    if not upper.startswith("SELECT"):
        raise HTTPException(status_code=403, detail="Solo SELECT")
    for word in ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "ATTACH"]:
        if word in upper:
            raise HTTPException(status_code=403, detail=f"'{word}' no permitido")
    try:
        result = await session.execute(text(sql))
        cols = list(result.keys()) if result.returns_rows else []
        data = [dict(zip(cols, row)) for row in result.all()]
        return {"query": sql, "columns": cols, "rows": len(data), "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))