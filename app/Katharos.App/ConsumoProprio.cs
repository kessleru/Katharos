using System.Diagnostics;
using System.Runtime.InteropServices;

namespace Katharos.App;

/// <summary>
/// Quanto o próprio Katharos gasta neste PC agora. Entram a janela, o motor (Python), o segundo plano (o ícone perto do relógio)
/// e os PowerShell que o motor deixa abertos para ler o PC, que são reconhecidos pelo processo pai.
/// Só olha processos do próprio usuário. Não abre processo de mais ninguém (anti-cheat).
/// A RAM é a mesma conta da coluna "Memória" do Gerenciador de Tarefas: o conjunto de trabalho privado.
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

    static bool PodeSerFilho(Process p) => p.ProcessName.ToLowerInvariant() is "powershell" or "conhost" or "pwsh";

    [StructLayout(LayoutKind.Sequential)]
    struct InfoBasica { public IntPtr r1, peb, r2a, r2b, id, pai; }

    [DllImport("ntdll.dll")]
    static extern int NtQueryInformationProcess(IntPtr h, int classe, ref InfoBasica info, int tam, out int lido);

    [StructLayout(LayoutKind.Sequential)]
    struct Contadores
    {
        public uint cb, PageFaultCount;
        public UIntPtr PeakWorkingSetSize, WorkingSetSize, QuotaPeakPagedPoolUsage, QuotaPagedPoolUsage,
            QuotaPeakNonPagedPoolUsage, QuotaNonPagedPoolUsage, PagefileUsage, PeakPagefileUsage, PrivateUsage,
            PrivateWorkingSetSize, SharedCommitUsage;
    }

    [DllImport("kernel32.dll", EntryPoint = "K32GetProcessMemoryInfo")]
    static extern bool GetProcessMemoryInfo(IntPtr h, ref Contadores c, uint tam);

    static int Pai(Process p)
    {
        try
        {
            var i = new InfoBasica();
            return NtQueryInformationProcess(p.Handle, 0, ref i, Marshal.SizeOf<InfoBasica>(), out _) == 0 ? (int)i.pai : -1;
        }
        catch { return -1; }
    }

    /// <summary>Memória privada em uso (a do Gerenciador de Tarefas), em MB; sem a API, o conjunto de trabalho.</summary>
    public static double RamMb(Process p)
    {
        try
        {
            var c = new Contadores { cb = (uint)Marshal.SizeOf<Contadores>() };
            if (OperatingSystem.IsWindowsVersionAtLeast(10, 0, 17134) && GetProcessMemoryInfo(p.Handle, ref c, c.cb) && c.PrivateWorkingSetSize != UIntPtr.Zero)
                return (ulong)c.PrivateWorkingSetSize / 1048576.0;
        }
        catch { }
        try { return p.WorkingSet64 / 1048576.0; } catch { return 0; }
    }

    /// <summary>(CPU em % do PC inteiro, RAM em MB, quantos processos). Chamar a cada segundo ou mais.</summary>
    public static (double cpu, double ramMb, int n) Mede()
    {
        var agora = DateTime.UtcNow;
        double seg = quando == DateTime.MinValue ? 0 : (agora - quando).TotalSeconds;
        double cpuMs = 0, ram = 0; int qtd = 0;
        var vistos = new Dictionary<int, TimeSpan>();
        var todos = Process.GetProcesses();
        var nossos = new List<Process>();
        var ids = new HashSet<int>();
        try
        {
            foreach (var p in todos)
                try { if (EhNosso(p)) { nossos.Add(p); ids.Add(p.Id); } } catch { }
            // os PowerShell (e o console deles) cujo pai é um processo do Katharos; duas voltas pegam o conhost do PowerShell
            for (int volta = 0; volta < 2; volta++)
                foreach (var p in todos)
                    try { if (!ids.Contains(p.Id) && PodeSerFilho(p) && ids.Contains(Pai(p))) { nossos.Add(p); ids.Add(p.Id); } } catch { }
            foreach (var p in nossos)
                try
                {
                    var t = p.TotalProcessorTime;
                    vistos[p.Id] = t;
                    if (antes.TryGetValue(p.Id, out var t0)) cpuMs += (t - t0).TotalMilliseconds;
                    ram += RamMb(p); qtd++;
                }
                catch { }
        }
        finally { foreach (var p in todos) p.Dispose(); }
        antes.Clear(); foreach (var kv in vistos) antes[kv.Key] = kv.Value;
        quando = agora;
        double cpu = seg > 0 ? Math.Min(100, cpuMs / (seg * 1000 * Environment.ProcessorCount) * 100) : 0;
        HistCpu.Add(cpu); HistRam.Add(ram);
        if (HistCpu.Count > 300) { HistCpu.RemoveAt(0); HistRam.RemoveAt(0); }
        return (cpu, ram, qtd);
    }
}
