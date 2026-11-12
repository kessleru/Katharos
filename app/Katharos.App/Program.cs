using Avalonia;
using Microsoft.Win32;

namespace Katharos.App;

static class Program
{
    /// <summary>A tela pedida na linha de comando (o ícone do segundo plano abre "--tela aovivo", por exemplo).</summary>
    public static string TelaInicial = "inicio";
    static Mutex? unica;

    [STAThread]
    public static void Main(string[] args)
    {
        // primeiro de tudo: o Velopack trata a instalação, a desinstalação e a troca de versão (e sai, quando é com ele)
        Velopack.VelopackApp.Build()
            .OnBeforeUpdateFastCallback(_ => SegundoPlano.PedeParaSair(reabrir: true))
            .OnBeforeUninstallFastCallback(_ => { SegundoPlano.PedeParaSair(reabrir: false); SegundoPlano.TiraDoInicio(); })
            .Run();
        // ensaio do CI (5.2): atualiza esta instalação a partir de uma pasta de releases, do mesmo jeito que pelo GitHub
        // logo depois de uma troca de versão sem janela (automática ao fechar, ou o ensaio): só religa o segundo plano e sai
        if (args.Contains("--depois-da-troca")) { SegundoPlano.ReligaDepoisDaTroca(); return; }
        int ta = Array.IndexOf(args, "--teste-atualizacao");
        if (ta >= 0 && ta + 1 < args.Length) { Environment.Exit(TesteAtualizacao(args[ta + 1])); return; }
        // ensaio do CI (S5): abre o motor de administrador como a janela abre (cópia protegida conferida) e pede a versão
        if (args.Contains("--teste-motor-elevado")) { Environment.Exit(TesteMotorElevado().GetAwaiter().GetResult()); return; }
        int i = Array.IndexOf(args, "--tela");
        if (i >= 0 && i + 1 < args.Length) TelaInicial = args[i + 1];
        // uma janela só: abrir de novo (pelo ícone, pelo menu Iniciar) traz a que já está aberta, na tela pedida
        unica = new Mutex(true, @"Local\Katharos.Janela", out bool primeira);
        if (!primeira)
        {
            SegundoPlano.PedeTela(TelaInicial);
            return;
        }
        // erro que derruba o aplicativo (raro: as telas já tratam os seus) fica no registro, para saber o que houve
        AppDomain.CurrentDomain.UnhandledException += (_, e) => Registro.Escreve("o aplicativo fechou por um erro: " + e.ExceptionObject);
        // o segundo plano (que pode estar rodando de outra pasta) lê daqui onde está a janela, para nunca abrir o Katharos de terminal
        try
        {
            if (Directory.Exists(Path.Combine(AppContext.BaseDirectory, "python")))
            {
                var casa = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
                Directory.CreateDirectory(casa);
                File.WriteAllText(Path.Combine(casa, "janela.txt"), Environment.ProcessPath ?? Path.Combine(AppContext.BaseDirectory, "Katharos.exe"));
            }
        }
        catch (Exception e) { Registro.Escreve("janela.txt: " + e.Message); }
        try { MontaApp().StartWithClassicDesktopLifetime(args); }
        catch (Exception e) { Registro.Escreve("o aplicativo fechou por um erro: " + e); throw; }
        GC.KeepAlive(unica);
    }

    static async Task<int> TesteMotorElevado()
    {
        try
        {
            await using var m = await MotorElevado.Abre();
            var v = await m.Pede("versao");
            Registro.Escreve("ensaio do motor elevado: " + v?.ToJsonString() + " (cópia protegida: " + (CopiaProtegida.HashEsperado() != null) + ")");
            return v?["versao"] != null ? 0 : 4;
        }
        catch (Exception e) { Registro.Escreve("ensaio do motor elevado: " + e); return e is ErroDoMotor { Codigo: "motor_alterado" } m && m.Message.Contains("não conferem") ? 11 : 1; }
    }

    static int TesteAtualizacao(string pasta)
    {
        try
        {
            var g = new Velopack.UpdateManager(pasta);
            if (!g.IsInstalled) { Registro.Escreve("ensaio de atualização: não está instalado"); return 3; }
            var info = g.CheckForUpdates();
            if (info == null) { Registro.Escreve("ensaio de atualização: nada novo em " + pasta); return 2; }
            g.DownloadUpdates(info);
            SegundoPlano.PedeParaSair(reabrir: true);
            Registro.Escreve("ensaio de atualização: aplicando " + info.TargetFullRelease.Version);
            g.ApplyUpdatesAndRestart(info.TargetFullRelease, new[] { "--depois-da-troca" });
            return 0;
        }
        catch (Exception e) { Registro.Escreve("ensaio de atualização: " + e); return 1; }
    }

    public static AppBuilder MontaApp() => AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();
}

/// <summary>A conversa da janela com o segundo plano (o ícone perto do relógio), pelos arquivos de sempre em ~/.katharos.</summary>
public static class SegundoPlano
{
    static string Casa => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
    static string Arq(string nome) => Path.Combine(Casa, nome);

    /// <summary>Os processos do segundo plano desta instalação (motor\Katharos.exe), achados pelo caminho: funciona mesmo com a
    /// leitura pausada (aí o agora.json fica parado).</summary>
    static List<System.Diagnostics.Process> Processos()
    {
        string exe = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "motor", "Katharos.exe"));
        var out_ = new List<System.Diagnostics.Process>();
        foreach (var p in System.Diagnostics.Process.GetProcessesByName("Katharos"))
        {
            try { if (p.Id != Environment.ProcessId && string.Equals(p.MainModule?.FileName, exe, StringComparison.OrdinalIgnoreCase)) { out_.Add(p); continue; } } catch { }
            p.Dispose();
        }
        return out_;
    }

    /// <summary>O segundo plano está rodando (pelo processo; o agora.json recente vale para a versão de terminal).</summary>
    public static bool Rodando() => Processos().Count > 0 || (File.Exists(Arq("agora.json")) && (DateTime.Now - File.GetLastWriteTime(Arq("agora.json"))).TotalSeconds < 20);

    /// <summary>Pede para o segundo plano sair (ele confere a cada 3 s) e, se pedir, marca para reabrir na próxima abertura da janela.
    /// Usado antes de trocar de versão (os arquivos dele vão ser trocados) e ao desinstalar.</summary>
    public static void PedeParaSair(bool reabrir)
    {
        try
        {
            var ps = Processos();
            if (ps.Count == 0) return;
            Directory.CreateDirectory(Casa);
            if (reabrir) File.WriteAllText(Arq("reabrir-segundo-plano.txt"), DateTime.Now.ToString("s"));
            File.WriteAllText(Arq("segundo-plano-sair.txt"), DateTime.Now.ToString("s"));
            foreach (var p in ps) { try { p.WaitForExit(15000); } catch { } p.Dispose(); }   // espera o processo sair de verdade
            try { File.Delete(Arq("segundo-plano-sair.txt")); } catch { }   // ninguém atendeu: não fica pedido velho para o próximo
        }
        catch (Exception e) { Registro.Escreve("segundo plano: pedir para sair: " + e.Message); }
    }

    /// <summary>Na desinstalação: tira o "iniciar com o Windows" que aponta para dentro desta instalação (o resto em ~/.katharos fica).</summary>
    public static void TiraDoInicio()
    {
        if (!OperatingSystem.IsWindows()) return;
        try
        {
            using var k = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run", true);
            if (k?.GetValue("Katharos") is string v && v.Contains(AppContext.BaseDirectory.TrimEnd('\\'), StringComparison.OrdinalIgnoreCase)) k.DeleteValue("Katharos", false);
        }
        catch (Exception e) { Registro.Escreve("desinstalar: " + e.Message); }
    }

    /// <summary>Outra abertura pediu uma tela: a janela aberta lê este arquivo e vem para a frente.</summary>
    public static void PedeTela(string tela)
    {
        try { Directory.CreateDirectory(Casa); File.WriteAllText(Arq("abrir-tela.txt"), tela); } catch { }
    }

    public static string? TelaPedida()
    {
        try
        {
            var a = Arq("abrir-tela.txt");
            if (!File.Exists(a)) return null;
            var t = File.ReadAllText(a).Trim();
            File.Delete(a);
            return t == "" ? "inicio" : t;
        }
        catch { return null; }
    }

    /// <summary>Logo depois da troca de versão, na versão nova aberta com --depois-da-troca (não no gancho rápido do Velopack: o que ele abre
    /// é encerrado junto com ele): religa o segundo plano já na pasta nova, sem abrir janela.</summary>
    public static void ReligaDepoisDaTroca()
    {
        var m = Arq("reabrir-segundo-plano.txt");
        var exe = Path.Combine(AppContext.BaseDirectory, "motor", "Katharos.exe");
        Registro.Escreve($"depois da troca: reabrir={File.Exists(m)}, segundo plano em {exe} ({File.Exists(exe)})");
        if (!File.Exists(m) || !File.Exists(exe)) return;
        try
        {
            File.Delete(m);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(exe, "--segundo-plano") { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(exe)! });
            Registro.Escreve("depois da troca: segundo plano religado");
        }
        catch (Exception e) { Registro.Escreve("religar o segundo plano: " + e.Message); }
    }

    /// <summary>Depois de trocar de versão: religa o segundo plano que estava rodando antes.</summary>
    public static async Task ReabreSePreciso()
    {
        var m = Arq("reabrir-segundo-plano.txt");
        if (!File.Exists(m)) return;
        try { File.Delete(m); await Servico.Le("segundo_plano", new { ligar = true }); }
        catch (Exception e) { Registro.Escreve("reabrir o segundo plano: " + e.Message); }
    }
}
