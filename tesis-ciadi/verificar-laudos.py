#!/usr/bin/env python3
"""
SCRIPT DE VERIFICACIÓN INTERACTIVA DE LAUDOS CIADI
===================================================
Uso: python3 verificar-laudos.py

Muestra caso por caso los datos extraídos automáticamente,
permite consultar el laudo via RAG, y registra tus correcciones.

Comandos durante la revisión:
  [ENTER]  → Confirmar datos como correctos
  c        → Corregir un campo
  r        → Consultar RAG sobre este caso
  s        → Saltar caso (revisar después)
  q        → Guardar y salir
  ?        → Ver ayuda
"""

import json, os, sys, subprocess, warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAR_PATH  = os.path.join(BASE_DIR, 'variables-extraidas.json')
LOG_VER   = os.path.join(BASE_DIR, 'verificacion-log.json')
UNCTAD_PATH = os.path.join(BASE_DIR, 'datos-capital', 'CASOS-CIADI-2000-2022.xlsx')

# ── Colores ANSI ──────────────────────────────────────────────────────────
R  = '\033[91m'; G  = '\033[92m'; Y  = '\033[93m'
B  = '\033[94m'; M  = '\033[95m'; C  = '\033[96m'
W  = '\033[97m'; DIM = '\033[2m'; BOLD = '\033[1m'; RST = '\033[0m'

def bold(s):   return f"{BOLD}{s}{RST}"
def red(s):    return f"{R}{s}{RST}"
def green(s):  return f"{G}{s}{RST}"
def yellow(s): return f"{Y}{s}{RST}"
def blue(s):   return f"{B}{s}{RST}"
def cyan(s):   return f"{C}{s}{RST}"
def dim(s):    return f"{DIM}{s}{RST}"

def clear():
    os.system('clear')

def print_banner():
    print(bold(cyan("═" * 65)))
    print(bold(cyan("  VERIFICADOR INTERACTIVO DE LAUDOS CIADI — TESIS JPCaputo")))
    print(bold(cyan("═" * 65)))

# ── Cargar datos ──────────────────────────────────────────────────────────
def load_data():
    try:
        import pandas as pd
        unctad = pd.read_excel(UNCTAD_PATH, sheet_name='CON LAUDO PÚBLICO')
        unctad_dict = {}
        for _, row in unctad.iterrows():
            url = str(row.get('Link Italaw','')).strip()
            unctad_dict[url] = {
                'nombre_completo': str(row.get('Nombre completo','')),
                'nombre_corto':    str(row.get('N° / Nombre corto','')),
                'estado':          str(row.get('Estado Demandado','')),
                'pais_inversor':   str(row.get('País Inversor','')),
                'año':             str(row.get('Año Inicio','')),
                'resultado_unctad':str(row.get('Resultado','')),
                'tratado':         str(row.get('Tratado Aplicable','')),
                'sector':          str(row.get('Sector Económico','')),
                'monto_reclamado': str(row.get('Monto Reclamado (USD mill.)','')),
                'monto_otorgado':  str(row.get('Monto Otorgado (USD mill.)','')),
                'arbitros':        str(row.get('Árbitros','')),
                'anulacion':       str(row.get('¿Hubo anulación?','')),
                'estado_anulacion':str(row.get('Estado anulación','')),
            }
        return unctad_dict
    except Exception as e:
        print(red(f"Error cargando UNCTAD: {e}"))
        return {}

def load_vars():
    try:
        with open(VAR_PATH) as f:
            return json.load(f)
    except:
        return {}

def load_ver_log():
    try:
        with open(LOG_VER) as f:
            return json.load(f)
    except:
        return {}

def save_ver_log(log):
    with open(LOG_VER, 'w') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

def save_vars(data):
    with open(VAR_PATH, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── RAG query ─────────────────────────────────────────────────────────────
def rag_query(pregunta):
    print(yellow(f"\n  🔍 Consultando RAG: '{pregunta}'"))
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        client = chromadb.PersistentClient(
            path=os.path.join(BASE_DIR, 'rag-db'))
        col = client.get_collection('laudos_ciadi')
        if col.count() == 0:
            print(red("  RAG sin datos aún."))
            return
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        vec = model.encode([pregunta]).tolist()
        results = col.query(
            query_embeddings=vec,
            n_results=6,
            include=['documents','metadatas','distances']
        )
        print()
        seen = set()
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            caso = meta.get('caso','')
            if caso in seen: continue
            seen.add(caso)
            relevancia = max(0, round((2-dist)/2*100))
            print(f"  {bold(cyan(caso))} — {yellow(f'{relevancia}% relevancia')}")
            # Try to read actual text from chunks file
            pdf = meta.get('pdf_path','')
            chunk_n = meta.get('chunk',0)
            chunks_path = pdf.replace('.pdf','_chunks.json') if pdf else ''
            if os.path.exists(chunks_path):
                try:
                    with open(chunks_path) as f:
                        chunks = json.load(f)
                    if chunk_n < len(chunks):
                        texto = chunks[chunk_n][:400]
                        print(f"  {dim(texto)}...")
                except:
                    pass
            print()
    except ImportError:
        print(red("  chromadb/sentence_transformers no disponible."))
    except Exception as e:
        print(red(f"  Error RAG: {e}"))

# ── Mostrar caso ──────────────────────────────────────────────────────────
CAMPOS = [
    ('resultado_unctad',          'Resultado (UNCTAD)'),
    ('tipo_condena',              'Tipo de condena'),
    ('monto_reclamado',           'Monto reclamado (USD mill.)'),
    ('monto_otorgado',            'Monto otorgado (USD mill.)'),
    ('tratado',                   'Tratado aplicable'),
    ('sector',                    'Sector económico'),
    ('decisiones_impugnadas',     'Decisiones impugnadas'),
    ('composicion_accionaria',    'Composición accionaria inversor'),
    ('arbitros',                  'Árbitros'),
    ('anulacion',                 'Proceso de anulación'),
    ('estado_anulacion',          'Estado anulación'),
    ('idioma',                    'Idioma del laudo'),
]

def display_case(url, unctad_info, var_info, ver_log, idx, total):
    clear()
    print_banner()

    estado_ver = ver_log.get(url, {})
    ver_status = estado_ver.get('status', 'pendiente')
    status_icon = green('✅ VERIFICADO') if ver_status=='ok' else (
                  yellow('⏭  SALTADO')   if ver_status=='skip' else
                  red('📝 PENDIENTE'))

    print(f"\n  Caso {bold(str(idx))} de {total}  |  {status_icon}")
    print(f"  {bold(blue(unctad_info.get('nombre_corto',''))[:70])}")
    print(f"  {dim(unctad_info.get('nombre_completo','')[:80])}")
    print(f"  {cyan('Estado:')} {unctad_info.get('estado','')}  ·  "
          f"{cyan('Inversor:')} {unctad_info.get('pais_inversor','')}  ·  "
          f"{cyan('Año:')} {unctad_info.get('año','')}")
    print(f"  {cyan('URL:')} {dim(url)}")
    print()
    print(bold("  VARIABLES (automáticas + UNCTAD):"))
    print("  " + "─" * 60)

    for key, label in CAMPOS:
        # Prefer UNCTAD value, then extracted, then correction
        if key in unctad_info:
            val_src = unctad_info.get(key,'')
            val_ext = var_info.get(key,'') if var_info else ''
            val_cor = estado_ver.get('correcciones',{}).get(key,'')
        else:
            val_src = var_info.get(key,'') if var_info else ''
            val_ext = ''
            val_cor = estado_ver.get('correcciones',{}).get(key,'')

        # Display
        val_show = val_cor if val_cor else (val_src if val_src and val_src not in ('nan','') else val_ext)
        val_show = str(val_show)[:80] if val_show else dim('— no disponible')

        prefix = green('✏ ') if val_cor else ''
        src_tag = ''
        if val_cor:
            src_tag = yellow(' [corregido]')
        elif key in unctad_info and val_src not in ('nan','','None'):
            src_tag = cyan(' [UNCTAD]')
        elif var_info and val_ext:
            src_tag = dim(' [auto]')

        print(f"  {bold(f'{label:<30}')}{prefix}{val_show}{src_tag}")

    print("  " + "─" * 60)

    # Show PDF path
    if var_info and var_info.get('laudo_pdf'):
        print(f"\n  {cyan('PDF:')} {dim(var_info['laudo_pdf'][-60:])}")

    print()
    print(dim("  [ENTER] Confirmar  [c] Corregir campo  [r] Consultar RAG  [s] Saltar  [q] Salir  [?] Ayuda"))

# ── Corrección interactiva ────────────────────────────────────────────────
def correct_field(url, unctad_info, var_info, ver_log):
    print(f"\n  {bold('Campos disponibles para corregir:')} (número o nombre)")
    for i, (key, label) in enumerate(CAMPOS, 1):
        print(f"  {Y}{i:2d}{RST}. {label}")
    print(f"  {Y} 0{RST}. Cancelar")
    choice = input(f"\n  → Campo a corregir: ").strip()
    if choice == '0' or not choice:
        return ver_log

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(CAMPOS):
            key, label = CAMPOS[idx]
            # Current value
            cur = (unctad_info.get(key,'') or (var_info.get(key,'') if var_info else ''))
            print(f"\n  {bold(label)}")
            print(f"  Valor actual: {yellow(str(cur)[:80])}")
            nuevo = input(f"  Nuevo valor (ENTER para cancelar): ").strip()
            if nuevo:
                if url not in ver_log:
                    ver_log[url] = {'status': 'pendiente', 'correcciones': {}}
                if 'correcciones' not in ver_log[url]:
                    ver_log[url]['correcciones'] = {}
                ver_log[url]['correcciones'][key] = nuevo
                print(green(f"  ✅ Corrección guardada."))
    except (ValueError, IndexError):
        # Try by name
        for key, label in CAMPOS:
            if choice.lower() in label.lower() or choice.lower() in key.lower():
                cur = unctad_info.get(key,'') or (var_info.get(key,'') if var_info else '')
                print(f"\n  {bold(label)}: {yellow(str(cur)[:80])}")
                nuevo = input(f"  Nuevo valor: ").strip()
                if nuevo:
                    if url not in ver_log:
                        ver_log[url] = {'status': 'pendiente', 'correcciones': {}}
                    ver_log[url].setdefault('correcciones', {})[key] = nuevo
                    print(green(f"  ✅ Guardado."))
                break

    save_ver_log(ver_log)
    return ver_log

def show_help():
    clear()
    print_banner()
    print(f"""
  {bold('COMANDOS:')}

  {green('[ENTER]')}  Marcar caso como verificado (datos correctos)
  {yellow('[c]')}      Corregir un campo específico
  {cyan('[r]')}      Consultar el RAG — busca fragmentos del laudo real
             Podés preguntar: monto otorgado, tipo condena, árbitros, etc.
  {Y}[s]{RST}      Saltar este caso para revisarlo después
  {Y}[n]{RST}      Ir al caso siguiente sin marcar
  {Y}[p]{RST}      Ir al caso anterior
  {R}[q]{RST}      Guardar progreso y salir

  {bold('CÓMO VERIFICAR:')}
  1. Revisá el resultado (condena/absolución) — fuente UNCTAD, muy confiable
  2. Verificá el monto otorgado — buscalo en el PDF o preguntale al RAG
  3. Corregí el tipo de condena si no coincide con el laudo
  4. Anotá el tratado y sector si faltan

  {bold('TIP RAG:')} Preguntá "{yellow('nombre del caso monto otorgado')}" o
  "{yellow('nombre del caso trato justo equitativo expropiacion')}"

  {dim('Presioná cualquier tecla para continuar...')}""")
    input()

# ── Resumen final ─────────────────────────────────────────────────────────
def show_summary(ver_log, total):
    clear()
    print_banner()
    ok    = sum(1 for v in ver_log.values() if v.get('status') == 'ok')
    skip  = sum(1 for v in ver_log.values() if v.get('status') == 'skip')
    pend  = total - ok - skip
    corr  = sum(1 for v in ver_log.values() if v.get('correcciones'))
    n_cor = sum(len(v.get('correcciones',{})) for v in ver_log.values())

    print(f"""
  {bold('PROGRESO DE VERIFICACIÓN:')}

  {green(f'✅ Verificados:   {ok:3d} / {total}')} ({ok/total*100:.0f}%)
  {yellow(f'⏭  Saltados:      {skip:3d}')}
  {red(f'📝 Pendientes:    {pend:3d}')}
  {cyan(f'✏  Con correcciones: {corr} casos, {n_cor} campos modificados')}

  {dim(f'Log guardado en: verificacion-log.json')}
""")

# ── MAIN ─────────────────────────────────────────────────────────────────
def main():
    print_banner()
    print(f"\n  Cargando datos...")

    unctad_dict = load_data()
    var_data    = load_vars()
    ver_log     = load_ver_log()

    # Build ordered list of cases
    # Priority: unverified first, then verified
    all_urls = [url for url in unctad_dict.keys()
                if url not in ('nan', '', 'Not available')
                and url in var_data]

    # Sort: pendientes first
    def sort_key(url):
        status = ver_log.get(url, {}).get('status', 'pendiente')
        if status == 'pendiente': return 0
        if status == 'skip': return 1
        return 2

    all_urls.sort(key=sort_key)
    total = len(all_urls)

    print(f"\n  {green(str(total))} casos con variables extraídas encontrados.")
    ok = sum(1 for v in ver_log.values() if v.get('status')=='ok')
    print(f"  {green(str(ok))} ya verificados, {red(str(total-ok))} pendientes.")

    # Filter options
    print(f"\n  ¿Qué querés revisar?")
    print(f"  {Y}1{RST} → Solo pendientes ({total - ok})")
    print(f"  {Y}2{RST} → Todo desde el principio")
    print(f"  {Y}3{RST} → Buscar un caso específico")
    print(f"  {Y}4{RST} → Ver resumen y salir")
    choice = input(f"\n  → ").strip()

    if choice == '4':
        show_summary(ver_log, total)
        return

    if choice == '3':
        buscar = input(f"  Nombre del caso: ").strip().lower()
        filtered = [u for u in all_urls
                    if buscar in unctad_dict[u].get('nombre_corto','').lower()
                    or buscar in unctad_dict[u].get('estado','').lower()]
        if not filtered:
            print(red(f"  No se encontraron casos con '{buscar}'"))
            input("  [ENTER] para continuar...")
            return main()
        all_urls_work = filtered
    elif choice == '2':
        all_urls_work = all_urls
    else:
        all_urls_work = [u for u in all_urls
                         if ver_log.get(u, {}).get('status', 'pendiente') != 'ok']

    total_work = len(all_urls_work)
    idx = 0

    while idx < total_work:
        url = all_urls_work[idx]
        unctad_info = unctad_dict.get(url, {})
        var_info    = var_data.get(url, {})

        display_case(url, unctad_info, var_info, ver_log, idx + 1, total_work)

        cmd = input("  → ").strip().lower()

        if cmd == '' or cmd == 'ok':
            # Confirm
            if url not in ver_log:
                ver_log[url] = {}
            ver_log[url]['status'] = 'ok'
            save_ver_log(ver_log)
            idx += 1

        elif cmd == 'c':
            ver_log = correct_field(url, unctad_info, var_info, ver_log)
            # Don't advance — stay on same case to see change

        elif cmd == 'r':
            # RAG query
            q_default = f"{unctad_info.get('nombre_corto','')} monto otorgado tipo condena"
            q = input(f"  Pregunta [{dim(q_default[:50])}]: ").strip()
            if not q: q = q_default
            rag_query(q)
            input(f"\n  {dim('[ENTER] para continuar...')}")

        elif cmd == 's':
            if url not in ver_log:
                ver_log[url] = {}
            ver_log[url]['status'] = 'skip'
            save_ver_log(ver_log)
            idx += 1

        elif cmd == 'n':
            idx += 1

        elif cmd == 'p':
            idx = max(0, idx - 1)

        elif cmd == 'q':
            save_ver_log(ver_log)
            show_summary(ver_log, total)
            print(f"  {green('Progreso guardado. ¡Hasta luego!')}\n")
            return

        elif cmd == '?':
            show_help()

        else:
            print(red(f"  Comando '{cmd}' no reconocido. ? para ayuda."))
            import time; time.sleep(1)

    save_ver_log(ver_log)
    show_summary(ver_log, total)
    print(f"\n  {bold(green('¡Verificación completada!'))} {dim('Resultados en verificacion-log.json')}\n")

# ── Aplicar correcciones al JSON principal ─────────────────────────────---
def apply_corrections():
    """Fusiona las correcciones del log de verificación al archivo principal."""
    var_data = load_vars()
    ver_log  = load_ver_log()

    updated = 0
    for url, entry in ver_log.items():
        correcciones = entry.get('correcciones', {})
        if not correcciones: continue
        if url not in var_data: continue
        for campo, valor in correcciones.items():
            var_data[url][campo] = valor
        updated += 1

    save_vars(var_data)
    print(green(f"✅ Correcciones aplicadas a {updated} casos en variables-extraidas.json"))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'aplicar':
        apply_corrections()
    else:
        try:
            main()
        except KeyboardInterrupt:
            print(f"\n\n  {yellow('Interrumpido. Progreso guardado.')}\n")
