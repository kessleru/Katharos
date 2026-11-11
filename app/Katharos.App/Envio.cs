using System.Net.Http;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;

namespace Katharos.App;

/// <summary>
/// Manda o pacote que o motor montou (já limpo e visto pela pessoa) para o servidor de relatórios. O endereço do servidor vem do site
/// (envio.json), para poder mudar sem versão nova. Sem internet ou com o servidor fora, o pacote fica guardado neste PC, em
/// ~/.katharos/envios-pendentes, e a tela Enviar deixa mandar depois. Nunca manda nada sozinho.
/// </summary>
public static class Envio
{
    const string Config = "https://kessleru.github.io/Katharos/envio.json";
    static readonly HttpClient http = new() { Timeout = TimeSpan.FromSeconds(30) };
    static string Pasta => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "envios-pendentes");

    static ErroDoMotor SemInternet() => new("sem_internet", "Não deu para falar com o servidor do Katharos. Confira a internet e tente de novo.");

    static async Task<string> Url()
    {
        string txt;
        try { txt = await http.GetStringAsync(Config + "?m=" + DateTime.UtcNow.ToString("yyyyMMddHHmm")); }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException) { throw SemInternet(); }
        JsonNode? j = null;
        try { j = JsonNode.Parse(txt); } catch { }
        string url = j?["url"]?.ToString() ?? "";
        bool ativo = j?["ativo"] is JsonValue v && v.TryGetValue(out bool b) && b;
        if (!ativo || !url.StartsWith("https://"))
            throw new ErroDoMotor("envio_fora", "O envio ainda não está no ar.");
        return url;
    }

    /// <summary>Manda e devolve o código (KTH-...). Lança ErroDoMotor com um código que a caixa de erro explica.</summary>
    public static async Task<string> Manda(string json)
    {
        if (Servico.Exemplo) { await Task.Delay(400); return "KTH-7Q4MZD"; }
        string url = await Url();
        HttpResponseMessage r;
        try { r = await http.PostAsync(url, new StringContent(json, Encoding.UTF8, "application/json")); }
        catch (Exception e) when (e is HttpRequestException or TaskCanceledException) { throw SemInternet(); }
        string corpo = await r.Content.ReadAsStringAsync();
        JsonNode? d = null;
        try { d = JsonNode.Parse(corpo); } catch { }
        if ((int)r.StatusCode == 429) throw new ErroDoMotor("envio_limite", "Muitos envios em pouco tempo. Tente de novo daqui a alguns minutos.");
        bool ok = d?["ok"] is JsonValue okv && okv.TryGetValue(out bool okb) && okb;
        string codigo = d?["codigo"]?.ToString() ?? "";
        if (!r.IsSuccessStatusCode || !ok || !Regex.IsMatch(codigo, "^KTH-[A-Z0-9]{4,12}$"))
            throw new ErroDoMotor("envio_recusado", "O servidor não aceitou o envio" + (d?["erro"] is JsonNode er ? ": " + er : $" (código {(int)r.StatusCode})") + ".");
        return codigo;
    }

    /// <summary>Guarda o pacote para mandar depois (só o que a pessoa já viu e quis mandar).</summary>
    public static string Guarda(string json, string tipo)
    {
        Directory.CreateDirectory(Pasta);
        var arq = Path.Combine(Pasta, $"{DateTime.Now:yyyyMMdd-HHmmss}_{(tipo is "relatorio" or "feedback" or "ambos" ? tipo : "envio")}.json");
        File.WriteAllText(arq, json, new UTF8Encoding(false));
        return arq;
    }

    public static List<(string arq, DateTime quando, string tipo)> Pendentes()
    {
        var l = new List<(string, DateTime, string)>();
        try
        {
            if (!Directory.Exists(Pasta)) return l;
            foreach (var f in Directory.GetFiles(Pasta, "*.json").OrderByDescending(x => x))
            {
                var nome = Path.GetFileNameWithoutExtension(f);
                var partes = nome.Split('_');
                DateTime.TryParseExact(partes[0], "yyyyMMdd-HHmmss", null, System.Globalization.DateTimeStyles.None, out var q);
                l.Add((f, q, partes.Length > 1 ? partes[1] : "envio"));
            }
        }
        catch (Exception e) { Registro.Escreve("envios pendentes: " + e.Message); }
        return l;
    }

    public static void Apaga(string arq)
    {
        try { if (Path.GetDirectoryName(Path.GetFullPath(arq)) == Path.GetFullPath(Pasta)) File.Delete(arq); }
        catch (Exception e) { Registro.Escreve("apagar envio pendente: " + e.Message); }
    }
}
