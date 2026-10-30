# Documento de diseño

**Intérprete del lenguaje del curso de Compiladores (EIA)** · Evelyn Gómez Aristizábal · Python 3.10+

## 1. Gramática

### Tokens

| Categoría | Tokens |
|---|---|
| Palabras reservadas | `let function true false if elif else return while for` |
| Identificadores | Letra o `_`, seguida de letras, dígitos o `_`. Admite ñ y tildes |
| Literales | Enteros, cadenas entre comillas dobles, `true` y `false` |
| Operadores | Aritméticos `+ - * / % **`, relacionales `== != < > <= >=`, lógicos `&& \|\| !`, asignación `=` |
| Delimitadores | `, ; : ( ) { } [ ]`. Los comentarios `//` llegan hasta el final de la línea y el lexer los descarta |

### Reglas (EBNF)

`{ x }` es cero o más repeticiones, `[ x ]` es opcional y `|` separa alternativas.

```ebnf
program              = { statement } EOF ;
statement            = let_statement | return_statement | expression_statement ;
let_statement        = "let" IDENT "=" expression [ ";" ] ;
return_statement     = "return" expression [ ";" ] ;
expression_statement = expression [ ";" ] ;
block                = "{" { statement } "}" ;
expression  = assignment ;
assignment  = or_expr [ "=" assignment ] ;
or_expr     = and_expr { "||" and_expr } ;
and_expr    = equality { "&&" equality } ;
equality    = comparison { ( "==" | "!=" ) comparison } ;
comparison  = term { ( "<" | ">" | "<=" | ">=" ) term } ;
term        = factor { ( "+" | "-" ) factor } ;
factor      = unary { ( "*" | "/" | "%" ) unary } ;
unary       = ( "-" | "!" ) unary | power ;
power       = postfix [ "**" unary ] ;
postfix     = primary { "(" [ arguments ] ")" | "[" expression "]" } ;
arguments   = expression { "," expression } ;
primary     = INT | STRING | "true" | "false" | IDENT
            | "(" expression ")"
            | array | hash | function | if_expr | while_expr | for_expr ;
array       = "[" [ arguments ] "]" ;
hash        = "{" [ pair { "," pair } ] "}" ;
pair        = expression ":" expression ;
function    = "function" "(" [ IDENT { "," IDENT } ] ")" block ;
if_expr     = "if" "(" expression ")" block
              { "elif" "(" expression ")" block } [ "else" block ] ;
while_expr  = "while" "(" expression ")" block ;
for_expr    = "for" "(" [ for_init ] ";" [ expression ] ";" [ expression ] ")" block ;
for_init    = "let" IDENT "=" expression | expression ;
IDENT  = letter { letter | digit } ;
INT    = digit { digit } ;
STRING = '"' { cualquier carácter excepto '"' } '"' ;
```

- Cuanto más abajo está la regla, más fuerte agrupa, por eso `1 + 2 * 3` es `1 + (2 * 3)`.
- `=` y `**` asocian por la derecha porque su regla se llama a sí misma por la derecha (`2 ** 3 ** 2` es `2 ** (3 ** 2)`), las demás por la izquierda. `-2 ** 2` es `-(2 ** 2)` porque `unary` envuelve a `power`.
- La EBNF acepta `5 = 3`. El parser rechaza como error sintáctico todo destino de `=` que no sea un identificador o un índice.

## 2. Arquitectura

```
texto ──Lexer──▶ tokens ──Parser──▶ AST ──Evaluador──▶ valor o error
```

| Componente (archivos en `src/`) | Funcionamiento |
|---|---|
| Lexer (`tokens.py`, `lexer.py`) | Recorre el texto carácter a carácter con un carácter de anticipación y aplica la coincidencia más larga (`==` antes que `=`). Cada `Token` guarda tipo, literal, línea y columna |
| Parser (`parser.py`) | Pratt con un token de anticipación. Cada nivel de la EBNF es un valor de `Precedence`, y cada token tiene función prefija, infija o ambas |
| AST (`ast_nodes.py`) | Dataclasses divididas en `Statement` y `Expression`. Cada nodo guarda su token inicial, de donde sale la posición de los errores de ejecución |
| Evaluador (`evaluator.py`, `builtin_functions.py`) | Recorre el árbol con `match` sobre el tipo de nodo. Integradas `print`, `len`, `str`, `int`, `type` y `push` |
| Entornos (`objects.py`) | `Environment` con `store` y `outer`. Buscar sube por la cadena, `let` escribe en el ámbito actual y `=` modifica el ámbito más cercano donde existe el nombre |
| Errores (`errors.py`) | `InterpreterError` y sus subclases `LexerError`, `ParserError` y `EvalError`, todas con línea y columna |
| Entrada (`repl.py`, `main.py`) | Ambas modalidades. `python main.py archivo.ssg` ejecuta un archivo y `python main.py` abre el REPL |

Todo el programa se analiza antes de ejecutarse. Por eso un error léxico o sintáctico impide ejecutar cualquier instrucción, mientras que un error de ejecución conserva lo que ya se imprimió.

## 3. Decisiones de diseño

| Decisión | Elección | Razón |
|---|---|---|

| Análisis sintáctico | Pratt | La precedencia vive en una tabla. Agregar un operador es agregar una entrada |
| Errores | Excepciones con posición, se detiene en el primero | Evita propagar errores como valores en cada función, como hace la base |
| `return` | Envoltorio `ReturnValue` | Atraviesa `if` y ciclos hasta `eval_call`, que lo desenvuelve |
| Ámbitos | Solo las funciones crean ámbito, con alcance léxico. `=` no declara | La función guarda el entorno donde se definió, lo que permite recursión y closures. Asignar a un nombre inexistente es error |
| Verdad | Solo `false` y `null` son falsos | Igual que la base. `0`, `""` y `[]` son verdaderos |
| Enteros | Precisión arbitraria. La división trunca hacia cero (`-7 / 2` da `-3`) | Sin desbordamiento (la base usa int64). El truncamiento imita a Go, porque el `//` de Python daría `-4` |
| Igualdad | Tipos distintos dan `false`. Listas y diccionarios se comparan por contenido | La base compara listas por identidad |
| Lógicos | `&&` y `\|\|` con cortocircuito, devuelven booleano | Extensión opcional del enunciado |
| Valores | `Integer`, `String` y `Boolean` son dataclasses inmutables | En Python `True == 1`, así que con tipos nativos `{1: "a", true: "b"}` tendría una sola clave |
| Recursión | Límite de Python en 10 000 | El límite por defecto solo daba 140 niveles. `RecursionError` pasa a `EvalError` |

Extensiones implementadas: closures, cortocircuito, funciones de orden superior, `elif`, comentarios y entrada de varias líneas en el REPL.

## 4. Limitaciones conocidas

- **Rendimiento.** `fibonacci(25)` tarda cerca de 2 s y el `fibonacci(34)` del ejemplo base unos 2,5 minutos, por eso `examples/09_programa_base.ssg` usa `fibonacci(20)`.
- **Recursión.** Hasta unas 1 400 llamadas anidadas.
- **Tipos y cadenas.** Solo enteros, y solo ellos se comparan con `<`, `>`, `<=` y `>=`. Las cadenas no tienen secuencias de escape, así que no pueden contener `"`.
- **Control de flujo.** No existen `break` ni `continue`, y `return` siempre exige un valor.
- **Ámbitos de bloque.** Un `let` dentro de `if` o `for` vive en el ámbito de la función que lo contiene, y la variable de un `for` sigue visible después del ciclo.
- **Errores y REPL.** El parser reporta solo el primer error. Ctrl+C cierra el REPL con traza, se sale con `:salir`.

## 5. Uso de inteligencia artificial

Usé Claude (Anthropic) 

| Tarea | 
|---|---|
| Planteamiento | 
| Pruebas del lexer, evaluador | 
|  ejemplos y casos |

**Verificación.** 127 pruebas con `pytest` cubren cada construcción obligatoria y 9 programas de error con línea y columna exactas. Los `.esperado` se generaron con el intérprete y se revisaron uno por uno. El programa de ejemplo de la rama base dio los resultados documentados en su README.
