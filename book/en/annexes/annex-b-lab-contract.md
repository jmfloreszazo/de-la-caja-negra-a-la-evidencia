**English** · [Español](../../es/anexos/anexo-b-contrato-del-laboratorio.md)

[← Annex A · A lab that can prove us wrong](annex-a-a-lab-that-can-prove-us-wrong.md) · [Contents](../README.md) · [Annex C · Reference run →](annex-c-reference-run.md)

# Annex B · Lab contract

| Element | Fixed rule |
|---|---|
| Input | Fourteen characters without separators |
| Amount | Eight ASCII digits with non-negative cents |
| Rate | Five ASCII digits of basis points between 0 and 10,000 |
| Status | Y active or N inactive |
| Priority | Validate format and range before deciding |
| Inactive | REJECT and zero fee |
| Active above 1,000,000 cents | REVIEW |
| Active at or below the threshold | APPROVE |
| Fee for an active customer | Amount times rate divided by 10,000 and rounded to the nearest integer with ties away from zero |
| Output | Status followed by a vertical bar and eight fee digits |
| Missing evidence or invalid reference | INCONCLUSIVE and block |
| Discrepancy with the expectation | FAIL and block |
| Correct behaviour without a mandate | Functional PASS and delivery blocked |

The scope of the invalid tests is limited to fourteen-character records. Native COBOL reading has its own width rules. A production adapter must reject incorrect lengths before passing records to the program. The guided walkthrough applies that validation to interactive inputs.

The fee service does not include CICS, Db2, JCL, IBM i, distributed transactions, EBCDIC or negative values. The banking module adds local persistence and concurrency. Neither includes real IAM or a verified human identity. The internal COMP-3 does not prove cross-platform file interoperability.

---

[← Annex A · A lab that can prove us wrong](annex-a-a-lab-that-can-prove-us-wrong.md) · [Contents](../README.md) · [Annex C · Reference run →](annex-c-reference-run.md)
