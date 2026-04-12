# Cómo se armó este proyecto

Este documento explica paso a paso qué hice para crear y subir el repositorio NCH a GitHub. Es una guía técnica para que entiendas qué pasó detrás de escena.

---

## 1. El punto de partida

Tenías una carpeta llamada `Proyecto nch` en el escritorio, completamente vacía (salvo por algunos archivos de Obsidian). El objetivo era convertirla en un repositorio de GitHub organizado para tu aprendizaje de renta fija.

---

## 2. Herramientas que usamos

### Git
**Git** es un programa que registra los cambios que hacés en tus archivos a lo largo del tiempo. Es como un historial de versiones muy detallado. Cada vez que guardás una "foto" del estado de tu proyecto (eso se llama *commit*), Git la registra con fecha, hora y un mensaje que vos escribís.

Git viene instalado en tu Mac por defecto. Lo confirmamos con:
```
git --version
```

### GitHub
**GitHub** es un sitio web donde podés guardar tus repositorios de Git en la nube. Es como Google Drive pero para código y proyectos técnicos. Tiene además funciones para organizar tareas, mostrar el README como página principal, y ver el historial de cambios.

### GitHub CLI (`gh`)
**GitHub CLI** es una herramienta que permite manejar GitHub desde la terminal, sin entrar al navegador. La usamos para:
- Autenticarte con tu cuenta de GitHub
- Crear el repositorio directamente desde la terminal
- Subir el proyecto con un solo comando

No venía instalada en tu Mac, así que la descargamos e instalamos manualmente en `~/bin/gh`.

---

## 3. Configurar Git con tus datos

Antes de poder hacer commits, Git necesita saber quién los hace. Ejecuté:

```bash
git config --global user.name "jpcaputo91-afk"
git config --global user.email "jpcaputo91@gmail.com"
```

Esto queda guardado en tu Mac para siempre. Todos los commits que hagas en el futuro van a llevar tu nombre y email.

---

## 4. Autenticación con GitHub

Para que la terminal pueda hablar con tu cuenta de GitHub, corriste:

```bash
~/bin/gh auth login
```

Esto abrió el navegador, ingresaste un código de 8 caracteres, y GitHub confirmó que tu computadora tiene permiso para crear y modificar repositorios en tu nombre.

---

## 5. Estructura del proyecto

Creé los siguientes archivos y carpetas:

```
Proyecto nch/
├── README.md                          ← Página principal del repositorio
├── .gitignore                         ← Lista de archivos que Git debe ignorar
├── 01-conceptos/
│   └── renta-fija-introduccion.md    ← Plantilla para tus notas de conceptos
├── 02-instrumentos/
│   └── treasuries.md                 ← Plantilla sobre T-Bills, T-Notes, etc.
├── 03-mecanismos/
│   └── la-fed-y-las-tasas.md         ← Plantilla sobre la Fed y tasas
├── 04-recursos/
│   └── lecturas-y-herramientas.md    ← Libros, sitios y ETFs recomendados
└── 05-progreso/
    └── diario.md                     ← Tu diario de aprendizaje semanal
```

### ¿Qué es el `.gitignore`?
Es un archivo especial donde le decís a Git qué archivos *no* debe incluir en el repositorio. En este caso, le dijimos que ignore la carpeta `.obsidian` (configuración de Obsidian) y `.claude` (configuración de Claude Code), porque son archivos personales de tu computadora que no tienen sentido subir a GitHub.

### ¿Qué es el `README.md`?
Es el archivo principal del repositorio. GitHub lo muestra automáticamente como la página de inicio cuando alguien (o vos) entra al repositorio. Contiene el objetivo del proyecto y la hoja de ruta con todo lo que querés aprender.

---

## 6. Inicializar Git en la carpeta

Dentro de la carpeta del proyecto, ejecuté:

```bash
git init
```

Esto convierte la carpeta en un **repositorio de Git**. Git empieza a "vigilar" todos los cambios que hagas en los archivos.

---

## 7. Hacer el primer commit

Un **commit** es una "foto" del estado del proyecto en un momento dado. Para hacerlo, hay dos pasos:

**Paso 1 — Agregar los archivos al "área de preparación"** (decirle a Git qué archivos incluir en la foto):
```bash
git add README.md .gitignore 01-conceptos/ 02-instrumentos/ ...
```

**Paso 2 — Crear el commit con un mensaje descriptivo:**
```bash
git commit -m "Inicio del proyecto NCH — aprendizaje de renta fija EE.UU."
```

Después de esto, Git registró todos los archivos con ese mensaje. Si en el futuro querés ver el historial, podés correr `git log`.

---

## 8. Crear el repositorio en GitHub y subir el proyecto

Con un solo comando de GitHub CLI:

```bash
gh repo create proyecto-nch --public --source=. --remote=origin --push
```

Esto hizo tres cosas a la vez:
1. **Creó el repositorio** `proyecto-nch` en tu cuenta de GitHub (público, visible para cualquiera)
2. **Lo vinculó** con la carpeta local de tu Mac
3. **Subió** todos los archivos (el commit que habíamos hecho)

El repositorio quedó disponible en:
**https://github.com/jpcaputo91-afk/proyecto-nch**

---

## 9. Cómo seguir usando el repositorio

### Para agregar nuevas notas
1. Creá o editá archivos en la carpeta del proyecto
2. En la terminal: `git add .` (agrega todos los cambios)
3. En la terminal: `git commit -m "descripción de lo que hiciste"`
4. En la terminal: `git push` (sube los cambios a GitHub)

### Para ver el historial de cambios
```bash
git log --oneline
```

### Flujo resumido
```
Editar archivos → git add . → git commit -m "mensaje" → git push
```

---

## Glosario rápido

| Término | Significado |
|---|---|
| **Repositorio** | Carpeta de proyecto que Git está vigilando |
| **Commit** | Foto guardada del estado del proyecto |
| **Push** | Subir los commits locales a GitHub |
| **Pull** | Bajar cambios de GitHub a tu computadora |
| **Branch** | Rama paralela del proyecto (para versiones experimentales) |
| **README.md** | Archivo de presentación del repositorio |
| **.gitignore** | Lista de archivos que Git debe ignorar |

---

*Documento generado el 12 de abril de 2026*
