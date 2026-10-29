       >>SOURCE FORMAT FREE
identification division.
program-id. commission.
environment division.
configuration section.
repository.
    function all intrinsic.
data division.
working-storage section.
01 line-in              pic x(100).
01 amount-text          pic x(30).
01 rate-text            pic x(30).
01 amount-value         pic 9(8)v99.
01 rate-value           pic 9(3)v99.
01 fee-value            pic 9(8)v99.
01 fee-formatted        pic z(7)9.99.
procedure division.
    accept line-in
    unstring line-in delimited by ","
        into amount-text rate-text
    end-unstring
    compute amount-value = function numval(amount-text)
    compute rate-value = function numval(rate-text)
    compute fee-value rounded = amount-value * rate-value / 100
    move fee-value to fee-formatted
    display function trim(fee-formatted)
    goback.
