# Documento de diseño

## Gramática

### Tokens

| Categoría | Tokens |
|---|---|
| Palabras reservadas | `let function true false if elif else return while for` |
| Identificadores | Letra o `_`, seguida de letras, dígitos o `_`. Admite ñ y tildes |
| Literales | Enteros `0-9`, cadenas entre comillas dobles, `true` y `false` |
| Aritméticos | `+ - * / % **` |
| Relacionales | `== != < > <= >=` |
| Lógicos | `&& \|\| !` |
| Asignación | `=` |
| Delimitadores | `, ; : ( ) { } [ ]` |
| Comentarios | `//` hasta el final de la línea. El lexer los descarta, no son tokens |

### Reglas (EBNF)

Notación. `{ x }` es cero o más repeticiones, `[ x ]` es opcional y `|` separa alternativas.

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
              { "elif" "(" expression ")" block }
              [ "else" block ] ;
while_expr  = "while" "(" expression ")" block ;
for_expr    = "for" "(" [ for_init ] ";" [ expression ] ";" [ expression ] ")" block ;
for_init    = "let" IDENT "=" expression | expression ;

IDENT  = letter { letter | digit } ;
INT    = digit { digit } ;
STRING = '"' { cualquier carácter excepto '"' } '"' ;
```

### Precedencia y asociatividad

- Cuanto más abajo está la regla, más fuerte agrupa. En `1 + 2 * 3`, `term` pide sus operandos a `factor`, por eso `2 * 3` se agrupa primero.
- `=` y `**` asocian por la derecha porque su regla se llama a sí misma por la derecha. `a = b = 5` es `a = (b = 5)` y `2 ** 3 ** 2` es `2 ** (3 ** 2)`. Las demás asocian por la izquierda.
- `-2 ** 2` es `-(2 ** 2)`, igual que en Python, porque `unary` envuelve a `power`.
- La EBNF acepta `5 = 3`. Que el destino de `=` sea un identificador o un índice lo valida el parser como error sintáctico.
