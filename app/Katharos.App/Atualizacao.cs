using Velopack;
using Velopack.Sources;

namespace Katharos.App;

/// <summary>
/// Atualização pelo Velopack, das releases do GitHub: confere ao abrir (no máximo uma vez por dia), baixa só a diferença e troca de
/// versão quando a pessoa pede ou ao fechar (config "atualizacoes": avisar, automatico ou nunca). Nunca no meio de uma mudança no PC.
/// Fora da instalação (rodando do código, fotos) não faz nada.
/// </summary>
public static class Atualizacao
{
    static UpdateManager? gerente;
    static UpdateInfo? pronta;
    public static string? VersaoPronta => pronta?.TargetFullRelease.Version.ToString();
    public static event Action? Mudou;
    public static bool Ocupado;
    /// <summary>A versão nova entra quando a janela fechar: o segundo plano sai junto e volta sozinho depois da troca.</summary>
    public static bool AoFechar;   // true enquanto o motor elevado aplica ou desfaz algo

    static string canal = "estavel";

    static UpdateManager? Gerente()
    {
        if (Servico.Exemplo) return null;
        try
        {
            // canal "prévia": as releases marcadas como pré-lançamento no GitHub entram também (para testar antes de todo mundo)
            gerente ??= new UpdateManager(new GithubSource("https://github.com/kessleru/Katharos", null, canal == "previa"));
            return gerente.IsInstalled ? gerente : null;
        }
        catch (Exception e) { Registro.Escreve("atualização: " + e.Message); return null; }
    }

    public static async Task Confere(string modo, string canalPedido = "estavel")
    {
        if (modo == "nunca") return;
        canal = canalPedido;
        var g = Gerente();
        if (g == null) return;
        try
        {
            var marca = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "atualizacao-conferida.txt");
            if (File.Exists(marca) && (DateTime.Now - File.GetLastWriteTime(marca)).TotalHours < 20) return;
            var info = await g.CheckForUpdatesAsync();
            Directory.CreateDirectory(Path.GetDirectoryName(marca)!);
            File.WriteAllText(marca, DateTime.Now.ToString("s"));
            if (info == null) return;
            await g.DownloadUpdatesAsync(info);
            pronta = info;
            Registro.Escreve("atualização baixada: " + VersaoPronta);
            Mudou?.Invoke();
            // automático: troca ao fechar a janela (o segundo plano sai antes e a janela o religa na próxima abertura)
            if (modo == "automatico") { AoFechar = true; g.WaitExitThenApplyUpdates(info.TargetFullRelease, silent: true, restart: false); }
        }
        catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
    }

    /// <summary>Reinicia já na versão nova (o botão "Reiniciar agora").</summary>
    public static bool Aplica()
    {
        var g = Gerente();
        if (g == null || pronta == null || Ocupado) return false;
        SegundoPlano.PedeParaSair(reabrir: true);
        g.ApplyUpdatesAndRestart(pronta.TargetFullRelease);
        return true;
    }
}
