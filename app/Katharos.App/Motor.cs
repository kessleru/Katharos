using System.Collections.Concurrent;
using System.Diagnostics;
using System.IO.Pipes;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Katharos.App;

/// <summary>Resposta de erro do motor, com o código do protocolo (precisa_aceite, precisa_admin, ocupado, ...).</summary>
public class ErroDoMotor(string codigo, string texto) : Exception(texto)
{
    public string Codigo { get; } = codigo;
}

/// <summary>
/// Conversa com o motor (katharos.py api) por JSON, uma linha por mensagem. Um pedido por vez pode estar em voo por id; os eventos
/// de progresso chegam antes da resposta e vão para quem pediu.
/// </summary>
public abstract class Conversa : IAsyncDisposable
{
    readonly ConcurrentDictionary<int, (TaskCompletionSource<JsonNode?> fim, Action<string, JsonNode?>? evento)> esperando = new();
    readonly SemaphoreSlim escrita = new(1, 1);
    TextWriter? saida;
    int proximo;
    public string Versao { get; private set; } = "";
    public event Action<string>? Caiu;

    protected async Task Liga(TextReader entrada, TextWriter saida, CancellationToken ct)
    {
        this.saida = saida;
        var primeira = await entrada.ReadLineAsync(ct) ?? throw new ErroDoMotor("sem_resposta", "o motor fechou antes de responder");
        var p = JsonNode.Parse(primeira);
        if (p?["pronto"]?.GetValue<bool>() != true)
            throw new ErroDoMotor(p?["erro"]?["codigo"]?.ToString() ?? "sem_resposta", p?["erro"]?["texto"]?.ToString() ?? "o motor não ficou pronto");
        Versao = p["versao"]?.ToString() ?? "";
        _ = Task.Run(() => Le(entrada));
    }

    async Task Le(TextReader entrada)
    {
        string motivo = "o motor fechou";
        try
        {
            string? l;
            while ((l = await entrada.ReadLineAsync()) != null)
            {
                JsonNode? m;
                try { m = JsonNode.Parse(l); } catch (JsonException) { continue; }
                if (m?["id"] is not JsonValue v || !v.TryGetValue(out int id) || !esperando.TryGetValue(id, out var quem)) continue;
                if (m["evento"] is JsonNode ev) { quem.evento?.Invoke(ev.ToString(), m["dados"]); continue; }
                esperando.TryRemove(id, out _);
                if (m["ok"]?.GetValue<bool>() == true) quem.fim.TrySetResult(m["dados"]);
                else quem.fim.TrySetException(new ErroDoMotor(m["erro"]?["codigo"]?.ToString() ?? "interno", m["erro"]?["texto"]?.ToString() ?? "erro sem texto"));
            }
        }
        catch (Exception e) { motivo = e.Message; }
        foreach (var (_, q) in esperando) q.fim.TrySetException(new ErroDoMotor("caiu", motivo));
        esperando.Clear();
        Caiu?.Invoke(motivo);
    }

    /// <summary>Pede um método. Eventos (progresso, etapa, pacote) vão para <paramref name="evento"/>, na linha de leitura.</summary>
    public async Task<JsonNode?> Pede(string metodo, object? parametros = null, Action<string, JsonNode?>? evento = null)
    {
        int id = Interlocked.Increment(ref proximo);
        var tcs = new TaskCompletionSource<JsonNode?>(TaskCreationOptions.RunContinuationsAsynchronously);
        esperando[id] = (tcs, evento);
        var linha = JsonSerializer.Serialize(new { id, metodo, @params = parametros ?? new { } });
        await escrita.WaitAsync();
        try { await saida!.WriteLineAsync(linha); await saida.FlushAsync(); }
        finally { escrita.Release(); }
        return await tcs.Task;
    }

    public virtual async ValueTask DisposeAsync()
    {
        try { if (saida != null) await Pede("sair").WaitAsync(TimeSpan.FromSeconds(3)); } catch { }
    }
}

/// <summary>Onde estão o Python e o katharos.py: ao lado do aplicativo (instalado) ou o que a pessoa já tem (versão de terminal).</summary>
public static class OndeEsta
{
    public static (string python, string motor)? Acha()
    {
        string app = AppContext.BaseDirectory;
        string? motor = new[]
        {
            // instalado: o motor ao lado do aplicativo vem primeiro, e nada de fora (variável de ambiente) passa na frente dele,
            // porque é este mesmo caminho que o motor de administrador abre
            Path.Combine(app, "motor", "programa", "katharos.py"),
            Environment.GetEnvironmentVariable("KATHAROS_MOTOR"),
            Path.Combine(app, "..", "..", "..", "..", "..", "programa", "katharos.py"),   // rodando de dentro do repositório
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "katharos.py"),
        }.Where(p => !string.IsNullOrEmpty(p)).Select(p => Path.GetFullPath(p!)).FirstOrDefault(File.Exists);
        if (motor == null) return null;
        string? py = new[] { Path.Combine(app, "python", "python.exe") }.FirstOrDefault(File.Exists) ?? NoPath(OperatingSystem.IsWindows() ? new[] { "python.exe", "py.exe" } : new[] { "python3" });
        return py == null ? null : (py, motor);
    }

    static string? NoPath(string[] nomes)
    {
        foreach (var dir in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator))
            foreach (var n in nomes)
            {
                try { var c = Path.Combine(dir, n); if (File.Exists(c) && !c.Contains("WindowsApps", StringComparison.OrdinalIgnoreCase)) return c; } catch { }
            }
        return null;
    }
}

/// <summary>O motor comum: roda como o usuário, para tudo o que só lê. Fica aberto enquanto o aplicativo está aberto.</summary>
public sealed class MotorComum : Conversa
{
    Process? proc;

    public static async Task<MotorComum> Abre(CancellationToken ct = default)
    {
        var onde = OndeEsta.Acha() ?? throw new ErroDoMotor("sem_motor", "Não achei o Python e o katharos.py. Reinstale o Katharos.");
        var m = new MotorComum();
        var psi = new ProcessStartInfo(onde.python) { RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true, StandardOutputEncoding = Encoding.UTF8 };
        psi.ArgumentList.Add("-X"); psi.ArgumentList.Add("utf8");
        psi.ArgumentList.Add(onde.motor); psi.ArgumentList.Add("api");
        psi.Environment["PYTHONIOENCODING"] = "utf-8";
        m.proc = Process.Start(psi) ?? throw new ErroDoMotor("sem_motor", "o Python não abriu");
        m.proc.ErrorDataReceived += (_, e) => { if (e.Data != null) Registro.Escreve("motor: " + e.Data); };
        m.proc.BeginErrorReadLine();
        var entrada = new StreamWriter(m.proc.StandardInput.BaseStream, new UTF8Encoding(false)) { AutoFlush = false };
        await m.Liga(m.proc.StandardOutput, entrada, ct);
        return m;
    }

    public override async ValueTask DisposeAsync()
    {
        await base.DisposeAsync();
        try { if (proc is { HasExited: false }) { if (!proc.WaitForExit(2000)) proc.Kill(); } } catch { }
        proc?.Dispose();
    }
}

/// <summary>
/// O motor elevado: o mesmo katharos.py como administrador (um pedido de permissão do Windows por sessão), num pipe que só o seu
/// usuário abre, com uma senha de uso único que vai na linha de comando do processo elevado (um programa comum não consegue ler).
/// </summary>
public sealed class MotorElevado : Conversa
{
    NamedPipeClientStream? pipe;

    public static async Task<MotorElevado> Abre(CancellationToken ct = default)
    {
        if (!OperatingSystem.IsWindows()) throw new ErroDoMotor("so_windows", "mudar o PC só funciona no Windows");
        var onde = OndeEsta.Acha() ?? throw new ErroDoMotor("sem_motor", "Não achei o Python e o katharos.py. Reinstale o Katharos.");
        string nome = "katharos-" + Convert.ToHexString(RandomNumberGenerator.GetBytes(8)).ToLowerInvariant();
        string senha = Convert.ToHexString(RandomNumberGenerator.GetBytes(24)).ToLowerInvariant();
        string sid = WindowsIdentity.GetCurrent().User!.Value;
        var psi = new ProcessStartInfo(onde.python) { UseShellExecute = true, Verb = "runas", WindowStyle = ProcessWindowStyle.Hidden };
        psi.Arguments = $"-X utf8 \"{onde.motor}\" api --pipe {nome} --dono {sid} --senha {senha}";
        try { Process.Start(psi); }
        catch (System.ComponentModel.Win32Exception e) when (e.NativeErrorCode == 1223)
        { throw new ErroDoMotor("recusado", "Sem a permissão de administrador, o Katharos não muda nada. Nada foi alterado."); }
        var m = new MotorElevado { pipe = new NamedPipeClientStream(".", nome, PipeDirection.InOut, PipeOptions.Asynchronous) };
        await m.pipe.ConnectAsync(TimeSpan.FromSeconds(60), ct);
        var w = new StreamWriter(m.pipe, new UTF8Encoding(false)) { AutoFlush = false, NewLine = "\n" };
        await w.WriteLineAsync(JsonSerializer.Serialize(new { senha })); await w.FlushAsync(ct);
        await m.Liga(new StreamReader(m.pipe, Encoding.UTF8), w, ct);
        return m;
    }

    public override async ValueTask DisposeAsync()
    {
        await base.DisposeAsync();
        pipe?.Dispose();
    }
}

/// <summary>Registro da interface (ao lado do log do motor), para entender um problema depois.</summary>
public static class Registro
{
    static readonly object trava = new();
    public static void Escreve(string texto)
    {
        try
        {
            var d = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
            Directory.CreateDirectory(d);
            lock (trava) File.AppendAllText(Path.Combine(d, "interface.log"), $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {texto}\n");
        }
        catch { }
    }
}
