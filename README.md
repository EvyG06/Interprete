# Intérprete del lenguaje del curso de Compiladores

Intérprete escrito en Python para el lenguaje del proyecto base (rama `evaluator` del repositorio del curso). Lee código fuente, lo convierte en tokens, construye un árbol de sintaxis abstracta (AST) y lo ejecuta recorriendo el árbol.

**Integrante:** Evelyn Gómez Aristizábal (trabajo individual).

## Requisitos

- Python 3.10 o superior. El evaluador usa `match`.
- `pytest`, solo para correr las pruebas. El intérprete no tiene dependencias externas.

## Instalación

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pytest
```

Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pytest
```

## Uso

El intérprete admite las dos modalidades de entrada.

### Archivo

```bash
python main.py examples/05_funciones.ssg
```

Ejecuta el archivo completo. Lo que imprime `print` sale por la salida estándar. Si la última sentencia produce un valor distinto de `null`, también se imprime. Los errores salen por la salida de error y el proceso termina con código 1.

### Consola interactiva (REPL)

```bash
python main.py
```

Cada entrada se ejecuta en la misma sesión, así que las variables y funciones se conservan. Si una entrada deja `(`, `[` o `{` sin cerrar, el REPL pide más líneas con `..`.

| Comando | Acción |
|---|---|
| `:lexer` | Muestra los tokens de cada entrada, con línea y columna |
| `:parser` | Muestra el AST de cada entrada, como código con paréntesis y como árbol |
| `:evaluator` | Ejecuta cada entrada (modo inicial) |
| `:cargar RUTA` | Ejecuta un archivo dentro de la sesión actual |
| `:ayuda` | Muestra los comandos |
| `:salir` | Termina la sesión (también Ctrl+Z y Enter en Windows, Ctrl+D en Linux) |

## Pruebas

```bash
pytest
```

| Archivo | Qué prueba |
|---|---|
| `tests/test_lexer.py` | Tokens, coincidencia más larga, posiciones y errores léxicos |
| `tests/test_parser.py` | Precedencia, asociatividad, construcciones y errores sintácticos |
| `tests/test_evaluator.py` | Expresiones, control de flujo, funciones, ámbitos, closures, colecciones, funciones integradas y errores de ejecución |
| `tests/test_programas.py` | Cada programa de `tests/casos/` contra su archivo `.esperado`, y que todos los `examples/` se ejecuten sin errores |
| `tests/test_repl.py` | Sesión interactiva, entradas de varias líneas y modos |

Los casos de `tests/casos/` cuyo nombre empieza por `error_` deben fallar con el mensaje exacto de su `.esperado` y con código 1. Los demás deben terminar con código 0.

## Ejemplos

| Archivo | Característica |
|---|---|
| `01_variables.ssg` | Declaración, consulta y asignación |
| `02_expresiones.ssg` | Aritmética, relacionales, lógicos, precedencia y cortocircuito |
| `03_condicionales.ssg` | `if`, `elif`, `else` y condicionales anidados |
| `04_ciclos.ssg` | `while` y `for` |
| `05_funciones.ssg` | Parámetros, retorno, recursión y funciones de orden superior |
| `06_ambitos.ssg` | Variables locales y globales, alcance léxico y closures |
| `07_estructuras.ssg` | Listas, matrices y diccionarios |
| `08_integradas.ssg` | `print`, `len`, `str`, `int`, `type` y `push` |
| `09_programa_base.ssg` | Programa de ejemplo del proyecto base |

## Estructura

| Ruta | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. Sin argumentos abre el REPL, con una ruta ejecuta el archivo |
| `src/tokens.py` | Tipos de token, palabras reservadas y tablas de operadores |
| `src/lexer.py` | Analizador léxico. Texto a tokens con línea y columna |
| `src/ast_nodes.py` | Nodos del AST e impresión en forma de árbol |
| `src/parser.py` | Analizador sintáctico de Pratt. Tokens a AST |
| `src/objects.py` | Valores en ejecución y entornos (ámbitos) |
| `src/builtin_functions.py` | Funciones integradas |
| `src/evaluator.py` | Recorre el AST y ejecuta el programa |
| `src/errors.py` | Errores léxicos, sintácticos y de ejecución con posición |
| `src/repl.py` | REPL y ejecución de archivos |
| `docs/diseno.md` | Gramática, arquitectura, decisiones y limitaciones |

## El lenguaje en breve

```
// comentario de una línea
let edad = 20;
let saludo = "hola" + " " + "mundo";
let lista = [1, 2, 3];
let persona = {"nombre": "Ada", "edad": 36};

let factorial = function(n) {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
};

for (let i = 0; i < len(lista); i = i + 1) {
    print(i, lista[i]);
}

while (edad < 25) { edad = edad + 1; }

if (edad > 30) { print("mayor"); } elif (edad > 20) { print("medio"); } else { print("menor"); }
```

- Tipos: enteros, cadenas, booleanos, listas, diccionarios, funciones y `null`.
- Solo `false` y `null` son falsos.
- `let` declara en el ámbito actual y `=` modifica una variable ya declarada.
- Solo las funciones crean un ámbito nuevo, y el alcance es léxico.

La gramática completa en EBNF y las decisiones de diseño están en `docs/diseno.md`.
