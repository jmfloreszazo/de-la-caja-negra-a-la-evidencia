**Español** · [English](../../en/annexes/annex-b-lab-contract.md)

[← Anexo A · Un laboratorio que pueda contradecirnos](anexo-a-un-laboratorio-que-pueda-contradecirnos.md) · [Índice](../README.md) · [Anexo C · Ejecución de referencia →](anexo-c-ejecucion-de-referencia.md)

# Anexo B · Contrato del laboratorio

| Elemento | Regla fijada |
|---|---|
| Entrada | Catorce caracteres sin separadores |
| Importe | Ocho dígitos ASCII con céntimos no negativos |
| Tasa | Cinco dígitos ASCII de puntos básicos entre 0 y 10 000 |
| Estado | Y activo o N inactivo |
| Prioridad | Validar formato y rango antes de decidir |
| Inactivo | REJECT y comisión cero |
| Activo por encima de 1 000 000 céntimos | REVIEW |
| Activo en el umbral o por debajo | APPROVE |
| Comisión de activo | Importe por tasa dividido por 10 000 y redondeado al entero más próximo con empate alejándose de cero |
| Salida | Estado seguido de barra vertical y ocho dígitos de comisión |
| Evidencia ausente o referencia no válida | INCONCLUSIVE y bloqueo |
| Discrepancia con expectativa | FAIL y bloqueo |
| Comportamiento correcto sin mandato | PASS funcional y bloqueo de entrega |

El alcance de las pruebas inválidas se limita a registros de catorce caracteres. La lectura nativa COBOL tiene reglas de anchura propias. Un adaptador de producción debe rechazar longitudes incorrectas antes de introducir registros en el programa. El recorrido guiado aplica esa validación para las entradas interactivas.

El servicio de comisión no incluye CICS, Db2, JCL, IBM i, transacciones distribuidas, EBCDIC ni valores negativos. El módulo bancario añade persistencia y concurrencia locales. Ninguno incorpora IAM real ni identidad humana verificada. El COMP-3 interno no prueba interoperabilidad de ficheros entre plataformas.

---

[← Anexo A · Un laboratorio que pueda contradecirnos](anexo-a-un-laboratorio-que-pueda-contradecirnos.md) · [Índice](../README.md) · [Anexo C · Ejecución de referencia →](anexo-c-ejecucion-de-referencia.md)
