// Katharos.exe: a porta de entrada do Katharos e o acompanhamento em segundo plano.
//
//   Katharos.exe                      abre o Katharos (o mesmo que o KATHAROS.bat: o katharos.ps1 pede administrador quando precisa)
//   Katharos.exe raiox                abre direto num comando
//   Katharos.exe --segundo-plano      acompanhamento contínuo: ícone perto do relógio e métricas em tempo real
//   Katharos.exe --parar-segundo-plano
//
// O que o segundo plano faz, sem parar, no ritmo que você escolher (config tempo-real, padrão 1 s):
//   lê CPU (total, por núcleo e a frequência efetiva), placa de vídeo (uso e memória), RAM, disco, rede, temperatura e bateria,
//   percebe quando há um jogo aberto e grava a sessão (quanto tempo, o que ficou no limite), soma uma linha por minuto,
//   e tira conclusões na hora (o que está segurando o jogo, calor, RAM cheia, CPU freando). Tudo fica em ~/.katharos:
//   agora.json (a leitura de agora), minutos.jsonl (14 dias), sessoes.jsonl (as sessões de jogo). O painel e a central de
//   inteligência do Katharos leem esses arquivos.
//
// Cuidado com jogos (anti-cheat): só usa o que o Gerenciador de Tarefas usa: contadores de desempenho do Windows, a lista de nomes
// de processo e a temperatura que o driver de vídeo informa. Nunca abre o processo de um jogo, nunca lê memória, não injeta nada,
// não instala driver nem sobreposição. O teste tests/test_katharos.py confere que este arquivo não chama nenhuma dessas APIs.
//
// Compilar em qualquer Windows 10 ou 11, sem instalar nada (é o que a publicação faz):
//   C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /optimize+ /out:Katharos.exe
//     /win32icon:katharos.ico /win32manifest:katharos.manifest /resource:katharos.ico,katharos.ico
//     /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Management.dll /r:System.Web.Extensions.dll /r:System.Core.dll Katharos.cs
// O código é C# 5 de propósito: é a versão do compilador que vem dentro do Windows.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Globalization;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Management;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Katharos")]
[assembly: AssemblyProduct("Katharos")]
[assembly: AssemblyDescription("Katharos: abre o otimizador e acompanha o PC em segundo plano")]
[assembly: AssemblyCompany("Katharos, código aberto (github.com/kessleru/Katharos)")]
[assembly: AssemblyCopyright("Licença MIT")]
[assembly: AssemblyVersion("3.1.1.0")]
[assembly: AssemblyFileVersion("3.1.1.0")]

namespace KatharosApp
{
    static class K
    {
        public const string VERSAO = "3.1.1";
        public const string MUTEX = "Local\\KatharosSegundoPlano";
        public const string EV_SAIR = "Local\\KatharosSegundoPlanoSair";
        public const string EV_MOSTRAR = "Local\\KatharosSegundoPlanoMostrar";
        public static readonly string CASA = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
        public static readonly CultureInfo BR = new CultureInfo("pt-BR");
        public static readonly CultureInfo INV = CultureInfo.InvariantCulture;

        public static string Arq(string nome) { return Path.Combine(CASA, nome); }

        public static string Num(double? v, int casas)
        {
            if (!v.HasValue) return "-";
            return v.Value.ToString("F" + casas, BR);
        }

        public static object R(double? v, int casas)
        {
            if (!v.HasValue || double.IsNaN(v.Value) || double.IsInfinity(v.Value)) return null;
            return Math.Round(v.Value, casas);
        }

        public static string Iso(DateTime d) { return d.ToString("yyyy-MM-ddTHH:mm:ss", INV); }

        // aspas no padrão do Windows (CommandLineToArgvW): barras antes de aspas dobram
        public static string Q(string a)
        {
            if (a == null) return "\"\"";
            if (a.Length > 0 && a.IndexOfAny(new[] { ' ', '\t', '"', ';', '&', '|' }) < 0) return a;
            var sb = new StringBuilder("\"");
            int barras = 0;
            foreach (char c in a)
            {
                if (c == '\\') { barras++; continue; }
                if (c == '"') { sb.Append('\\', barras * 2 + 1); sb.Append('"'); barras = 0; continue; }
                sb.Append('\\', barras); barras = 0; sb.Append(c);
            }
            sb.Append('\\', barras * 2);
            sb.Append('"');
            return sb.ToString();
        }

        public static string Junta(IEnumerable<string> args)
        {
            var l = new List<string>();
            foreach (var a in args) l.Add(Q(a));
            return string.Join(" ", l.ToArray());
        }

        public static void GravaAtomico(string arq, string texto)
        {
            arq = Path.GetFullPath(arq);
            Directory.CreateDirectory(Path.GetDirectoryName(arq));
            string tmp = arq + ".tmp";
            File.WriteAllText(tmp, texto, new UTF8Encoding(false));
            if (File.Exists(arq)) File.Replace(tmp, arq, null); else File.Move(tmp, arq);
        }
    }

    static class Log
    {
        static readonly object trava = new object();
        public static void Escreve(string msg)
        {
            try
            {
                lock (trava)
                {
                    string arq = K.Arq("segundo-plano.log");
                    Directory.CreateDirectory(K.CASA);
                    var fi = new FileInfo(arq);
                    if (fi.Exists && fi.Length > 256 * 1024) File.Delete(arq);
                    File.AppendAllText(arq, K.Iso(DateTime.Now) + "  " + msg + Environment.NewLine, new UTF8Encoding(false));
                }
            }
            catch { }
        }
    }

    // ───────── configuração: o Katharos (Python) grava ~/.katharos/segundo-plano.json; relida a cada 30 s ─────────
    class Config
    {
        public string Ps1, Py, Pyw, Kpy;
        public int IntervaloMs = 1000;
        public bool PausarEmJogo = false;
        public double AvisoCpu = 90, AvisoGpu = 85;
        public bool Notificar = true;
        public List<string> NomesJogo = new List<string>();

        public static Config Le()
        {
            var c = new Config();
            try
            {
                string arq = K.Arq("segundo-plano.json");
                if (!File.Exists(arq)) return c;
                var d = new JavaScriptSerializer().DeserializeObject(File.ReadAllText(arq, Encoding.UTF8)) as Dictionary<string, object>;
                if (d == null) return c;
                c.Ps1 = Txt(d, "ps1"); c.Py = Txt(d, "py"); c.Pyw = Txt(d, "pyw"); c.Kpy = Txt(d, "kpy");
                double v;
                if (Dbl(d, "intervalo_s", out v) && v >= 0.5 && v <= 60) c.IntervaloMs = (int)(v * 1000);
                if (Dbl(d, "aviso_cpu", out v) && v > 40 && v < 120) c.AvisoCpu = v;
                if (Dbl(d, "aviso_gpu", out v) && v > 40 && v < 120) c.AvisoGpu = v;
                c.PausarEmJogo = Txt(d, "em_jogo") == "pausar";
                c.Notificar = Txt(d, "notificar") != "nao";
                object n;
                if (d.TryGetValue("nomes_de_jogo", out n) && n is object[])
                    foreach (var x in (object[])n) if (x != null) c.NomesJogo.Add(x.ToString().ToLowerInvariant());
            }
            catch (Exception e) { Log.Escreve("config: " + e.Message); }
            return c;
        }

        static string Txt(Dictionary<string, object> d, string k)
        {
            object v; return d.TryGetValue(k, out v) && v != null ? v.ToString() : null;
        }

        static bool Dbl(Dictionary<string, object> d, string k, out double r)
        {
            r = 0; object v;
            if (!d.TryGetValue(k, out v) || v == null) return false;
            return double.TryParse(Convert.ToString(v, K.INV), NumberStyles.Float, K.INV, out r);
        }
    }

    // ───────── abrir o Katharos (terminal) ─────────
    static class Abridor
    {
        public static int Abre(IList<string> args)
        {
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            string ps1 = Path.Combine(Path.Combine(dir, "programa"), "katharos.ps1");
            Config c = null;
            if (!File.Exists(ps1))
            {
                c = Config.Le();
                ps1 = (c.Ps1 != null && File.Exists(c.Ps1)) ? c.Ps1 : null;
            }
            try
            {
                if (ps1 != null)
                {
                    Inicia("powershell.exe", "-NoProfile -ExecutionPolicy Bypass -File " + K.Q(ps1) + (args.Count > 0 ? " " + K.Junta(args) : ""),
                           Path.GetDirectoryName(Path.GetDirectoryName(ps1)));
                    return 0;
                }
                if (c.Py != null && File.Exists(c.Py) && c.Kpy != null && File.Exists(c.Kpy))
                {
                    Inicia(c.Py, K.Q(c.Kpy) + (args.Count > 0 ? " " + K.Junta(args) : ""), K.CASA);
                    return 0;
                }
            }
            catch (Exception e)
            {
                Log.Escreve("abrir: " + e.Message);
            }
            MessageBox.Show("Não achei o Katharos. Extraia o Katharos.zip inteiro numa pasta e abra o Katharos.exe de dentro dela.",
                            "Katharos", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 1;
        }

        static void Inicia(string exe, string args, string pasta)
        {
            var p = new ProcessStartInfo(exe, args);
            p.UseShellExecute = true;
            if (pasta != null && Directory.Exists(pasta)) p.WorkingDirectory = pasta;
            Process.Start(p);
        }

        // roda o Katharos escondido (pythonw), para tarefas do segundo plano como exportar as propostas
        public static void Escondido(Config c, string args)
        {
            try
            {
                string py = (c.Pyw != null && File.Exists(c.Pyw)) ? c.Pyw : c.Py;
                if (py == null || !File.Exists(py) || c.Kpy == null || !File.Exists(c.Kpy)) return;
                var p = new ProcessStartInfo(py, K.Q(c.Kpy) + " " + args);
                p.UseShellExecute = false; p.CreateNoWindow = true; p.WindowStyle = ProcessWindowStyle.Hidden;
                p.WorkingDirectory = K.CASA;
                using (var x = Process.Start(p)) { try { x.PriorityClass = ProcessPriorityClass.BelowNormal; } catch { } }
            }
            catch (Exception e) { Log.Escreve("escondido: " + e.Message); }
        }
    }

    // ───────── chamadas do Windows ─────────
    static class Nat
    {
        [StructLayout(LayoutKind.Sequential)]
        public class MEMSTAT
        {
            public uint dwLength = (uint)Marshal.SizeOf(typeof(MEMSTAT));
            public uint dwMemoryLoad;
            public ulong ullTotalPhys, ullAvailPhys, ullTotalPageFile, ullAvailPageFile, ullTotalVirtual, ullAvailVirtual, ullAvailExtendedVirtual;
        }
        [DllImport("kernel32.dll", SetLastError = true)] [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GlobalMemoryStatusEx([In, Out] MEMSTAT m);
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
        [DllImport("shell32.dll")] public static extern int SHQueryUserNotificationState(out int estado);
        [DllImport("user32.dll")] [return: MarshalAs(UnmanagedType.Bool)] public static extern bool DestroyIcon(IntPtr h);

        // temperatura da placa de vídeo pelo driver (D3DKMT): o mesmo dado da aba Desempenho do Gerenciador de Tarefas
        [StructLayout(LayoutKind.Sequential)] struct LUID { public uint Low; public int High; }
        [StructLayout(LayoutKind.Sequential)] struct INFO { public uint hAdapter; public LUID Luid; public uint Sources; public int Precise; }
        [StructLayout(LayoutKind.Sequential)] struct ENUM2 { public uint Num; public IntPtr pAdapters; }
        [StructLayout(LayoutKind.Sequential)] struct QUERY { public uint hAdapter; public int Type; public IntPtr pData; public uint Size; }
        [StructLayout(LayoutKind.Sequential)] struct PERF { public uint Index; public ulong MemFreq, MaxMemFreq, MaxMemFreqOC, MemBw, PcieBw; public uint Fan, Power, Temperature; public byte Override; }
        [StructLayout(LayoutKind.Sequential)] struct CLOSE { public uint hAdapter; }
        [DllImport("gdi32.dll")] static extern int D3DKMTEnumAdapters2(ref ENUM2 e);
        [DllImport("gdi32.dll")] static extern int D3DKMTQueryAdapterInfo(ref QUERY q);
        [DllImport("gdi32.dll")] static extern int D3DKMTCloseAdapter(ref CLOSE c);

        public static double? TemperaturaGpu()
        {
            try
            {
                var e = new ENUM2(); D3DKMTEnumAdapters2(ref e);
                if (e.Num == 0 || e.Num > 16) return null;
                int ti = Marshal.SizeOf(typeof(INFO)), tp = Marshal.SizeOf(typeof(PERF));
                IntPtr buf = Marshal.AllocHGlobal(ti * (int)e.Num); double max = -1;
                try
                {
                    e.pAdapters = buf;
                    if (D3DKMTEnumAdapters2(ref e) != 0) return null;
                    for (int i = 0; i < e.Num; i++)
                    {
                        var a = (INFO)Marshal.PtrToStructure(new IntPtr(buf.ToInt64() + (long)i * ti), typeof(INFO));
                        IntPtr pb = Marshal.AllocHGlobal(tp);
                        try
                        {
                            Marshal.StructureToPtr(new PERF(), pb, false);
                            var q = new QUERY { hAdapter = a.hAdapter, Type = 62, pData = pb, Size = (uint)tp };
                            if (D3DKMTQueryAdapterInfo(ref q) == 0)
                            {
                                var p = (PERF)Marshal.PtrToStructure(pb, typeof(PERF));
                                double t = p.Temperature / 10.0;
                                if (t > 5 && t < 125 && t > max) max = t;
                            }
                        }
                        finally { Marshal.FreeHGlobal(pb); var c = new CLOSE { hAdapter = a.hAdapter }; D3DKMTCloseAdapter(ref c); }
                    }
                }
                finally { Marshal.FreeHGlobal(buf); }
                return max > 0 ? (double?)Math.Round(max, 0) : null;
            }
            catch { return null; }
        }
    }

    // ───────── contadores de desempenho ─────────
    class Cont
    {
        PerformanceCounter pc;
        public Cont(string cat, string nome, string inst)
        {
            try { pc = new PerformanceCounter(cat, nome, inst, true); pc.NextValue(); }
            catch { pc = null; }
        }
        public bool Ok { get { return pc != null; } }
        public double? Le()
        {
            if (pc == null) return null;
            try { return pc.NextValue(); } catch { return null; }
        }
    }

    // lê uma categoria inteira de uma vez (todas as instâncias), com a diferença para a leitura anterior
    class Categoria
    {
        readonly string nome;
        PerformanceCounterCategory cat;
        readonly Dictionary<string, Dictionary<string, CounterSample>> ant = new Dictionary<string, Dictionary<string, CounterSample>>();
        public bool Existe;
        public Categoria(string nome)
        {
            this.nome = nome;
            try { Existe = PerformanceCounterCategory.Exists(nome); if (Existe) cat = new PerformanceCounterCategory(nome); }
            catch { Existe = false; }
        }

        // devolve {instância: valor} de cada contador pedido; diferenciais (por segundo, %) só a partir da 2ª leitura
        public Dictionary<string, Dictionary<string, double>> Le(params string[] contadores)
        {
            var res = new Dictionary<string, Dictionary<string, double>>();
            if (!Existe) return res;
            InstanceDataCollectionCollection todos;
            try { todos = cat.ReadCategory(); }
            catch { return res; }
            foreach (var nomeC in contadores)
            {
                var r = new Dictionary<string, double>();
                res[nomeC] = r;
                InstanceDataCollection col;
                try { col = todos[nomeC]; } catch { col = null; }
                if (col == null) continue;
                Dictionary<string, CounterSample> velho;
                ant.TryGetValue(nomeC, out velho);
                var novo = new Dictionary<string, CounterSample>();
                foreach (InstanceData d in col.Values)
                {
                    var s = d.Sample;
                    novo[d.InstanceName] = s;
                    try
                    {
                        if (s.CounterType == PerformanceCounterType.NumberOfItems32 || s.CounterType == PerformanceCounterType.NumberOfItems64 ||
                            s.CounterType == PerformanceCounterType.RawFraction)
                            r[d.InstanceName] = CounterSample.Calculate(s);
                        else
                        {
                            CounterSample a;
                            if (velho != null && velho.TryGetValue(d.InstanceName, out a)) r[d.InstanceName] = CounterSample.Calculate(a, s);
                        }
                    }
                    catch { }
                }
                ant[nomeC] = novo;
            }
            return res;
        }
    }

    // ───────── temperatura dos programas de monitoramento que já estão abertos ─────────
    // A CPU só mostra a temperatura para quem tem driver no kernel. MSI Afterburner, HWiNFO, Core Temp e AIDA64 têm esse driver e publicam
    // as leituras numa memória compartilhada, só de leitura, para outros programas (o overlay do RivaTuner usa a mesma durante os jogos).
    // O Katharos lê dali: não instala driver nenhum (driver de sensor é o que anti-cheat bloqueia e o Defender marca).
    static class Externos
    {
        public class Leitura { public double? Cpu, Gpu; public string CpuFonte, GpuFonte; }

        static byte[] Abre(string nome, int maximo)
        {
            foreach (var n in new[] { nome, "Global\\" + nome })
            {
                try
                {
                    using (var m = MemoryMappedFile.OpenExisting(n, MemoryMappedFileRights.Read))
                    using (var v = m.CreateViewStream(0, 0, MemoryMappedFileAccess.Read))
                    {
                        int tam = (int)Math.Min(maximo, v.Length);
                        var b = new byte[tam]; int lido = 0;
                        while (lido < tam) { int r = v.Read(b, lido, tam - lido); if (r <= 0) break; lido += r; }
                        if (lido >= 64) { if (lido < tam) Array.Resize(ref b, lido); return b; }
                    }
                }
                catch { }
            }
            return null;
        }

        static string Txt(byte[] b, int ini, int max)
        {
            int fim = ini; while (fim < ini + max && fim < b.Length && b[fim] != 0) fim++;
            return Encoding.Default.GetString(b, ini, fim - ini);
        }

        static bool Valida(double t) { return t > 5 && t < 125; }

        public static Leitura Le()
        {
            var r = new Leitura();
            try { HwInfo(r); } catch { }
            try { if (!r.Cpu.HasValue || !r.Gpu.HasValue) Afterburner(r); } catch { }
            try { if (!r.Cpu.HasValue) CoreTemp(r); } catch { }
            try { if (!r.Cpu.HasValue || !r.Gpu.HasValue) Aida(r); } catch { }
            return r;
        }

        // HWiNFO (com "Shared Memory Support" ligado nas configurações)
        static void HwInfo(Leitura r)
        {
            var b = Abre("HWiNFO_SENS_SM2", 4 * 1024 * 1024);
            if (b == null || BitConverter.ToUInt32(b, 0) != 0x53695748) return;   // "HWiS"; "DEAD" = HWiNFO fechou
            uint offR = BitConverter.ToUInt32(b, 32), tamR = BitConverter.ToUInt32(b, 36), nR = BitConverter.ToUInt32(b, 40);
            uint offS = BitConverter.ToUInt32(b, 20), tamS = BitConverter.ToUInt32(b, 24), nS = BitConverter.ToUInt32(b, 28);
            double cpuPac = -1, cpuMax = -1, gpu = -1;
            for (uint i = 0; i < nR && i < 4096; i++)
            {
                long o = offR + i * tamR;
                if (o + 316 > b.Length) break;
                if (BitConverter.ToUInt32(b, (int)o) != 1) continue;   // 1 = temperatura
                uint si = BitConverter.ToUInt32(b, (int)o + 4);
                string rot = Txt(b, (int)o + 12, 128);
                string un = Txt(b, (int)o + 268, 16);
                double v = BitConverter.ToDouble(b, (int)o + 284);
                if (un.Contains("F")) v = (v - 32) * 5 / 9;
                if (!Valida(v)) continue;
                string sensor = (si < nS && offS + si * tamS + 136 <= b.Length) ? Txt(b, (int)(offS + si * tamS + 8), 128) : "";
                bool ehCpu = sensor.StartsWith("CPU") || rot.StartsWith("CPU") || rot.StartsWith("Core");
                if (ehCpu && (rot == "CPU Package" || rot.StartsWith("CPU (Tctl") || rot == "CPU (Tdie)" || rot == "Core Max")) cpuPac = Math.Max(cpuPac, v);
                else if (ehCpu && rot.StartsWith("Core")) cpuMax = Math.Max(cpuMax, v);
                if (sensor.StartsWith("GPU") && rot == "GPU Temperature") gpu = Math.Max(gpu, v);
            }
            double c = cpuPac > 0 ? cpuPac : cpuMax;
            if (c > 0 && !r.Cpu.HasValue) { r.Cpu = Math.Round(c, 0); r.CpuFonte = "HWiNFO"; }
            if (gpu > 0 && !r.Gpu.HasValue) { r.Gpu = Math.Round(gpu, 0); r.GpuFonte = "HWiNFO"; }
        }

        // MSI Afterburner (a temperatura da CPU aparece se estiver marcada no monitoramento dele)
        static void Afterburner(Leitura r)
        {
            var b = Abre("MAHMSharedMemory", 2 * 1024 * 1024);
            if (b == null || BitConverter.ToUInt32(b, 0) != 0x4D41484D) return;   // 'MAHM'; 0xDEAD = fechou
            uint tamH = BitConverter.ToUInt32(b, 8), n = BitConverter.ToUInt32(b, 12), tamE = BitConverter.ToUInt32(b, 16);
            double cpu = -1, gpu = -1;
            for (uint i = 0; i < n && i < 1024; i++)
            {
                long o = tamH + i * tamE;
                if (o + 1304 > b.Length) break;
                string nome = Txt(b, (int)o, 260);
                double v = BitConverter.ToSingle(b, (int)o + 1300);
                if (!Valida(v) || nome.IndexOf("temperature", StringComparison.OrdinalIgnoreCase) < 0) continue;
                if (nome.StartsWith("CPU")) cpu = Math.Max(cpu, v);
                else if (nome.StartsWith("GPU")) gpu = Math.Max(gpu, v);
            }
            if (cpu > 0 && !r.Cpu.HasValue) { r.Cpu = Math.Round(cpu, 0); r.CpuFonte = "MSI Afterburner"; }
            if (gpu > 0 && !r.Gpu.HasValue) { r.Gpu = Math.Round(gpu, 0); r.GpuFonte = "MSI Afterburner"; }
        }

        // Core Temp
        static void CoreTemp(Leitura r)
        {
            var b = Abre("CoreTempMappingObjectEx", 8192) ?? Abre("CoreTempMappingObject", 8192);
            if (b == null || b.Length < 2686) return;
            uint nucleos = BitConverter.ToUInt32(b, 1536), cpus = BitConverter.ToUInt32(b, 1540);
            bool fahr = b[2684] != 0, delta = b[2685] != 0;
            double max = -1;
            for (uint c = 0; c < Math.Max(1, cpus) && c < 128; c++)
                for (uint i = 0; i < nucleos && c * nucleos + i < 256; i++)
                {
                    double v = BitConverter.ToSingle(b, (int)(1544 + (c * nucleos + i) * 4));
                    if (delta) v = BitConverter.ToUInt32(b, (int)(1024 + c * 4)) - v;
                    if (fahr) v = (v - 32) * 5 / 9;
                    if (Valida(v)) max = Math.Max(max, v);
                }
            if (max > 0) { r.Cpu = Math.Round(max, 0); r.CpuFonte = "Core Temp"; }
        }

        // AIDA64 (com "Shared Memory" ligado nas preferências de comunicação externa)
        static void Aida(Leitura r)
        {
            var b = Abre("AIDA64_SensorValues", 256 * 1024);
            if (b == null) return;
            string x = Txt(b, 0, b.Length);
            double cpu = -1, gpu = -1;
            int i = 0;
            while ((i = x.IndexOf("<temp>", i, StringComparison.Ordinal)) >= 0)
            {
                int f = x.IndexOf("</temp>", i, StringComparison.Ordinal); if (f < 0) break;
                string bloco = x.Substring(i, f - i); i = f;
                string id = Tag(bloco, "id"); double v;
                if (!double.TryParse(Tag(bloco, "value"), NumberStyles.Float, K.INV, out v) || !Valida(v)) continue;
                if (id == "TCPUPKG" || id == "TCPU" || id == "TCPUDIO") cpu = Math.Max(cpu, v);
                if (id == "TGPU1DIO" || id == "TGPU1") gpu = Math.Max(gpu, v);
            }
            if (cpu > 0 && !r.Cpu.HasValue) { r.Cpu = Math.Round(cpu, 0); r.CpuFonte = "AIDA64"; }
            if (gpu > 0 && !r.Gpu.HasValue) { r.Gpu = Math.Round(gpu, 0); r.GpuFonte = "AIDA64"; }
        }

        static string Tag(string x, string t)
        {
            int a = x.IndexOf("<" + t + ">", StringComparison.Ordinal); if (a < 0) return "";
            a += t.Length + 2; int f = x.IndexOf("</" + t + ">", a, StringComparison.Ordinal);
            return f < 0 ? "" : x.Substring(a, f - a);
        }
    }

    class Amostra
    {
        public DateTime Quando;
        public double? Cpu, NucleoMax, CpuDesempenho, CpuGhz, Gpu, VramGb, VramTotalGb, RamPct, RamGb, RamTotalGb;
        public double? Disco, DiscoLe, DiscoGrava, RedeBaixa, RedeSobe, TempCpu, TempGpu;
        public string TempCpuFonte, TempGpuFonte;
        public int? Bateria; public bool NaBateria;
        public int TopGpuPid; public double TopGpu;
        public int PrimeiroPlanoPid; public bool TelaCheia; public bool AntiCheat;
        public string Jogo; public int JogoPid;
        public double? VramPct { get { return (VramGb.HasValue && VramTotalGb.HasValue && VramTotalGb.Value > 0) ? (double?)(VramGb.Value / VramTotalGb.Value * 100) : null; } }
    }

    class Leitor
    {
        Cont cpuTotal, cpuDesemp, discoOcioso, discoLe, discoGrava;
        readonly List<Cont> nucleos = new List<Cont>();
        readonly Categoria gpuMotor = new Categoria("GPU Engine");
        readonly Categoria gpuMem = new Categoria("GPU Adapter Memory");
        readonly Categoria rede = new Categoria("Network Interface");
        readonly Categoria zona = new Categoria("Thermal Zone Information");
        double baseMhz;
        double? vramTotal;
        DateTime proxLhm = DateTime.MinValue, proxD3d = DateTime.MinValue, proxSmi = DateTime.MinValue, proxProc = DateTime.MinValue, proxUltima = DateTime.MinValue;
        double? lhmCpu, lhmGpu, d3dGpu, smiGpu, ultCpu, ultGpu; string lhmFonte, ultQuando;
        bool lhmExiste = true, d3dExiste = true, smiExiste = true;
        DateTime proxExt = DateTime.MinValue; Externos.Leitura ext;
        public Dictionary<int, string> Nomes = new Dictionary<int, string>();
        public HashSet<string> NomesVistos = new HashSet<string>();

        public Leitor()
        {
            cpuTotal = new Cont("Processor Information", "% Processor Utility", "_Total");
            if (!cpuTotal.Ok) cpuTotal = new Cont("Processor", "% Processor Time", "_Total");
            cpuDesemp = new Cont("Processor Information", "% Processor Performance", "_Total");
            try
            {
                var inst = new PerformanceCounterCategory("Processor Information").GetInstanceNames();
                Array.Sort(inst, StringComparer.Ordinal);
                foreach (var i in inst)
                    if (i.IndexOf("_Total", StringComparison.OrdinalIgnoreCase) < 0) { var c = new Cont("Processor Information", "% Processor Utility", i); if (c.Ok) nucleos.Add(c); }
            }
            catch { }
            if (nucleos.Count == 0)
                for (int i = 0; i < Environment.ProcessorCount; i++) { var c = new Cont("Processor", "% Processor Time", i.ToString(K.INV)); if (c.Ok) nucleos.Add(c); }
            discoOcioso = new Cont("PhysicalDisk", "% Idle Time", "_Total");
            discoLe = new Cont("PhysicalDisk", "Disk Read Bytes/sec", "_Total");
            discoGrava = new Cont("PhysicalDisk", "Disk Write Bytes/sec", "_Total");
            try
            {
                using (var k = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\CentralProcessor\0"))
                    if (k != null) baseMhz = Convert.ToDouble(k.GetValue("~MHz", 0), K.INV);
            }
            catch { }
            vramTotal = VramTotal();
        }

        static double? VramTotal()
        {
            double max = 0;
            try
            {
                using (var cls = Registry.LocalMachine.OpenSubKey(@"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"))
                {
                    if (cls == null) return null;
                    foreach (var n in cls.GetSubKeyNames())
                    {
                        if (n.Length != 4) continue;
                        try
                        {
                            using (var k = cls.OpenSubKey(n))
                            {
                                if (k == null) continue;
                                object v = k.GetValue("HardwareInformation.qwMemorySize") ?? k.GetValue("HardwareInformation.MemorySize");
                                double b = 0;
                                if (v is long) b = (long)v;
                                else if (v is int) b = (uint)(int)v;
                                else if (v is byte[] && ((byte[])v).Length >= 4) b = ((byte[])v).Length >= 8 ? BitConverter.ToInt64((byte[])v, 0) : BitConverter.ToUInt32((byte[])v, 0);
                                if (b > max) max = b;
                            }
                        }
                        catch { }
                    }
                }
            }
            catch { }
            return max > 256 * 1024.0 * 1024 ? (double?)(max / 1073741824.0) : null;
        }

        public Amostra Le(Config cfg, bool emJogo)
        {
            var a = new Amostra { Quando = DateTime.Now };
            DateTime agora = a.Quando;
            var c = cpuTotal.Le(); if (c.HasValue) a.Cpu = Math.Min(100, c.Value);
            double nm = -1;
            foreach (var n in nucleos) { var v = n.Le(); if (v.HasValue && v.Value > nm) nm = v.Value; }
            if (nm >= 0) a.NucleoMax = Math.Min(100, nm);
            var d = cpuDesemp.Le();
            if (d.HasValue && d.Value > 0) { a.CpuDesempenho = d.Value; if (baseMhz > 0) a.CpuGhz = baseMhz * d.Value / 100.0 / 1000.0; }

            try
            {
                var m = new Nat.MEMSTAT();
                if (Nat.GlobalMemoryStatusEx(m) && m.ullTotalPhys > 0)
                {
                    a.RamTotalGb = m.ullTotalPhys / 1073741824.0;
                    a.RamGb = (m.ullTotalPhys - m.ullAvailPhys) / 1073741824.0;
                    a.RamPct = a.RamGb / a.RamTotalGb * 100;
                }
            }
            catch (Exception e) { Falha("ram", e); }

            var oc = discoOcioso.Le(); if (oc.HasValue) a.Disco = Math.Max(0, Math.Min(100, 100 - oc.Value));
            var dl = discoLe.Le(); if (dl.HasValue) a.DiscoLe = dl.Value / 1048576.0;
            var dg = discoGrava.Le(); if (dg.HasValue) a.DiscoGrava = dg.Value / 1048576.0;

            var rr = rede.Le("Bytes Received/sec", "Bytes Sent/sec");
            if (rr.ContainsKey("Bytes Received/sec") && rr["Bytes Received/sec"].Count > 0)
            {
                double baixa = 0, sobe = 0;
                foreach (var v in rr["Bytes Received/sec"].Values) baixa += v;
                foreach (var v in rr["Bytes Sent/sec"].Values) sobe += v;
                a.RedeBaixa = baixa / 1048576.0; a.RedeSobe = sobe / 1048576.0;
            }

            // placa de vídeo: uso = o motor mais ocupado (soma dos processos em cada motor), como o Gerenciador de Tarefas
            var g = gpuMotor.Le("Utilization Percentage");
            if (g.ContainsKey("Utilization Percentage") && g["Utilization Percentage"].Count > 0)
            {
                var porMotor = new Dictionary<string, double>();
                var por3d = new Dictionary<int, double>();
                foreach (var kv in g["Utilization Percentage"])
                {
                    string inst = kv.Key; double v = kv.Value;
                    int ip = inst.IndexOf("_luid_", StringComparison.Ordinal);
                    string motor = ip >= 0 ? inst.Substring(ip) : inst;
                    double soma; porMotor.TryGetValue(motor, out soma); porMotor[motor] = soma + v;
                    if (inst.EndsWith("engtype_3D", StringComparison.OrdinalIgnoreCase) && inst.StartsWith("pid_", StringComparison.Ordinal))
                    {
                        int fim = inst.IndexOf('_', 4); int pid;
                        if (fim > 4 && int.TryParse(inst.Substring(4, fim - 4), NumberStyles.Integer, K.INV, out pid))
                        { double s; por3d.TryGetValue(pid, out s); por3d[pid] = s + v; }
                    }
                }
                double max = 0; foreach (var v in porMotor.Values) if (v > max) max = v;
                a.Gpu = Math.Min(100, max);
                foreach (var kv in por3d) if (kv.Value > a.TopGpu) { a.TopGpu = Math.Min(100, kv.Value); a.TopGpuPid = kv.Key; }
            }
            var gm = gpuMem.Le("Dedicated Usage");
            if (gm.ContainsKey("Dedicated Usage") && gm["Dedicated Usage"].Count > 0)
            {
                double max = 0; foreach (var v in gm["Dedicated Usage"].Values) if (v > max) max = v;
                a.VramGb = max / 1073741824.0;
                a.VramTotalGb = vramTotal;
            }

            // temperatura: do mais certo para o mais pobre, e diz de onde veio
            if (lhmExiste && agora >= proxLhm) { proxLhm = agora.AddSeconds(3); LeLhm(); }
            if (d3dExiste && agora >= proxD3d) { proxD3d = agora.AddSeconds(2); d3dGpu = Nat.TemperaturaGpu(); if (!d3dGpu.HasValue) { d3dExiste = false; } }
            if (agora >= proxExt) { proxExt = agora.AddSeconds(2); ext = Externos.Le(); }
            if (lhmCpu.HasValue) { a.TempCpu = lhmCpu; a.TempCpuFonte = lhmFonte; }
            else if (ext != null && ext.Cpu.HasValue) { a.TempCpu = ext.Cpu; a.TempCpuFonte = ext.CpuFonte; }
            if (lhmGpu.HasValue) { a.TempGpu = lhmGpu; a.TempGpuFonte = lhmFonte; }
            else if (ext != null && ext.Gpu.HasValue) { a.TempGpu = ext.Gpu; a.TempGpuFonte = ext.GpuFonte; }
            else if (d3dGpu.HasValue) { a.TempGpu = d3dGpu; a.TempGpuFonte = "driver de vídeo"; }
            else if (smiExiste && !emJogo && agora >= proxSmi) { proxSmi = agora.AddSeconds(15); LeSmi(); }
            if (!a.TempGpu.HasValue && smiGpu.HasValue) { a.TempGpu = smiGpu; a.TempGpuFonte = "nvidia-smi"; }
            if (!a.TempCpu.HasValue)
            {
                var z = zona.Le("High Precision Temperature", "Temperature");
                double best = -1;
                foreach (var nomeC in new[] { "High Precision Temperature", "Temperature" })
                {
                    if (!z.ContainsKey(nomeC)) continue;
                    foreach (var v in z[nomeC].Values)
                    {
                        double kel = nomeC.StartsWith("High") ? v / 10.0 : v;
                        if (kel <= 0 || Math.Abs(kel - 298.15) < .25 || Math.Abs(kel - 300) < .25 || Math.Abs(kel - 301) < .25) continue;
                        double cel = kel - 273.15;
                        if (cel > 15 && cel < 120 && cel > best) best = cel;
                    }
                    if (best > 0) break;
                }
                if (best > 0) { a.TempCpu = Math.Round(best, 0); a.TempCpuFonte = "zona térmica"; }
            }
            if (agora >= proxUltima) { proxUltima = agora.AddSeconds(60); LeUltima(); }
            if (!a.TempCpu.HasValue && ultCpu.HasValue) { a.TempCpu = ultCpu; a.TempCpuFonte = "leitura das " + ultQuando; }
            if (!a.TempGpu.HasValue && ultGpu.HasValue) { a.TempGpu = ultGpu; a.TempGpuFonte = "leitura das " + ultQuando; }

            try
            {
                var ps = SystemInformation.PowerStatus;
                if (ps.BatteryChargeStatus != BatteryChargeStatus.NoSystemBattery && ps.BatteryChargeStatus != BatteryChargeStatus.Unknown)
                {
                    a.Bateria = (int)Math.Round(ps.BatteryLifePercent * 100);
                    a.NaBateria = ps.PowerLineStatus == PowerLineStatus.Offline;
                }
            }
            catch (Exception e) { Falha("bateria", e); }

            // quem está na frente e se é tela cheia (para saber se há jogo)
            try { uint pid; Nat.GetWindowThreadProcessId(Nat.GetForegroundWindow(), out pid); a.PrimeiroPlanoPid = (int)pid; } catch { }
            try { int st; if (Nat.SHQueryUserNotificationState(out st) == 0) a.TelaCheia = st == 2 || st == 3 || st == 4; } catch { }
            if (agora >= proxProc) { proxProc = agora.AddSeconds(5); LeNomes(); }
            foreach (var n in cfg.NomesJogo) if (NomesVistos.Contains(n)) { a.AntiCheat = true; break; }
            return a;
        }

        // cada fonte que falha é anotada uma vez no log; as outras continuam
        readonly HashSet<string> falhas = new HashSet<string>();
        void Falha(string fonte, Exception e)
        {
            if (falhas.Add(fonte)) Log.Escreve("leitura de " + fonte + " falhou: " + e.GetType().Name + ": " + e.Message);
        }

        // só os nomes: GetProcesses lê a lista do sistema, não abre processo nenhum
        void LeNomes()
        {
            var nomes = new Dictionary<int, string>(); var vistos = new HashSet<string>();
            try
            {
                foreach (var p in Process.GetProcesses())
                {
                    try { string n = p.ProcessName; nomes[p.Id] = n; vistos.Add(n.ToLowerInvariant()); } catch { }
                    p.Dispose();
                }
            }
            catch { }
            Nomes = nomes; NomesVistos = vistos;
        }

        void LeLhm()
        {
            lhmCpu = null; lhmGpu = null;
            bool algum = false;
            foreach (var ns in new[] { "LibreHardwareMonitor", "OpenHardwareMonitor" })
            {
                try
                {
                    var busca = new ManagementObjectSearcher(new ManagementScope(@"root\" + ns), new ObjectQuery("SELECT Identifier, Name, Value FROM Sensor WHERE SensorType='Temperature'"));
                    busca.Options.Timeout = TimeSpan.FromSeconds(2);
                    double cpu = -1, cpuPac = -1, gpu = -1, gpuCore = -1;
                    foreach (ManagementObject o in busca.Get())
                    {
                        algum = true;
                        string id = Convert.ToString(o["Identifier"]).ToLowerInvariant(), nome = Convert.ToString(o["Name"]);
                        double v = Convert.ToDouble(o["Value"], K.INV);
                        if (v <= 5 || v >= 125) continue;
                        bool pac = nome.Contains("Package") || nome.Contains("Tctl") || nome.Contains("Tdie") || nome.Contains("Core Average");
                        if (id.Contains("cpu")) { if (pac) cpuPac = Math.Max(cpuPac, v); else cpu = Math.Max(cpu, v); }
                        if (id.Contains("gpu")) { if (nome.Contains("GPU Core") || nome.StartsWith("Core")) gpuCore = Math.Max(gpuCore, v); else gpu = Math.Max(gpu, v); }
                    }
                    double c = cpuPac > 0 ? cpuPac : cpu, g = gpuCore > 0 ? gpuCore : gpu;
                    if (!lhmCpu.HasValue && c > 0) { lhmCpu = Math.Round(c, 0); lhmFonte = ns; }
                    if (!lhmGpu.HasValue && g > 0) { lhmGpu = Math.Round(g, 0); lhmFonte = ns; }
                }
                catch { }
            }
            if (!algum) { proxLhm = DateTime.Now.AddSeconds(60); }   // não está aberto: tenta de novo em 1 min
        }

        void LeSmi()
        {
            try
            {
                string exe = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "nvidia-smi.exe");
                if (!File.Exists(exe)) { smiExiste = false; return; }
                var p = new ProcessStartInfo(exe, "--query-gpu=temperature.gpu --format=csv,noheader,nounits");
                p.UseShellExecute = false; p.CreateNoWindow = true; p.RedirectStandardOutput = true;
                using (var x = Process.Start(p))
                {
                    string l = x.StandardOutput.ReadLine();
                    x.WaitForExit(3000);
                    double t;
                    if (l != null && double.TryParse(l.Trim(), NumberStyles.Float, K.INV, out t) && t > 5) smiGpu = t; else smiGpu = null;
                }
            }
            catch { smiExiste = false; }
        }

        // a leitura de 15 min do Katharos (Python) tem mais fontes de temperatura; serve de reserva se for recente
        void LeUltima()
        {
            ultCpu = null; ultGpu = null;
            try
            {
                string arq = K.Arq("ultima-amostra.json");
                if (!File.Exists(arq)) return;
                var d = new JavaScriptSerializer().DeserializeObject(File.ReadAllText(arq, Encoding.UTF8)) as Dictionary<string, object>;
                if (d == null) return;
                DateTime q;
                if (!d.ContainsKey("quando") || !DateTime.TryParse(Convert.ToString(d["quando"]), K.INV, DateTimeStyles.AssumeLocal, out q)) return;
                if ((DateTime.Now - q).TotalMinutes > 30) return;
                ultQuando = q.ToString("HH:mm", K.INV);
                if (d.ContainsKey("temp") && d["temp"] != null) ultCpu = Convert.ToDouble(d["temp"], K.INV);
                if (d.ContainsKey("gpu_temp") && d["gpu_temp"] != null) ultGpu = Convert.ToDouble(d["gpu_temp"], K.INV);
            }
            catch { }
        }
    }

    // ───────── o que está acontecendo agora: jogo aberto e conclusões ─────────
    class Conclusao
    {
        public string Id, Titulo, Texto, Comando; public int Nivel;   // 0 informação, 1 atenção, 2 grave
        public Conclusao(string id, int nivel, string titulo, string texto, string comando) { Id = id; Nivel = nivel; Titulo = titulo; Texto = texto; Comando = comando; }
    }

    static class Regras
    {
        // os mesmos critérios contam o tempo de cada limite na sessão de jogo e geram as conclusões de agora
        public static readonly string[] MARCAS = { "gpu", "cpu", "freio", "ram", "vram", "disco", "calor" };

        public static bool Marca(string m, Amostra a, Config c)
        {
            switch (m)
            {
                case "gpu": return a.Gpu >= 95 && a.NucleoMax < 90;
                case "cpu": return a.NucleoMax >= 95 && a.Gpu.HasValue && a.Gpu < 85;
                case "freio": return a.CpuDesempenho.HasValue && a.CpuDesempenho < 75 && a.Cpu >= 40;
                case "ram": return a.RamPct >= 90;
                case "vram": return a.VramPct >= 95;
                case "disco": return a.Disco >= 95;
                case "calor": return a.TempCpu >= c.AvisoCpu || a.TempGpu >= c.AvisoGpu;
            }
            return false;
        }

        public static List<Conclusao> Agora(List<Amostra> janela, Config c, bool emJogo)
        {
            var r = new List<Conclusao>();
            if (janela.Count < 3) return r;
            var ult = janela[janela.Count - 1];
            Func<string, double> frac = delegate (string m) { int n = 0; foreach (var a in janela) if (Marca(m, a, c)) n++; return (double)n / janela.Count; };
            if (frac("calor") >= .5)
            {
                bool cpu = ult.TempCpu >= c.AvisoCpu;
                r.Add(new Conclusao("calor", 2, "PC quente",
                    (cpu ? "CPU em " + K.Num(ult.TempCpu, 0) + " °C" : "Placa de vídeo em " + K.Num(ult.TempGpu, 0) + " °C") +
                    ". Acima disso o chip reduz a velocidade para se proteger. Confira ventoinha e poeira.", "painel"));
            }
            if (frac("freio") >= .6)
                r.Add(new Conclusao("freio", 1, "CPU abaixo da velocidade normal",
                    "Com carga, ela está rodando a " + K.Num(ult.CpuDesempenho, 0) + " % da frequência normal" +
                    (ult.NaBateria ? ": é a economia da bateria. Na tomada ela volta." : ": calor ou plano de energia economizando."), ult.NaBateria ? "" : "energia"));
            if (emJogo)
            {
                if (frac("gpu") >= .6)
                    r.Add(new Conclusao("gpu", 0, "A placa de vídeo é o limite agora",
                        "Ela está em " + K.Num(ult.Gpu, 0) + " % e a CPU sobra. O jogo roda o máximo que ela entrega; mais FPS vem de baixar resolução ou qualidade.", ""));
                else if (frac("cpu") >= .6)
                    r.Add(new Conclusao("cpu", 1, "A CPU segura o jogo",
                        "Um núcleo está em " + K.Num(ult.NucleoMax, 0) + " % e a placa de vídeo sobra (" + K.Num(ult.Gpu, 0) + " %). Feche o que roda em segundo plano; o modo extremo do turbo ajuda.", "turbo"));
                if (frac("vram") >= .6)
                    r.Add(new Conclusao("vram", 1, "Memória da placa de vídeo cheia",
                        K.Num(ult.VramGb, 1) + " de " + K.Num(ult.VramTotalGb, 1) + " GB. Baixe a qualidade das texturas: acima disso o jogo engasga.", ""));
            }
            else if (ult.Cpu >= 85 && frac("cpu") < .5)
            {
                int n = 0; foreach (var a in janela) if (a.Cpu >= 85) n++;
                if (n >= janela.Count * .8)
                    r.Add(new Conclusao("cpu-ocupada", 1, "Algo mantém a CPU ocupada", "CPU em " + K.Num(ult.Cpu, 0) + " % sem jogo aberto. O raio-x mostra quem é.", "raiox"));
            }
            if (frac("ram") >= .8)
                r.Add(new Conclusao("ram", 1, "RAM quase cheia",
                    K.Num(ult.RamGb, 1) + " de " + K.Num(ult.RamTotalGb, 1) + " GB em uso. O Windows passa a usar o disco no lugar e tudo fica mais lento.", "memoria"));
            if (frac("disco") >= .8)
                r.Add(new Conclusao("disco", 1, "Disco ocupado o tempo todo",
                    "Em " + K.Num(ult.Disco, 0) + " %. Jogos e programas esperam por ele: travadas curtas vêm daqui.", "raiox"));
            r.Sort(delegate (Conclusao x, Conclusao y) { return y.Nivel.CompareTo(x.Nivel); });
            return r;
        }
    }

    class Sessao
    {
        public string Jogo; public int Pid; public DateTime Inicio, Ultimo;
        public int N; double sCpu, sGpu, sNuc, sRam; double mCpu, mGpu, mNuc, mRam, mVram, mTc = -1, mTg = -1; double mDesemp = 1000;
        public readonly Dictionary<string, int> Marcas = new Dictionary<string, int>();

        public void Soma(Amostra a, Config c)
        {
            N++; Ultimo = a.Quando;
            if (a.Cpu.HasValue) { sCpu += a.Cpu.Value; mCpu = Math.Max(mCpu, a.Cpu.Value); }
            if (a.Gpu.HasValue) { sGpu += a.Gpu.Value; mGpu = Math.Max(mGpu, a.Gpu.Value); }
            if (a.NucleoMax.HasValue) { sNuc += a.NucleoMax.Value; mNuc = Math.Max(mNuc, a.NucleoMax.Value); }
            if (a.RamPct.HasValue) { sRam += a.RamPct.Value; mRam = Math.Max(mRam, a.RamPct.Value); }
            if (a.VramPct.HasValue) mVram = Math.Max(mVram, a.VramPct.Value);
            if (a.TempCpu.HasValue) mTc = Math.Max(mTc, a.TempCpu.Value);
            if (a.TempGpu.HasValue) mTg = Math.Max(mTg, a.TempGpu.Value);
            if (a.CpuDesempenho.HasValue && a.Cpu >= 40) mDesemp = Math.Min(mDesemp, a.CpuDesempenho.Value);
            foreach (var m in Regras.MARCAS) if (Regras.Marca(m, a, c)) { int n; Marcas.TryGetValue(m, out n); Marcas[m] = n + 1; }
        }

        public string Principal()
        {
            string melhor = "equilibrado"; double fm = .2;
            foreach (var kv in Marcas) { double f = (double)kv.Value / Math.Max(1, N); if (f > fm) { fm = f; melhor = kv.Key; } }
            return melhor;
        }

        public Dictionary<string, object> Json()
        {
            var d = new Dictionary<string, object>();
            d["jogo"] = Jogo; d["inicio"] = K.Iso(Inicio); d["fim"] = K.Iso(Ultimo);
            d["min"] = Math.Round((Ultimo - Inicio).TotalMinutes, 1); d["leituras"] = N;
            double n = Math.Max(1, N);
            d["cpu"] = Math.Round(sCpu / n, 1); d["cpu_max"] = Math.Round(mCpu, 0);
            d["nucleo"] = Math.Round(sNuc / n, 1); d["gpu"] = Math.Round(sGpu / n, 1); d["gpu_max"] = Math.Round(mGpu, 0);
            d["ram"] = Math.Round(sRam / n, 1); d["ram_max"] = Math.Round(mRam, 0);
            if (mVram > 0) d["vram_max"] = Math.Round(mVram, 0);
            if (mTc > 0) d["temp_cpu_max"] = mTc;
            if (mTg > 0) d["temp_gpu_max"] = mTg;
            if (mDesemp < 1000) d["desempenho_min"] = Math.Round(mDesemp, 0);
            var t = new Dictionary<string, object>();
            foreach (var kv in Marcas) t[kv.Key] = Math.Round(100.0 * kv.Value / n, 0);
            d["tempo_no_limite"] = t;
            d["principal"] = Principal();
            return d;
        }
    }

    class Minuto
    {
        public DateTime Inicio; int n; double sCpu, sGpu, sRam, sDisco, sRede; double mCpu, mGpu, mNuc, mTc = -1, mTg = -1, mVram; double mDesemp = 1000; public string Jogo;
        public Minuto(DateTime t) { Inicio = new DateTime(t.Year, t.Month, t.Day, t.Hour, t.Minute, 0); }
        public void Soma(Amostra a)
        {
            n++;
            if (a.Cpu.HasValue) { sCpu += a.Cpu.Value; mCpu = Math.Max(mCpu, a.Cpu.Value); }
            if (a.NucleoMax.HasValue) mNuc = Math.Max(mNuc, a.NucleoMax.Value);
            if (a.Gpu.HasValue) { sGpu += a.Gpu.Value; mGpu = Math.Max(mGpu, a.Gpu.Value); }
            if (a.RamPct.HasValue) sRam += a.RamPct.Value;
            if (a.Disco.HasValue) sDisco += a.Disco.Value;
            sRede += (a.RedeBaixa ?? 0) + (a.RedeSobe ?? 0);
            if (a.TempCpu.HasValue) mTc = Math.Max(mTc, a.TempCpu.Value);
            if (a.TempGpu.HasValue) mTg = Math.Max(mTg, a.TempGpu.Value);
            if (a.VramPct.HasValue) mVram = Math.Max(mVram, a.VramPct.Value);
            if (a.CpuDesempenho.HasValue && a.Cpu >= 40) mDesemp = Math.Min(mDesemp, a.CpuDesempenho.Value);
            if (a.Jogo != null) Jogo = a.Jogo;
        }
        public string Linha()
        {
            if (n == 0) return null;
            var d = new Dictionary<string, object>();
            d["t"] = Inicio.ToString("yyyy-MM-ddTHH:mm", K.INV); d["n"] = n;
            d["cpu"] = Math.Round(sCpu / n, 1); d["cpu_max"] = Math.Round(mCpu, 0); d["nucleo_max"] = Math.Round(mNuc, 0);
            d["gpu"] = Math.Round(sGpu / n, 1); d["gpu_max"] = Math.Round(mGpu, 0);
            d["ram"] = Math.Round(sRam / n, 1); d["disco"] = Math.Round(sDisco / n, 1); d["rede_mbs"] = Math.Round(sRede / n, 2);
            if (mTc > 0) d["temp_cpu"] = mTc;
            if (mTg > 0) d["temp_gpu"] = mTg;
            if (mVram > 0) d["vram"] = Math.Round(mVram, 0);
            if (mDesemp < 1000) d["desempenho_min"] = Math.Round(mDesemp, 0);
            if (Jogo != null) d["jogo"] = Jogo;
            return new JavaScriptSerializer().Serialize(d);
        }
    }

    // ───────── o motor: lê no ritmo escolhido, detecta jogo, guarda e conclui ─────────
    class Motor
    {
        // o que roda com 3D mas não é jogo: navegador, vídeo, chamada, a própria área de trabalho
        static readonly HashSet<string> NAO_JOGO = new HashSet<string>(StringComparer.OrdinalIgnoreCase) {
            "dwm", "explorer", "csrss", "chrome", "msedge", "firefox", "brave", "opera", "opera_gx", "vivaldi", "iexplore", "msedgewebview2",
            "applicationframehost", "searchhost", "searchapp", "shellexperiencehost", "startmenuexperiencehost", "textinputhost", "lockapp", "widgets",
            "obs64", "obs32", "vlc", "mpc-hc64", "mpc-hc", "mpc-be64", "wmplayer", "potplayermini64", "potplayermini", "video.ui", "microsoft.media.player",
            "discord", "spotify", "teams", "ms-teams", "zoom", "slack", "whatsapp", "telegram", "code", "devenv", "katharos",
            "nvcontainer", "nvidia share", "nvsphelper64", "steamwebhelper", "epicgameslauncher", "eadesktop", "ea desktop", "galaxyclient", "battle.net",
            "upc", "ubisoftconnect", "riotclientux", "riotclientservices", "wallpaper32", "wallpaper64", "lively", "rainmeter",
            "photoshop", "afterfx", "adobe premiere pro", "resolve", "blender", "unity", "unrealeditor", "olk", "outlook", "winword", "excel", "powerpnt",
            "acrobat", "acrord32", "photos", "microsoft.photos", "systemsettings", "taskmgr", "windowsterminal", "conhost", "powershell", "cmd", "mspaint"
        };

        public Config Cfg = Config.Le();
        readonly Leitor leitor = new Leitor();
        public readonly List<Amostra> Janela = new List<Amostra>();   // últimos 30 s, para as conclusões
        public readonly List<Amostra> Historico = new List<Amostra>(); // últimos 2 min, para os gráficos do painel
        public Amostra Ultima;
        public Sessao Sessao;
        public List<Conclusao> Conclusoes = new List<Conclusao>();
        public bool Pausado;
        public DateTime Desde = DateTime.Now;
        Minuto minuto;
        int candidatoPid; DateTime candidatoDesde, semJogoDesde = DateTime.MaxValue;
        DateTime proxCfg = DateTime.Now.AddSeconds(30), proxRotacao = DateTime.MinValue;
        public event Action Atualizou;
        public readonly object Trava = new object();
        volatile bool parar;

        public void Roda()
        {
            Thread.CurrentThread.Priority = ThreadPriority.BelowNormal;
            Thread.Sleep(300);
            while (!parar)
            {
                var t0 = DateTime.Now;
                try { Passo(); }
                catch (Exception e) { Log.Escreve("leitura: " + e); }
                int falta = Cfg.IntervaloMs - (int)(DateTime.Now - t0).TotalMilliseconds;
                Thread.Sleep(Math.Max(100, falta));
            }
            try { FechaSessao(); FechaMinuto(); } catch { }
        }

        public void Para() { parar = true; }

        public static bool LeituraPausada()
        {
            try
            {
                string arq = K.Arq("leitura-pausada-ate.txt");
                if (!File.Exists(arq)) return false;
                DateTime ate;
                return DateTime.TryParse(File.ReadAllText(arq).Trim(), K.INV, DateTimeStyles.AssumeLocal, out ate) && ate > DateTime.Now;
            }
            catch { return false; }
        }

        void Passo()
        {
            DateTime agora = DateTime.Now;
            if (agora >= proxCfg) { proxCfg = agora.AddSeconds(30); Cfg = Config.Le(); }
            if (agora >= proxRotacao) { proxRotacao = agora.AddHours(6); Rotaciona("minutos.jsonl", 14); Rotaciona("sessoes.jsonl", 400); }
            Pausado = LeituraPausada();
            if (Pausado) { if (Atualizou != null) Atualizou(); return; }
            // o PC dormiu ou hibernou: o que estava aberto fecha no momento em que parou, não conta o tempo dormindo
            if (Ultima != null && (agora - Ultima.Quando).TotalSeconds > 60) { FechaSessao(); FechaMinuto(); lock (Trava) { Janela.Clear(); Historico.Clear(); } }
            bool emJogo = Sessao != null;
            if (emJogo && Cfg.PausarEmJogo)
            {
                var s = leitor.Le(Cfg, true);   // só para saber quando o jogo fecha
                DetectaJogo(s);
                lock (Trava) { Ultima = s; }
                if (Atualizou != null) Atualizou();
                return;
            }
            var a = leitor.Le(Cfg, emJogo);
            DetectaJogo(a);
            lock (Trava)
            {
                Ultima = a;
                Janela.Add(a); while (Janela.Count > 1 && (a.Quando - Janela[0].Quando).TotalSeconds > 30) Janela.RemoveAt(0);
                Historico.Add(a); while (Historico.Count > 1 && (a.Quando - Historico[0].Quando).TotalSeconds > 120) Historico.RemoveAt(0);
                Conclusoes = Regras.Agora(Janela, Cfg, Sessao != null);
            }
            if (Sessao != null) Sessao.Soma(a, Cfg);
            if (minuto == null || minuto.Inicio.Minute != agora.Minute || (agora - minuto.Inicio).TotalMinutes >= 1) { FechaMinuto(); minuto = new Minuto(agora); }
            minuto.Soma(a);
            GravaAgora(a);
            if (Atualizou != null) Atualizou();
        }

        void DetectaJogo(Amostra a)
        {
            DateTime agora = a.Quando;
            string nomeTop = null;
            if (a.TopGpuPid > 0) leitor.Nomes.TryGetValue(a.TopGpuPid, out nomeTop);
            bool candidato = a.TopGpuPid > 0 && a.TopGpu >= 20 && nomeTop != null && !NAO_JOGO.Contains(nomeTop) &&
                             (a.TopGpuPid == a.PrimeiroPlanoPid || a.TelaCheia || a.AntiCheat);
            if (Sessao == null)
            {
                if (candidato)
                {
                    if (candidatoPid != a.TopGpuPid) { candidatoPid = a.TopGpuPid; candidatoDesde = agora; }
                    else if ((agora - candidatoDesde).TotalSeconds >= 10)
                    {
                        Sessao = new Sessao { Jogo = nomeTop, Pid = a.TopGpuPid, Inicio = candidatoDesde, Ultimo = agora };
                        semJogoDesde = DateTime.MaxValue;
                        Log.Escreve("jogo aberto: " + nomeTop);
                    }
                }
                else candidatoPid = 0;
            }
            else
            {
                bool vivo = leitor.Nomes.ContainsKey(Sessao.Pid);
                bool ativo = vivo && (a.TopGpuPid == Sessao.Pid && a.TopGpu >= 5 || a.PrimeiroPlanoPid == Sessao.Pid);
                if (ativo) semJogoDesde = DateTime.MaxValue;
                else if (semJogoDesde == DateTime.MaxValue) semJogoDesde = agora;
                if (!vivo || (agora - semJogoDesde).TotalSeconds >= 30) FechaSessao();
            }
            if (Sessao != null) { a.Jogo = Sessao.Jogo; a.JogoPid = Sessao.Pid; }
        }

        void FechaSessao()
        {
            var s = Sessao; Sessao = null; candidatoPid = 0;
            if (s == null) return;
            Log.Escreve("jogo fechado: " + s.Jogo + ", " + Math.Round((s.Ultimo - s.Inicio).TotalMinutes, 1).ToString(K.INV) + " min");
            if ((s.Ultimo - s.Inicio).TotalMinutes < 1 || s.N < 5) return;
            Acrescenta("sessoes.jsonl", new JavaScriptSerializer().Serialize(s.Json()));
        }

        void FechaMinuto()
        {
            if (minuto == null) return;
            string l = minuto.Linha();
            if (l != null) Acrescenta("minutos.jsonl", l);
            minuto = null;
        }

        static void Acrescenta(string nome, string linha)
        {
            try { Directory.CreateDirectory(K.CASA); File.AppendAllText(K.Arq(nome), linha + "\n", new UTF8Encoding(false)); }
            catch (Exception e) { Log.Escreve(nome + ": " + e.Message); }
        }

        static void Rotaciona(string nome, int dias)
        {
            try
            {
                string arq = K.Arq(nome);
                if (!File.Exists(arq) || new FileInfo(arq).Length < 2 * 1024 * 1024) return;
                string corte = DateTime.Now.AddDays(-dias).ToString("yyyy-MM-dd", K.INV);
                var ficam = new List<string>();
                foreach (var l in File.ReadAllLines(arq, Encoding.UTF8))
                {
                    int i = l.IndexOf("\"t\":\"", StringComparison.Ordinal); if (i < 0) i = l.IndexOf("\"inicio\":\"", StringComparison.Ordinal);
                    if (i < 0) continue;
                    int a = l.IndexOf(':', i) + 2;
                    if (a + 10 <= l.Length && string.CompareOrdinal(l.Substring(a, 10), corte) >= 0) ficam.Add(l);
                }
                K.GravaAtomico(arq, string.Join("\n", ficam.ToArray()) + (ficam.Count > 0 ? "\n" : ""));
            }
            catch (Exception e) { Log.Escreve("rotação " + nome + ": " + e.Message); }
        }

        void GravaAgora(Amostra a)
        {
            var d = new Dictionary<string, object>();
            d["versao"] = K.VERSAO; d["quando"] = K.Iso(a.Quando); d["intervalo_s"] = Cfg.IntervaloMs / 1000.0;
            d["cpu"] = K.R(a.Cpu, 1); d["nucleo_max"] = K.R(a.NucleoMax, 1); d["cpu_desempenho"] = K.R(a.CpuDesempenho, 0); d["cpu_ghz"] = K.R(a.CpuGhz, 2);
            d["gpu"] = K.R(a.Gpu, 1); d["vram_gb"] = K.R(a.VramGb, 2); d["vram_total_gb"] = K.R(a.VramTotalGb, 1);
            d["ram_pct"] = K.R(a.RamPct, 1); d["ram_gb"] = K.R(a.RamGb, 2); d["ram_total_gb"] = K.R(a.RamTotalGb, 1);
            d["disco"] = K.R(a.Disco, 1); d["disco_le_mbs"] = K.R(a.DiscoLe, 2); d["disco_grava_mbs"] = K.R(a.DiscoGrava, 2);
            d["rede_baixa_mbs"] = K.R(a.RedeBaixa, 3); d["rede_sobe_mbs"] = K.R(a.RedeSobe, 3);
            d["temp_cpu"] = K.R(a.TempCpu, 0); d["temp_cpu_fonte"] = a.TempCpuFonte; d["temp_gpu"] = K.R(a.TempGpu, 0); d["temp_gpu_fonte"] = a.TempGpuFonte;
            if (a.Bateria.HasValue) { d["bateria"] = a.Bateria; d["na_bateria"] = a.NaBateria; }
            if (Sessao != null)
            {
                var j = new Dictionary<string, object>();
                j["nome"] = Sessao.Jogo; j["desde"] = K.Iso(Sessao.Inicio); j["min"] = Math.Round((a.Quando - Sessao.Inicio).TotalMinutes, 1);
                j["principal"] = Sessao.Principal();
                d["jogo"] = j;
            }
            var cs = new List<object>();
            foreach (var c in Conclusoes) { var x = new Dictionary<string, object>(); x["id"] = c.Id; x["nivel"] = c.Nivel; x["titulo"] = c.Titulo; x["texto"] = c.Texto; x["comando"] = c.Comando; cs.Add(x); }
            d["conclusoes"] = cs;
            using (var eu = Process.GetCurrentProcess())
            {
                var p = new Dictionary<string, object>();
                p["ram_mb"] = Math.Round(eu.WorkingSet64 / 1048576.0, 1); p["desde"] = K.Iso(Desde);
                d["segundo_plano"] = p;
            }
            try { K.GravaAtomico(K.Arq("agora.json"), new JavaScriptSerializer().Serialize(d)); } catch { }
        }
    }

    // ───────── cores e letras do site ─────────
    static class Cor
    {
        public static readonly Color Fundo = Color.FromArgb(12, 12, 13), Painel = Color.FromArgb(18, 18, 20), Linha = Color.FromArgb(36, 36, 40),
            LinhaForte = Color.FromArgb(56, 56, 62), Apagado = Color.FromArgb(134, 131, 124), Texto = Color.FromArgb(205, 200, 190),
            Osso = Color.FromArgb(239, 233, 222), Ambar = Color.FromArgb(226, 168, 92), Verde = Color.FromArgb(156, 207, 140), Vermelho = Color.FromArgb(229, 115, 122);
        public static Color DoNivel(int n) { return n >= 2 ? Vermelho : n == 1 ? Ambar : Verde; }
    }

    class Tabela : ProfessionalColorTable
    {
        public override Color ToolStripDropDownBackground { get { return Cor.Painel; } }
        public override Color MenuBorder { get { return Cor.LinhaForte; } }
        public override Color MenuItemBorder { get { return Cor.Linha; } }
        public override Color MenuItemSelected { get { return Cor.Linha; } }
        public override Color MenuItemSelectedGradientBegin { get { return Cor.Linha; } }
        public override Color MenuItemSelectedGradientEnd { get { return Cor.Linha; } }
        public override Color ImageMarginGradientBegin { get { return Cor.Painel; } }
        public override Color ImageMarginGradientMiddle { get { return Cor.Painel; } }
        public override Color ImageMarginGradientEnd { get { return Cor.Painel; } }
        public override Color SeparatorDark { get { return Cor.Linha; } }
        public override Color SeparatorLight { get { return Cor.Linha; } }
        public override Color CheckBackground { get { return Cor.Linha; } }
        public override Color CheckSelectedBackground { get { return Cor.LinhaForte; } }
    }

    class Desenho : ToolStripProfessionalRenderer
    {
        public Desenho() : base(new Tabela()) { RoundedEdges = false; }
        protected override void OnRenderItemText(ToolStripItemTextRenderEventArgs e)
        {
            e.TextColor = e.Item.Enabled ? (e.Item.Selected ? Cor.Osso : Cor.Texto) : (e.Item.Tag as string == "titulo" ? Cor.Ambar : Cor.Apagado);
            base.OnRenderItemText(e);
        }
        protected override void OnRenderItemCheck(ToolStripItemImageRenderEventArgs e)
        {
            var r = e.ImageRectangle; r.Inflate(-3, -3);
            using (var b = new SolidBrush(Cor.Ambar)) e.Graphics.FillRectangle(b, r);
        }
    }

    // ───────── o painel ao vivo que abre ao clicar no ícone ─────────
    class PainelAoVivo : Form
    {
        readonly Motor motor;
        readonly Action<string[]> abre;
        float s = 1;
        Font fTitulo, fNum, fRotulo, fTexto, fNegrito, fPequeno, fMono;
        readonly List<KeyValuePair<RectangleF, string[]>> botoes = new List<KeyValuePair<RectangleF, string[]>>();
        int sobre = -1;
        List<string[]> propostas = new List<string[]>();
        DateTime propostasLidas = DateTime.MinValue;
        readonly Icon marca;

        public PainelAoVivo(Motor m, Action<string[]> abre, Icon marca)
        {
            motor = m; this.abre = abre; this.marca = marca;
            FormBorderStyle = FormBorderStyle.None; ShowInTaskbar = false; TopMost = true; StartPosition = FormStartPosition.Manual;
            BackColor = Cor.Fundo; DoubleBuffered = true; KeyPreview = true; Text = "Katharos";
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw, true);
            Deactivate += delegate { Hide(); Escondido = DateTime.Now; };
            KeyDown += delegate (object o, KeyEventArgs e) { if (e.KeyCode == Keys.Escape) Hide(); };
            MouseMove += delegate (object o, MouseEventArgs e) { int i = Botao(e.Location); if (i != sobre) { sobre = i; Cursor = i >= 0 ? Cursors.Hand : Cursors.Default; Invalidate(); } };
            MouseLeave += delegate { if (sobre != -1) { sobre = -1; Invalidate(); } };
            MouseClick += delegate (object o, MouseEventArgs e)
            {
                int i = Botao(e.Location);
                if (i < 0) return;
                Hide();
                if (botoes[i].Value != null) abre(botoes[i].Value);   // null = o X: só fecha
            };
        }

        public DateTime Escondido = DateTime.MinValue;

        int Botao(Point p) { for (int i = 0; i < botoes.Count; i++) if (botoes[i].Key.Contains(p)) return i; return -1; }

        void Fontes()
        {
            using (var g = CreateGraphics()) s = g.DpiX / 96f;
            if (fTitulo != null) return;
            fTitulo = new Font("Segoe UI Semibold", 11f, GraphicsUnit.Point);
            fNum = new Font("Consolas", 15f, FontStyle.Bold, GraphicsUnit.Point);
            fRotulo = new Font("Consolas", 8.5f, GraphicsUnit.Point);
            fTexto = new Font("Segoe UI", 9f, GraphicsUnit.Point);
            fNegrito = new Font("Segoe UI Semibold", 9f, GraphicsUnit.Point);
            fPequeno = new Font("Segoe UI", 8f, GraphicsUnit.Point);
            fMono = new Font("Consolas", 8.5f, GraphicsUnit.Point);
        }

        public void PreparaFoto()
        {
            Fontes();
            propostas = new List<string[]> { new[] { "Desligar o que abre com o Windows e pesa no jogo", "inicializacao", "alta" } };
            propostasLidas = DateTime.Now;
            Width = (int)(400 * s);
            Height = AlturaDesejada();
            CreateControl();
        }

        public void Mostra()
        {
            Fontes();
            LePropostas();
            Width = (int)(400 * s);
            Height = AlturaDesejada();
            Posiciona();
            Show(); Activate();
            Invalidate();
        }

        void Posiciona()
        {
            var tela = Screen.FromPoint(Cursor.Position);
            var wa = tela.WorkingArea; int m = (int)(10 * s);
            int x = wa.Right - Width - m, y = wa.Bottom - Height - m;
            if (wa.Top > tela.Bounds.Top) y = wa.Top + m;          // barra de tarefas em cima
            if (wa.Left > tela.Bounds.Left) x = wa.Left + m;        // barra à esquerda
            Location = new Point(x, Math.Max(wa.Top + m, y));
        }

        public void Atualiza()
        {
            if (!Visible) return;
            if ((DateTime.Now - propostasLidas).TotalSeconds > 30) LePropostas();
            int h = AlturaDesejada();
            if (Math.Abs(h - Height) > 2) { Height = h; Posiciona(); }
            Invalidate();
        }

        void LePropostas()
        {
            propostasLidas = DateTime.Now;
            var l = new List<string[]>();
            try
            {
                string arq = K.Arq("propostas.json");
                if (File.Exists(arq))
                {
                    var d = new JavaScriptSerializer().DeserializeObject(File.ReadAllText(arq, Encoding.UTF8)) as Dictionary<string, object>;
                    var ps = d != null && d.ContainsKey("propostas") ? d["propostas"] as object[] : null;
                    if (ps != null)
                        foreach (var o in ps)
                        {
                            var x = o as Dictionary<string, object>; if (x == null) continue;
                            l.Add(new[] { Convert.ToString(x["titulo"]), x.ContainsKey("comando") ? Convert.ToString(x["comando"]) : "", x.ContainsKey("confianca") ? Convert.ToString(x["confianca"]) : "" });
                            if (l.Count >= 2) break;
                        }
                }
            }
            catch { }
            propostas = l;
        }

        // a altura depende de quantas conclusões e propostas há: mede o texto antes de desenhar
        int AlturaDesejada()
        {
            using (var g = CreateGraphics()) return (int)Math.Ceiling(Desenha(g, false));
        }

        protected override void OnPaint(PaintEventArgs e) { Desenha(e.Graphics, true); }

        float Desenha(Graphics g, bool pinta)
        {
            if (fTitulo == null) Fontes();
            g.SmoothingMode = SmoothingMode.AntiAlias; g.TextRenderingHint = TextRenderingHint.ClearTypeGridFit;
            float W = Width, pad = 18 * s, y = 0;
            Amostra a; Sessao ses; List<Conclusao> concl; List<Amostra> hist;
            lock (motor.Trava) { a = motor.Ultima; ses = motor.Sessao; concl = new List<Conclusao>(motor.Conclusoes); hist = new List<Amostra>(motor.Historico); }
            if (pinta)
            {
                using (var b = new SolidBrush(Cor.Fundo)) g.FillRectangle(b, 0, 0, Width, Height);
                using (var b = new SolidBrush(Cor.Ambar)) g.FillRectangle(b, 0, 0, Width, 2 * s);
                using (var p = new Pen(Cor.LinhaForte)) g.DrawRectangle(p, 0, 0, Width - 1, Height - 1);
                botoes.Clear();
            }
            // cabeçalho
            y = 16 * s;
            if (pinta && marca != null) using (var ic = new Icon(marca, (int)(28 * s), (int)(28 * s))) g.DrawIcon(ic, new Rectangle((int)pad, (int)y, (int)(28 * s), (int)(28 * s)));
            if (pinta)
            {
                Texto(g, "katharos", fTitulo, Cor.Osso, pad + 38 * s, y - 2 * s);
                string ritmo = "ao vivo · a cada " + K.Num(motor.Cfg.IntervaloMs / 1000.0, motor.Cfg.IntervaloMs % 1000 == 0 ? 0 : 1) + " s";
                Texto(g, motor.Pausado ? "acompanhamento pausado" : ritmo, fPequeno, Cor.Apagado, pad + 38 * s, y + 17 * s);
                string st; Color cs;
                if (motor.Pausado) { st = "pausado"; cs = Cor.Apagado; }
                else if (concl.Count > 0 && concl[0].Nivel >= 2) { st = "atenção"; cs = Cor.Vermelho; }
                else if (ses != null) { st = "jogando"; cs = Cor.Verde; }
                else if (concl.Count > 0 && concl[0].Nivel == 1) { st = "atenção"; cs = Cor.Ambar; }
                else { st = "tudo certo"; cs = Cor.Verde; }
                // o X que fecha o painel (o segundo plano continua)
                float tx = 22 * s, xx = W - pad - tx + 4 * s, xy = y - 2 * s;
                var rx = new RectangleF(xx, xy, tx, tx);
                bool hx = sobre == botoes.Count;
                if (hx) using (var b = new SolidBrush(Cor.Linha)) g.FillRectangle(b, rx);
                using (var pn = new Pen(hx ? Cor.Osso : Cor.Apagado, 1.5f * s))
                {
                    float m = 7 * s;
                    g.DrawLine(pn, rx.Left + m, rx.Top + m, rx.Right - m, rx.Bottom - m);
                    g.DrawLine(pn, rx.Right - m, rx.Top + m, rx.Left + m, rx.Bottom - m);
                }
                botoes.Add(new KeyValuePair<RectangleF, string[]>(rx, null));
                var tam = g.MeasureString(st, fRotulo);
                float xs = xx - 12 * s - tam.Width;
                using (var b = new SolidBrush(cs)) g.FillEllipse(b, xs - 12 * s, y + 6 * s, 7 * s, 7 * s);
                Texto(g, st, fRotulo, cs, xs, y + 2 * s);
            }
            y += 42 * s;
            if (ses != null)
            {
                string nomes; double minutos = a != null ? (a.Quando - ses.Inicio).TotalMinutes : 0;
                nomes = ses.Jogo + " · há " + (minutos < 60 ? K.Num(Math.Floor(minutos), 0) + " min" : K.Num(Math.Floor(minutos / 60), 0) + " h " + K.Num(Math.Floor(minutos % 60), 0) + " min");
                if (pinta)
                {
                    using (var b = new SolidBrush(Cor.Painel)) g.FillRectangle(b, pad, y, W - 2 * pad, 26 * s);
                    Texto(g, "jogo aberto", fRotulo, Cor.Apagado, pad + 10 * s, y + 6 * s);
                    Texto(g, nomes, fNegrito, Cor.Osso, pad + 92 * s, y + 4 * s);
                }
                y += 34 * s;
            }
            if (pinta) Linha(g, pad, y, W - pad);
            y += 6 * s;
            if (a == null)
            {
                if (pinta) Texto(g, motor.Pausado ? "Pausado. Retome pelo menu do ícone." : "Lendo o PC...", fTexto, Cor.Apagado, pad, y + 10 * s);
                y += 40 * s;
            }
            else
            {
                Func<Amostra, double?> fCpu = x => x.Cpu, fGpu = x => x.Gpu, fRam = x => x.RamPct, fTemp = x => x.TempCpu ?? x.TempGpu, fDisco = x => x.Disco,
                                       fRede = x => (x.RedeBaixa ?? 0) + (x.RedeSobe ?? 0);
                string subCpu = (a.CpuGhz.HasValue ? K.Num(a.CpuGhz, 1) + " GHz · " : "") + "núcleo máx. " + K.Num(a.NucleoMax, 0) + " %";
                string subGpu = a.VramGb.HasValue ? "memória " + K.Num(a.VramGb, 1) + (a.VramTotalGb.HasValue ? " de " + K.Num(a.VramTotalGb, 0) : "") + " GB" : "uso do motor 3D e vídeo";
                string valTemp, subTemp;
                if (a.TempCpu.HasValue) { valTemp = K.Num(a.TempCpu, 0) + " °C"; subTemp = "CPU · GPU " + (a.TempGpu.HasValue ? K.Num(a.TempGpu, 0) + " °C" : "-") + " · " + Curta(a.TempCpuFonte); }
                else if (a.TempGpu.HasValue) { valTemp = K.Num(a.TempGpu, 0) + " °C"; subTemp = "placa de vídeo · CPU: abra Afterburner ou HWiNFO"; }
                else { valTemp = "-"; subTemp = "abra MSI Afterburner, HWiNFO ou Core Temp"; }
                y = Linha(g, pinta, y, pad, "cpu", K.Num(a.Cpu, 0) + " %", subCpu, hist, fCpu, 100, a.Cpu >= 90);
                y = Linha(g, pinta, y, pad, "placa de vídeo", a.Gpu.HasValue ? K.Num(a.Gpu, 0) + " %" : "-", subGpu, hist, fGpu, 100, a.Gpu >= 95);
                y = Linha(g, pinta, y, pad, "memória", K.Num(a.RamPct, 0) + " %", K.Num(a.RamGb, 1) + " de " + K.Num(a.RamTotalGb, 0) + " GB", hist, fRam, 100, a.RamPct >= 90);
                y = Linha(g, pinta, y, pad, "temperatura", valTemp, subTemp, hist, fTemp, 100, a.TempCpu >= motor.Cfg.AvisoCpu || a.TempGpu >= motor.Cfg.AvisoGpu);
                y = Linha(g, pinta, y, pad, "disco", K.Num(a.Disco, 0) + " %", "lê " + K.Num(a.DiscoLe, 1) + " · grava " + K.Num(a.DiscoGrava, 1) + " MB/s", hist, fDisco, 100, a.Disco >= 95);
                y = Linha(g, pinta, y, pad, "rede", K.Num((a.RedeBaixa ?? 0) * 8, 1) + " Mb/s", "baixando · enviando " + K.Num((a.RedeSobe ?? 0) * 8, 1) + " Mb/s", hist, fRede, 0, false);
                if (a.Bateria.HasValue && pinta) Texto(g, "bateria " + a.Bateria + " %" + (a.NaBateria ? ", fora da tomada" : ", na tomada"), fPequeno, Cor.Apagado, pad, y);
                if (a.Bateria.HasValue) y += 18 * s;
            }
            // o que eu vejo agora
            y += 6 * s;
            if (pinta) Texto(g, "o que eu vejo agora", fRotulo, Cor.Apagado, pad, y);
            y += 20 * s;
            if (concl.Count == 0)
            {
                if (pinta) Texto(g, ses != null ? "O jogo está rodando sem nada no limite." : "Tudo dentro do normal.", fTexto, Cor.Texto, pad, y);
                y += 22 * s;
            }
            float larg = W - 2 * pad - 16 * s;
            foreach (var c in concl)
            {
                if (pinta) using (var b = new SolidBrush(Cor.DoNivel(c.Nivel))) g.FillRectangle(b, pad, y + 4 * s, 3 * s, 12 * s);
                if (pinta) Texto(g, c.Titulo, fNegrito, Cor.Osso, pad + 12 * s, y);
                y += 19 * s;
                var t = g.MeasureString(c.Texto, fPequeno, (int)larg);
                if (pinta) using (var b = new SolidBrush(Cor.Texto)) g.DrawString(c.Texto, fPequeno, b, new RectangleF(pad + 12 * s, y, larg, t.Height + 2));
                y += t.Height + 8 * s;
            }
            // central de inteligência
            y += 4 * s;
            if (pinta) { Linha(g, pad, y, W - pad); Texto(g, "central de inteligência", fRotulo, Cor.Apagado, pad, y + 10 * s); }
            y += 30 * s;
            if (propostas.Count == 0)
            {
                if (pinta) Texto(g, "Nada a propor agora. Ela olha tudo de novo a cada hora.", fPequeno, Cor.Apagado, pad, y);
                y += 20 * s;
            }
            foreach (var p in propostas)
            {
                var t = g.MeasureString(p[0], fTexto, (int)(W - 2 * pad));
                if (pinta) using (var b = new SolidBrush(Cor.Texto)) g.DrawString(p[0], fTexto, b, new RectangleF(pad, y, W - 2 * pad, t.Height + 2));
                y += t.Height + 1 * s;
                if (!string.IsNullOrEmpty(p[1]))
                {
                    if (pinta) Texto(g, "katharos " + p[1], fMono, Cor.Ambar, pad, y);
                    y += 18 * s;
                }
                y += 6 * s;
            }
            // botões
            y += 6 * s;
            string[][] bs = { new[] { "central", "conselheiro" }, new[] { "painel", "painel" }, new[] { "raio-x", "raiox" }, new[] { "abrir", "" } };
            float gap = 8 * s, bw = (W - 2 * pad - gap * (bs.Length - 1)) / bs.Length, bh = 30 * s;
            for (int i = 0; i < bs.Length; i++)
            {
                var r = new RectangleF(pad + i * (bw + gap), y, bw, bh);
                if (pinta)
                {
                    bool h = sobre == botoes.Count;
                    using (var b = new SolidBrush(h ? Cor.Linha : Cor.Painel)) g.FillRectangle(b, r);
                    using (var pn = new Pen(h ? Cor.Ambar : Cor.LinhaForte)) g.DrawRectangle(pn, r.X, r.Y, r.Width, r.Height);
                    var tm = g.MeasureString(bs[i][0], fRotulo);
                    Texto(g, bs[i][0], fRotulo, h ? Cor.Ambar : Cor.Texto, r.X + (r.Width - tm.Width) / 2, r.Y + (r.Height - tm.Height) / 2);
                    botoes.Add(new KeyValuePair<RectangleF, string[]>(r, bs[i][1] == "" ? new string[0] : new[] { bs[i][1] }));
                }
            }
            y += bh + 12 * s;
            if (pinta)
            {
                string rodape = "Katharos " + K.VERSAO;
                try { using (var eu = Process.GetCurrentProcess()) rodape += " · usa " + K.Num(eu.WorkingSet64 / 1048576.0, 0) + " MB de RAM"; } catch { }
                Texto(g, rodape, fPequeno, Cor.Apagado, pad, y);
            }
            y += 26 * s;
            return y;
        }

        float Linha(Graphics g, bool pinta, float y, float pad, string rotulo, string valor, string sub, List<Amostra> hist, Func<Amostra, double?> f, double teto, bool alerta)
        {
            float W = Width, h = 50 * s;
            if (pinta)
            {
                Texto(g, rotulo, fRotulo, Cor.Apagado, pad, y + 4 * s);
                Texto(g, valor, fNum, alerta ? Cor.Vermelho : Cor.Osso, pad + 112 * s, y);
                // gráfico dos últimos 2 minutos
                float gx = W - pad - 92 * s, gy = y + 6 * s, gw = 92 * s, gh = 26 * s;
                using (var b = new SolidBrush(Cor.Apagado))
                using (var sf = new StringFormat(StringFormatFlags.NoWrap) { Trimming = StringTrimming.EllipsisCharacter })
                    g.DrawString(sub ?? "", fPequeno, b, new RectangleF(pad + 112 * s, y + 25 * s, gx - (pad + 112 * s) - 8 * s, 18 * s), sf);
                var pts = new List<double>();
                foreach (var a in hist) { var v = f(a); pts.Add(v.HasValue ? v.Value : double.NaN); }
                double max = teto;
                if (teto <= 0) { max = 0.1; foreach (var v in pts) if (!double.IsNaN(v) && v > max) max = v; }
                using (var p = new Pen(Cor.Linha)) g.DrawLine(p, gx, gy + gh, gx + gw, gy + gh);
                if (pts.Count >= 2)
                {
                    var linha = new List<PointF>();
                    for (int i = 0; i < pts.Count; i++)
                    {
                        if (double.IsNaN(pts[i])) continue;
                        float px = gx + gw * i / (pts.Count - 1), py = gy + gh - (float)(Math.Min(1, pts[i] / max) * gh);
                        linha.Add(new PointF(px, py));
                    }
                    if (linha.Count >= 2)
                    {
                        var area = new List<PointF>(linha); area.Add(new PointF(linha[linha.Count - 1].X, gy + gh)); area.Add(new PointF(linha[0].X, gy + gh));
                        Color c = alerta ? Cor.Vermelho : Cor.Ambar;
                        using (var b = new SolidBrush(Color.FromArgb(38, c))) g.FillPolygon(b, area.ToArray());
                        using (var p = new Pen(c, 1.4f * s)) g.DrawLines(p, linha.ToArray());
                    }
                }
            }
            return y + h;
        }

        static string Curta(string fonte)
        {
            if (fonte == null) return "";
            if (fonte.StartsWith("LibreHardware")) return "LHM";
            if (fonte.StartsWith("OpenHardware")) return "OHM";
            if (fonte.StartsWith("MSI ")) return "Afterburner";
            return fonte;
        }

        void Linha(Graphics g, float x1, float y, float x2) { using (var p = new Pen(Cor.Linha)) g.DrawLine(p, x1, y, x2, y); }

        static void Texto(Graphics g, string t, Font f, Color c, float x, float y)
        {
            using (var b = new SolidBrush(c)) g.DrawString(t ?? "", f, b, x, y);
        }
    }

    static class Marca
    {
        public static Icon Carrega()
        {
            try { var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("katharos.ico"); if (st != null) return new Icon(st); } catch { }
            try { return Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
            return SystemIcons.Application;
        }
    }

    // ───────── o ícone perto do relógio ─────────
    class Bandeja : ApplicationContext
    {
        readonly Motor motor = new Motor();
        readonly NotifyIcon ni = new NotifyIcon();
        readonly ContextMenuStrip menu = new ContextMenuStrip();
        readonly PainelAoVivo painel;
        readonly Icon marca, marcaPequena;
        readonly Control ui = new Control();
        ToolStripMenuItem iStatus, iPausa, iInicio;
        IntPtr iconeAtual = IntPtr.Zero; string estadoIcone = "";
        readonly Dictionary<string, DateTime> avisado = new Dictionary<string, DateTime>();
        DateTime proxPropostas = DateTime.Now.AddMinutes(2);
        Thread fio;

        public Bandeja(bool mostrar)
        {
            ui.CreateControl();
            marca = Marca.Carrega();
            marcaPequena = new Icon(marca, SystemInformation.SmallIconSize);
            painel = new PainelAoVivo(motor, Abre, marca);
            MontaMenu();
            ni.Icon = marcaPequena; ni.Text = "Katharos"; ni.ContextMenuStrip = menu; ni.Visible = true;
            ni.MouseUp += delegate (object o, MouseEventArgs e) { if (e.Button == MouseButtons.Left) AlternaPainel(); };
            motor.Atualizou += delegate { try { ui.BeginInvoke(new Action(Atualiza)); } catch { } };
            fio = new Thread(motor.Roda); fio.IsBackground = true; fio.Name = "leitura"; fio.Start();
            new Thread(EsperaSinais) { IsBackground = true }.Start();
            if (mostrar) ui.BeginInvoke(new Action(delegate { painel.Mostra(); }));
            try { File.Delete(K.Arq("segundo-plano-fechado.txt")); } catch { }
            Log.Escreve("segundo plano ligado (" + K.VERSAO + ")");
        }

        void EsperaSinais()
        {
            try
            {
                using (var sair = new EventWaitHandle(false, EventResetMode.AutoReset, K.EV_SAIR))
                using (var mostrar = new EventWaitHandle(false, EventResetMode.AutoReset, K.EV_MOSTRAR))
                {
                    while (true)
                    {
                        int i = WaitHandle.WaitAny(new WaitHandle[] { sair, mostrar });
                        if (i == 0) { ui.BeginInvoke(new Action(delegate { Sai(false); })); return; }
                        ui.BeginInvoke(new Action(delegate { painel.Mostra(); }));
                    }
                }
            }
            catch (Exception e) { Log.Escreve("sinais: " + e.Message); }
        }

        // clicar no ícone com o painel aberto: o painel some ao perder o foco (antes do clique chegar), então não reabre logo em seguida
        void AlternaPainel()
        {
            if (painel.Visible) { painel.Hide(); return; }
            if ((DateTime.Now - painel.Escondido).TotalMilliseconds < 400) return;
            painel.Mostra();
        }

        ToolStripMenuItem Item(string texto, EventHandler acao)
        {
            var i = new ToolStripMenuItem(texto);
            if (acao != null) i.Click += acao; else i.Enabled = false;
            menu.Items.Add(i); return i;
        }

        void MontaMenu()
        {
            menu.Renderer = new Desenho(); menu.ShowImageMargin = false; menu.ShowCheckMargin = true;
            menu.Font = new Font("Segoe UI", 9f); menu.BackColor = Cor.Painel; menu.ForeColor = Cor.Texto;
            var t = Item("Katharos " + K.VERSAO + ", acompanhando", null); t.Tag = "titulo"; t.Font = new Font("Segoe UI Semibold", 9f);
            iStatus = Item("lendo...", null);
            menu.Items.Add(new ToolStripSeparator());
            Item("Painel ao vivo", delegate { painel.Mostra(); });
            Item("Abrir o Katharos", delegate { Abre(new string[0]); });
            Item("Central de inteligência", delegate { Abre(new[] { "conselheiro" }); });
            Item("Gráficos do PC e dos jogos", delegate { Abre(new[] { "painel" }); });
            Item("Ao vivo no terminal", delegate { Abre(new[] { "aovivo" }); });
            Item("Raio-x", delegate { Abre(new[] { "raiox" }); });
                        menu.Items.Add(new ToolStripSeparator());
            Item("Turbo", delegate { Abre(new[] { "turbo" }); });
            Item("Conferir se os ajustes continuam", delegate { Abre(new[] { "verificar" }); });
            Item("Limpar", delegate { Abre(new[] { "limpar" }); });
            Item("Desfazer mudanças", delegate { Abre(new[] { "desfazer" }); });
            menu.Items.Add(new ToolStripSeparator());
            iPausa = Item("Pausar por 1 hora", delegate { AlternaPausa(); });
            iInicio = Item("Iniciar com o Windows", delegate { AlternaInicio(); });
            Item("Abrir a pasta dos dados", delegate { try { Process.Start("explorer.exe", K.Q(K.CASA)); } catch { } });
            menu.Items.Add(new ToolStripSeparator());
            Item("Sair do segundo plano", delegate { Sai(); });
            menu.Opening += delegate { AtualizaMenu(); };
        }

        void AtualizaMenu()
        {
            iPausa.Text = Motor.LeituraPausada() ? "Retomar agora" : "Pausar por 1 hora";
            iInicio.Checked = IniciaComWindows();
        }

        static bool IniciaComWindows()
        {
            try { using (var k = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run")) return k != null && k.GetValue("Katharos") != null; }
            catch { return false; }
        }

        void AlternaInicio()
        {
            try
            {
                using (var k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
                {
                    if (k.GetValue("Katharos") != null) k.DeleteValue("Katharos", false);
                    else k.SetValue("Katharos", K.Q(Application.ExecutablePath) + " --segundo-plano");
                }
            }
            catch (Exception e) { Log.Escreve("início: " + e.Message); }
        }

        void AlternaPausa()
        {
            string arq = K.Arq("leitura-pausada-ate.txt");
            try
            {
                if (Motor.LeituraPausada()) File.Delete(arq);
                else File.WriteAllText(arq, DateTime.Now.AddHours(1).ToString("yyyy-MM-ddTHH:mm:ss", K.INV), Encoding.ASCII);
            }
            catch { }
        }

        void Abre(string[] args) { Abridor.Abre(args); }

        void Atualiza()
        {
            Amostra a; Sessao ses; List<Conclusao> concl;
            lock (motor.Trava) { a = motor.Ultima; ses = motor.Sessao; concl = new List<Conclusao>(motor.Conclusoes); }
            string est = motor.Pausado ? "pausa" : (concl.Count > 0 ? (concl[0].Nivel >= 2 ? "grave" : concl[0].Nivel == 1 ? "atencao" : "") : "");
            if (est == "" && ses != null) est = "jogo";
            TrocaIcone(est);
            string dica;
            if (motor.Pausado) dica = "Katharos: pausado";
            else if (a == null) dica = "Katharos: lendo...";
            else
            {
                dica = "Katharos · CPU " + K.Num(a.Cpu, 0) + "% · GPU " + K.Num(a.Gpu, 0) + "%";
                if (a.TempCpu.HasValue || a.TempGpu.HasValue) dica += " · " + K.Num(a.TempCpu ?? a.TempGpu, 0) + " °C";
                if (ses != null) dica += "\n" + ses.Jogo;
            }
            ni.Text = dica.Length > 63 ? dica.Substring(0, 63) : dica;
            if (iStatus != null) iStatus.Text = a == null ? (motor.Pausado ? "pausado" : "lendo...") :
                ("CPU " + K.Num(a.Cpu, 0) + " %   GPU " + K.Num(a.Gpu, 0) + " %   RAM " + K.Num(a.RamPct, 0) + " %" + (a.TempCpu.HasValue ? "   " + K.Num(a.TempCpu, 0) + " °C" : ""));
            painel.Atualiza();
            // avisos que valem uma notificação: calor sempre; o resto só fora de jogo; cada um no máximo a cada 30 min
            if (motor.Cfg.Notificar)
                foreach (var c in concl)
                {
                    if (c.Nivel < 1 || (ses != null && c.Id != "calor") || c.Id == "gpu") continue;
                    DateTime ult;
                    if (avisado.TryGetValue(c.Id, out ult) && (DateTime.Now - ult).TotalMinutes < 30) continue;
                    avisado[c.Id] = DateTime.Now;
                    ni.ShowBalloonTip(8000, "Katharos: " + c.Titulo, c.Texto, c.Nivel >= 2 ? ToolTipIcon.Warning : ToolTipIcon.Info);
                    break;
                }
            // a central de inteligência pensa de novo a cada hora, com as medidas novas
            if (DateTime.Now >= proxPropostas)
            {
                proxPropostas = DateTime.Now.AddHours(1);
                if (ses == null) Abridor.Escondido(motor.Cfg, "conselheiro --exportar --sem-cor");
                else proxPropostas = DateTime.Now.AddMinutes(10);
            }
        }

        void TrocaIcone(string est)
        {
            if (est == estadoIcone) return;
            estadoIcone = est;
            Icon novo;
            if (est == "") novo = marcaPequena;
            else
            {
                Color c = est == "grave" ? Cor.Vermelho : est == "atencao" ? Cor.Ambar : est == "jogo" ? Cor.Verde : Cor.Apagado;
                var sz = SystemInformation.SmallIconSize;
                using (var bmp = marcaPequena.ToBitmap())
                using (var g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias;
                    float d = sz.Width * 0.46f;
                    var r = new RectangleF(sz.Width - d - 0.5f, sz.Height - d - 0.5f, d, d);
                    using (var b = new SolidBrush(Cor.Fundo)) g.FillEllipse(b, RectangleF.Inflate(r, 1.2f, 1.2f));
                    using (var b = new SolidBrush(c)) g.FillEllipse(b, r);
                    IntPtr h = bmp.GetHicon();
                    novo = Icon.FromHandle(h);
                    ni.Icon = novo;
                    if (iconeAtual != IntPtr.Zero) Nat.DestroyIcon(iconeAtual);
                    iconeAtual = h;
                    return;
                }
            }
            ni.Icon = novo;
            if (iconeAtual != IntPtr.Zero) { Nat.DestroyIcon(iconeAtual); iconeAtual = IntPtr.Zero; }
        }

        void Sai() { Sai(true); }

        void Sai(bool peloUsuario)
        {
            if (peloUsuario)
                try { File.WriteAllText(K.Arq("segundo-plano-fechado.txt"), K.Iso(DateTime.Now), Encoding.ASCII); } catch { }
            Log.Escreve("segundo plano desligado");
            motor.Para();
            ni.Visible = false; ni.Dispose();
            if (iconeAtual != IntPtr.Zero) Nat.DestroyIcon(iconeAtual);
            ExitThread();
        }
    }


    // ───────── modos de conferência: usados na publicação e para investigar um PC ─────────
    static class Testes
    {
        // lê o PC três vezes, 1 s entre elas, e grava tudo o que conseguiu (e o que não) num JSON
        public static int Diagnostico(string destino)
        {
            var cfg = Config.Le();
            var l = new Leitor();
            var r = new Dictionary<string, object>();
            var lista = new List<object>();
            for (int i = 0; i < 3; i++)
            {
                var a = l.Le(cfg, false);
                var d = new Dictionary<string, object>();
                foreach (var f in typeof(Amostra).GetFields()) { var v = f.GetValue(a); d[f.Name] = v is DateTime ? (object)K.Iso((DateTime)v) : v; }
                d["VramPct"] = a.VramPct;
                lista.Add(d);
                Thread.Sleep(1000);
            }
            r["versao"] = K.VERSAO; r["windows"] = Environment.OSVersion.VersionString; r["nucleos"] = Environment.ProcessorCount;
            var cats = new Dictionary<string, object>();
            foreach (var c in new[] { "Processor Information", "GPU Engine", "GPU Adapter Memory", "Network Interface", "Thermal Zone Information", "PhysicalDisk" })
            { try { cats[c] = PerformanceCounterCategory.Exists(c); } catch (Exception e) { cats[c] = "erro: " + e.Message; } }
            r["categorias"] = cats; r["leituras"] = lista;
            K.GravaAtomico(destino, new JavaScriptSerializer().Serialize(r));
            return 0;
        }

        // cria um bloco falso de cada programa, no layout que cada um publica, e confere se a leitura sai certa
        public static int TesteExternos(string destino)
        {
            var res = new List<string>(); bool ok = true;
            var mapas = new List<MemoryMappedFile>();
            Func<string, byte[], bool> cria = delegate (string nome, byte[] b)
            {
                try { var m = MemoryMappedFile.CreateNew(nome, b.Length); using (var v = m.CreateViewStream()) v.Write(b, 0, b.Length); mapas.Add(m); return true; }
                catch (Exception e) { res.Add(nome + ": não criei (" + e.Message + ")"); return false; }
            };
            Action<byte[], int, string> txt = delegate (byte[] b, int o, string t) { var x = Encoding.ASCII.GetBytes(t); Array.Copy(x, 0, b, o, x.Length); };
            // MSI Afterburner: CPU 67, GPU 71
            var ab = new byte[32 + 3 * 1324];
            BitConverter.GetBytes(0x4D41484Du).CopyTo(ab, 0); BitConverter.GetBytes(0x20000u).CopyTo(ab, 4); BitConverter.GetBytes(32u).CopyTo(ab, 8);
            BitConverter.GetBytes(3u).CopyTo(ab, 12); BitConverter.GetBytes(1324u).CopyTo(ab, 16);
            string[] nomes = { "GPU temperature", "CPU usage", "CPU temperature" }; float[] vals = { 71, 33, 67 };
            for (int i = 0; i < 3; i++) { txt(ab, 32 + i * 1324, nomes[i]); BitConverter.GetBytes(vals[i]).CopyTo(ab, 32 + i * 1324 + 1300); }
            bool temAb = cria("MAHMSharedMemory", ab);
            var r = new Externos.Leitura();
            if (temAb)
            {
                typeof(Externos).GetMethod("Afterburner", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { r });
                bool b1 = r.Cpu == 67 && r.Gpu == 71; ok &= b1; res.Add("Afterburner: CPU " + r.Cpu + ", GPU " + r.Gpu + (b1 ? " ok" : " ERRADO"));
            }
            // HWiNFO: sensor 0 CPU, sensor 1 GPU; leituras CPU Package 58, Core #0 61 (não é a do pacote), GPU Temperature 64
            int offS = 44, tamS = 264, offR = offS + 2 * tamS, tamR = 316;
            var hw = new byte[offR + 3 * tamR];
            BitConverter.GetBytes(0x53695748u).CopyTo(hw, 0);
            BitConverter.GetBytes((uint)offS).CopyTo(hw, 20); BitConverter.GetBytes((uint)tamS).CopyTo(hw, 24); BitConverter.GetBytes(2u).CopyTo(hw, 28);
            BitConverter.GetBytes((uint)offR).CopyTo(hw, 32); BitConverter.GetBytes((uint)tamR).CopyTo(hw, 36); BitConverter.GetBytes(3u).CopyTo(hw, 40);
            txt(hw, offS + 8, "CPU [#0]: Intel Core i7: DTS"); txt(hw, offS + tamS + 8, "GPU [#0]: NVIDIA GeForce");
            object[][] lr = { new object[] { 0u, "CPU Package", 58.0 }, new object[] { 0u, "Core #0", 61.0 }, new object[] { 1u, "GPU Temperature", 64.0 } };
            for (int i = 0; i < 3; i++)
            {
                int o = offR + i * tamR;
                BitConverter.GetBytes(1u).CopyTo(hw, o); BitConverter.GetBytes((uint)lr[i][0]).CopyTo(hw, o + 4);
                txt(hw, o + 12, (string)lr[i][1]); txt(hw, o + 268, "°C".Replace("°", "")); BitConverter.GetBytes((double)lr[i][2]).CopyTo(hw, o + 284);
            }
            if (cria("HWiNFO_SENS_SM2", hw))
            {
                r = new Externos.Leitura();
                typeof(Externos).GetMethod("HwInfo", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { r });
                bool b2 = r.Cpu == 58 && r.Gpu == 64; ok &= b2; res.Add("HWiNFO: CPU " + r.Cpu + ", GPU " + r.Gpu + (b2 ? " ok" : " ERRADO"));
            }
            // Core Temp: 2 núcleos, 52 e 57
            var ct = new byte[2700];
            BitConverter.GetBytes(2u).CopyTo(ct, 1536); BitConverter.GetBytes(1u).CopyTo(ct, 1540);
            BitConverter.GetBytes(52f).CopyTo(ct, 1544); BitConverter.GetBytes(57f).CopyTo(ct, 1548);
            if (cria("CoreTempMappingObjectEx", ct))
            {
                r = new Externos.Leitura();
                typeof(Externos).GetMethod("CoreTemp", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { r });
                bool b3 = r.Cpu == 57; ok &= b3; res.Add("Core Temp: CPU " + r.Cpu + (b3 ? " ok" : " ERRADO"));
            }
            // AIDA64
            var ai = Encoding.ASCII.GetBytes("<sys><id>SCPUCLK</id><label>CPU Clock</label><value>4300</value></sys><temp><id>TCPU</id><label>CPU</label><value>49</value></temp>" +
                                             "<temp><id>TGPU1DIO</id><label>GPU</label><value>66</value></temp>\0");
            if (cria("AIDA64_SensorValues", ai))
            {
                r = new Externos.Leitura();
                typeof(Externos).GetMethod("Aida", BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, new object[] { r });
                bool b4 = r.Cpu == 49 && r.Gpu == 66; ok &= b4; res.Add("AIDA64: CPU " + r.Cpu + ", GPU " + r.Gpu + (b4 ? " ok" : " ERRADO"));
            }
            foreach (var m in mapas) m.Dispose();
            File.WriteAllText(Path.GetFullPath(destino), string.Join("\n", res.ToArray()) + "\n", new UTF8Encoding(false));
            return ok && res.Count == 4 ? 0 : 4;
        }

        public static int Sensores(string destino)
        {
            var a = new Leitor().Le(Config.Le(), false);
            var d = new Dictionary<string, object>();
            d["quando"] = K.Iso(DateTime.Now); d["cpu"] = a.TempCpu; d["cpu_fonte"] = a.TempCpuFonte; d["gpu"] = a.TempGpu; d["gpu_fonte"] = a.TempGpuFonte;
            K.GravaAtomico(destino, new JavaScriptSerializer().Serialize(d));
            return 0;
        }

        // desenha o painel ao vivo com dados de exemplo num PNG, para conferir o visual sem abrir a bandeja
        public static int Foto(string destino)
        {
            Application.EnableVisualStyles();
            var m = new Motor();
            var rnd = new Random(7);
            var agora = DateTime.Now;
            for (int i = 0; i < 120; i++)
            {
                double f = i / 119.0;
                var a = new Amostra { Quando = agora.AddSeconds(i - 120), Cpu = 38 + 20 * Math.Sin(i / 9.0) + rnd.Next(8), NucleoMax = 70 + rnd.Next(20),
                    CpuDesempenho = 112, CpuGhz = 4.2, Gpu = 90 + rnd.Next(9), VramGb = 6.1 + f, VramTotalGb = 8, RamPct = 61 + 4 * f, RamGb = 9.8 + 0.6 * f, RamTotalGb = 16,
                    Disco = 4 + rnd.Next(10), DiscoLe = 2.1, DiscoGrava = 0.8, RedeBaixa = 0.4 + rnd.NextDouble(), RedeSobe = 0.05,
                    TempCpu = 68 + 6 * f + rnd.Next(2), TempCpuFonte = "LibreHardwareMonitor", TempGpu = 71 + 3 * f, TempGpuFonte = "driver de vídeo" };
                m.Historico.Add(a); m.Ultima = a;
            }
            m.Sessao = new Sessao { Jogo = "eldenring", Pid = 1, Inicio = agora.AddMinutes(-47), Ultimo = agora };
            m.Conclusoes = new List<Conclusao> {
                new Conclusao("gpu", 0, "A placa de vídeo é o limite agora", "Ela está em 97 % e a CPU sobra. O jogo roda o máximo que ela entrega; mais FPS vem de baixar resolução ou qualidade.", ""),
                new Conclusao("vram", 1, "Memória da placa de vídeo cheia", "7,9 de 8,0 GB. Baixe a qualidade das texturas: acima disso o jogo engasga.", "") };
            Icon marca = Marca.Carrega();
            var p = new PainelAoVivo(m, delegate (string[] x) { }, marca);
            p.PreparaFoto();
            using (var bmp = new Bitmap(p.Width, p.Height))
            {
                p.DrawToBitmap(bmp, new Rectangle(0, 0, p.Width, p.Height));
                bmp.Save(destino, System.Drawing.Imaging.ImageFormat.Png);
            }
            return 0;
        }
    }

    static class Programa
    {
        [STAThread]
        static int Main(string[] args)
        {
            var lista = new List<string>(args);
            if (lista.Contains("--teste-externos"))
            {
                try { int i = lista.IndexOf("--teste-externos"); return Testes.TesteExternos(i + 1 < lista.Count ? lista[i + 1] : K.Arq("teste-externos.txt")); }
                catch (Exception e) { Log.Escreve("teste externos: " + e); return 3; }
            }
            if (lista.Contains("--sensores"))
            {   // só a temperatura, rápido, para o Katharos (Python) usar no raio-x e no medir
                try
                {
                    int i = lista.IndexOf("--sensores");
                    return Testes.Sensores(i + 1 < lista.Count ? lista[i + 1] : K.Arq("sensores.json"));
                }
                catch (Exception e) { Log.Escreve("sensores: " + e); return 3; }
            }
            if (lista.Contains("--foto") || lista.Contains("--diagnostico"))
            {   // modos de conferência: nunca abrem janela (num servidor de testes ela travaria esperando um clique)
                try
                {
                    int i = lista.IndexOf("--foto");
                    if (i >= 0) return i + 1 < lista.Count ? Testes.Foto(lista[i + 1]) : 2;
                    i = lista.IndexOf("--diagnostico");
                    return Testes.Diagnostico(i + 1 < lista.Count ? lista[i + 1] : K.Arq("diagnostico-leitura.json"));
                }
                catch (Exception e) { Log.Escreve("conferência: " + e); return 3; }
            }
            try
            {
                if (lista.Contains("--parar-segundo-plano"))
                {
                    EventWaitHandle ev;
                    if (EventWaitHandle.TryOpenExisting(K.EV_SAIR, out ev)) { ev.Set(); ev.Dispose(); }
                    return 0;
                }
                if (lista.Contains("--segundo-plano"))
                {
                    bool novo;
                    using (var m = new Mutex(true, K.MUTEX, out novo))
                    {
                        if (!novo)
                        {   // já está rodando: só mostra o painel
                            EventWaitHandle ev;
                            if (!lista.Contains("--sem-painel") && EventWaitHandle.TryOpenExisting(K.EV_MOSTRAR, out ev)) { ev.Set(); ev.Dispose(); }
                            return 0;
                        }
                        try { Process.GetCurrentProcess().PriorityClass = ProcessPriorityClass.BelowNormal; } catch { }
                        Application.EnableVisualStyles();
                        Application.SetCompatibleTextRenderingDefault(false);
                        Application.ThreadException += delegate (object o, ThreadExceptionEventArgs e) { Log.Escreve("erro: " + e.Exception); };
                        Application.Run(new Bandeja(lista.Contains("--mostrar")));
                        m.ReleaseMutex();
                    }
                    return 0;
                }
                lista.Remove("--");
                return Abridor.Abre(lista);
            }
            catch (Exception e)
            {
                Log.Escreve("erro: " + e);
                MessageBox.Show("O Katharos encontrou um erro: " + e.Message + "\n\nDetalhes em " + K.Arq("segundo-plano.log"), "Katharos", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }
    }
}
