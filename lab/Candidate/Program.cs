using System.Globalization;
using System.Text.RegularExpressions;

var mode = args.Length == 0 ? "none" : args[0];
if (!new[]{"none","round-even","wrong-threshold","approve-inactive"}.Contains(mode)) return 4;
string? line;
while ((line=Console.ReadLine()) is not null)
{
    if (!Regex.IsMatch(line, "^[0-9]{13}[YN]$", RegexOptions.CultureInvariant))
    { Console.WriteLine("INVALID|00000000"); continue; }
    var amount=int.Parse(line[..8],CultureInfo.InvariantCulture);
    var rate=int.Parse(line.Substring(8,5),CultureInfo.InvariantCulture);
    if (rate>10000) { Console.WriteLine("INVALID|00000000"); continue; }
    if (line[13]=='N' && mode!="approve-inactive")
    { Console.WriteLine("REJECT|00000000"); continue; }
    var fee=decimal.Round(amount*(decimal)rate/10000m,0,
        mode=="round-even" ? MidpointRounding.ToEven : MidpointRounding.AwayFromZero);
    var threshold=mode=="wrong-threshold" ? 1200000 : 1000000;
    Console.WriteLine($"{(amount>threshold ? "REVIEW" : "APPROVE")}|{fee.ToString("00000000",CultureInfo.InvariantCulture)}");
}
return 0;
