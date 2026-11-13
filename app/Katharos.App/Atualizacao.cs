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
    public static int EmUso;
    public static bool Ocupado => Volatile.Read(ref EmUso) > 0;
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
        if (canalPedido != canal) gerente = null;   // trocou de canal: o gerente novo procura no canal certo
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
            // a versão nova abre só para religar o segundo plano (--depois-da-troca), sem janela
            if (modo == "automatico") { AoFechar = true; g.WaitExitThenApplyUpdates(info.TargetFullRelease, silent: true, restart: true, new[] { "--depois-da-troca" }); }
        }
        catch (Exception e) { Registro.Escreve("atualização: " + e.Message); }
    }

    /// <summary>
    /// Na abertura com o Windows: procura versão nova (até 25 s, para não segurar o boot) e, se houver, baixa e troca já, reabrindo a
    /// janela na versão nova. Respeita "atualizações: nunca" (lê a config direto do arquivo: o motor ainda não abriu).
    /// </summary>
    public static void AntesDeAbrir()
    {
        try
        {
            var cfg = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "config.json");
            if (File.Exists(cfg) && System.Text.RegularExpressions.Regex.IsMatch(File.ReadAllText(cfg), "\"atualizacoes\"\\s*:\\s*\"nunca\"")) return;
            var g = Gerente();
            if (g == null) return;
            var t = Task.Run(async () =>
            {
                var info = await g.CheckForUpdatesAsync();
                if (info == null) return null;
                await g.DownloadUpdatesAsync(info);
                return info;
            });
            if (!t.Wait(TimeSpan.FromSeconds(25)) || t.Result == null) return;
            Registro.Escreve("abertura com o Windows: trocando para " + t.Result.TargetFullRelease.Version);
            SegundoPlano.PedeParaSair(reabrir: true);
            g.ApplyUpdatesAndRestart(t.Result.TargetFullRelease, new[] { "--tela", "inicio" });
        }
        catch (Exception e) { Registro.Escreve("abertura com o Windows: " + e.Message); }
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
