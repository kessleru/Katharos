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

    /// <summary>Quanto tempo sem nenhuma mensagem do motor (resposta ou progresso) até a interface desistir de esperar. Zero = espera sempre.</summary>
    protected virtual TimeSpan SilencioDe(string metodo) => TimeSpan.Zero;
    /// <summary>Quanto o motor pode levar para dizer que está pronto.</summary>
    protected virtual TimeSpan Abertura => TimeSpan.FromSeconds(60);
    /// <summary>Fecha à força um motor que parou de responder, para o próximo pedido abrir um novo.</summary>
    protected virtual void Derruba() { }
    readonly ConcurrentDictionary<int, long> ultimaMensagem = new();

    protected async Task Liga(TextReader entrada, TextWriter saida, CancellationToken ct)
    {
        this.saida = saida;
        string? primeira;
        try { primeira = await entrada.ReadLineAsync(ct).AsTask().WaitAsync(Abertura, ct); }
        catch (TimeoutException)
        {
            Derruba();
            throw new ErroDoMotor("demorou", "O motor do Katharos não ficou pronto em " + (int)Abertura.TotalSeconds + " segundos. Pode ser o antivírus verificando o programa na primeira vez: espere um pouco e tente de novo.");
        }
        if (primeira == null) throw new ErroDoMotor("sem_resposta", "o motor fechou antes de responder");
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
                ultimaMensagem[id] = Environment.TickCount64;
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
        ultimaMensagem[id] = Environment.TickCount64;
        await escrita.WaitAsync();
        try { await saida!.WriteLineAsync(linha); await saida.FlushAsync(); }
        catch { esperando.TryRemove(id, out _); ultimaMensagem.TryRemove(id, out _); throw; }
        finally { escrita.Release(); }
        try
        {
            var silencio = SilencioDe(metodo);
            if (silencio == TimeSpan.Zero) return await tcs.Task;
            // sem mensagem nenhuma do motor pelo tempo do silêncio (nem o progresso que ele manda enquanto trabalha): desiste e
            // derruba o motor, para a tela mostrar "tentar de novo" em vez de carregar para sempre
            while (true)
            {
                var fim = await Task.WhenAny(tcs.Task, Task.Delay(1000));
                if (fim == tcs.Task) return await tcs.Task;
                if (Environment.TickCount64 - ultimaMensagem.GetValueOrDefault(id) > silencio.TotalMilliseconds)
                {
                    esperando.TryRemove(id, out _);
                    Derruba();
                    throw new ErroDoMotor("demorou", $"O Katharos não recebeu resposta do motor em {(int)silencio.TotalSeconds} segundos ({metodo}). Tente de novo; se repetir, veja ~/.katharos/interface.log.");
                }
            }
        }
        finally { ultimaMensagem.TryRemove(id, out _); }
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
    // o raio-x manda progresso a cada etapa, mas uma etapa lenta pode passar de 2 minutos sem mensagem: ele espera mais
    protected override TimeSpan SilencioDe(string metodo) => TimeSpan.FromSeconds(metodo == "raiox" ? 600 : 120);
    protected override void Derruba() { try { proc?.Kill(true); } catch { } }

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
        try { await m.Liga(m.proc.StandardOutput, entrada, ct); }
        catch { m.Derruba(); throw; }   // não deixa um Python sem resposta aberto para trás
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
        // instalado: o motor de administrador roda de uma cópia em %ProgramData%\Katharos (só administrador grava lá), conferida pelo
        // manifesto de SHA-256 cujo hash foi gravado neste aplicativo no build. Assim, um programa comum do mesmo usuário não consegue
        // trocar o Python ou o katharos.py que vai rodar como administrador. Fora da instalação (código, testes), roda direto.
        var protegido = CopiaProtegida.Comando(onde.python, onde.motor, nome, sid, senha);
        var psi = protegido ?? new ProcessStartInfo(onde.python) { Arguments = $"-X utf8 \"{onde.motor}\" api --pipe {nome} --dono {sid} --senha {senha}" };
        psi.UseShellExecute = true; psi.Verb = "runas"; psi.WindowStyle = ProcessWindowStyle.Hidden;
        Process? lancador;
        try { lancador = Process.Start(psi); }
        catch (System.ComponentModel.Win32Exception e) when (e.NativeErrorCode == 1223)
        { throw new ErroDoMotor("recusado", "Sem a permissão de administrador, o Katharos não muda nada. Nada foi alterado."); }
        var m = new MotorElevado { pipe = new NamedPipeClientStream(".", nome, PipeDirection.InOut, PipeOptions.Asynchronous) };
        var liga = m.pipe.ConnectAsync(TimeSpan.FromSeconds(90), ct);
        if (protegido != null && lancador != null)
        {   // o lançador (PowerShell) confere e copia; se algo não confere, ele sai com erro antes de abrir o motor
            var saiu = lancador.WaitForExitAsync(ct);
            if (await Task.WhenAny(liga, saiu) == saiu && !liga.IsCompleted)
            {
                int cod = -1; try { cod = lancador.ExitCode; } catch { }
                if (cod != 0)
                {
                    try
                    {
                        var arq = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "motor-elevado-erro.txt");
                        if (File.Exists(arq)) { Registro.Escreve("motor elevado: " + File.ReadAllText(arq).Trim()); File.Delete(arq); }
                    }
                    catch { }
                    throw new ErroDoMotor("motor_alterado", cod is 11 or 12
                        ? "Os arquivos do Katharos não conferem com os desta instalação (alguém mexeu neles). Nada foi alterado. Reinstale o Katharos pelo site."
                        : $"O motor de administrador não abriu (código {cod}). Nada foi alterado.");
                }
            }
        }
        await liga;
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

/// <summary>
/// A cópia protegida do motor para rodar como administrador: o PowerShell do Windows (pelo caminho completo), já elevado, confere o
/// manifesto (hash gravado no aplicativo), copia python\ e motor\ para %ProgramData%\Katharos\VERSÃO com permissão só de administrador,
/// confere de novo a cópia, e só então abre o motor dali. Uma versão por vez; a anterior sai.
/// </summary>
public static class CopiaProtegida
{
    public static string? HashEsperado() => typeof(CopiaProtegida).Assembly.GetCustomAttributes(typeof(System.Reflection.AssemblyMetadataAttribute), false)
        .OfType<System.Reflection.AssemblyMetadataAttribute>().FirstOrDefault(a => a.Key == "ManifestoSha256")?.Value;

    public static ProcessStartInfo? Comando(string python, string motor, string pipe, string sid, string senha)
    {
        string? h = HashEsperado();
        string app = AppContext.BaseDirectory.TrimEnd('\\', '/');
        if (!OperatingSystem.IsWindows() || string.IsNullOrEmpty(h) || !File.Exists(Path.Combine(app, "motor", "manifesto.json"))) return null;
        string ver = typeof(CopiaProtegida).Assembly.GetName().Version?.ToString() ?? "0";
        string Q(string s) => "'" + s.Replace("'", "''") + "'";
        string script = $$"""
            $ErrorActionPreference = 'Stop'
            # aberto a partir do PowerShell 7 (ou de um programa que herdou o ambiente dele), o caminho de módulos aponta para os do 7,
            # que o Windows PowerShell não carrega: volta ao do Windows antes de usar qualquer comando de módulo
            $env:PSModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Machine')
            trap { try { ($_ | Out-String) | Set-Content -LiteralPath (Join-Path $env:USERPROFILE '.katharos\motor-elevado-erro.txt') -Encoding UTF8 } catch { }; exit 13 }
            $src = {{Q(app)}}; $ver = {{Q(ver)}}; $esperado = {{Q(h)}}
            $base = Join-Path $env:ProgramData 'Katharos'; $dst = Join-Path $base $ver
            $man = Join-Path $src 'motor\manifesto.json'
            if ((Get-FileHash -LiteralPath $man -Algorithm SHA256).Hash.ToLower() -ne $esperado) { exit 11 }
            $m = Get-Content -LiteralPath $man -Raw | ConvertFrom-Json
            $admins = New-Object System.Security.Principal.SecurityIdentifier 'S-1-5-32-544'; $sistema = 'S-1-5-18'
            function DonoSeguro($caminho) {
                $o = (Get-Acl -LiteralPath $caminho).GetOwner([System.Security.Principal.SecurityIdentifier]).Value
                return ($o -eq $admins.Value -or $o -eq $sistema)
            }
            function Apaga($caminho) {
                # rd não segue junção (apaga só o link); nunca Remove-Item -Recurse aqui, que no 5.1 pode seguir
                & (Join-Path $env:SystemRoot 'System32\cmd.exe') /d /c rd /s /q ('"' + $caminho + '"') | Out-Null
            }
            function Confere($raiz) {
                if (-not (DonoSeguro $raiz)) { return $false }
                # exatamente os arquivos do manifesto: nada a mais (uma DLL plantada), nenhum link, todos com dono administrador
                $tem = @(Get-ChildItem -LiteralPath $raiz -Recurse -Force)
                if (@($tem | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) { return $false }
                $arqs = @($tem | Where-Object { -not $_.PSIsContainer })
                if ($arqs.Count -ne @($m.arquivos.PSObject.Properties).Count) { return $false }
                foreach ($f in $arqs) { if (-not (DonoSeguro $f.FullName)) { return $false } }
                foreach ($p in $m.arquivos.PSObject.Properties) {
                    $f = Join-Path $raiz ($p.Name -replace '/', '\')
                    if (-not (Test-Path -LiteralPath $f)) { return $false }
                    if ((Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash.ToLower() -ne $p.Value) { return $false }
                }
                return $true
            }
            # a pasta base tem que ser nossa desde o começo: criada por outro (ou um link), some inteira e é criada de novo
            if (Test-Path -LiteralPath $base) {
                $bi = Get-Item -LiteralPath $base -Force
                if (($bi.Attributes -band [IO.FileAttributes]::ReparsePoint) -or -not (DonoSeguro $base)) { Apaga $base }
            }
            if (-not (Test-Path -LiteralPath $base)) { New-Item -ItemType Directory -Path $base | Out-Null }
            if (-not ((Test-Path -LiteralPath $dst) -and (Confere $dst))) {
                $acl = New-Object System.Security.AccessControl.DirectorySecurity
                $acl.SetAccessRuleProtection($true, $false)
                $acl.SetOwner($admins)
                foreach ($r in @(@('S-1-5-32-544', 'FullControl'), @('S-1-5-18', 'FullControl'), @('S-1-5-32-545', 'ReadAndExecute'))) {
                    $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule((New-Object System.Security.Principal.SecurityIdentifier $r[0]), $r[1], 'ContainerInherit,ObjectInherit', 'None', 'Allow')))
                }
                Set-Acl -LiteralPath $base -AclObject $acl
                $tmp = $dst + '.novo'
                if (Test-Path -LiteralPath $tmp) { Apaga $tmp }
                New-Item -ItemType Directory -Path $tmp | Out-Null
                foreach ($p in $m.arquivos.PSObject.Properties) {
                    $rel = $p.Name -replace '/', '\'
                    $para = Join-Path $tmp $rel
                    New-Item -ItemType Directory -Force -Path (Split-Path $para) | Out-Null
                    Copy-Item -LiteralPath (Join-Path $src $rel) -Destination $para -Force
                }
                # dono Administradores em tudo (em PCs onde o dono padrão é o próprio usuário, ele poderia trocar a permissão depois)
                & (Join-Path $env:SystemRoot 'System32\icacls.exe') $tmp /setowner '*S-1-5-32-544' /T /C /Q | Out-Null
                if (-not (Confere $tmp)) { Apaga $tmp; exit 12 }
                if (Test-Path -LiteralPath $dst) { Apaga $dst }
                Rename-Item -LiteralPath $tmp -NewName (Split-Path $dst -Leaf)
                Get-ChildItem -LiteralPath $base -Force | Where-Object { $_.Name -ne $ver } | ForEach-Object { Apaga $_.FullName }
            }
            $py = Join-Path $dst 'python\python.exe'; $kpy = Join-Path $dst 'motor\programa\katharos.py'
            Start-Process -FilePath $py -WindowStyle Hidden -ArgumentList @('-X', 'utf8', ('"' + $kpy + '"'), 'api', '--pipe', {{Q(pipe)}}, '--dono', {{Q(sid)}}, '--senha', {{Q(senha)}})
            exit 0
            """;
        string ps = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "WindowsPowerShell", "v1.0", "powershell.exe");
        string b64 = Convert.ToBase64String(Encoding.Unicode.GetBytes(script));
        return new ProcessStartInfo(ps) { Arguments = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand " + b64 };
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
