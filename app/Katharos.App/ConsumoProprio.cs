using System.Diagnostics;

namespace Katharos.App;

/// <summary>
/// Quanto o próprio Katharos gasta neste PC agora: a janela, o motor (Python) e o segundo plano (o ícone perto do relógio).
/// Só olha processos do próprio usuário com o nome do Katharos ou um Python que roda de dentro da pasta dele; não abre processo de
/// mais ninguém (anti-cheat). Os PowerShell que o motor abre para ler o PC não entram (o Windows não diz de quem é cada um sem
/// perguntar ao WMI, e isso custaria mais que o que se mede).
/// </summary>
public static class ConsumoProprio
{
    static readonly Dictionary<int, TimeSpan> antes = new();
    static DateTime quando = DateTime.MinValue;
    public static readonly List<double> HistCpu = new(), HistRam = new();

    static bool EhNosso(Process p)
    {
        string n = p.ProcessName.ToLowerInvariant();
        if (n == "katharos" || n == "katharos.app") return true;
        if (n is "python" or "pythonw")
            try { var f = p.MainModule?.FileName ?? ""; return f.Contains("Katharos", StringComparison.OrdinalIgnoreCase) || f.Contains(".katharos", StringComparison.OrdinalIgnoreCase); }
            catch { return false; }
        return false;
    }

    /// <summary>(CPU em % do PC inteiro, RAM em MB, quantos processos). Chamar a cada segundo ou mais.</summary>
    public static (double cpu, double ramMb, int n) Mede()
    {
        var agora = DateTime.UtcNow;
        double seg = quando == DateTime.MinValue ? 0 : (agora - quando).TotalSeconds;
        double cpuMs = 0, ram = 0; int qtd = 0;
        var vistos = new Dictionary<int, TimeSpan>();
        foreach (var p in Process.GetProcesses())
            using (p)
                try
                {
                    if (!EhNosso(p)) continue;
                    var t = p.TotalProcessorTime;
                    vistos[p.Id] = t;
                    if (antes.TryGetValue(p.Id, out var t0)) cpuMs += (t - t0).TotalMilliseconds;
                    ram += p.PrivateMemorySize64 / 1048576.0; qtd++;
                }
                catch { }
        antes.Clear(); foreach (var kv in vistos) antes[kv.Key] = kv.Value;
        quando = agora;
        double cpu = seg > 0 ? Math.Min(100, cpuMs / (seg * 1000 * Environment.ProcessorCount) * 100) : 0;
        HistCpu.Add(cpu); HistRam.Add(ram);
        if (HistCpu.Count > 300) { HistCpu.RemoveAt(0); HistRam.RemoveAt(0); }
        return (cpu, ram, qtd);
    }
}
