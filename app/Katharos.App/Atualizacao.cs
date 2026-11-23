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
    /// <summary>Baixou uma versão com a janela aberta: a janela pergunta "reiniciar agora ou na próxima vez".</summary>
    public static event Action<string>? Pergunta;
    public static int EmUso;
    public static bool Ocupado => Volatile.Read(ref EmUso) > 0;
    /// <summary>A versão nova entra quando a janela fechar: o segundo plano sai junto e volta sozinho depois da troca.</summary>
    public static bool AoFechar;   // true enquanto o motor elevado aplica ou desfaz algo

    static string canal = "estavel";

    /// <summary>
    /// Sem rede agora (abertura com o Windows antes de o Wi-Fi conectar, internet caída, conexão segura que não fechou): não é defeito do
    /// Katharos. Vai para o registro sem as palavras que o relatório conta como erro, e a próxima conferência tenta de novo.
    /// Relatório KTH-67C68B: "The SSL connection could not be established" três vezes, todas na abertura com o Windows.
    /// </summary>
    public static bool SemRede(Exception? e)
    {
        for (var x = e; x != null; x = x.InnerException)
        {
            if (x is System.Net.Http.HttpRequestException || x is System.Security.Authentication.AuthenticationException ||
                x is System.Net.Sockets.SocketException || x is TaskCanceledException || x is TimeoutException || x is System.IO.IOException) return true;
            if (x is AggregateException a)
                foreach (var i in a.InnerExceptions) if (SemRede(i)) return true;
        }
        return false;
    }

    static string Motivo(Exception e) => SemRede(e) ? "sem internet agora; confere de novo mais tarde" : e.Message;

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
            // a cada 3 h no máximo (antes, 20 h: uma versão que saía de manhã só chegava no dia seguinte, e a janela aberta o dia todo nunca
            // mais conferia; relatório ELQUQN)
            if (pronta != null || File.Exists(marca) && (DateTime.Now - File.GetLastWriteTime(marca)).TotalHours < 3) return;
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
            if (modo == "automatico") NaProximaVez();
            else Pergunta?.Invoke(VersaoPronta!);
        }
        catch (Exception e) { Registro.Escreve("atualização: " + Motivo(e)); }
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
        catch (Exception e) { Registro.Escreve("abertura com o Windows: " + Motivo(e)); }
    }

    /// <summary>A versão nova entra quando a janela fechar (sem perguntar de novo); a versão nova abre só para religar o segundo plano.</summary>
    public static void NaProximaVez()
    {
        var g = Gerente();
        if (g == null || pronta == null || AoFechar) return;
        AoFechar = true;
        try { g.WaitExitThenApplyUpdates(pronta.TargetFullRelease, silent: true, restart: true, new[] { "--depois-da-troca" }); }
        catch (Exception e) { AoFechar = false; Registro.Escreve("atualização: na próxima vez: " + Motivo(e)); }
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
