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
            .OnAfterUpdateFastCallback(_ => SegundoPlano.ReligaDepoisDaTroca())
            .OnBeforeUninstallFastCallback(_ => { SegundoPlano.PedeParaSair(reabrir: false); SegundoPlano.TiraDoInicio(); })
            .Run();
        int i = Array.IndexOf(args, "--tela");
        if (i >= 0 && i + 1 < args.Length) TelaInicial = args[i + 1];
        // uma janela só: abrir de novo (pelo ícone, pelo menu Iniciar) traz a que já está aberta, na tela pedida
        unica = new Mutex(true, @"Local\Katharos.Janela", out bool primeira);
        if (!primeira)
        {
            SegundoPlano.PedeTela(TelaInicial);
            return;
        }
        MontaApp().StartWithClassicDesktopLifetime(args);
        GC.KeepAlive(unica);
    }

    public static AppBuilder MontaApp() => AppBuilder.Configure<App>().UsePlatformDetect().LogToTrace();
}

/// <summary>A conversa da janela com o segundo plano (o ícone perto do relógio), pelos arquivos de sempre em ~/.katharos.</summary>
public static class SegundoPlano
{
    static string Casa => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
    static string Arq(string nome) => Path.Combine(Casa, nome);

    /// <summary>O segundo plano está lendo (o agora.json foi escrito há pouco)?</summary>
    public static bool Rodando() => File.Exists(Arq("agora.json")) && (DateTime.Now - File.GetLastWriteTime(Arq("agora.json"))).TotalSeconds < 20;

    /// <summary>Pede para o segundo plano sair (ele confere a cada 3 s) e, se pedir, marca para reabrir na próxima abertura da janela.
    /// Usado antes de trocar de versão (os arquivos dele vão ser trocados) e ao desinstalar.</summary>
    public static void PedeParaSair(bool reabrir)
    {
        try
        {
            if (!Rodando()) return;
            Directory.CreateDirectory(Casa);
            if (reabrir) File.WriteAllText(Arq("reabrir-segundo-plano.txt"), DateTime.Now.ToString("s"));
            File.WriteAllText(Arq("segundo-plano-sair.txt"), DateTime.Now.ToString("s"));
            for (int i = 0; i < 40 && Rodando(); i++) Thread.Sleep(250);
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

    /// <summary>Logo depois da troca de versão (o Velopack chama a versão nova): religa o segundo plano já na pasta nova, sem abrir janela.</summary>
    public static void ReligaDepoisDaTroca()
    {
        var m = Arq("reabrir-segundo-plano.txt");
        var exe = Path.Combine(AppContext.BaseDirectory, "motor", "Katharos.exe");
        if (!File.Exists(m) || !File.Exists(exe)) return;
        try
        {
            File.Delete(m);
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo(exe, "--segundo-plano") { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(exe)! });
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
