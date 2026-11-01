# Continuación de C2 · Inscripción SQL y recuperación del cambio de autoridad

**Evidencia técnica acotada, 1 de noviembre de 2026; no cierra toda la issue #64.**
La [CI original #41352470918](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41352470918),
job `124985443092`, superó **19 controles** sobre el SHA exacto de origen/checkout
`3dd279c682ece00dfe62e68f68b1e4b967c4d333`.

- [ZIP original](brownfield-c2-pr69-original.zip), conservado sin modificar:
  artefacto `13101916329`, 4088 bytes, SHA-256
  `f1ed8582f1e0bea5ef98fe723ec63d1748cb918b9f34c0f1cbb041bd7aa488c1`.
- [JSON original](brownfield-c2-pr69-original-summary.json), extraído sin cambios
  del ZIP. El archivo conserva también compilación, procedencia y las seis
  respuestas concurrentes con el mismo identificador.
- [Registro del primer fallo](brownfield-c2-pr69-first-failure.json): la
  [ejecución #41352306908](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41352306908)
  falló al comprobar las respuestas concurrentes. No imprimió cada respuesta.
  La inspección del código identificó que el bloqueo de la operación se
  liberaba antes de la conciliación independiente; mantenerlo corrigió la
  prueba observada. Se conserva el fallo, sin convertirlo en PASS.

La ejecución correcta incluye restricciones de dirección del controlador,
inscripción persistida que impide desactivar ambos adaptadores por entorno,
idempotencia concurrente, conciliación SQL después de perder ACK, corrupción
del journal, SIGKILL externo real, épocas antiguas, outbox ausente, época
alterada y veto al rollback tras decisiones del candidato.

| Frontera del SIGKILL externo | Controlador persistido | Autoridad persistida del candidato | Intención preparada |
| --- | --- | --- | --- |
| Después de preparar | legacy / 1 / SWITCHING | legacy / 1 | legacy/1 → candidate/2 |
| Después del COMMIT de autoridad candidata | candidate / 2 / SWITCHING | legacy / 3 | candidate/2 → legacy/3 |

Ambos procesos murieron con código **-9**. La segunda transición ensayó una
vuelta atrás antes de ninguna decisión originada por el candidato. La
recuperación concilió la intención exacta; una época inesperada o la ausencia
de outbox impidieron descongelar el tráfico. La época final fue 4. Una decisión
posterior del candidato bloqueó el rollback.

La auditoría final del journal es **false deliberadamente**: `J-ADMIT-DEAD` y
`J-DISPATCH-DEAD` siguen sin resolver, y el asiento SQL directo equilibrado
`J-RAW-SQL` no tiene admisión. Los dos oráculos contables pasaron. El ensayo
solo pasa si detecta esos casos inseguros; no autoriza el cutover.

Los cambios posteriores del test añaden el rechazo del cambio de autoridad
independiente tras la inscripción y más hashes de origen. Necesitan su CI
propia sobre HEAD exacto: los bytes de estos 19 controles no se reescriben para
atribuirles cobertura posterior. El JSON y el commit conservan los hashes de
la implementación observada.

**Límites:** tres contenedores PostgreSQL en un runner; adaptadores cooperativos
inscritos, sin fencing del incumbente real ni COMMIT distribuido atómico.
Siguen sin verificar las particiones del controlador durante operaciones,
los dominios físicos de fallo, los efectos externos y la política y mandatos
del propietario. G2=INCONCLUSIVE, G6=BLOCK; #64/#58 abiertas, #53 congelada,
sin cambios de release ni tags.

[Evidencia C2 anterior](BROWNFIELD-JOURNAL.es.md) · [Protocolo y reproducción](../../lab/brownfield/journal/README.md) · [English](BROWNFIELD-C2-RECOVERY.md)
