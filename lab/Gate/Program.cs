using System.Security.Cryptography;
using System.Text.Json;

// Didactic verifier. The digest anchor must be outside candidate write scope in production.
var findings=new List<string>();
var verdict="INCONCLUSIVE";
var authority=args.Length==4 && args[3]=="demo-authorized";
try
{
    if(args.Length!=4) throw new InvalidDataException("Expected baseline, sha256, observations, demo mandate");
    var bytes=File.ReadAllBytes(args[0]);
    if(!Convert.ToHexString(SHA256.HashData(bytes)).Equals(args[1],StringComparison.OrdinalIgnoreCase))
        throw new InvalidDataException("Baseline digest mismatch");
    using var baseline=JsonDocument.Parse(bytes);
    using var observations=JsonDocument.Parse(File.ReadAllBytes(args[2]));
    var cases=baseline.RootElement.EnumerateArray().ToArray();
    var rows=observations.RootElement.EnumerateArray().ToArray();
    var expectedIds=cases.Select(c=>c.GetProperty("id").GetString()!).ToArray();
    if(cases.Length==0 || expectedIds.Distinct().Count()!=cases.Length)
        throw new InvalidDataException("Empty or duplicate baseline");
    var actualIds=rows.Select(c=>c.GetProperty("id").GetString()!).ToArray();
    if(actualIds.Distinct().Count()!=rows.Length || actualIds.Any(id=>!expectedIds.Contains(id)))
        throw new InvalidDataException("Duplicate or unknown observation identity");
    bool failed=false, missing=false;
    foreach(var c in cases)
    {
        var id=c.GetProperty("id").GetString();
        var row=rows.FirstOrDefault(x=>x.GetProperty("id").GetString()==id);
        if(row.ValueKind==JsonValueKind.Undefined) {missing=true;findings.Add(id+": missing case");continue;}
        foreach(var key in new[]{"legacy","candidate"})
        {
            if(!row.TryGetProperty(key,out var value) || value.ValueKind!=JsonValueKind.String)
            {missing=true;findings.Add(id+": missing "+key);continue;}
            if(value.GetString()!=c.GetProperty("expected").GetString())
            {failed=true;findings.Add(id+": "+key+" violates contract");}
        }
    }
    verdict=failed ? "FAIL" : missing ? "INCONCLUSIVE" : "PASS";
}
catch(Exception e) when(e is IOException or JsonException or InvalidDataException or InvalidOperationException or KeyNotFoundException)
{findings.Add(e.Message);}
var release=verdict=="PASS" && authority ? "SIMULATED_ALLOW" : "BLOCK";
Console.WriteLine(JsonSerializer.Serialize(new {verdict,authority=authority?"DEMO_ONLY":"DENY",release,findings}));
return verdict=="FAIL" ? 2 : verdict=="INCONCLUSIVE" ? 3 : authority ? 0 : 4;
