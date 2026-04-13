# Documentación del Proyecto de Tesis — CIADI 2000-2022

**Autor:** Juan Pablo Caputo  
**Tesis:** *Distribución de laudos condenatorios entre países exportadores e importadores de capital ante el CIADI durante el siglo XXI (2000-2022)*  
**Última actualización:** Abril 2026

---

## Índice

1. [Qué es este proyecto](#1-qué-es-este-proyecto)
2. [Estructura de carpetas y archivos](#2-estructura-de-carpetas-y-archivos)
3. [Cómo se construyó la base de datos](#3-cómo-se-construyó-la-base-de-datos)
4. [Los datos: qué tenemos y de dónde vienen](#4-los-datos-qué-tenemos-y-de-dónde-vienen)
5. [Metodología de clasificación exportador/importador](#5-metodología-de-clasificación-exportadorimportador)
6. [Resultados y conclusiones](#6-resultados-y-conclusiones)
7. [El sistema RAG: búsqueda en los laudos](#7-el-sistema-rag-búsqueda-en-los-laudos)
8. [Cómo verificar los datos manualmente](#8-cómo-verificar-los-datos-manualmente)
9. [Qué falta para cerrar la investigación](#9-qué-falta-para-cerrar-la-investigación)
10. [Glosario técnico](#10-glosario-técnico)

---

## 1. Qué es este proyecto

Esta carpeta contiene toda la infraestructura de datos de la tesis. El objetivo era transformar ~350 laudos arbitrales del CIADI —documentos legales de entre 50 y 800 páginas cada uno— en una base de datos estructurada que permita hacer análisis estadístico.

La pregunta central de la tesis es:

> **¿Los países que exportan capital (países ricos, emisores de inversión extranjera) reciben menos condenas en el CIADI que los países que importan capital (países en desarrollo, receptores de inversión)?**

Para responderla construimos tres cosas:
1. Una **base de datos** con los 350 laudos públicos del período 2000-2022 y sus variables clave
2. Un **análisis cruzado** de esos laudos con los flujos de IED (Inversión Extranjera Directa) de cada país según el Banco Mundial
3. Un **sistema de búsqueda inteligente** que permite consultar el texto de los laudos en lenguaje natural

---

## 2. Estructura de carpetas y archivos

```
tesis-ciadi/
│
├── BASE-DATOS-TESIS-CIADI.xlsx          ← Base principal de laudos (350 filas, 22 columnas)
├── ANÁLISIS-CAPITAL-CIADI.xlsx          ← Análisis estadístico y conclusiones
├── variables-extraidas.json             ← Variables extraídas automáticamente de PDFs (320 casos)
├── descarga-log.json                    ← Registro de qué PDFs se descargaron y de dónde
├── verificacion-log.json                ← Tu registro de verificación manual (se crea al verificar)
│
├── rag-laudos.py                        ← Sistema de búsqueda en lenguaje natural
├── verificar-laudos.py                  ← Script de verificación interactiva caso por caso
│
├── datos-capital/
│   ├── CASOS-CIADI-2000-2022.xlsx       ← Dataset base de UNCTAD (717 casos, filtrado a 350 con laudo)
│   ├── fdi-banco-mundial-raw.csv        ← Flujos IED 2000-2022 de 121 países (Banco Mundial)
│   └── UNCTAD-ISDS-Navigator-data-set-31December2023.xlsx  ← Dataset original UNCTAD
│
├── laudos/                              ← 3.294 PDFs organizados por región
│   ├── america-del-sur/
│   ├── america-central-caribe/
│   ├── america-del-norte/
│   ├── europa-occidental/
│   ├── este-europa-asia-central/
│   ├── asia-sur-este-pacifico/
│   ├── africa-subsahariana/
│   ├── medio-oriente-norte-africa/
│   └── sin-clasificar/
│
└── rag-db/                              ← Base de datos vectorial del sistema RAG
    └── chroma.sqlite3                   ← 88.600 fragmentos de texto indexados
```

### Los dos Excels principales

#### `BASE-DATOS-TESIS-CIADI.xlsx`
Es la base de laudos. Tiene **350 filas** (una por laudo) y **22 columnas**:

| Columna | Descripción | Fuente |
|---|---|---|
| Nombre corto / completo | Identificación del caso | UNCTAD |
| Estado demandado | País que fue llevado al CIADI | UNCTAD |
| País inversor | País de origen del inversor demandante | UNCTAD |
| Año inicio | Año en que se inició el arbitraje | UNCTAD |
| Resultado | Condena con daños / sin daños / Estado absuelto | UNCTAD |
| ¿Condena? | Sí/No (simplificado) | Derivado |
| Tipo condena | TJE, Expropiación, NMF, etc. | Extraído del PDF |
| Monto reclamado | USD mill. reclamados por el inversor | UNCTAD |
| Monto otorgado | USD mill. que el árbitro ordenó pagar | UNCTAD |
| Sector económico | Industria involucrada | UNCTAD |
| Decisiones impugnadas | Qué acto estatal se cuestionó | Extraído del PDF |
| Tratado aplicable | TBI, ECT, NAFTA, etc. | UNCTAD |
| Composición accionaria | Inversión directa, holding, joint venture | Extraído del PDF |
| Árbitros | Nombres y roles de los tres árbitros | UNCTAD |
| ¿Anulación? | Si se inició proceso de anulación post-laudo | UNCTAD |
| Estado anulación | Resultado del proceso de anulación | UNCTAD |
| Idioma | Español, inglés o francés | Extraído del PDF |
| Variables extraídas | Si el PDF fue procesado o no | Sistema |

**Código de colores:**
- 🔴 Rojo: condena con daños
- 🟡 Amarillo claro: condena sin daños
- 🟢 Verde: estado absuelto
- 🟡 Amarillo fuerte: datos pendientes de revisión

#### `ANÁLISIS-CAPITAL-CIADI.xlsx`
Tiene **6 hojas**:

| Hoja | Contenido |
|---|---|
| **CONCLUSIONES** | 16 conclusiones con texto y sustento empírico |
| **TABLA MAESTRA RESULTADOS** | Distribución completa de resultados por clasificación |
| **MONTOS Y ÁRBITROS** | USD otorgados, top condenas, ECT vs no-ECT, árbitros, anulaciones |
| **ANÁLISIS CENTRAL** | Tablas resumen por estado demandado e inversor |
| **ESTADOS Y PAÍSES** | Ranking completo de todos los países |
| **PAÍSES Y CLASIFICACIÓN** | Clasificación exportador/importador de los 121 países |
| **FLUJOS DE CAPITAL BM** | Datos crudos de IED del Banco Mundial |

---

## 3. Cómo se construyó la base de datos

### Paso 1 — Dataset base (UNCTAD)

El punto de partida fue el **UNCTAD Investment Policy Hub**, que mantiene el registro más completo de casos ISDS (arbitrajes de inversión). Descargamos el dataset a diciembre 2023, que incluye **717 casos CIADI del período 2000-2022**.

De esos 717:
- **350 tienen laudo público** → son los casos que analizamos
- **367 no tienen laudo público** → discontinuados, arreglos amistosos, o confidenciales

### Paso 2 — Descarga de PDFs

Para los 350 casos con laudo público, descargamos los PDFs desde:
- **Italaw.com** → fuente principal, tiene el 93% de los laudos CIADI
- **Servidor legacy del ICSID** (icsidfiles.worldbank.org) → para casos no disponibles en Italaw

Resultado:
- **321 carpetas** con al menos un PDF descargado
- **3.294 PDFs** en total (cada caso puede tener varios documentos: laudo principal, decisión de jurisdicción, decisión de anulación, etc.)
- **29 casos genuinamente confidenciales** → las partes acordaron no publicar el laudo

### Paso 3 — Extracción automática de variables

Usando la librería `pdfminer` (que convierte PDF a texto) y expresiones regulares (patrones de búsqueda), el sistema leyó automáticamente cada PDF y extrajo:

- **Tipo de condena** (TJE, Expropiación, NMF, Protección y Seguridad, etc.)
- **Decisiones impugnadas** (decretos, leyes, contratos revocados)
- **Composición accionaria** (inversión directa, holding, joint venture)
- **Idioma del laudo** (inglés, español, francés)
- **Monto reclamado** (cuando no estaba en UNCTAD)

Resultado: **320 de los 350 casos** tienen variables extraídas. Los 30 restantes tienen PDFs escaneados que el sistema no puede leer como texto.

### Paso 4 — Cruce con datos de flujos de capital

Para clasificar cada país como exportador o importador neto de capital, descargamos los datos de IED del **Banco Mundial** para **121 países** en el período 2000-2022, usando los indicadores:
- `BX.KLT.DINV.CD.WD` → entradas de IED (inflows)
- `BM.KLT.DINV.CD.WD` → salidas de IED (outflows)

La fórmula de clasificación se explica en la sección siguiente.

---

## 4. Los datos: qué tenemos y de dónde vienen

### Universo de análisis

| Ítem | Número |
|---|---|
| Casos CIADI registrados 2000-2022 | 717 |
| Con laudo público | **350** |
| Sin laudo (arreglos, discontinuados) | 367 |
| Con PDF descargado | 321 |
| Genuinamente confidenciales | 29 |
| Con variables extraídas del PDF | 320 |
| PDFs descargados en total | 3.294 |

### Distribución de resultados (350 laudos)

| Resultado | N° | % |
|---|---|---|
| 🔴 Condena con daños | 150 | 42.9% |
| 🟡 Condena sin daños | 14 | 4.0% |
| 🟢 Estado absuelto | 186 | 53.1% |
| **Total condenas** | **164** | **46.9%** |

### Fuentes de datos

| Dato | Fuente | Confiabilidad |
|---|---|---|
| Lista de casos, resultado, monto | UNCTAD Investment Policy Hub | ⭐⭐⭐ Muy alta |
| Texto del laudo, tipo de condena | PDF del laudo (pdfminer) | ⭐⭐ Alta (verificar) |
| Flujos de IED por país | Banco Mundial API | ⭐⭐⭐ Muy alta |
| Clasificación España | Banco Mundial (verificar con UNCTAD) | ⚠️ Pendiente |
| Clasificación Reino Unido | Banco Mundial (verificar con UNCTAD) | ⚠️ Pendiente |

---

## 5. Metodología de clasificación exportador/importador

### La fórmula

Para cada país, se sumaron todos los flujos anuales de IED entre 2000 y 2022 y se calculó el promedio anual neto:

```
Neto = (Σ salidas IED 2000-2022  −  Σ entradas IED 2000-2022) / 23 años

Si Neto > 0  →  Exportador neto de capital
Si Neto < 0  →  Importador neto de capital
```

No hay categoría intermedia. La clasificación es binaria.

### Ejemplos

| País | Neto promedio anual | Clasificación |
|---|---|---|
| Países Bajos | +USD 48.071 mill. | Exportador neto |
| Francia | +USD 34.748 mill. | Exportador neto |
| Alemania | +USD 33.133 mill. | Exportador neto |
| España | +USD 12.616 mill. | Exportador neto ⚠️ |
| EE.UU. | +USD 2.164 mill. | Exportador neto |
| China | −USD 93.956 mill. | Importador neto |
| México | −USD 21.380 mill. | Importador neto |
| Reino Unido | −USD 13.645 mill. | Importador neto ⚠️ |
| Argentina | −USD 6.440 mill. | Importador neto |
| Venezuela | −USD (datos limitados) | Importador neto |

### Casos a verificar con UNCTAD

- **España** → El Banco Mundial la clasifica como exportadora neta. El autor cree que podría ser importadora. Verificar en [UNCTADstat](https://unctadstat.unctad.org) → FDI flows → Spain. **Esta decisión tiene impacto crítico en los resultados** (ver Conclusión C4).

- **Reino Unido** → El Banco Mundial la clasifica como importadora neta, empujada por una anomalía en 2016 (entrada de £324 mil millones en un solo año). El autor cree que debería ser exportadora. Verificar en UNCTADstat. **Impacto bajo** porque UK no fue demandada ninguna vez como estado en el período.

---

## 6. Resultados y conclusiones

### Tabla central

| | Total casos | Condena c/daños | Condena s/daños | Absuelto | **Total condenas** |
|---|---|---|---|---|---|
| **Exportador neto** | 60 | 33 (55.0%) | 0 (0.0%) | 27 (45.0%) | **33 (55.0%)** |
| **Importador neto** | 283 | 115 (40.6%) | 14 (4.9%) | 154 (54.4%) | **129 (45.6%)** |
| Sin datos | 7 | 2 | 0 | 5 | 2 |
| **TOTAL** | **350** | **150 (42.9%)** | **14 (4.0%)** | **186 (53.1%)** | **164 (46.9%)** |

### Tabla cruzada Estado × Inversor

| Estado demandado | País inversor | Casos | Total condenas | Tasa |
|---|---|---|---|---|
| Exportador neto | Exportador neto | 47 | 27 | **57.4%** |
| Exportador neto | Importador neto | 8 | 4 | 50.0% |
| Importador neto | Exportador neto | 177 | 79 | 44.6% |
| Importador neto | Importador neto | 71 | 24 | **33.8%** |

### Impacto económico

| | Condenas con dato de monto | Total USD otorgado | Promedio por caso |
|---|---|---|---|
| Exportador neto (estado) | 32 | USD 1.979 mill. | USD 61.9 mill. |
| Importador neto (estado) | 106 | USD 30.302 mill. | USD 285.9 mill. |
| **TOTAL GLOBAL** | **138** | **USD 32.378 mill.** | **USD 234.6 mill.** |

> Los importadores netos pagaron **15 veces más** en montos absolutos que los exportadores netos.

### Las 16 conclusiones

#### A. Hipótesis central

**C1.** Los importadores netos concentran el **80.9% de los casos** (283/350) y el **78.7% de las condenas absolutas** (129/164). El sistema CIADI pesa desproporcionalmente sobre los Estados que más necesitan capital extranjero.

**C2.** La tasa de condena por caso es mayor en exportadores (55%) que en importadores (45.6%), pero esto se explica casi enteramente por España. Sin España, los exportadores tienen **28.6% de tasa** — claramente por debajo de los importadores.

**C3.** Las 14 condenas "sin daños" recaen exclusivamente sobre importadores netos (0 sobre exportadores). Los árbitros reconocen la violación del TBI pero niegan compensación monetaria solo cuando el estado demandado es importador.

#### B. El caso España y el ECT

**C4.** España es un outlier no generalizable. Sus 25 casos (23 condenas, 92%) son todos post-2012 por el recorte a energías renovables bajo el Tratado sobre la Carta de la Energía (ECT). No refleja un patrón sistémico de exportadores que pierden más.

**C5.** El ECT es el factor explicativo clave. **Sin ECT**: exportadores tienen 26.7% de tasa vs 46.5% de importadores — la relación se invierte completamente. **Con ECT**: exportadores 83.3% vs importadores 28.6% (todos los casos ECT de exportadores son España/Italia regulando renovables).

#### C. Actores específicos

**C6.** América Latina es la región más expuesta: 110 casos, **56.4% de tasa de condena**. Venezuela (65.4%), Argentina (79.2%) y México (61.5%) encabezan. Todos son importadores netos.

**C7.** EE.UU. es el mayor inversor demandante (62 casos, 37.1% tasa). Nunca fue condenado como estado demandado en el período. Paradoja: es exportador neto pero con el margen más bajo entre los exportadores (+USD 2.164 mill./año).

**C8.** Países Bajos: 28 casos como inversor, fenómeno de **treaty shopping**. Holdings holandeses canalizan inversión real de EE.UU., Rusia, España y otros países. La nacionalidad nominal del inversor no equivale al origen real del capital.

**C9.** China es el mayor importador neto del mundo (−USD 93.956 mill./año) pero tiene exposición mínima al CIADI. La exposición al arbitraje no es solo función de flujos de capital sino de la arquitectura de TBIs que el Estado acepta firmar.

#### D. Funcionamiento del sistema

**C10.** Tendencia decreciente de condenas en el tiempo: **49.1%** (2000-2007) → **49.7%** (2008-2015) → **38.0%** (2016-2022). Los estados mejoran su defensa y/o los árbitros son progresivamente más cautelosos.

**C11.** Energía y minería: 118 casos (33.7% del universo), **56.8% de tasa de condena**. Sector agua: 14 casos, **78.6% de tasa** — la más alta de todos los sectores. Los sectores donde el estado regula interés público son los más expuestos.

**C12.** El Trato Justo y Equitativo (TJE) es la violación más alegada y más exitosa. Aparece en la mayoría de las condenas, solo o combinado con expropiación. La noción de "expectativas legítimas" del inversor es el principal vector de expansión de la responsabilidad estatal.

**C13.** Alta concentración en pocos árbitros: Brigitte Stern fue nombrada por estados demandados **52 veces**, más del doble que cualquier otro árbitro. Gabrielle Kaufmann-Kohler presidió 20 tribunales. Esta concentración es un hallazgo sobre el funcionamiento interno del sistema.

#### E. Impacto económico

**C14.** Los importadores netos pagaron USD 30.302 mill. en condenas (promedio USD 285.9 mill./caso). Los exportadores netos: USD 1.979 mill. (promedio USD 61.9 mill./caso). El impacto económico absoluto es **15 veces mayor** sobre los importadores.

**C15.** Las anulaciones modifican el resultado final en muy pocos casos: solo 5 laudos anulados totalmente y 10 parcialmente, de 174 procesos de anulación iniciados. El sistema tiende fuertemente a confirmar los laudos originales (94 confirmados de los resueltos).

#### F. Limitaciones metodológicas

**C16.** 29 casos tienen laudo confidencial: 14 son absoluciones del estado, 9 son condenas con daños, 2 son condenas sin daños. No hay sesgo grosero (19 de 29 son importadores netos, similar a la distribución general), pero la muestra no es del 100% del universo. Esta limitación debe declararse en la tesis.

---

## 7. El sistema RAG: búsqueda en los laudos

### Qué es

RAG es un sistema de búsqueda inteligente que permite hacerle preguntas en lenguaje natural a los 320 laudos descargados. En vez de leer un PDF entero, le preguntás algo específico y el sistema te devuelve los párrafos más relevantes de entre los 3.294 PDFs descargados.

### Cómo funciona por dentro

1. Cada PDF fue convertido a texto (con `pdfminer`)
2. El texto de cada PDF fue cortado en fragmentos de ~800 palabras con superposición de 150 palabras
3. Cada fragmento fue convertido en un vector numérico (una representación matemática del significado del texto) usando el modelo de lenguaje `paraphrase-multilingual-MiniLM-L12-v2`, que entiende español, inglés y francés
4. Los 88.600 fragmentos y sus vectores quedaron guardados en una base de datos (ChromaDB)
5. Cuando hacés una pregunta, el sistema la convierte al mismo formato vectorial y busca los fragmentos más similares matemáticamente

### Estado actual

| Ítem | Número |
|---|---|
| PDFs totales | 3.294 |
| PDFs procesados | 2.838 (86.8%) |
| Fragmentos indexados | 88.600 |
| Tamaño de la base | ~61 MB |

### Cómo usarlo

Desde la Terminal, dentro de la carpeta `tesis-ciadi`:

```bash
# Consulta libre:
python3 rag-laudos.py "expropiación Venezuela monto otorgado"

# Otros ejemplos:
python3 rag-laudos.py "trato justo y equitativo expectativas legítimas"
python3 rag-laudos.py "CMS Argentina monto USD millones"
python3 rag-laudos.py "energy charter treaty fair and equitable treatment Spain"
```

El sistema devuelve los casos más relevantes con un porcentaje de relevancia y un fragmento del texto del laudo.

---

## 8. Cómo verificar los datos manualmente

### Por qué es necesario

La extracción automática de texto desde PDFs legales no es perfecta. Funciona bien para los PDFs digitales, pero algunos laudos están escaneados (imagen de texto, no texto real) y otros tienen formatos complejos. La verificación manual es indispensable para una tesis académica.

### Qué verificar sí o sí

| Prioridad | Variable | Por qué |
|---|---|---|
| 🔴 Crítica | Resultado (condena/absolución) | Es la variable dependiente principal — UNCTAD ya la tiene bien |
| 🔴 Crítica | Monto otorgado | Impacto económico — a veces falta o está mal parseado |
| 🟡 Alta | Tipo de condena (TJE, expropiación, etc.) | Extraído por regex, puede haber errores en casos ambiguos |
| 🟡 Alta | Tratado aplicable | UNCTAD lo tiene bien, pero verificar los combinados |
| 🟢 Normal | Sector económico | UNCTAD lo tiene, revisar casos genéricos |
| 🟢 Normal | Decisiones impugnadas | Variable extraída automáticamente, verificar muestra |

### El script de verificación paso a paso

#### Paso 1 — Abrir la Terminal

La Terminal es la app de tu Mac donde escribís comandos (la usamos durante todo el proyecto). La encontrás en: **Aplicaciones → Utilidades → Terminal**, o buscándola con Spotlight (Cmd + Espacio → escribís "Terminal").

#### Paso 2 — Ir a la carpeta correcta

Escribís esto y apretás Enter:

```bash
cd ~/Desktop/Proyecto\ nch/tesis-ciadi
```

#### Paso 3 — Iniciar el verificador

```bash
python3 verificar-laudos.py
```

El programa arranca y te pregunta:

```
¿Qué querés revisar?
1 → Solo pendientes (320)
2 → Todo desde el principio
3 → Buscar un caso específico
4 → Ver resumen y salir
```

Elegís **1** para arrancar por los pendientes.

#### Paso 4 — Revisar caso por caso

Para cada caso, la pantalla muestra algo así:

```
Caso 1 de 320  |  📝 PENDIENTE

  CMS v. Argentina
  CMS Gas Transmission Company v. Argentine Republic
  Estado: Argentina  ·  Inversor: United States  ·  Año: 2001

  Resultado (UNCTAD)             Sí con daños           [UNCTAD]
  Tipo de condena                TJE - Trato Justo...   [auto]
  Monto reclamado                Data not available
  Monto otorgado                 133.20 USD             [UNCTAD]
  Tratado aplicable              Argentina - US BIT     [UNCTAD]
  Sector económico               Gas/energía            [UNCTAD]
  Decisiones impugnadas          Decreto/Reglamento     [auto]
  ...

  [ENTER] Confirmar  [c] Corregir campo  [r] Consultar RAG  [s] Saltar  [q] Salir  [?] Ayuda
```

Lo que dice **[UNCTAD]** viene de la base de datos oficial y es muy confiable. Lo que dice **[auto]** fue extraído automáticamente y puede tener errores.

#### Comandos disponibles

| Tecla | Acción |
|---|---|
| `Enter` | Marcar como correcto y pasar al siguiente |
| `c` | Corregir un campo — el programa te pregunta cuál y cuál es el valor correcto |
| `r` | Consultar el RAG — buscás un dato específico dentro del texto real del laudo |
| `s` | Saltar este caso para revisarlo después |
| `p` | Volver al caso anterior |
| `q` | Guardar progreso y salir |
| `?` | Ver ayuda completa |

#### Cómo usar la consulta RAG durante la verificación

Cuando apretás `r`, el programa te pide que escribas una pregunta. Por ejemplo:

```
Pregunta: CMS Argentina monto otorgado USD
```

El sistema busca en los PDFs y te devuelve el párrafo exacto del laudo donde aparece ese dato, por ejemplo:

> *"...the Tribunal awards CMS the amount of US$ 133.2 million, together with interest at the rate of 2.56% per annum..."*

Así podés confirmar el dato sin abrir el PDF manualmente.

#### Paso 5 — Guardar y continuar después

Cuando apretás `q`, el programa guarda todo el progreso automáticamente en `verificacion-log.json`. La próxima vez que lo abrás, retoma desde donde dejaste.

#### Paso 6 — Aplicar las correcciones al archivo principal

Cuando terminás de revisar (o cuando querés aplicar lo que corregiste hasta ese momento):

```bash
python3 verificar-laudos.py aplicar
```

Esto fusiona todas las correcciones que marcaste con `c` al archivo `variables-extraidas.json` (el archivo principal con todos los datos).

### Cuánto tiempo lleva

| Tipo de caso | Tiempo estimado |
|---|---|
| Casos claros (resultado y monto confirmados por UNCTAD) | ~20-30 segundos |
| Casos con tipo de condena a verificar (consulta RAG) | ~2-3 minutos |
| Casos complicados (monto no disponible, buscar en PDF) | ~5-10 minutos |

Estimación total para los **150 casos con condena** (los más importantes):
- Optimista: 2-3 horas
- Realista: 4-5 horas en total

Podés hacerlo en sesiones de 30-60 minutos, cerrando y retomando cuando quieras.

### Herramientas complementarias recomendadas

#### NotebookLM (Google) — Gratuito
La mejor herramienta externa para verificación profunda.

1. Entrás a [notebooklm.google.com](https://notebooklm.google.com)
2. Creás un notebook por bloque temático (ej. "Casos Argentina", "Casos ECT/España")
3. Subís los PDFs de esos casos (tenés los archivos en la carpeta `laudos/`)
4. Le preguntás en lenguaje natural: *"¿Cuál fue el monto otorgado en este caso?"* o *"¿Qué violación del TBI reconocieron los árbitros?"*
5. NotebookLM te cita la página exacta del PDF fuente

**Ventaja sobre el RAG propio:** NotebookLM tiene mejor comprensión de lectura, cita páginas específicas, y es más preciso para preguntas complejas. **Desventaja:** hay que subir los PDFs manualmente y tiene un límite de archivos por notebook.

#### UNCTAD Investment Policy Hub
Para verificar resultado, tratado, árbitros y sector de cualquier caso:
```
https://investmentpolicy.unctad.org/investment-dispute-settlement/cases/XXX/nombre-del-caso
```

#### UNCTADstat — Para verificar clasificación España y UK
```
https://unctadstat.unctad.org
→ FDI → FDI flows → by economy → Spain / United Kingdom
```

---

## 9. Qué falta para cerrar la investigación

En orden de prioridad:

### Urgente (define el resultado central)

1. **Verificar España y UK en UNCTAD** *(15-30 min)*  
   Ir a UNCTADstat, buscar los flujos acumulados 2000-2022 para España y UK. Si España resulta importadora, el hallazgo cambia completamente — los exportadores sin España tienen 28.6% de tasa, debajo de los importadores (45.6%). Esto confirma en vez de contradecir la hipótesis de la tesis.

2. **Verificar montos otorgados** *(parte de la verificación manual)*  
   Los 150 casos con condena con daños necesitan monto confirmado. UNCTAD ya tiene 106 de ellos; los 44 restantes hay que buscarlos en el RAG o en el PDF.

### Importante (enriquece el análisis)

3. **Controlar por el ECT en la tesis**  
   Presentar el análisis con y sin los 44 casos ECT para demostrar que el hallazgo sobre exportadores no es generalizable sino específico de ese régimen. Esto aclara la C2 y la C5.

4. **Verificación manual de tipo de condena** *(muestra aleatoria)*  
   No es necesario verificar los 320 casos. Alcanza con verificar una muestra de ~50 casos (los más citados en la literatura y los de mayor monto) para poder declarar un margen de error aceptable.

5. **Completar los montos reclamados**  
   La columna "Monto reclamado" tiene muchos vacíos. Los montos reclamados vs otorgados permiten calcular la "efectividad" del reclamo — otro ángulo de análisis.

### Opcional (si el tiempo lo permite)

6. **Análisis de árbitros por resultado**  
   Cruzar qué árbitros estuvieron en casos con condena vs absolución. ¿Hay árbitros nombrados por inversores con más tasa de condena?

7. **Línea de tiempo de los casos Argentina**  
   Los 24 casos argentinos están concentrados en 2001-2005 (crisis). Un análisis temporal de Argentina sola podría ser un cuadro específico muy potente para la tesis.

8. **Buscar los 29 casos confidenciales en Jus Mundi**  
   Algunos pueden estar disponibles en [jusmundi.com](https://jusmundi.com), especialmente los más recientes. Vale la pena buscar manualmente los que tienen condena (9 casos).

---

## 10. Glosario técnico

| Término | Significado |
|---|---|
| **CIADI** | Centro Internacional de Arreglo de Diferencias relativas a Inversiones. Organismo del Banco Mundial que administra arbitrajes entre inversores extranjeros y estados. En inglés: ICSID. |
| **Laudo** | La sentencia del tribunal arbitral. Equivale a una sentencia judicial pero en arbitraje. |
| **TBI** | Tratado Bilateral de Inversión. Acuerdo entre dos países que protege a los inversores de uno en el territorio del otro. |
| **ECT** | Energy Charter Treaty (Tratado sobre la Carta de la Energía). Tratado multilateral que protege inversiones en el sector energético. Es el tratado más litigioso del período. |
| **NAFTA** | Tratado de Libre Comercio de América del Norte (EE.UU., Canadá, México). Tiene un capítulo 11 que permite arbitrajes de inversión. Reemplazado por el USMCA/T-MEC en 2020. |
| **TJE** | Trato Justo y Equitativo. Estándar de protección del inversor que obliga al estado a no frustrar las "expectativas legítimas" del inversor. Es la violación más alegada en el CIADI. |
| **Expropiación** | Cuando el estado toma o destruye la inversión directamente (expropiación directa) o mediante regulaciones que anulan su valor (expropiación indirecta). |
| **NMF** | Nación Más Favorecida. Cláusula que obliga al estado a dar al inversor el mismo trato que da a los inversores del país más favorecido. |
| **Treaty shopping** | Práctica de usar una empresa holding en un tercer país (típicamente Países Bajos o Luxemburgo) para acceder a un TBI más favorable que el del país real del inversor. |
| **IED** | Inversión Extranjera Directa. Capital que un inversor de un país inyecta en una empresa o proyecto de otro país, con intención de control (≥10% de participación). |
| **Exportador neto de capital** | País cuyas empresas invierten más en el exterior de lo que empresas extranjeras invierten en él. Típicamente: países ricos con exceso de capital. |
| **Importador neto de capital** | País que recibe más inversión extranjera de la que sus empresas invierten en el exterior. Típicamente: países en desarrollo con necesidad de capital. |
| **RAG** | Retrieval-Augmented Generation. Sistema de búsqueda en documentos que usa inteligencia artificial para encontrar los párrafos más relevantes ante una pregunta en lenguaje natural. |
| **ChromaDB** | Base de datos vectorial. Almacena los fragmentos de texto como vectores numéricos para permitir búsqueda por similaridad semántica. |
| **pdfminer** | Librería de Python que extrae el texto de archivos PDF. Funciona bien con PDFs digitales; no funciona con PDFs escaneados (imágenes). |
| **Anulación** | Proceso post-laudo por el que un comité ad hoc del CIADI puede anular el laudo original si hubo errores graves de procedimiento o aplicación del derecho. No es una apelación sobre el fondo. |
| **Git / GitHub** | Sistema de control de versiones. Guarda el historial de cambios de todos los archivos del proyecto. GitHub es la plataforma en la nube donde se almacena el repositorio: `github.com/jpcaputo91-afk/proyecto-nch` |
| **JSON** | Formato de archivo de texto estructurado para guardar datos. Es el formato interno donde guardamos las variables extraídas de los PDFs (`variables-extraidas.json`). |
| **UNCTAD** | Conferencia de las Naciones Unidas sobre Comercio y Desarrollo. Publica el dataset más completo de casos ISDS a nivel mundial. |

---

*Documento generado en abril de 2026. Última actualización con datos al 13 de abril de 2026.*  
*Repositorio: [github.com/jpcaputo91-afk/proyecto-nch](https://github.com/jpcaputo91-afk/proyecto-nch)*
