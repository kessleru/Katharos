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
//     /r:System.Windows.Forms.dll /r:System.Drawing.dll /r:System.Management.dll /r:System.Web.Extensions.dll /r:System.Core.dll /resource:regras.json,regras.json Katharos.cs
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
[assembly: AssemblyVersion("4.4.0.0")]
[assembly: AssemblyFileVersion("4.4.0.0")]

namespace KatharosApp
{
    static class K
    {
        public const string VERSAO = "4.4.0";
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
        public double AvisoCpu = Lim.G("calor_cpu"), AvisoGpu = Lim.G("calor_gpu");
        public bool Notificar = true;
        public bool Fps = true;
        // orçamento de avisos: no máximo um por tipo a cada N horas; no jogo, só o grave (calor), ou nada, ou tudo
        public double AvisosIntervaloH = 6; public string AvisosNoJogo = "so-grave";
        // notebook: plano de energia sozinho na tomada e na bateria (só se a pessoa ligou; os planos ela escolheu no Katharos)
        public bool EnergiaAuto; public Guid? EnergiaTomada, EnergiaBateria; public string EnergiaTomadaNome, EnergiaBateriaNome;
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
                c.Fps = Txt(d, "fps") != "nao";
                if (Dbl(d, "avisos_intervalo_h", out v) && v >= 1 && v <= 48) c.AvisosIntervaloH = v;
                string anj = Txt(d, "avisos_no_jogo"); if (anj == "nunca" || anj == "todos" || anj == "so-grave") c.AvisosNoJogo = anj;
                c.EnergiaAuto = Txt(d, "energia_auto") == "True" || Txt(d, "energia_auto") == "true";
                Guid g;
                if (Guid.TryParse(Txt(d, "energia_tomada") ?? "", out g)) c.EnergiaTomada = g;
                if (Guid.TryParse(Txt(d, "energia_bateria") ?? "", out g)) c.EnergiaBateria = g;
                c.EnergiaTomadaNome = Txt(d, "energia_tomada_nome"); c.EnergiaBateriaNome = Txt(d, "energia_bateria_nome");
                if (c.EnergiaTomada == null || c.EnergiaBateria == null) c.EnergiaAuto = false;
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
                    Inicia(PowerShell(), "-NoProfile -ExecutionPolicy Bypass -File " + K.Q(ps1) + (args.Count > 0 ? " " + K.Junta(args) : ""),
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

        // sempre o PowerShell do Windows, pelo caminho completo: um "powershell.exe" plantado na pasta do download nunca é o que roda
        public static string PowerShell()
        {
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), @"WindowsPowerShell\v1.0\powershell.exe");
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
        [DllImport("kernel32.dll")] public static extern ulong GetTickCount64();
        [StructLayout(LayoutKind.Sequential)] struct ULTIMA_ENTRADA { public uint cbSize; public uint dwTime; }
        [DllImport("user32.dll")] [return: MarshalAs(UnmanagedType.Bool)] static extern bool GetLastInputInfo(ref ULTIMA_ENTRADA u);
        // há quanto tempo ninguém mexe no teclado ou no mouse (só lê o relógio da última entrada; não vê o que foi digitado)
        public static double OciosoSegundos()
        {
            var u = new ULTIMA_ENTRADA(); u.cbSize = (uint)Marshal.SizeOf(typeof(ULTIMA_ENTRADA));
            if (!GetLastInputInfo(ref u)) return 0;
            return Math.Max(0, ((uint)Environment.TickCount - u.dwTime) / 1000.0);
        }
        // tempo de CPU do PRÓPRIO Katharos.exe: GetCurrentProcess devolve o pseudo-identificador de si mesmo (-1), nunca o de outro processo
        [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll")] [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool GetProcessTimes(IntPtr h, out long criacao, out long saida, out long nucleo, out long usuario);
        public static TimeSpan MeuTempoDeCpu()
        {
            long c, e, n, u;
            return GetProcessTimes(GetCurrentProcess(), out c, out e, out n, out u) ? TimeSpan.FromTicks(n + u) : TimeSpan.Zero;
        }

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

    // ───────── plano de energia ativo (o mesmo que escolher o plano no Painel de Controle) ─────────
    // Só troca qual plano está ativo; não muda nenhum valor dentro dos planos e não precisa de administrador.
    static class Energia
    {
        [DllImport("powrprof.dll")] static extern uint PowerGetActiveScheme(IntPtr raiz, out IntPtr guid);
        [DllImport("powrprof.dll")] static extern uint PowerSetActiveScheme(IntPtr raiz, ref Guid guid);
        [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr h);
        public static Guid? Ativo()
        {
            try
            {
                IntPtr p;
                if (PowerGetActiveScheme(IntPtr.Zero, out p) != 0 || p == IntPtr.Zero) return null;
                try { return (Guid)Marshal.PtrToStructure(p, typeof(Guid)); } finally { LocalFree(p); }
            }
            catch { return null; }
        }
        // devolve o código do Windows: 0 = feito; 2 = o plano não existe mais; outro = recusado (política, por exemplo)
        public static uint Ativa(Guid g)
        {
            try { return PowerSetActiveScheme(IntPtr.Zero, ref g); } catch { return 0xFFFFFFFF; }
        }
    }

    // ───────── todos os processos numa chamada só ─────────
    // NtQuerySystemInformation(SystemProcessInformation) é o que o próprio Process.GetProcesses e o Gerenciador de Tarefas usam por baixo:
    // devolve nome, PID, sessão, tempo de CPU e memória privada de cada processo de uma vez, sem abrir processo nenhum (sem handle, sem
    // memória de ninguém: seguro com anti-cheat). Custa poucos milissegundos. O contador "Process" do Monitor de Desempenho, que dava o
    // mesmo, custa dezenas a centenas de milissegundos por leitura e acorda o provedor de contadores do Windows: era o maior pico do ícone.
    class Processos
    {
        [DllImport("ntdll.dll")] static extern int NtQuerySystemInformation(int classe, IntPtr buf, int tam, out int precisa);
        const int SISTEMA_PROCESSOS = 5, TAMANHO_ERRADO = unchecked((int)0xC0000004);
        public struct P { public int Pid, Sessao; public string Nome; public double Cpu, Privada; }
        // o buffer fica guardado entre as leituras: nada de alocar 1 MB a cada 5 s (RAM sobra; o coletor de lixo agradece)
        IntPtr buf = IntPtr.Zero; int tam;
        readonly Dictionary<int, long[]> antes = new Dictionary<int, long[]>();   // pid → [criação, tempo de CPU] da leitura anterior
        long antesQuando;
        public bool Ok = true;

        public List<P> Le()
        {
            var lista = new List<P>();
            if (!Ok) return lista;
            try
            {
                int precisa = 0, st = TAMANHO_ERRADO;
                for (int tentativa = 0; tentativa < 6; tentativa++)
                {
                    if (buf == IntPtr.Zero || tam < precisa)
                    {
                        if (buf != IntPtr.Zero) Marshal.FreeHGlobal(buf);
                        tam = Math.Max(Math.Max(tam * 2, 1 << 20), precisa + (256 << 10));
                        buf = Marshal.AllocHGlobal(tam);
                    }
                    st = NtQuerySystemInformation(SISTEMA_PROCESSOS, buf, tam, out precisa);
                    if (st != TAMANHO_ERRADO) break;
                }
                if (st != 0) { Ok = false; return lista; }
                long agora = DateTime.UtcNow.Ticks, passou = antesQuando > 0 ? agora - antesQuando : 0;
                int nucleos = Math.Max(1, Environment.ProcessorCount);
                bool x64 = IntPtr.Size == 8;
                // deslocamentos de SYSTEM_PROCESS_INFORMATION (iguais do Windows Vista ao 11)
                int oNome = x64 ? 64 : 60, oPid = x64 ? 80 : 68, oSessao = x64 ? 100 : 80;
                var novo = new Dictionary<int, long[]>();
                int pos = 0;
                while (true)
                {
                    IntPtr e = new IntPtr(buf.ToInt64() + pos);
                    int prox = Marshal.ReadInt32(e, 0);
                    long privada = Marshal.ReadInt64(e, 8), criacao = Marshal.ReadInt64(e, 32);
                    long cpu = Marshal.ReadInt64(e, 40) + Marshal.ReadInt64(e, 48);
                    int len = Marshal.ReadInt16(e, 56) & 0xFFFF;
                    IntPtr pNome = Marshal.ReadIntPtr(e, oNome);
                    int pid = (int)Marshal.ReadIntPtr(e, oPid).ToInt64();
                    int sessao = Marshal.ReadInt32(e, oSessao);
                    string nome = pid == 0 ? "Idle" : (pNome != IntPtr.Zero && len > 0 ? Marshal.PtrToStringUni(pNome, len / 2) : "System");
                    if (nome.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)) nome = nome.Substring(0, nome.Length - 4);
                    novo[pid] = new[] { criacao, cpu };
                    double uso = 0; long[] ant;   // o mesmo PID com outra hora de criação é outro processo: não compara
                    if (passou > 0 && pid != 0 && antes.TryGetValue(pid, out ant) && ant[0] == criacao) uso = Math.Max(0, (cpu - ant[1]) * 100.0 / passou / nucleos);
                    lista.Add(new P { Pid = pid, Sessao = sessao, Nome = nome, Cpu = uso, Privada = privada });
                    if (prox <= 0 || pos + prox >= tam) break;
                    pos += prox;
                }
                antes.Clear(); foreach (var kv in novo) antes[kv.Key] = kv.Value;
                antesQuando = agora;
            }
            catch { Ok = false; }
            return lista;
        }
    }

    // ───────── quanto custa cada leitura ─────────
    // Mede o tempo de cada fonte a cada leitura. Fica no agora.json e no diagnóstico: é a prova de que o segundo plano é leve, e é o que
    // o freio de segurança usa (se a leitura ficar cara num PC, o ritmo se espaça sozinho, sem nunca travar nada).
    class Custo
    {
        readonly Stopwatch sw = Stopwatch.StartNew();
        public readonly Dictionary<string, double[]> Fontes = new Dictionary<string, double[]>();   // nome → [vezes, soma ms, maior ms]
        long t;
        int n;
        public void Comeca() { if (++n == 4) Fontes.Clear(); t = sw.ElapsedTicks; }   // as 3 primeiras leituras (carregando) não contam
        public void Marca(string nome)
        {
            long a = sw.ElapsedTicks; double ms = (a - t) * 1000.0 / Stopwatch.Frequency; t = a;
            double[] f; if (!Fontes.TryGetValue(nome, out f)) { f = new double[3]; Fontes[nome] = f; }
            f[0]++; f[1] += ms; f[2] = Math.Max(f[2] * 0.999, ms);
        }
        public Dictionary<string, object> Json()
        {
            var d = new Dictionary<string, object>();
            foreach (var kv in Fontes)
                d[kv.Key] = new Dictionary<string, object> { { "media_ms", Math.Round(kv.Value[1] / Math.Max(1, kv.Value[0]), 2) }, { "maior_ms", Math.Round(kv.Value[2], 1) } };
            return d;
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
        // contexto (2e): o que pode distorcer a medida
        public double? Fps;
        public double? UptimeH, RamSistemaGb, RamContaGb; public int? Processos; public string Manutencao, Top;
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
        readonly Processos lista = new Processos();
        Categoria procs;   // só se a chamada direta falhar (nunca visto): o contador do Monitor de Desempenho, mais caro, a cada 10 s
        DateTime proxCtx = DateTime.MinValue; string ctxManut, ctxTop; double? ctxRamSis, ctxRamConta;
        public readonly Custo Custo = new Custo();
        public bool Espacar;   // ritmo de 1 s: no máximo uma leitura pesada por vez
        public Dictionary<int, int> Sessoes = new Dictionary<int, int>();
        // o que, rodando, deixa a medida suja: atualização, Defender verificando, indexação, manutenção do Windows
        static readonly string[] MANUTENCAO = { "tiworker", "trustedinstaller", "mousocoreworker", "wuauclt", "usoclient", "msmpeng", "mpcmdrun",
            "searchindexer", "searchprotocolhost", "compattelrunner", "dismhost", "msiexec", "defrag", "cleanmgr", "sihclient" };
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
            // as leituras pesadas (WMI, nvidia-smi, arquivo) nunca caem todas no mesmo instante: no ritmo de 1 s, uma por vez
            bool pesada = false;
            Custo.Comeca();
            var c = cpuTotal.Le(); if (c.HasValue) a.Cpu = Math.Min(100, c.Value);
            double nm = -1;
            foreach (var n in nucleos) { var v = n.Le(); if (v.HasValue && v.Value > nm) nm = v.Value; }
            if (nm >= 0) a.NucleoMax = Math.Min(100, nm);
            var d = cpuDesemp.Le();
            if (d.HasValue && d.Value > 0) { a.CpuDesempenho = d.Value; if (baseMhz > 0) a.CpuGhz = baseMhz * d.Value / 100.0 / 1000.0; }
            Custo.Marca("cpu");

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
            Custo.Marca("ram");

            var oc = discoOcioso.Le(); if (oc.HasValue) a.Disco = Math.Max(0, Math.Min(100, 100 - oc.Value));
            var dl = discoLe.Le(); if (dl.HasValue) a.DiscoLe = dl.Value / 1048576.0;
            var dg = discoGrava.Le(); if (dg.HasValue) a.DiscoGrava = dg.Value / 1048576.0;

            Custo.Marca("disco");
            var rr = rede.Le("Bytes Received/sec", "Bytes Sent/sec");
            if (rr.ContainsKey("Bytes Received/sec") && rr["Bytes Received/sec"].Count > 0)
            {
                double baixa = 0, sobe = 0;
                foreach (var v in rr["Bytes Received/sec"].Values) baixa += v;
                foreach (var v in rr["Bytes Sent/sec"].Values) sobe += v;
                a.RedeBaixa = baixa / 1048576.0; a.RedeSobe = sobe / 1048576.0;
            }

            Custo.Marca("rede");
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
            Custo.Marca("gpu");
            var gm = gpuMem.Le("Dedicated Usage");
            if (gm.ContainsKey("Dedicated Usage") && gm["Dedicated Usage"].Count > 0)
            {
                double max = 0; foreach (var v in gm["Dedicated Usage"].Values) if (v > max) max = v;
                a.VramGb = max / 1073741824.0;
                a.VramTotalGb = vramTotal;
            }

            Custo.Marca("vram");
            // temperatura: do mais certo para o mais pobre, e diz de onde veio
            if (lhmExiste && agora >= proxLhm && !pesada) { pesada = Espacar; proxLhm = agora.AddSeconds(3); LeLhm(); Custo.Marca("temperatura LibreHardwareMonitor"); }
            if (d3dExiste && agora >= proxD3d) { proxD3d = agora.AddSeconds(2); d3dGpu = Nat.TemperaturaGpu(); if (!d3dGpu.HasValue) { d3dExiste = false; } }
            if (agora >= proxExt) { proxExt = agora.AddSeconds(2); ext = Externos.Le(); }
            Custo.Marca("temperatura");
            if (lhmCpu.HasValue) { a.TempCpu = lhmCpu; a.TempCpuFonte = lhmFonte; }
            else if (ext != null && ext.Cpu.HasValue) { a.TempCpu = ext.Cpu; a.TempCpuFonte = ext.CpuFonte; }
            if (lhmGpu.HasValue) { a.TempGpu = lhmGpu; a.TempGpuFonte = lhmFonte; }
            else if (ext != null && ext.Gpu.HasValue) { a.TempGpu = ext.Gpu; a.TempGpuFonte = ext.GpuFonte; }
            else if (d3dGpu.HasValue) { a.TempGpu = d3dGpu; a.TempGpuFonte = "driver de vídeo"; }
            else if (smiExiste && !emJogo && agora >= proxSmi && !pesada) { pesada = Espacar; proxSmi = agora.AddSeconds(15); LeSmi(); Custo.Marca("temperatura nvidia-smi"); }
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
            Custo.Marca("temperatura (zona térmica)");
            if (agora >= proxUltima && !pesada) { pesada = Espacar; proxUltima = agora.AddSeconds(60); LeUltima(); Custo.Marca("temperatura do Katharos"); }
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
            Custo.Marca("bateria e janela");
            // processos: nomes (jogo, anti-cheat), sessão e quem está usando a CPU, numa chamada só a cada 5 s
            if (agora >= proxProc && !pesada)
            {
                pesada = Espacar; proxProc = agora.AddSeconds(5);
                if (lista.Ok) { LeProcessos(); try { JuntaRam(); } catch (Exception e) { Falha("ram por programa", e); } }
                if (!lista.Ok)
                {
                    LeNomes();
                    if (agora >= proxCtx) { proxCtx = agora.AddSeconds(10); LeContexto(); }
                }
                Custo.Marca("processos");
            }
            foreach (var n in cfg.NomesJogo) if (NomesVistos.Contains(n)) { a.AntiCheat = true; break; }
            try { a.UptimeH = Nat.GetTickCount64() / 3600000.0; } catch (Exception e) { Falha("tempo ligado", e); }
            a.Processos = Nomes.Count;
            a.Manutencao = ctxManut; a.Top = ctxTop; a.RamSistemaGb = ctxRamSis; a.RamContaGb = ctxRamConta;
            return a;
        }

        // cada fonte que falha é anotada uma vez no log; as outras continuam
        readonly HashSet<string> falhas = new HashSet<string>();
        void Falha(string fonte, Exception e)
        {
            if (falhas.Add(fonte)) Log.Escreve("leitura de " + fonte + " falhou: " + e.GetType().Name + ": " + e.Message);
        }

        // só os nomes e a sessão: GetProcesses lê a lista do sistema, não abre processo nenhum
        void LeNomes()
        {
            var nomes = new Dictionary<int, string>(); var vistos = new HashSet<string>(); var sess = new Dictionary<int, int>();
            try
            {
                foreach (var p in Process.GetProcesses())
                {
                    try { string n = p.ProcessName; nomes[p.Id] = n; vistos.Add(n.ToLowerInvariant()); sess[p.Id] = p.SessionId; } catch { }
                    p.Dispose();
                }
            }
            catch { }
            Nomes = nomes; NomesVistos = vistos; Sessoes = sess;
        }

        // a lista inteira numa chamada: nomes, sessões, CPU e memória privada de cada processo (ver a classe Processos)
        void LeProcessos()
        {
            var l = lista.Le();
            if (!lista.Ok || l.Count == 0) { if (lista.Ok) lista.Ok = false; Falha("processos (chamada direta)", new Exception("sem dados; usando o contador do Windows")); return; }
            var nomes = new Dictionary<int, string>(l.Count); var vistos = new HashSet<string>(); var sess = new Dictionary<int, int>(l.Count);
            double sis = 0, conta = 0; var manut = new List<string>(); var top = new List<KeyValuePair<string, double>>();
            var ram = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
            foreach (var p in l)
            {
                nomes[p.Pid] = p.Nome; sess[p.Pid] = p.Sessao;
                string n = p.Nome.ToLowerInvariant(); vistos.Add(n);
                if (p.Pid == 0) continue;
                // RAM por programa: o Chrome com as abas (todos os chrome.exe) vira um só
                double ja; ram.TryGetValue(p.Nome, out ja); ram[p.Nome] = ja + p.Privada;
                if (p.Sessao > 0) conta += p.Privada; else sis += p.Privada;
                if (p.Cpu >= 3 && Array.IndexOf(MANUTENCAO, n) >= 0 && !manut.Contains(p.Nome)) manut.Add(p.Nome);
                if (p.Cpu >= 1) top.Add(new KeyValuePair<string, double>(p.Nome, p.Cpu));
            }
            Nomes = nomes; NomesVistos = vistos; Sessoes = sess;
            Contexto(sis, conta, manut, top);
            ramPorPrograma = ram;   // a mesma linha de leitura grava e lê: sem trava
        }

        // a última RAM por programa (de 10 em 10 s) e o pico do minuto; uma linha por minuto em ram.jsonl, com os 15 maiores
        Dictionary<string, double> ramPorPrograma, ramPicoMinuto = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
        DateTime proxRam = DateTime.Now.AddMinutes(1);
        void JuntaRam()
        {
            var r = ramPorPrograma;
            if (r == null) return;
            foreach (var kv in r) { double v; if (!ramPicoMinuto.TryGetValue(kv.Key, out v) || kv.Value > v) ramPicoMinuto[kv.Key] = kv.Value; }
            if (DateTime.Now < proxRam) return;
            proxRam = DateTime.Now.AddMinutes(1);
            var l = new List<KeyValuePair<string, double>>(ramPicoMinuto);
            l.Sort(delegate (KeyValuePair<string, double> x, KeyValuePair<string, double> y) { return y.Value.CompareTo(x.Value); });
            var top = new List<object>();
            foreach (var kv in l) { if (top.Count >= 15) break; top.Add(new object[] { kv.Key, Math.Round(kv.Value / 1048576.0, 0) }); }
            var d = new Dictionary<string, object>();
            d["t"] = K.Iso(DateTime.Now); d["p"] = top;
            // pressão de verdade: o quanto da memória total (RAM + arquivo de paginação) está prometido, e a memória comprimida
            try
            {
                var m = new Nat.MEMSTAT();
                if (Nat.GlobalMemoryStatusEx(m) && m.ullTotalPageFile > 0) d["commit_pct"] = Math.Round(100.0 * (m.ullTotalPageFile - m.ullAvailPageFile) / m.ullTotalPageFile, 1);
            }
            catch { }
            double comp; if (r.TryGetValue("Memory Compression", out comp)) d["comprimida_mb"] = Math.Round(comp / 1048576.0, 0);
            ramPicoMinuto = new Dictionary<string, double>(StringComparer.OrdinalIgnoreCase);
            Motor.Acrescenta("ram.jsonl", new JavaScriptSerializer().Serialize(d));
        }

        void Contexto(double sis, double conta, List<string> manut, List<KeyValuePair<string, double>> top)
        {
            top.Sort(delegate (KeyValuePair<string, double> x, KeyValuePair<string, double> y) { return y.Value.CompareTo(x.Value); });
            var t5 = new List<string>(); foreach (var t in top) { if (t5.Count >= 5) break; t5.Add(t.Key + " " + Math.Round(t.Value, 0).ToString(K.INV) + "%"); }
            ctxManut = manut.Count > 0 ? string.Join(", ", manut.ToArray()) : null;
            ctxTop = t5.Count > 0 ? string.Join(", ", t5.ToArray()) : null;
            ctxRamSis = sis / 1073741824.0; ctxRamConta = conta / 1073741824.0;
        }

        // reserva: contadores por processo (o mesmo do Monitor de Desempenho): CPU e memória privada de cada um, sem abrir processo nenhum.
        // Separa a RAM dos serviços do Windows (sessão 0) da RAM da sua conta, e acha quem está fazendo manutenção agora.
        void LeContexto()
        {
            try
            {
                if (procs == null) procs = new Categoria("Process");
                var c = procs.Le("% Processor Time", "Working Set - Private", "ID Process");
                if (!c.ContainsKey("ID Process") || c["ID Process"].Count == 0) return;
                var cpu = c["% Processor Time"]; var ws = c["Working Set - Private"]; int nucleos = Math.Max(1, Environment.ProcessorCount);
                double sis = 0, conta = 0; var manut = new List<string>(); var top = new List<KeyValuePair<string, double>>();
                foreach (var kv in c["ID Process"])
                {
                    string inst = kv.Key; int pid = (int)kv.Value;
                    if (inst == "_Total" || inst == "Idle" || pid == 0) continue;
                    string nome = inst; int h = nome.IndexOf('#'); if (h > 0) nome = nome.Substring(0, h);
                    double w; if (ws.TryGetValue(inst, out w)) { int se; if (Sessoes.TryGetValue(pid, out se) && se > 0) conta += w; else sis += w; }
                    double u; if (!cpu.TryGetValue(inst, out u)) continue;
                    u = u / nucleos;
                    if (u >= 3 && Array.IndexOf(MANUTENCAO, nome.ToLowerInvariant()) >= 0 && !manut.Contains(nome)) manut.Add(nome);
                    if (u >= 1) top.Add(new KeyValuePair<string, double>(nome, u));
                }
                Contexto(sis, conta, manut, top);
            }
            catch (Exception e) { Falha("contexto", e); }
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

    // ───────── limites do motor: uma fonte só (REGRAS_MOTOR no Python) ─────────
    // A montagem grava exe/regras.json (embutido aqui); o Katharos grava ~/.katharos/regras.json, que vale por cima (versão nova sem
    // recompilar). Nenhum limite fica escrito neste arquivo: um teste confere.
    static class Lim
    {
        static Dictionary<string, double> v = new Dictionary<string, double>();
        static DateTime lido = DateTime.MinValue;

        static void Carrega()
        {
            var novo = new Dictionary<string, double>();
            Action<string> junta = delegate (string json)
            {
                var d = new JavaScriptSerializer().DeserializeObject(json) as Dictionary<string, object>;
                if (d == null) return;
                foreach (var kv in d)
                {
                    double x;
                    if (kv.Value != null && double.TryParse(Convert.ToString(kv.Value, K.INV), NumberStyles.Float, K.INV, out x)) novo[kv.Key] = x;
                }
            };
            try
            {
                var st = Assembly.GetExecutingAssembly().GetManifestResourceStream("regras.json");
                if (st != null) using (var r = new StreamReader(st, Encoding.UTF8)) junta(r.ReadToEnd());
            }
            catch (Exception e) { Log.Escreve("regras embutidas: " + e.Message); }
            try { string arq = K.Arq("regras.json"); if (File.Exists(arq)) junta(File.ReadAllText(arq, Encoding.UTF8)); }
            catch (Exception e) { Log.Escreve("regras.json: " + e.Message); }
            v = novo; lido = DateTime.Now;
        }

        public static double G(string chave)
        {
            if ((DateTime.Now - lido).TotalSeconds > 60) Carrega();
            double x; return v.TryGetValue(chave, out x) ? x : double.NaN;   // NaN: toda comparação dá falso (nada de alarme sem regra)
        }
    }

    static class Regras
    {
        // os mesmos critérios contam o tempo de cada limite na sessão de jogo e geram as conclusões de agora
        public static readonly string[] MARCAS = { "gpu", "cpu", "freio", "ram", "vram", "disco", "calor" };

        public static bool Marca(string m, Amostra a, Config c)
        {
            switch (m)
            {
                case "gpu": return a.Gpu >= Lim.G("gpu_limite") && a.NucleoMax < Lim.G("gpu_nucleo_folga");
                case "cpu": return a.NucleoMax >= Lim.G("cpu_nucleo_limite") && a.Gpu.HasValue && a.Gpu < Lim.G("cpu_gpu_folga");
                case "freio": return a.CpuDesempenho.HasValue && a.CpuDesempenho < Lim.G("freio_desempenho") && a.Cpu >= Lim.G("freio_cpu_min");
                case "ram": return a.RamPct >= Lim.G("ram_cheia");
                case "vram": return a.VramPct >= Lim.G("vram_cheia");
                case "disco": return a.Disco >= Lim.G("disco_cheio");
                case "calor": return a.TempCpu >= c.AvisoCpu || a.TempGpu >= c.AvisoGpu;
            }
            return false;
        }

        public static List<Conclusao> Agora(List<Amostra> janela, Config c, bool emJogo)
        {
            var r = new List<Conclusao>();
            if (janela.Count < Lim.G("janela_min_leituras")) return r;
            var ult = janela[janela.Count - 1];
            Func<string, double> frac = delegate (string m) { int n = 0; foreach (var a in janela) if (Marca(m, a, c)) n++; return (double)n / janela.Count; };
            if (frac("calor") >= Lim.G("fracao_calor"))
            {
                bool cpu = ult.TempCpu >= c.AvisoCpu;
                r.Add(new Conclusao("calor", 2, "PC quente",
                    (cpu ? "CPU em " + K.Num(ult.TempCpu, 0) + " °C" : "Placa de vídeo em " + K.Num(ult.TempGpu, 0) + " °C") +
                    ". Acima disso o chip reduz a velocidade para se proteger. Confira ventoinha e poeira.", "painel"));
            }
            if (frac("freio") >= Lim.G("fracao_freio"))
                r.Add(new Conclusao("freio", 1, "CPU abaixo da velocidade normal",
                    "Com carga, ela está rodando a " + K.Num(ult.CpuDesempenho, 0) + " % da frequência normal" +
                    (ult.NaBateria ? ": é a economia da bateria. Na tomada ela volta." : ": calor ou plano de energia economizando."), ult.NaBateria ? "" : "energia"));
            if (emJogo)
            {
                if (frac("gpu") >= Lim.G("fracao_gargalo"))
                    r.Add(new Conclusao("gpu", 0, "A placa de vídeo é o limite agora",
                        "Ela está em " + K.Num(ult.Gpu, 0) + " % e a CPU sobra. O jogo roda o máximo que ela entrega; mais FPS vem de baixar resolução ou qualidade.", ""));
                else if (frac("cpu") >= Lim.G("fracao_gargalo"))
                    r.Add(new Conclusao("cpu", 1, "A CPU segura o jogo",
                        "Um núcleo está em " + K.Num(ult.NucleoMax, 0) + " % e a placa de vídeo sobra (" + K.Num(ult.Gpu, 0) + " %). Feche o que roda em segundo plano; o modo extremo do turbo ajuda.", "turbo"));
                if (frac("vram") >= Lim.G("fracao_vram"))
                    r.Add(new Conclusao("vram", 1, "Memória da placa de vídeo cheia",
                        K.Num(ult.VramGb, 1) + " de " + K.Num(ult.VramTotalGb, 1) + " GB. Baixe a qualidade das texturas: acima disso o jogo engasga.", ""));
            }
            else if (ult.Cpu >= Lim.G("cpu_ocupada") && frac("cpu") < Lim.G("fracao_gargalo"))
            {
                int n = 0; foreach (var a in janela) if (a.Cpu >= Lim.G("cpu_ocupada")) n++;
                if (n >= janela.Count * Lim.G("fracao_cpu_ocupada"))
                    r.Add(new Conclusao("cpu-ocupada", 1, "Algo mantém a CPU ocupada", "CPU em " + K.Num(ult.Cpu, 0) + " % sem jogo aberto. O raio-x mostra quem é.", "raiox"));
            }
            if (frac("ram") >= Lim.G("fracao_ram"))
                r.Add(new Conclusao("ram", 1, "RAM quase cheia",
                    K.Num(ult.RamGb, 1) + " de " + K.Num(ult.RamTotalGb, 1) + " GB em uso. O Windows passa a usar o disco no lugar e tudo fica mais lento.", "memoria"));
            if (frac("disco") >= Lim.G("fracao_disco"))
                r.Add(new Conclusao("disco", 1, "Disco ocupado o tempo todo",
                    "Em " + K.Num(ult.Disco, 0) + " %. Jogos e programas esperam por ele: travadas curtas vêm daqui.", "raiox"));
            r.Sort(delegate (Conclusao x, Conclusao y) { return y.Nivel.CompareTo(x.Nivel); });
            return r;
        }
    }

    // ───────── FPS de verdade (fase 2c): PresentMon, da Intel, só durante a sessão de jogo ─────────
    // O PresentMon lê os eventos de apresentação de quadros do próprio Windows (ETW), como o FrameView e o CapFrameX: não abre, não lê
    // e não injeta nada no jogo. Precisa que o usuário esteja no grupo "Usuários de log de desempenho" (o Katharos pede e explica antes).
    class Fps
    {
        Process proc; Thread fio;
        readonly object trava = new object();
        readonly int[] hist = new int[4000];          // tempo de quadro em décimos de ms, até 400 ms
        readonly Queue<KeyValuePair<DateTime, double>> recentes = new Queue<KeyValuePair<DateTime, double>>();
        readonly Queue<double> janela = new Queue<double>();   // últimos 60 quadros, para achar travada
        double somaJanela; long frames; double somaMs; int travadas; DateTime inicio;
        public string Estado = "";   // "" | "medindo" | "sem permissão" | "sem PresentMon" | "PresentMon alterado" | "erro"
        // por minuto
        long framesMin; double somaMsMin; double piorSegMin = double.MaxValue;

        // A impressão digital do PresentMon que vem no zip (v2.6.0 da Intel). Antes de rodar, o Katharos confere: um PresentMon trocado
        // (por um programa malicioso ou arquivo corrompido) não roda. O workflow confere o download contra este mesmo valor.
        public const string PRESENTMON_SHA256 = "b2a706bc6ad475749e3b7e3409263aa1e6906d45bdcf993f6dbc0f660188f1af";
        static string conferido;   // "caminho|tamanho|data" do arquivo já conferido (não recalcula a cada jogo)

        public static bool Confere(string exe)
        {
            try
            {
                var fi = new FileInfo(exe);
                string chave = fi.FullName + "|" + fi.Length + "|" + fi.LastWriteTimeUtc.Ticks;
                if (chave == conferido) return true;
                string h;
                using (var f = File.OpenRead(exe)) using (var sha = System.Security.Cryptography.SHA256.Create())
                    h = BitConverter.ToString(sha.ComputeHash(f)).Replace("-", "").ToLowerInvariant();
                if (h != PRESENTMON_SHA256) { Log.Escreve("PresentMon com impressão digital diferente da esperada (" + h + "): não vou rodar"); return false; }
                conferido = chave;
                return true;
            }
            catch (Exception e) { Log.Escreve("PresentMon: não consegui conferir: " + e.Message); return false; }
        }

        public static string Caminho()
        {
            string a = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "PresentMon.exe");
            if (File.Exists(a)) return a;
            a = K.Arq("PresentMon.exe");
            return File.Exists(a) ? a : null;
        }

        public void Inicia(int pid)
        {
            Para();
            string exe = Caminho();
            if (exe == null) { Estado = "sem PresentMon"; return; }
            if (!Confere(exe)) { Estado = "PresentMon alterado"; return; }
            lock (trava)
            {
                Array.Clear(hist, 0, hist.Length); recentes.Clear(); janela.Clear(); somaJanela = 0; frames = 0; somaMs = 0; travadas = 0;
                inicio = DateTime.Now; framesMin = 0; somaMsMin = 0; piorSegMin = double.MaxValue;
            }
            try
            {
                var p = new ProcessStartInfo(exe, "--process_id " + pid.ToString(K.INV) + " --output_stdout --no_console_stats --stop_existing_session --session_name KatharosFPS");
                p.UseShellExecute = false; p.CreateNoWindow = true; p.RedirectStandardOutput = true; p.RedirectStandardError = true;
                proc = Process.Start(p);
                try { proc.PriorityClass = ProcessPriorityClass.BelowNormal; } catch { }
                Estado = "medindo";
                var meu = proc;
                fio = new Thread(delegate () { Le(meu); }) { IsBackground = true, Priority = ThreadPriority.BelowNormal };
                fio.Start();
                new Thread(delegate ()
                {
                    try
                    {
                        string erro = meu.StandardError.ReadToEnd();
                        if (erro.IndexOf("access denied", StringComparison.OrdinalIgnoreCase) >= 0 || erro.IndexOf("acesso negado", StringComparison.OrdinalIgnoreCase) >= 0)
                        { Estado = "sem permissão"; Log.Escreve("FPS: sem permissão (usuário fora do grupo Usuários de log de desempenho)"); }
                        else if (erro.Trim().Length > 0) Log.Escreve("FPS: " + erro.Trim().Split('\n')[0]);
                    }
                    catch { }
                }) { IsBackground = true }.Start();
            }
            catch (Exception e) { Estado = "erro"; Log.Escreve("FPS: " + e.Message); }
        }

        void Le(Process p)
        {
            try
            {
                int col = -1; string linha;
                while ((linha = p.StandardOutput.ReadLine()) != null)
                {
                    var c = linha.Split(',');
                    if (col < 0) { col = Array.IndexOf(c, "MsBetweenPresents"); continue; }
                    double ms;
                    if (col >= c.Length || !double.TryParse(c[col], NumberStyles.Float, K.INV, out ms) || ms <= 0 || ms > 5000) continue;
                    Soma(ms);
                }
            }
            catch { }
        }

        public void SomaParaTeste(double ms) { lock (trava) { if (inicio == DateTime.MinValue) inicio = DateTime.Now.AddMinutes(-1); } Soma(ms); }

        void Soma(double ms)
        {
            lock (trava)
            {
                frames++; somaMs += ms; framesMin++; somaMsMin += ms;
                hist[Math.Min(hist.Length - 1, (int)(ms * 10))]++;
                if (janela.Count >= 20 && ms > 2 * somaJanela / janela.Count && ms > 25) travadas++;   // quadro 2x mais lento que o normal recente
                janela.Enqueue(ms); somaJanela += ms; if (janela.Count > 60) somaJanela -= janela.Dequeue();
                var agora = DateTime.Now;
                recentes.Enqueue(new KeyValuePair<DateTime, double>(agora, ms));
                while (recentes.Count > 0 && (agora - recentes.Peek().Key).TotalSeconds > 1) recentes.Dequeue();
            }
        }

        public double? Agora()
        {
            lock (trava)
            {
                if (recentes.Count < 2) return null;
                double soma = 0; foreach (var r in recentes) soma += r.Value;
                double f = 1000.0 * recentes.Count / soma;
                if (f < piorSegMin) piorSegMin = f;
                return f;
            }
        }

        // média do tempo de quadro dos `fracao` (ex.: 1 %) quadros mais lentos: é o "1% low" dos medidores de jogo (CapFrameX, FrameView)
        double MediaDosPiores(double fracao)
        {
            long alvo = Math.Max(1, (long)Math.Ceiling(frames * fracao)), conta = 0; double soma = 0;
            for (int i = hist.Length - 1; i >= 0 && conta < alvo; i--)
            {
                long usa = Math.Min(hist[i], alvo - conta);
                conta += usa; soma += usa * (i + 0.5) / 10.0;
            }
            return soma / Math.Max(1, conta);
        }

        public Dictionary<string, object> Resumo()
        {
            lock (trava)
            {
                if (frames < 100) return null;
                var d = new Dictionary<string, object>();
                d["fps_med"] = Math.Round(1000.0 * frames / somaMs, 1);
                d["fps_1low"] = Math.Round(1000.0 / MediaDosPiores(0.01), 1);
                d["fps_01low"] = Math.Round(1000.0 / MediaDosPiores(0.001), 1);
                double min = Math.Max(1, (DateTime.Now - inicio).TotalMinutes);
                d["travadas_por_min"] = Math.Round(travadas / min, 2);
                d["frames"] = frames;
                return d;
            }
        }

        public Dictionary<string, object> FechaMinuto()
        {
            lock (trava)
            {
                if (framesMin < 30) { framesMin = 0; somaMsMin = 0; piorSegMin = double.MaxValue; return null; }
                var d = new Dictionary<string, object>();
                d["fps"] = Math.Round(1000.0 * framesMin / somaMsMin, 1);
                if (piorSegMin < double.MaxValue) d["fps_pior_seg"] = Math.Round(piorSegMin, 1);
                framesMin = 0; somaMsMin = 0; piorSegMin = double.MaxValue;
                return d;
            }
        }

        public void Para()
        {
            var p = proc; proc = null;
            if (p != null) { try { if (!p.HasExited) p.Kill(); } catch { } try { p.Dispose(); } catch { } }   // só o PresentMon que o Katharos abriu
            if (Estado == "medindo") Estado = "";
        }
    }

    class Sessao
    {
        public string Jogo; public int Pid; public DateTime Inicio, Ultimo;
        public int N; double sCpu, sGpu, sNuc, sRam; double mCpu, mGpu, mNuc, mRam, mVram, mTc = -1, mTg = -1; double mDesemp = 1000;
        public readonly Dictionary<string, int> Marcas = new Dictionary<string, int>();
        public Dictionary<string, object> FpsResumo;

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
            string melhor = "equilibrado"; double fm = Lim.G("sessao_principal_min");
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
            if (FpsResumo != null) foreach (var kv in FpsResumo) d[kv.Key] = kv.Value;
            return d;
        }
    }

    class Minuto
    {
        public DateTime Inicio; int n; double sCpu, sGpu, sRam, sDisco, sRede; double mCpu, mGpu, mNuc, mTc = -1, mTg = -1, mVram; double mDesemp = 1000; public string Jogo;
        public Dictionary<string, object> FpsMin;
        public double EuCpu;
        int nManut, nBat, nProc; double sProc, sRamSis, sRamConta, minUp = double.MaxValue; int nRamSis; readonly HashSet<string> manut = new HashSet<string>();
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
            if (a.Manutencao != null) { nManut++; foreach (var x in a.Manutencao.Split(',')) manut.Add(x.Trim()); }
            if (a.NaBateria) nBat++;
            if (a.Processos.HasValue) { sProc += a.Processos.Value; nProc++; }
            if (a.RamSistemaGb.HasValue) { sRamSis += a.RamSistemaGb.Value; sRamConta += a.RamContaGb ?? 0; nRamSis++; }
            if (a.UptimeH.HasValue) minUp = Math.Min(minUp, a.UptimeH.Value);
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
            // contexto: o que pode distorcer este minuto. "sujo" = manutenção do Windows rodando em boa parte dele ou logo depois do boot;
            // fica guardado, mas a linha de base e as comparações não usam
            if (nProc > 0) d["processos"] = Math.Round(sProc / nProc, 0);
            if (nRamSis > 0) { d["ram_sistema_gb"] = Math.Round(sRamSis / nRamSis, 2); d["ram_conta_gb"] = Math.Round(sRamConta / nRamSis, 2); }
            if (minUp < double.MaxValue) d["ligado_h"] = Math.Round(minUp, 2);
            if (manut.Count > 0) d["manutencao"] = string.Join(", ", new List<string>(manut).ToArray());
            if (nBat > n / 2) d["bateria"] = true;
            if (FpsMin != null) foreach (var kv in FpsMin) d[kv.Key] = kv.Value;
            d["katharos_cpu"] = Math.Round(EuCpu, 2);   // o quanto o próprio segundo plano pesou neste minuto
            if (nManut * 3 >= n || (minUp < double.MaxValue && minUp * 60 < Lim.G("minutos_depois_do_boot"))) d["sujo"] = true;
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
        public readonly Fps Fps = new Fps();
        public List<Conclusao> Conclusoes = new List<Conclusao>();
        public bool Pausado;
        public DateTime Desde = DateTime.Now;
        Minuto minuto;
        int candidatoPid; DateTime candidatoDesde, semJogoDesde = DateTime.MaxValue;
        // a rotação dos arquivos (ler e regravar até alguns MB) espera o PC terminar de ligar
        DateTime proxCfg = DateTime.Now.AddSeconds(30), proxRotacao = DateTime.Now.AddMinutes(5);
        // custo do próprio segundo plano: tempo de cada passo, CPU e RAM do Katharos.exe
        readonly Stopwatch relogio = new Stopwatch();
        public double PassoMedioMs, PassoMaiorMs; int nPassos; volatile int esperaMs = 1000;
        public double EuCpuPct, EuRamMb; TimeSpan euCpuAntes; DateTime euAntes = DateTime.MinValue, proxEu = DateTime.MinValue;
        bool avisouLento; DateTime proxPausa = DateTime.MinValue;
        // energia: o último lado visto (tomada ou bateria) e se o "manter desempenho" estava valendo; o aviso vai para o ícone
        string energiaLado; public string EnergiaAviso; public bool EnergiaAvisoErro;
        // o que foi pedido e se o Windows ficou mesmo assim: nunca dizer "feito" sem ler de volta (sem falso positivo)
        Guid? energiaAlvo; string energiaAlvoNome; DateTime energiaConfere = DateTime.MaxValue; string energiaParou;
        public string EnergiaEstado = "", EnergiaErro; public DateTime? EnergiaConferidaEm;
        readonly JavaScriptSerializer json = new JavaScriptSerializer();
        public Leitor Leitor { get { return leitor; } }
        public event Action Atualizou;
        public event Action SessaoFechou;
        public readonly object Trava = new object();
        volatile bool parar;

        public void Roda()
        {
            Thread.CurrentThread.Priority = ThreadPriority.BelowNormal;
            Thread.Sleep(300);
            while (!parar)
            {
                relogio.Restart();
                try { leitor.Espacar = Cfg.IntervaloMs < 2000; Passo(); }
                catch (Exception e) { Log.Escreve("leitura: " + e); }
                double ms = relogio.Elapsed.TotalMilliseconds;
                // as 3 primeiras leituras carregam o programa e as fontes (mais lentas, uma vez só): não contam
                nPassos++;
                if (nPassos == 4) { PassoMedioMs = ms; PassoMaiorMs = ms; }
                else if (nPassos > 4) { PassoMedioMs = PassoMedioMs * 0.95 + ms * 0.05; PassoMaiorMs = Math.Max(PassoMaiorMs * 0.999, ms); }   // o maior recente (esquece devagar)
                // freio de segurança: a leitura nunca ocupa mais que 1/10 do tempo. Num PC em que ela fique cara (muitos processos, driver
                // lento), o ritmo se espaça sozinho em vez de pesar; volta ao normal quando o custo cai.
                int falta = Cfg.IntervaloMs - (int)ms;
                int minimo = nPassos > 10 ? (int)Math.Min(30000, PassoMedioMs * 9) : 0;
                if (minimo > falta && !avisouLento) { avisouLento = true; Log.Escreve("leitura custando " + Math.Round(PassoMedioMs, 0) + " ms: ritmo espaçado para não pesar"); }
                esperaMs = Math.Max(100, Math.Max(falta, minimo));
                Thread.Sleep(esperaMs);
            }
            try { FechaSessao(); FechaMinuto(); } catch { }
        }

        public void Para() { parar = true; }
        public void RelePausa() { proxPausa = DateTime.MinValue; }   // o clique em pausar vale na próxima leitura

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
            if (agora >= proxRotacao) { proxRotacao = agora.AddHours(6); Rotaciona("minutos.jsonl", 14); Rotaciona("ram.jsonl", 8); Rotaciona("sessoes.jsonl", 400); }
            if (agora >= proxPausa) { proxPausa = agora.AddSeconds(5); Pausado = LeituraPausada(); }
            CuidaEnergia();   // vale mesmo com a leitura pausada: é a pessoa que pediu
            if (agora >= proxEu) { proxEu = agora.AddSeconds(10); MedeEu(agora); }
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
                Janela.Add(a); while (Janela.Count > 1 && (a.Quando - Janela[0].Quando).TotalSeconds > Lim.G("janela_s")) Janela.RemoveAt(0);
                Historico.Add(a); while (Historico.Count > 1 && (a.Quando - Historico[0].Quando).TotalSeconds > 120) Historico.RemoveAt(0);
                Conclusoes = Regras.Agora(Janela, Cfg, Sessao != null);
            }
            if (Sessao != null) Sessao.Soma(a, Cfg);
            if (minuto == null || minuto.Inicio.Minute != agora.Minute || (agora - minuto.Inicio).TotalMinutes >= 1) { FechaMinuto(); minuto = new Minuto(agora); }
            minuto.Soma(a);
            GravaAgora(a);
            if (Atualizou != null) Atualizou();
        }

        public static DateTime? EnergiaTravadaAte()
        {
            try
            {
                string arq = K.Arq("energia-travada-ate.txt");
                DateTime ate;
                if (File.Exists(arq) && DateTime.TryParse(File.ReadAllText(arq).Trim(), K.INV, DateTimeStyles.AssumeLocal, out ate) && ate > DateTime.Now) return ate;
            }
            catch { }
            return null;
        }

        // Notebook com a troca ligada: quando o carregador entra ou sai (e ao abrir), ativa o plano daquele lado. Só na mudança de lado:
        // se a pessoa trocar o plano à mão depois, o Katharos respeita até a próxima vez que o carregador entrar ou sair.
        bool travadaCache; DateTime proxTrava = DateTime.MinValue;
        void CuidaEnergia()
        {
            if (!Cfg.EnergiaAuto) { energiaLado = null; energiaParou = null; EnergiaEstado = ""; EnergiaErro = null; return; }
            string cfgChave = Cfg.EnergiaTomada + "|" + Cfg.EnergiaBateria;
            if (energiaParou != null && energiaParou != cfgChave) energiaParou = null;   // escolheu planos novos: tenta de novo
            if (energiaParou != null) return;   // o plano escolhido não existe mais: espera a pessoa escolher de novo
            ConfereEnergia();
            PowerStatus ps;
            try { ps = SystemInformation.PowerStatus; } catch { return; }
            if (ps.BatteryChargeStatus == BatteryChargeStatus.NoSystemBattery || ps.PowerLineStatus == PowerLineStatus.Unknown) return;
            if (DateTime.Now >= proxTrava) { proxTrava = DateTime.Now.AddSeconds(5); travadaCache = EnergiaTravadaAte().HasValue; }
            bool naBateria = ps.PowerLineStatus == PowerLineStatus.Offline;
            bool desempenho = !naBateria || travadaCache;
            string lado = naBateria ? (travadaCache ? "bateria-mantida" : "bateria") : "tomada";
            Guid alvo = (desempenho ? Cfg.EnergiaTomada : Cfg.EnergiaBateria).Value;
            string chave = lado + alvo;   // trocar os planos escolhidos também conta como mudança
            if (chave == energiaLado) return;
            energiaLado = chave;
            string nome = (desempenho ? Cfg.EnergiaTomadaNome : Cfg.EnergiaBateriaNome) ?? "plano escolhido";
            string onde = lado == "tomada" ? "Na tomada" : lado == "bateria" ? "Na bateria" : "Na bateria, mantendo o desempenho";
            var atual = Energia.Ativo();
            if (atual.HasValue && atual.Value == alvo) { EnergiaEstado = onde + ": " + nome; EnergiaErro = null; EnergiaConferidaEm = DateTime.Now; return; }
            uint cod = Energia.Ativa(alvo);
            if (cod == 2)
            {   // apagaram o plano: para de tentar e diz o que fazer
                energiaParou = cfgChave;
                Erro("o plano \"" + nome + "\" não existe mais neste PC. Escolha os planos de novo no Katharos (segundo plano, opção e).");
                return;
            }
            // lê de volta na hora e de novo daqui a 15 s (programa do fabricante às vezes troca de volta logo depois)
            energiaAlvo = alvo; energiaAlvoNome = onde + ": " + nome; energiaConfere = DateTime.Now.AddSeconds(15);
            var depois = Energia.Ativo();
            if (cod != 0 || !depois.HasValue || depois.Value != alvo)
            {
                Erro("não consegui pôr o plano \"" + nome + "\" (" + onde.ToLowerInvariant() + "): o Windows " +
                     (cod != 0 ? "recusou (código " + cod + ", talvez política da empresa)" : "continua no plano de antes") + ".");
                energiaConfere = DateTime.MaxValue;
                return;
            }
            EnergiaEstado = energiaAlvoNome; EnergiaErro = null; EnergiaConferidaEm = DateTime.Now;
            EnergiaAviso = energiaAlvoNome; EnergiaAvisoErro = false;
            Log.Escreve("energia: " + energiaAlvoNome + " (conferido)");
            Evento("energia", "{\"plano\":" + new JavaScriptSerializer().Serialize(energiaAlvoNome ?? "") + ",\"ok\":true}");
        }

        void Erro(string texto)
        {
            EnergiaErro = texto; EnergiaEstado = "erro";
            EnergiaAviso = "Energia: " + texto; EnergiaAvisoErro = true;
            Log.Escreve("energia: " + texto);
            Evento("energia", "{\"erro\":" + new JavaScriptSerializer().Serialize(texto ?? "") + ",\"ok\":false}");
        }

        // a segunda leitura, 15 s depois: se algo trocou o plano de volta, avisa com o nome do culpado provável, sem insistir
        void ConfereEnergia()
        {
            if (DateTime.Now < energiaConfere || !energiaAlvo.HasValue) return;
            energiaConfere = DateTime.MaxValue;
            var agora = Energia.Ativo();
            if (agora.HasValue && agora.Value == energiaAlvo.Value) { EnergiaConferidaEm = DateTime.Now; return; }
            Erro("pus \"" + energiaAlvoNome + "\", mas algo trocou o plano de volta em seguida (costuma ser o programa de energia do " +
                 "fabricante do notebook). Desligue a troca de planos dele ou a do Katharos, para as duas não brigarem.");
        }
        public void ReleEnergia() { proxTrava = DateTime.MinValue; }

        // CPU e RAM do próprio Katharos.exe (o processo dele mesmo, nunca o de outro)
        void MedeEu(DateTime agora)
        {
            try
            {
                using (var eu = Process.GetCurrentProcess())
                {
                    var cpu = Nat.MeuTempoDeCpu();
                    if (euAntes != DateTime.MinValue)
                        EuCpuPct = Math.Max(0, (cpu - euCpuAntes).TotalMilliseconds * 100.0 / Math.Max(1, (agora - euAntes).TotalMilliseconds) / Math.Max(1, Environment.ProcessorCount));
                    euCpuAntes = cpu; euAntes = agora;
                    EuRamMb = eu.WorkingSet64 / 1048576.0;
                }
            }
            catch { }
        }

        void DetectaJogo(Amostra a)
        {
            DateTime agora = a.Quando;
            string nomeTop = null;
            if (a.TopGpuPid > 0) leitor.Nomes.TryGetValue(a.TopGpuPid, out nomeTop);
            bool candidato = a.TopGpuPid > 0 && a.TopGpu >= Lim.G("jogo_gpu_min") && nomeTop != null && !NAO_JOGO.Contains(nomeTop) &&
                             (a.TopGpuPid == a.PrimeiroPlanoPid || a.TelaCheia || a.AntiCheat);
            if (Sessao == null)
            {
                if (candidato)
                {
                    if (candidatoPid != a.TopGpuPid) { candidatoPid = a.TopGpuPid; candidatoDesde = agora; }
                    else if ((agora - candidatoDesde).TotalSeconds >= Lim.G("jogo_segundos_comecar"))
                    {
                        Sessao = new Sessao { Jogo = nomeTop, Pid = a.TopGpuPid, Inicio = candidatoDesde, Ultimo = agora };
                        semJogoDesde = DateTime.MaxValue;
                        Log.Escreve("jogo aberto: " + nomeTop);
                        Evento("sessao_comecou", "{\"jogo\":" + new JavaScriptSerializer().Serialize(nomeTop) + "}");
                        if (Cfg.Fps) Fps.Inicia(a.TopGpuPid);
                    }
                }
                else candidatoPid = 0;
            }
            else
            {
                bool vivo = leitor.Nomes.ContainsKey(Sessao.Pid);
                bool ativo = vivo && (a.TopGpuPid == Sessao.Pid && a.TopGpu >= Lim.G("jogo_gpu_ativo") || a.PrimeiroPlanoPid == Sessao.Pid);
                if (ativo) semJogoDesde = DateTime.MaxValue;
                else if (semJogoDesde == DateTime.MaxValue) semJogoDesde = agora;
                if (!vivo || (agora - semJogoDesde).TotalSeconds >= Lim.G("jogo_segundos_fechar")) FechaSessao();
            }
            if (Sessao != null) { a.Jogo = Sessao.Jogo; a.JogoPid = Sessao.Pid; a.Fps = Fps.Agora(); }
        }

        void FechaSessao()
        {
            var s = Sessao; Sessao = null; candidatoPid = 0;
            if (s == null) return;
            s.FpsResumo = Fps.Resumo();
            Fps.Para();
            Log.Escreve("jogo fechado: " + s.Jogo + ", " + Math.Round((s.Ultimo - s.Inicio).TotalMinutes, 1).ToString(K.INV) + " min");
            if ((s.Ultimo - s.Inicio).TotalMinutes < 1 || s.N < 5) return;
            Acrescenta("sessoes.jsonl", new JavaScriptSerializer().Serialize(s.Json()));
            Evento("sessao_terminou", "{\"jogo\":" + new JavaScriptSerializer().Serialize(s.Jogo) + ",\"min\":" + Math.Round((s.Ultimo - s.Inicio).TotalMinutes, 1).ToString(K.INV) + "}");
            if (SessaoFechou != null) SessaoFechou();   // evento: a central pensa agora, com a sessão nova
        }

        void FechaMinuto()
        {
            if (minuto == null) return;
            minuto.FpsMin = Fps.FechaMinuto();
            minuto.EuCpu = EuCpuPct;
            string l = minuto.Linha();
            if (l != null) Acrescenta("minutos.jsonl", l);
            minuto = null;
        }

        internal static void Acrescenta(string nome, string linha)
        {
            try { Directory.CreateDirectory(K.CASA); File.AppendAllText(K.Arq(nome), linha + "\n", new UTF8Encoding(false)); }
            catch (Exception e) { Log.Escreve(nome + ": " + e.Message); }
        }

        /// <summary>Fila de eventos em disco (eventos.jsonl): o motor importa na memória do PC e a interface lê de lá. Uma linha por evento.</summary>
        public static void Evento(string tipo, string dadosJson)
        {
            Acrescenta("eventos.jsonl", "{\"t\":\"" + K.Iso(DateTime.Now) + "\",\"tipo\":\"" + tipo + "\",\"dados\":" + (dadosJson ?? "{}") + "}");
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
            // o tempo real entre duas leituras (o freio espaça até 30 s num PC lento): quem lê o arquivo só diz "desligado" depois de bem mais que isso
            d["espera_s"] = Math.Round(esperaMs / 1000.0, 1);
            d["cpu"] = K.R(a.Cpu, 1); d["nucleo_max"] = K.R(a.NucleoMax, 1); d["cpu_desempenho"] = K.R(a.CpuDesempenho, 0); d["cpu_ghz"] = K.R(a.CpuGhz, 2);
            d["gpu"] = K.R(a.Gpu, 1); d["vram_gb"] = K.R(a.VramGb, 2); d["vram_total_gb"] = K.R(a.VramTotalGb, 1);
            d["ram_pct"] = K.R(a.RamPct, 1); d["ram_gb"] = K.R(a.RamGb, 2); d["ram_total_gb"] = K.R(a.RamTotalGb, 1);
            d["disco"] = K.R(a.Disco, 1); d["disco_le_mbs"] = K.R(a.DiscoLe, 2); d["disco_grava_mbs"] = K.R(a.DiscoGrava, 2);
            d["rede_baixa_mbs"] = K.R(a.RedeBaixa, 3); d["rede_sobe_mbs"] = K.R(a.RedeSobe, 3);
            d["temp_cpu"] = K.R(a.TempCpu, 0); d["temp_cpu_fonte"] = a.TempCpuFonte; d["temp_gpu"] = K.R(a.TempGpu, 0); d["temp_gpu_fonte"] = a.TempGpuFonte;
            if (a.Bateria.HasValue) { d["bateria"] = a.Bateria; d["na_bateria"] = a.NaBateria; }
            var cx = new Dictionary<string, object>();
            cx["ligado_h"] = K.R(a.UptimeH, 2); cx["processos"] = a.Processos; cx["ram_sistema_gb"] = K.R(a.RamSistemaGb, 2); cx["ram_conta_gb"] = K.R(a.RamContaGb, 2);
            cx["manutencao"] = a.Manutencao; cx["top"] = a.Top;
            d["contexto"] = cx;
            if (Sessao != null)
            {
                var j = new Dictionary<string, object>();
                j["nome"] = Sessao.Jogo; j["desde"] = K.Iso(Sessao.Inicio); j["min"] = Math.Round((a.Quando - Sessao.Inicio).TotalMinutes, 1);
                j["principal"] = Sessao.Principal();
                j["fps"] = K.R(a.Fps, 0); j["fps_estado"] = Fps.Estado;
                var fr = Fps.Resumo(); if (fr != null) foreach (var kv in fr) j[kv.Key] = kv.Value;
                d["jogo"] = j;
            }
            var cs = new List<object>();
            foreach (var c in Conclusoes) { var x = new Dictionary<string, object>(); x["id"] = c.Id; x["nivel"] = c.Nivel; x["titulo"] = c.Titulo; x["texto"] = c.Texto; x["comando"] = c.Comando; cs.Add(x); }
            d["conclusoes"] = cs;
            var p = new Dictionary<string, object>();
            p["ram_mb"] = Math.Round(EuRamMb, 1); p["cpu_pct"] = Math.Round(EuCpuPct, 2); p["desde"] = K.Iso(Desde);
            p["leitura_ms"] = Math.Round(PassoMedioMs, 1); p["leitura_maior_ms"] = Math.Round(PassoMaiorMs, 1);
            p["custo"] = leitor.Custo.Json();
            d["segundo_plano"] = p;
            if (Cfg.EnergiaAuto)
            {
                var en = new Dictionary<string, object>();
                en["estado"] = EnergiaEstado; en["erro"] = EnergiaErro; en["conferida"] = EnergiaConferidaEm.HasValue ? K.Iso(EnergiaConferidaEm.Value) : null;
                d["energia"] = en;
            }
            try { K.GravaAtomico(K.Arq("agora.json"), json.Serialize(d)); } catch { }
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

    /// <summary>
    /// O ícone perto do relógio, desenhado no tamanho exato da bandeja (a gravura do cavaleiro vira borrão em 16 px): o elmo do cavaleiro
    /// num quadrado escuro, sempre igual. O estado é só um selo no canto: jogando (círculo âmbar), atenção (triângulo âmbar), grave
    /// (círculo vermelho), pausado (duas barras). Montado como um .ico de 32 bits com transparência de verdade (o GetHicon de antes estragava as bordas).
    /// </summary>
    static class IconeBandeja
    {
        public static Icon Faz(string estado, int px)
        {
            if (px < 16) px = 16;
            using (var bmp = new Bitmap(px, px, System.Drawing.Imaging.PixelFormat.Format32bppArgb))
            {
                using (var g = Graphics.FromImage(bmp))
                {
                    g.SmoothingMode = SmoothingMode.AntiAlias; g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    g.Clear(Color.Transparent);
                    float k = px / 16f;
                    // a base é sempre a mesma (o elmo claro no quadrado escuro); o estado é só o selo no canto de baixo
                    using (var fundo = Arredondado(new RectangleF(0.5f * k, 0.5f * k, 15f * k, 15f * k), 3.2f * k))
                    {
                        using (var b = new SolidBrush(Cor.Fundo)) g.FillPath(b, fundo);
                        using (var c = new Pen(Cor.LinhaForte, Math.Max(1f, k))) g.DrawPath(c, fundo);
                    }
                    using (var corpo = new GraphicsPath())
                    {
                        corpo.AddLines(new[] { P(4.2f, 5.6f, k), P(4.6f, 4.0f, k), P(6.0f, 3.6f, k), P(10.0f, 3.6f, k), P(11.4f, 4.0f, k), P(11.8f, 5.6f, k),
                                               P(12.2f, 12.0f, k), P(11.4f, 12.8f, k), P(4.6f, 12.8f, k), P(3.8f, 12.0f, k) });
                        corpo.CloseFigure();
                        using (var b = new SolidBrush(Cor.Osso)) g.FillPath(b, corpo);
                    }
                    using (var b = new SolidBrush(Cor.Osso))
                        foreach (var x in new[] { 5.6f, 8f, 10.4f })
                            g.FillPolygon(b, new[] { P(x - 0.9f, 3.9f, k), P(x, x == 8f ? 1.6f : 2.2f, k), P(x + 0.9f, 3.9f, k) });
                    using (var b = new SolidBrush(Cor.Fundo))
                    {
                        g.FillRectangle(b, 4.9f * k, 6.6f * k, 6.2f * k, Math.Max(1.2f, 1.3f * k));
                        g.FillRectangle(b, 7.45f * k, 8.9f * k, Math.Max(1f, 1.1f * k), 3.0f * k);
                    }
                    // o selo: jogando = círculo âmbar; atenção = triângulo âmbar; grave = círculo vermelho; pausado = duas barras cinza
                    if (estado != "")
                    {
                        float r = 3.3f * k; float cx = 12.9f * k, cy = 12.9f * k;
                        using (var b = new SolidBrush(Cor.Fundo)) g.FillEllipse(b, cx - r - k, cy - r - k, 2 * (r + k), 2 * (r + k));
                        Color c = estado == "grave" ? Cor.Vermelho : estado == "pausa" ? Cor.Apagado : Cor.Ambar;
                        using (var b = new SolidBrush(c))
                        {
                            if (estado == "atencao") g.FillPolygon(b, new[] { new PointF(cx, cy - r), new PointF(cx + r, cy + r * 0.8f), new PointF(cx - r, cy + r * 0.8f) });
                            else if (estado == "pausa") { g.FillRectangle(b, cx - r * 0.8f, cy - r * 0.8f, r * 0.6f, r * 1.6f); g.FillRectangle(b, cx + r * 0.2f, cy - r * 0.8f, r * 0.6f, r * 1.6f); }
                            else g.FillEllipse(b, cx - r, cy - r, 2 * r, 2 * r);
                        }
                    }
                }
                return DeBitmap(bmp);
            }
        }

        static PointF P(float x, float y, float k) { return new PointF(x * k, y * k); }

        static GraphicsPath Arredondado(RectangleF r, float raio)
        {
            var p = new GraphicsPath(); float d = raio * 2;
            p.AddArc(r.X, r.Y, d, d, 180, 90); p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90); p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure(); return p;
        }

        /// <summary>Um .ico de um quadro só, 32 bits (BGRA, de baixo para cima) com a máscara AND toda zerada: o Windows usa o alfa.</summary>
        static Icon DeBitmap(Bitmap bmp)
        {
            int w = bmp.Width, h = bmp.Height, linhaMasc = ((w + 31) / 32) * 4;
            var px = new byte[w * h * 4];
            var dados = bmp.LockBits(new Rectangle(0, 0, w, h), System.Drawing.Imaging.ImageLockMode.ReadOnly, System.Drawing.Imaging.PixelFormat.Format32bppArgb);
            try { for (int y = 0; y < h; y++) Marshal.Copy(dados.Scan0 + y * dados.Stride, px, (h - 1 - y) * w * 4, w * 4); }
            finally { bmp.UnlockBits(dados); }
            int tamDib = 40 + px.Length + linhaMasc * h;
            using (var ms = new MemoryStream())
            using (var e = new BinaryWriter(ms))
            {
                e.Write((short)0); e.Write((short)1); e.Write((short)1);
                e.Write((byte)(w >= 256 ? 0 : w)); e.Write((byte)(h >= 256 ? 0 : h)); e.Write((byte)0); e.Write((byte)0);
                e.Write((short)1); e.Write((short)32); e.Write(tamDib); e.Write(22);
                e.Write(40); e.Write(w); e.Write(h * 2); e.Write((short)1); e.Write((short)32); e.Write(0); e.Write(px.Length + linhaMasc * h);
                e.Write(0); e.Write(0); e.Write(0); e.Write(0);
                e.Write(px); e.Write(new byte[linhaMasc * h]);
                e.Flush(); ms.Position = 0;
                return new Icon(ms, w, h);
            }
        }
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
        List<string[]> resultados = new List<string[]>();
        Dictionary<string, double[]> faixas = new Dictionary<string, double[]>();
        DateTime faixasLidas = DateTime.MinValue;

        // o normal deste PC (linha de base que a central calcula), por métrica e contexto: a faixa de 10 a 90 %
        void LeFaixas()
        {
            faixasLidas = DateTime.Now;
            var f = new Dictionary<string, double[]>();
            try
            {
                string arq = K.Arq("linha-de-base.json");
                if (File.Exists(arq))
                {
                    var d = new JavaScriptSerializer().DeserializeObject(File.ReadAllText(arq, Encoding.UTF8)) as Dictionary<string, object>;
                    var ms = d != null && d.ContainsKey("metricas") ? d["metricas"] as Dictionary<string, object> : null;
                    if (ms != null)
                        foreach (var m in ms)
                        {
                            var ctxs = m.Value as Dictionary<string, object>; if (ctxs == null) continue;
                            foreach (var c in ctxs)
                            {
                                var b = c.Value as Dictionary<string, object>; if (b == null || !b.ContainsKey("p10") || !b.ContainsKey("p90")) continue;
                                f[m.Key + "|" + c.Key] = new[] { Convert.ToDouble(b["p10"], K.INV), Convert.ToDouble(b["p90"], K.INV) };
                            }
                        }
                }
            }
            catch { }
            faixas = f;
        }

        double[] Faixa(string metrica, bool jogo)
        {
            if ((DateTime.Now - faixasLidas).TotalMinutes > 5) LeFaixas();
            double[] r; return faixas.TryGetValue(metrica + "|" + (jogo ? "jogo" : "sem_jogo"), out r) ? r : null;
        }
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
            propostas = new List<string[]> { new[] { "Desligar o que abre com o Windows e pesa no jogo", "inicializacao", "alta", "jogo-cpu-inicio" } };
            resultados = new List<string[]> { new[] { "jogo-freio", "plano de energia no máximo", "como previsto (31 → 4 % do tempo)" } };
            faixas = new Dictionary<string, double[]> { { "cpu|jogo", new double[] { 30, 62 } }, { "ram|jogo", new double[] { 55, 70 } }, { "temp_cpu|jogo", new double[] { 62, 74 } } };
            faixasLidas = DateTime.Now;
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
                            l.Add(new[] { Convert.ToString(x["titulo"]), x.ContainsKey("comando") ? Convert.ToString(x["comando"]) : "",
                                          x.ContainsKey("confianca") ? Convert.ToString(x["confianca"]) : "", x.ContainsKey("id") ? Convert.ToString(x["id"]) : "" });
                            if (l.Count >= 2) break;
                        }
                    var rs = d != null && d.ContainsKey("resultados") ? d["resultados"] as object[] : null;
                    var lr = new List<string[]>();
                    if (rs != null)
                        foreach (var o in rs)
                        {
                            var x = o as Dictionary<string, object>; if (x == null) continue;
                            Func<string, string> c = delegate (string k) { return x.ContainsKey(k) && x[k] != null ? Convert.ToString(x[k], K.BR) : ""; };
                            double a0, b0; string num = "";
                            if (double.TryParse(c("antes"), NumberStyles.Float, K.BR, out a0) && double.TryParse(c("depois"), NumberStyles.Float, K.BR, out b0))
                                num = " (" + K.Num(a0, 0) + " → " + K.Num(b0, 0) + " " + c("un") + ")";
                            lr.Add(new[] { c("id"), c("titulo"), c("veredito") + num });
                            break;
                        }
                    resultados = lr;
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
                bool jg = ses != null;
                y = Linha(g, pinta, y, pad, "cpu", K.Num(a.Cpu, 0) + " %", subCpu, hist, fCpu, 100, a.Cpu >= 90, Faixa("cpu", jg));
                y = Linha(g, pinta, y, pad, "placa de vídeo", a.Gpu.HasValue ? K.Num(a.Gpu, 0) + " %" : "-", subGpu, hist, fGpu, 100, a.Gpu >= 95);
                y = Linha(g, pinta, y, pad, "memória", K.Num(a.RamPct, 0) + " %", K.Num(a.RamGb, 1) + " de " + K.Num(a.RamTotalGb, 0) + " GB", hist, fRam, 100, a.RamPct >= 90, Faixa("ram", jg));
                y = Linha(g, pinta, y, pad, "temperatura", valTemp, subTemp, hist, fTemp, 100, a.TempCpu >= motor.Cfg.AvisoCpu || a.TempGpu >= motor.Cfg.AvisoGpu, a.TempCpu.HasValue ? Faixa("temp_cpu", jg) : Faixa("temp_gpu", jg));
                y = Linha(g, pinta, y, pad, "disco", K.Num(a.Disco, 0) + " %", "lê " + K.Num(a.DiscoLe, 1) + " · grava " + K.Num(a.DiscoGrava, 1) + " MB/s", hist, fDisco, 100, a.Disco >= 95, Faixa("disco", jg));
                if (ses != null)
                {   // em jogo, o FPS de verdade vale mais que a rede
                    var fr = motor.Fps.Resumo();
                    string est = motor.Fps.Estado;
                    string subFps = fr != null ? "média " + K.Num(Convert.ToDouble(fr["fps_med"]), 0) + " · 1% low " + K.Num(Convert.ToDouble(fr["fps_1low"]), 0)
                                  : est == "sem permissão" ? "ligue a medida de FPS no Katharos" : est == "sem PresentMon" ? "medida de FPS não instalada" : est == "PresentMon alterado" ? "PresentMon alterado: baixe o Katharos de novo" : "medindo...";
                    Func<Amostra, double?> fFps = x => x.Fps;
                    y = Linha(g, pinta, y, pad, "fps", a.Fps.HasValue ? K.Num(a.Fps, 0) : "-", subFps, hist, fFps, 0, false);
                }
                else
                    y = Linha(g, pinta, y, pad, "rede", K.Num((a.RedeBaixa ?? 0) * 8, 1) + " Mb/s", "baixando · enviando " + K.Num((a.RedeSobe ?? 0) * 8, 1) + " Mb/s", hist, fRede, 0, false);
                if (a.Bateria.HasValue && pinta) Texto(g, "bateria " + a.Bateria + " %" + (a.NaBateria ? ", fora da tomada" : ", na tomada"), fPequeno, Cor.Apagado, pad, y);
                if (a.Bateria.HasValue) y += 18 * s;
            }
            // "o que eu vejo agora" e a central saíram do painel (pedido do dono): o painel é só para ver os números; o resto fica na janela
            y += 4 * s;
            // botões
            y += 6 * s;
            string[][] bs = { new[] { "raio-x", "raiox" }, new[] { "jogos", "jogos" }, new[] { "abrir o Katharos", "" } };
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
            return Linha(g, pinta, y, pad, rotulo, valor, sub, hist, f, teto, alerta, null);
        }

        float Linha(Graphics g, bool pinta, float y, float pad, string rotulo, string valor, string sub, List<Amostra> hist, Func<Amostra, double?> f, double teto, bool alerta, double[] faixa)
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
                if (faixa != null && max > 0)
                {   // o normal deste PC: faixa clara atrás da linha
                    float y1 = gy + gh - (float)(Math.Min(1, faixa[1] / max) * gh), y2 = gy + gh - (float)(Math.Min(1, faixa[0] / max) * gh);
                    using (var b = new SolidBrush(Color.FromArgb(48, Cor.Osso))) g.FillRectangle(b, gx, y1, gw, Math.Max(1.5f * s, y2 - y1));
                }
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
        ToolStripMenuItem iStatus, iPausa, iInicio, iAvisos, iRitmo, iEnergia;
        IntPtr iconeAtual = IntPtr.Zero; string estadoIcone = "";
        readonly Dictionary<string, DateTime> avisado = new Dictionary<string, DateTime>();
        DateTime proxPropostas = DateTime.Now.AddMinutes(2);
        DateTime proxConferir = DateTime.Now.AddMinutes(15);
        Thread fio;

        public Bandeja(bool mostrar)
        {
            ui.CreateControl();
            marca = Marca.Carrega();
            marcaPequena = new Icon(marca, SystemInformation.SmallIconSize);
            painel = new PainelAoVivo(motor, Abre, marca);
            MontaMenu();
            try { iconeFeito = IconeBandeja.Faz("", SystemInformation.SmallIconSize.Width); ni.Icon = iconeFeito; } catch { ni.Icon = marcaPequena; }
            ni.Text = "Katharos"; ni.ContextMenuStrip = menu; ni.Visible = true;
            ni.MouseUp += delegate (object o, MouseEventArgs e) { if (e.Button == MouseButtons.Left) AlternaPainel(); };
            // clicar no aviso abre o Katharos com janelas na tela certa (ou o terminal, na versão de terminal)
            ni.BalloonTipClicked += delegate { AbreJanela("aovivo"); };
            motor.Atualizou += delegate { try { ui.BeginInvoke(new Action(Atualiza)); } catch { } };
            motor.SessaoFechou += delegate { Pensa("fim de sessão de jogo"); };
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
            var t = Item("Katharos " + K.VERSAO, null); t.Tag = "titulo"; t.Font = new Font("Segoe UI Semibold", 9f);
            iStatus = Item("lendo...", null);
            menu.Items.Add(new ToolStripSeparator());
            Item("Painel ao vivo", delegate { painel.Mostra(); });
            Item("Abrir o Katharos", delegate { AbreJanela("inicio"); });
            if (Janela() != null) Item("O que a central concluiu", delegate { AbreJanela("sugestoes"); });
            menu.Items.Add(new ToolStripSeparator());
            // o que é do próprio ícone e se resolve num clique; o resto está no Katharos
            iPausa = Item("Pausar por 1 hora", delegate { AlternaPausa(); });
            iRitmo = new ToolStripMenuItem("Ler a cada");
            foreach (var seg in new[] { "1", "2", "5", "10" })
            {
                var x = new ToolStripMenuItem(seg + " s"); x.Tag = seg;
                x.Click += delegate (object o, EventArgs e) { MudaConfig("tempo-real", (string)((ToolStripItem)o).Tag); };
                iRitmo.DropDownItems.Add(x);
            }
            iRitmo.DropDown.BackColor = Cor.Painel; ((ToolStripDropDownMenu)iRitmo.DropDown).ShowImageMargin = false; ((ToolStripDropDownMenu)iRitmo.DropDown).ShowCheckMargin = true;
            iRitmo.DropDown.Renderer = new Desenho();
            menu.Items.Add(iRitmo);
            iAvisos = Item("Avisar quando algo ficar no limite", delegate { MudaConfig("avisos", motor.Cfg.Notificar ? "nao" : "sim"); });
            iEnergia = Item("Manter desempenho por 1 hora na bateria", delegate { AlternaEnergia(); });
            iInicio = Item("Iniciar com o Windows", delegate { AlternaInicio(); });
            menu.Items.Add(new ToolStripSeparator());
            Item("Sair do segundo plano", delegate { Sai(); });
            menu.Opening += delegate { AtualizaMenu(); };
        }

        void AtualizaMenu()
        {
            iPausa.Text = Motor.LeituraPausada() ? "Retomar agora" : "Pausar por 1 hora";
            iInicio.Checked = IniciaComWindows();
            // só em notebook com a troca de energia ligada
            bool bateria = false;
            try { bateria = SystemInformation.PowerStatus.BatteryChargeStatus != BatteryChargeStatus.NoSystemBattery; } catch { }
            iEnergia.Visible = motor.Cfg.EnergiaAuto && bateria;
            iEnergia.Text = Motor.EnergiaTravadaAte().HasValue ? "Voltar à economia na bateria agora" : "Manter desempenho por 1 hora na bateria";
            iAvisos.Checked = motor.Cfg.Notificar;
            string atual = (motor.Cfg.IntervaloMs / 1000).ToString(K.INV);
            iRitmo.Text = "Ler a cada " + atual + " s";
            foreach (ToolStripMenuItem x in iRitmo.DropDownItems) x.Checked = (string)x.Tag == atual;
        }

        // muda a preferência no mesmo arquivo do Katharos (config.json) e na config do segundo plano; vale na hora
        void MudaConfig(string chave, string valor)
        {
            try
            {
                var js = new JavaScriptSerializer();
                foreach (var nome in new[] { "config.json", "segundo-plano.json" })
                {
                    string arq = K.Arq(nome);
                    Dictionary<string, object> d = null;
                    if (File.Exists(arq)) d = js.DeserializeObject(File.ReadAllText(arq, Encoding.UTF8)) as Dictionary<string, object>;
                    if (d == null) d = new Dictionary<string, object>();
                    if (nome == "config.json") d[chave] = valor;
                    else if (chave == "tempo-real") d["intervalo_s"] = double.Parse(valor, K.INV);
                    else if (chave == "avisos") d["notificar"] = valor;
                    K.GravaAtomico(arq, js.Serialize(d));
                }
                motor.Cfg = Config.Le();
            }
            catch (Exception e) { Log.Escreve("preferência: " + e.Message); }
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

        void AlternaEnergia()
        {
            string arq = K.Arq("energia-travada-ate.txt");
            try
            {
                if (Motor.EnergiaTravadaAte().HasValue) File.Delete(arq);
                else File.WriteAllText(arq, DateTime.Now.AddHours(1).ToString("yyyy-MM-ddTHH:mm:ss", K.INV), Encoding.ASCII);
            }
            catch { }
            motor.ReleEnergia();
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
            motor.RelePausa();
        }

        void Abre(string[] args)
        {
            if (args.Length == 3 && args[0] == "@resp")
            {   // a sua resposta vai para a central, que pensa de novo e reexporta
                Log.Escreve("resposta: " + args[1] + " = " + args[2]);
                Abridor.Escondido(motor.Cfg, "conselheiro --resposta " + K.Q(args[1]) + " " + args[2] + " --sem-cor");
                return;
            }
            // com a versão de janelas instalada, nada abre o terminal: o comando vira a tela que faz a mesma coisa
            if (Janela() != null) { AbreJanela(TelaDoComando(args.Length > 0 ? args[0] : "")); return; }
            Abridor.Abre(args);
        }

        static string TelaDoComando(string c)
        {
            switch (c)
            {
                case "raiox": case "saude": case "medir": return "raiox";
                case "aovivo": case "segundo-plano": case "painel": return "aovivo";
                case "tendencia": case "historico": return "historico";
                case "conselheiro": case "sugestoes": return "sugestoes";
                case "desfazer": return "desfazer";
                case "jogos": return "jogos";
                case "memoria": return "memoria";
                case "inicializacao": return "inicializacao";
                case "turbo": case "escolher": case "otimizar": return "otimizar";
                case "": return "inicio";
                default: return "otimizar:" + c;   // as áreas (servicos, privacidade, limpar...) abrem no Otimizar, já na área
            }
        }

        /// <summary>O Katharos com janelas, quando este segundo plano veio com ele (instalado: app\Katharos.exe e app\motor\Katharos.exe).</summary>
        static string Janela()
        {
            // 1) ao lado (app\motor\Katharos.exe → app\Katharos.exe); 2) onde a janela disse que está (ela grava ao abrir); 3) a instalação
            // padrão. Sem isso, o segundo plano copiado para ~/.katharos (pelo motor) não achava a janela e abria o Katharos de terminal
            // em quem tinha instalado a versão com janelas (aconteceu depois de atualizar)
            var cands = new List<string>();
            try { cands.Add(Path.Combine(Path.GetDirectoryName(Path.GetDirectoryName(Application.ExecutablePath)), "Katharos.exe")); } catch { }
            try { string j = K.Arq("janela.txt"); if (File.Exists(j)) cands.Add(File.ReadAllText(j).Trim()); } catch { }
            try { cands.Add(Path.Combine(Path.Combine(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Katharos"), "current"), "Katharos.exe")); } catch { }
            foreach (var app in cands)
                try
                {
                    if (string.IsNullOrEmpty(app) || !File.Exists(app) || string.Equals(app, Application.ExecutablePath, StringComparison.OrdinalIgnoreCase)) continue;
                    string dir = Path.GetDirectoryName(app);
                    // a janela instalada tem python\ e motor\ ao lado; qualquer um dos dois (ou a DLL dela) basta para saber que é a janela
                    if (Directory.Exists(Path.Combine(dir, "python")) || Directory.Exists(Path.Combine(dir, "motor")) || File.Exists(Path.Combine(dir, "Katharos.App.dll"))) return app;
                }
                catch { }
            Log.Escreve("janela não encontrada (" + string.Join(" | ", cands.ToArray()) + "): abrindo o terminal");
            return null;
        }

        void AbreJanela(string tela)
        {
            string app = Janela();
            if (app == null) { Abridor.Abre(new string[0]); return; }
            try { Process.Start(new ProcessStartInfo(app, "--tela " + tela) { UseShellExecute = false, WorkingDirectory = Path.GetDirectoryName(app) }); }
            catch (Exception e) { Log.Escreve("abrir a janela: " + e.Message); Abridor.Abre(new string[0]); }
        }

        DateTime proxSair = DateTime.MinValue;
        readonly DateTime inicio = DateTime.Now;

        void Atualiza()
        {
            // a janela pede para o segundo plano sair (antes de trocar de versão ou ao desinstalar): sai e a janela reabre depois
            if (DateTime.Now >= proxSair)
            {
                proxSair = DateTime.Now.AddSeconds(3);
                string pedido = K.Arq("segundo-plano-sair.txt");
                if (File.Exists(pedido))
                {
                    // pedido antigo (de antes deste segundo plano abrir) não vale: só apaga
                    bool novo = File.GetLastWriteTime(pedido) >= inicio.AddSeconds(-1);
                    try { File.Delete(pedido); } catch { }
                    if (novo) { Log.Escreve("saindo a pedido da janela (troca de versão)"); Sai(false); return; }
                }
            }
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
            // só fala com a barra de tarefas (explorer) quando o texto muda de verdade
            dica = dica.Length > 63 ? dica.Substring(0, 63) : dica;
            if (dica != ni.Text) ni.Text = dica;
            if (iStatus != null) iStatus.Text = a == null ? (motor.Pausado ? "pausado" : "lendo...") :
                ("CPU " + K.Num(a.Cpu, 0) + " %   GPU " + K.Num(a.Gpu, 0) + " %   RAM " + K.Num(a.RamPct, 0) + " %" + (a.TempCpu.HasValue ? "   " + K.Num(a.TempCpu, 0) + " °C" : ""));
            painel.Atualiza();
            // troca de energia (notebook): aviso discreto, uma vez por troca
            string ea = motor.EnergiaAviso;
            // erro sempre aparece (mesmo com avisos desligados): a pessoa precisa saber que não ficou como pediu
            if (ea != null) { motor.EnergiaAviso = null; if (motor.Cfg.Notificar || motor.EnergiaAvisoErro) ni.ShowBalloonTip(motor.EnergiaAvisoErro ? 10000 : 4000, "Katharos", ea, motor.EnergiaAvisoErro ? ToolTipIcon.Warning : ToolTipIcon.None); }
            // avisos que valem uma notificação: calor sempre; o resto só fora de jogo; cada um no máximo a cada 30 min
            if (motor.Cfg.Notificar)
                foreach (var c in concl)
                {
                    if (c.Nivel < 1 || c.Id == "gpu") continue;
                    bool grave = c.Id == "calor" && c.Nivel >= 2;
                    if (ses != null && (motor.Cfg.AvisosNoJogo == "nunca" || (motor.Cfg.AvisosNoJogo == "so-grave" && !grave))) continue;
                    DateTime ult;
                    // calor grave: no máximo a cada 30 min; o resto, o intervalo que a pessoa escolheu (6 h por padrão)
                    double espera = grave ? 30 : motor.Cfg.AvisosIntervaloH * 60;
                    if (avisado.TryGetValue(c.Id, out ult) && (DateTime.Now - ult).TotalMinutes < espera) continue;
                    avisado[c.Id] = DateTime.Now;
                    Motor.Evento("aviso", "{\"id\":" + new JavaScriptSerializer().Serialize(c.Id) + ",\"titulo\":" + new JavaScriptSerializer().Serialize(c.Titulo) + "}");
                    ni.ShowBalloonTip(8000, "Katharos: " + c.Titulo, c.Texto, c.Nivel >= 2 ? ToolTipIcon.Warning : ToolTipIcon.Info);
                    break;
                }
            // a central pensa nos eventos (fim de sessão; o Katharos pensa ao aplicar e desfazer); este relógio é só a reserva
            if (DateTime.Now >= proxPropostas)
            {
                if (ses == null) Pensa("reserva de 6 h");
                else proxPropostas = DateTime.Now.AddMinutes(10);
            }
            // com o PC parado (10 min sem mexer, sem jogo, CPU baixa), confere o "já está assim" que venceu: a janela abre com o dado fresco.
            // Roda escondido, com prioridade baixa e em modo teste (nada muda); uma vez a cada 20 h no máximo
            if (DateTime.Now >= proxConferir && !motor.Pausado && ses == null && a != null && a.Cpu < 25 && Nat.OciosoSegundos() >= 600)
            {
                proxConferir = DateTime.Now.AddHours(20);
                Log.Escreve("conferindo o já feito com o PC parado");
                Abridor.Escondido(motor.Cfg, "conferir --agendada --sem-cor");
            }
        }

        void Pensa(string porque)
        {
            proxPropostas = DateTime.Now.AddHours(6);
            Log.Escreve("central pensando: " + porque);
            Abridor.Escondido(motor.Cfg, "conselheiro --exportar --sem-cor");
        }

        void TrocaIcone(string est)
        {
            if (est == estadoIcone) return;
            estadoIcone = est;
            Icon novo;
            try { novo = IconeBandeja.Faz(est, SystemInformation.SmallIconSize.Width); }
            catch (Exception e) { Log.Escreve("ícone: " + e.Message); novo = marcaPequena; }
            ni.Icon = novo;
            if (iconeFeito != null && !ReferenceEquals(iconeFeito, marcaPequena)) iconeFeito.Dispose();
            iconeFeito = ReferenceEquals(novo, marcaPequena) ? null : novo;
        }
        Icon iconeFeito;

        void Sai() { Sai(true); }

        void Sai(bool peloUsuario)
        {
            if (peloUsuario)
                try { File.WriteAllText(K.Arq("segundo-plano-fechado.txt"), K.Iso(DateTime.Now), Encoding.ASCII); } catch { }
            Log.Escreve("segundo plano desligado");
            motor.Para();
            ni.Visible = false; ni.Dispose();
            if (iconeFeito != null) iconeFeito.Dispose();
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

        // tempos de quadro sintéticos: 990 a 120 FPS, 9 travadas de 50 ms, 1 de 100 ms
        // quanto o segundo plano pesa: 30 leituras no ritmo mais rápido (1 s), com o custo de cada fonte, o maior pico, CPU e RAM do
        // próprio processo; e confere a lista de processos da chamada direta contra a do .NET. Roda no CI e no PC real (teste-no-pc).
        public static int TesteCusto(string destino, int n)
        {
            bool listaOk, leve;
            var res = MedeCusto(n, out listaOk, out leve);
            K.GravaAtomico(destino, string.Join("\r\n", res.ToArray()) + "\r\n");
            return listaOk && leve ? 0 : 1;
        }

        static List<string> MedeCusto(int n, out bool listaOk, out bool leve)
        {
            var cfg = Config.Le();
            var l = new Leitor { Espacar = true };
            var sw = new Stopwatch(); var passos = new List<double>();
            TimeSpan cpu0 = Nat.MeuTempoDeCpu();
            var t0 = DateTime.Now;
            for (int i = 0; i < n; i++)
            {
                sw.Restart(); l.Le(cfg, false); double ms = sw.Elapsed.TotalMilliseconds;
                if (i >= 3) passos.Add(ms);
                Thread.Sleep(Math.Max(100, 1000 - (int)ms));
            }
            double cpuPct, ramMb;
            using (var eu = Process.GetCurrentProcess())
            {
                cpuPct = (Nat.MeuTempoDeCpu() - cpu0).TotalMilliseconds * 100.0 / (DateTime.Now - t0).TotalMilliseconds / Math.Max(1, Environment.ProcessorCount);
                ramMb = eu.WorkingSet64 / 1048576.0;
            }
            passos.Sort();
            double media = 0; foreach (var x in passos) media += x; media /= Math.Max(1, passos.Count);
            double maior = passos.Count > 0 ? passos[passos.Count - 1] : 0, p95 = passos.Count > 0 ? passos[(int)(passos.Count * 0.95)] : 0;
            // a lista direta tem de bater com a do Windows (.NET): os mesmos PIDs, o próprio processo com o nome e a sessão certos
            var direta = new Processos().Le(); var pids = new HashSet<int>(); foreach (var p in direta) pids.Add(p.Pid);
            int net = 0, achados = 0; string meuNome = null; int minhaSessao = -1, euPid;
            using (var eu = Process.GetCurrentProcess()) { euPid = eu.Id; minhaSessao = eu.SessionId; }
            foreach (var p in Process.GetProcesses()) { net++; if (pids.Contains(p.Id)) achados++; p.Dispose(); }
            foreach (var p in direta) if (p.Pid == euPid) { meuNome = p.Nome; if (p.Sessao != minhaSessao) meuNome += " (sessão errada)"; }
            listaOk = direta.Count > 0 && achados >= net * 0.9 && meuNome == "Katharos";
            leve = media < 50 && cpuPct < 2;
            var res = new List<string>();
            res.Add("leituras: " + passos.Count + " (depois das 3 de aquecimento), " + Environment.ProcessorCount + " núcleos, " + Environment.OSVersion.VersionString);
            res.Add("por leitura: média " + media.ToString("0.0", K.INV) + " ms, 95% abaixo de " + p95.ToString("0.0", K.INV) + " ms, maior " + maior.ToString("0.0", K.INV) + " ms");
            res.Add("Katharos.exe: CPU " + cpuPct.ToString("0.00", K.INV) + " % (de todo o PC), RAM " + ramMb.ToString("0", K.INV) + " MB");
            foreach (var kv in l.Custo.Fontes)
                res.Add("  " + kv.Key + ": média " + (kv.Value[1] / Math.Max(1, kv.Value[0])).ToString("0.00", K.INV) + " ms, maior " + kv.Value[2].ToString("0.0", K.INV) + " ms");
            res.Add("lista de processos direta: " + direta.Count + " (o .NET vê " + net + ", " + achados + " em comum), eu = " + (meuNome ?? "não achei") + (listaOk ? " ok" : " ERRADO"));
            res.Add(leve ? "leve ok" : "PESADO: média acima de 50 ms ou CPU acima de 2 %");
            return res;
        }

        // Teste no PC de verdade (fase 2c.1): tudo o que dá para conferir sem a pessoa, num relatório só, em ~/.katharos/teste-no-pc.txt.
        // Cada linha diz o que foi visto e de onde veio; "?" quando não deu para saber. Nada é mudado no PC.
        public static int TesteNoPc(string destino)
        {
            var r = new List<string>();
            Action<string> L = delegate (string x) { r.Add(x); };
            L("Katharos " + K.VERSAO + " · teste no PC · " + DateTime.Now.ToString("dd/MM/yyyy HH:mm", K.INV));
            L("Windows: " + Environment.OSVersion.VersionString + (Environment.Is64BitOperatingSystem ? " 64 bits" : " 32 bits") + " · " + Environment.ProcessorCount + " núcleos");
            L("");
            L("[segundo plano]");
            bool rodando = false;
            try { Mutex m; rodando = Mutex.TryOpenExisting(K.MUTEX, out m); if (m != null) m.Dispose(); } catch { }
            L("rodando agora: " + (rodando ? "sim" : "não"));
            try { using (var k = Registry.CurrentUser.OpenSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run")) L("abre com o Windows: " + (k != null && k.GetValue("Katharos") != null ? "sim" : "não")); } catch { L("abre com o Windows: ?"); }
            try
            {
                string ag = K.Arq("agora.json");
                if (File.Exists(ag))
                {
                    var d = new JavaScriptSerializer().DeserializeObject(File.ReadAllText(ag, Encoding.UTF8)) as Dictionary<string, object>;
                    object q, sp; d.TryGetValue("quando", out q); d.TryGetValue("segundo_plano", out sp);
                    L("última leitura gravada: " + q);
                    var spd = sp as Dictionary<string, object>;
                    if (spd != null) L("custo gravado pelo segundo plano: leitura " + Convert.ToString(spd.ContainsKey("leitura_ms") ? spd["leitura_ms"] : "?", K.INV) + " ms, CPU " +
                                       Convert.ToString(spd.ContainsKey("cpu_pct") ? spd["cpu_pct"] : "?", K.INV) + " %, RAM " + Convert.ToString(spd.ContainsKey("ram_mb") ? spd["ram_mb"] : "?", K.INV) + " MB");
                }
                else L("agora.json: não existe (o segundo plano nunca rodou nesta conta)");
                foreach (var nome in new[] { "minutos.jsonl", "sessoes.jsonl" })
                {
                    string a = K.Arq(nome);
                    L(nome + ": " + (File.Exists(a) ? File.ReadAllLines(a).Length + " linhas" : "não existe"));
                }
            }
            catch (Exception e) { L("arquivos do segundo plano: erro " + e.Message); }
            L("");
            L("[temperatura]");
            var lista = new Processos().Le(); var abertos = new HashSet<string>();
            foreach (var p in lista) abertos.Add(p.Nome.ToLowerInvariant());
            foreach (var prog in new[] { "MSIAfterburner", "HWiNFO64", "LibreHardwareMonitor", "CoreTemp", "aida64", "RTSS" })
                if (abertos.Contains(prog.ToLowerInvariant())) L("aberto: " + prog);
            var ext = Externos.Le();
            L("dos programas de monitoramento: CPU " + (ext.Cpu.HasValue ? ext.Cpu + " °C (" + ext.CpuFonte + ")" : "nada") + ", GPU " + (ext.Gpu.HasValue ? ext.Gpu + " °C (" + ext.GpuFonte + ")" : "nada"));
            var leitor = new Leitor();
            Amostra am = null;
            for (int i = 0; i < 3; i++) { am = leitor.Le(Config.Le(), false); Thread.Sleep(1000); }
            L("o que o Katharos usa: CPU " + (am.TempCpu.HasValue ? am.TempCpu + " °C (" + am.TempCpuFonte + ")" : "sem leitura") + ", GPU " + (am.TempGpu.HasValue ? am.TempGpu + " °C (" + am.TempGpuFonte + ")" : "sem leitura"));
            L("compare com o que o MSI Afterburner (ou o HWiNFO) mostra agora: a diferença deve ser de 1 ou 2 °C");
            L("");
            L("[leitura agora]");
            L("CPU " + K.Num(am.Cpu, 0) + " % (núcleo mais usado " + K.Num(am.NucleoMax, 0) + " %, " + K.Num(am.CpuGhz, 2) + " GHz) · GPU " + K.Num(am.Gpu, 0) + " % · VRAM " +
              K.Num(am.VramGb, 1) + " de " + K.Num(am.VramTotalGb, 1) + " GB · RAM " + K.Num(am.RamPct, 0) + " % · disco " + K.Num(am.Disco, 0) + " %");
            L("processos: " + am.Processos + " · ligado há " + K.Num(am.UptimeH, 1) + " h" + (am.Manutencao != null ? " · manutenção do Windows rodando: " + am.Manutencao : ""));
            L("");
            L("[FPS nos jogos]");
            string pm = Fps.Caminho();
            L("PresentMon: " + (pm == null ? "não encontrado" : pm + (Fps.Confere(pm) ? " (impressão digital ok)" : " (IMPRESSÃO DIGITAL DIFERENTE: não vai rodar)")));
            bool grupo = false;
            try { grupo = new System.Security.Principal.WindowsPrincipal(System.Security.Principal.WindowsIdentity.GetCurrent()).IsInRole(new System.Security.Principal.SecurityIdentifier("S-1-5-32-559")); } catch { }
            L("permissão (grupo Usuários de log de desempenho, valendo nesta sessão): " + (grupo ? "sim" : "não (Katharos > segundo plano > f; depois saia e entre na conta)"));
            L("");
            L("[energia]");
            var ps = SystemInformation.PowerStatus;
            bool bat = ps.BatteryChargeStatus != BatteryChargeStatus.NoSystemBattery;
            L(bat ? "bateria: " + (int)(ps.BatteryLifePercent * 100) + " %, " + (ps.PowerLineStatus == PowerLineStatus.Offline ? "na bateria" : "na tomada") : "sem bateria (desktop)");
            var cfg = Config.Le();
            L("troca automática de plano: " + (cfg.EnergiaAuto ? "ligada (" + cfg.EnergiaTomadaNome + " / " + cfg.EnergiaBateriaNome + ")" : "desligada"));
            var ativo = Energia.Ativo();
            L("plano ativo: " + (ativo.HasValue ? ativo.Value.ToString() : "?") + (cfg.EnergiaAuto && ativo.HasValue ? (ativo == cfg.EnergiaTomada ? " = o da tomada" : ativo == cfg.EnergiaBateria ? " = o da bateria" : " = NENHUM dos escolhidos") : ""));
            L("");
            L("[peso do segundo plano: 30 leituras no ritmo de 1 s]");
            bool listaOk, leve;
            foreach (var x in MedeCusto(30, out listaOk, out leve)) L(x);
            L("");
            L("[o que só você pode conferir: anote ao lado]");
            L("1. o ícone aparece perto do relógio e o painel abre no clique: ");
            L("2. jogue 10 min; depois, `katharos segundo-plano`: a sessão aparece com o jogo certo e o limite (compare com o Afterburner): ");
            L("3. FPS médio do Katharos x o do overlay do Afterburner/RTSS (diferença de até 5 %): ");
            L("4. pausar e voltar no menu do ícone; trocar o ritmo para 5 s: ");
            L("5. reiniciar o PC: o ícone volta sozinho: ");
            L("6. o Windows (SmartScreen ou antivírus) avisou algo ao abrir? o quê: ");
            L("7. notebook: tirar e pôr o carregador com a troca ligada; o ícone avisa o plano (ou o erro): ");
            K.GravaAtomico(destino, string.Join("\r\n", r.ToArray()) + "\r\n");
            return listaOk ? 0 : 1;
        }

        public static int TesteFps(string destino)
        {
            var f = new Fps();
            for (int i = 0; i < 1000; i++)
            {
                f.SomaParaTeste(i % 100 == 50 ? (i == 550 ? 100.0 : 50.0) : 1000.0 / 120);
            }
            var r = f.Resumo();
            double med = Convert.ToDouble(r["fps_med"]), low = Convert.ToDouble(r["fps_1low"]), low01 = Convert.ToDouble(r["fps_01low"]);
            bool ok = med > 100 && med < 115 && low > 15 && low < 22 && low01 > 9 && low01 < 11 && low < med && Convert.ToDouble(r["travadas_por_min"]) > 0;
            File.WriteAllText(Path.GetFullPath(destino), "media " + med.ToString(K.INV) + ", 1% low " + low.ToString(K.INV) + ", 0.1% low " + low01.ToString(K.INV) +
                              ", travadas/min " + Convert.ToString(r["travadas_por_min"], K.INV) + (ok ? " ok" : " ERRADO") + "\n", new UTF8Encoding(false));
            return ok ? 0 : 4;
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
                    TempCpu = 68 + 6 * f + rnd.Next(2), TempCpuFonte = "LibreHardwareMonitor", TempGpu = 71 + 3 * f, TempGpuFonte = "driver de vídeo",
                    Fps = 118 + 10 * Math.Sin(i / 7.0) + rnd.Next(6) };
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


    // ───────── teste de travadas por driver (o que o LatencyMon faz) ─────────
    // Liga por N segundos a sessão de rastreio do kernel do Windows só com os eventos de DPC e de interrupção (o tempo que cada driver
    // segurou um processador), soma por driver e devolve o pior. Só lê: não instala driver, não abre processo, não mexe em nada.
    // Precisa de administrador (o kernel só entrega esses eventos para ele). Se outra ferramenta já usa a sessão do kernel, não mexe
    // nela: diz isso e para.
    static class Travadas
    {
        const uint WNODE_FLAG_TRACED_GUID = 0x20000, EVENT_TRACE_REAL_TIME_MODE = 0x100, FLAG_DPC = 0x20, FLAG_INTERRUPT = 0x40;
        const uint PROCESS_TRACE_MODE_REAL_TIME = 0x100, PROCESS_TRACE_MODE_RAW_TIMESTAMP = 0x1000, PROCESS_TRACE_MODE_EVENT_RECORD = 0x10000000;
        const uint EVENT_TRACE_CONTROL_STOP = 1;
        const string NOME = "NT Kernel Logger";
        static readonly Guid SystemTrace = new Guid("9e814aad-3204-11d2-9a82-006008a86939");
        static readonly Guid PerfInfo = new Guid("ce1dbfb4-137e-4da6-87b0-3f59aa102cbc");

        [StructLayout(LayoutKind.Sequential)] struct WNODE_HEADER { public uint BufferSize, ProviderId; public ulong HistoricalContext; public long TimeStamp; public Guid Guid; public uint ClientContext, Flags; }
        [StructLayout(LayoutKind.Sequential)] struct EVENT_TRACE_PROPERTIES
        {
            public WNODE_HEADER Wnode; public uint BufferSize, MinimumBuffers, MaximumBuffers, MaximumFileSize, LogFileMode, FlushTimer, EnableFlags;
            public int AgeLimit; public uint NumberOfBuffers, FreeBuffers, EventsLost, BuffersWritten, LogBuffersLost, RealTimeBuffersLost; public IntPtr LoggerThreadId;
            public uint LogFileNameOffset, LoggerNameOffset;
        }
        [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate void EventRecordCallback(IntPtr rec);
        [UnmanagedFunctionPointer(CallingConvention.StdCall)] delegate uint BufferCallback(IntPtr log);
        // EVENT_TRACE_LOGFILEW, montado à mão (o tamanho muda entre 32 e 64 bits; só os campos usados importam)
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct EVENT_TRACE_LOGFILE
        {
            public string LogFileName; public string LoggerName; public long CurrentTime; public uint BuffersRead, ProcessTraceMode;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 88)] public byte[] CurrentEvent;   // EVENT_TRACE (88 bytes em 64 bits; 32 bits cabe)
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 280)] public byte[] LogfileHeader; // TRACE_LOGFILE_HEADER
            public BufferCallback BufferCallback; public uint BufferSize, Filled, EventsLost; public EventRecordCallback EventRecordCallback;
            public uint IsKernelTrace; public IntPtr Context;
        }
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)] static extern uint StartTraceW(out ulong h, string nome, IntPtr props);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)] static extern uint ControlTraceW(ulong h, string nome, IntPtr props, uint ctl);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern ulong OpenTraceW(ref EVENT_TRACE_LOGFILE log);
        [DllImport("advapi32.dll")] static extern uint ProcessTrace(ulong[] h, uint n, IntPtr ini, IntPtr fim);
        [DllImport("advapi32.dll")] static extern uint CloseTrace(ulong h);
        [DllImport("psapi.dll", SetLastError = true)] static extern bool EnumDeviceDrivers([Out] IntPtr[] bases, uint tam, out uint precisa);
        [DllImport("psapi.dll", CharSet = CharSet.Unicode)] static extern uint GetDeviceDriverBaseNameW(IntPtr b, StringBuilder nome, uint tam);
        [DllImport("kernel32.dll")] static extern bool QueryPerformanceFrequency(out long f);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool OpenProcessToken(IntPtr p, uint acesso, out IntPtr t);
        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool LookupPrivilegeValueW(string s, string n, out long luid);
        [DllImport("advapi32.dll", SetLastError = true)] static extern bool AdjustTokenPrivileges(IntPtr t, bool tudo, ref TOKEN_PRIV novo, uint tam, IntPtr ant, IntPtr ret);
        [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
        [StructLayout(LayoutKind.Sequential, Pack = 4)] struct TOKEN_PRIV { public uint Count; public long Luid; public uint Attr; }

        class PorDriver { public long N; public double TotalUs, MaiorUs; public int Acima1ms; public bool Isr; }

        static ulong[] bases; static string[] nomes;
        static readonly Dictionary<string, PorDriver> dpc = new Dictionary<string, PorDriver>(StringComparer.OrdinalIgnoreCase);
        static double usPorTick; static long eventos, semEndereco;

        // Windows 11 24H2 em diante só mostra endereço do kernel para quem tem o privilégio de depuração ligado (administrador tem, desligado)
        static void LigaDepuracao()
        {
            IntPtr t;
            if (!OpenProcessToken(GetCurrentProcess(), 0x28, out t)) return;
            try { long luid; if (LookupPrivilegeValueW(null, "SeDebugPrivilege", out luid)) { var p = new TOKEN_PRIV { Count = 1, Luid = luid, Attr = 2 }; AdjustTokenPrivileges(t, false, ref p, 0, IntPtr.Zero, IntPtr.Zero); } }
            finally { CloseHandle(t); }
        }

        static void CarregaDrivers()
        {
            uint precisa; var b = new IntPtr[4096];
            if (!EnumDeviceDrivers(b, (uint)(b.Length * IntPtr.Size), out precisa)) { bases = new ulong[0]; nomes = new string[0]; return; }
            int n = (int)Math.Min(b.Length, precisa / IntPtr.Size);
            var par = new List<KeyValuePair<ulong, string>>();
            for (int i = 0; i < n; i++)
            {
                if (b[i] == IntPtr.Zero) continue;
                var sb = new StringBuilder(260); GetDeviceDriverBaseNameW(b[i], sb, 260);
                par.Add(new KeyValuePair<ulong, string>(unchecked((ulong)b[i].ToInt64()), sb.ToString()));
            }
            par.Sort((x, y) => x.Key.CompareTo(y.Key));
            bases = new ulong[par.Count]; nomes = new string[par.Count];
            for (int i = 0; i < par.Count; i++) { bases[i] = par[i].Key; nomes[i] = par[i].Value; }
        }

        static string DriverDe(ulong rotina)
        {
            if (rotina == 0 || bases.Length == 0) return null;
            int i = Array.BinarySearch(bases, rotina);
            if (i < 0) i = ~i - 1;
            return i >= 0 ? nomes[i] : null;
        }

        static void AoEvento(IntPtr r)
        {
            try
            {
                var prov = (Guid)Marshal.PtrToStructure(new IntPtr(r.ToInt64() + 24), typeof(Guid));
                if (prov != PerfInfo) return;
                byte op = Marshal.ReadByte(r, 45);
                bool isr = op == 67 || op == 50;
                if (!(isr || op == 66 || op == 68 || op == 69)) return;
                long ts = Marshal.ReadInt64(r, 16);
                IntPtr dados = Marshal.ReadIntPtr(r, IntPtr.Size == 8 ? 96 : 92);
                int tam = Marshal.ReadInt16(r, 86);
                if (dados == IntPtr.Zero || tam < 8 + IntPtr.Size) return;
                long ini = Marshal.ReadInt64(dados, 0);
                ulong rotina = IntPtr.Size == 8 ? unchecked((ulong)Marshal.ReadInt64(dados, 8)) : (uint)Marshal.ReadInt32(dados, 8);
                double us = (ts - ini) * usPorTick;
                if (us < 0 || us > 1e6) return;   // relógio fora de ordem: descarta
                eventos++;
                string drv = DriverDe(rotina);
                if (drv == null) { semEndereco++; drv = "(desconhecido)"; }
                PorDriver p;
                if (!dpc.TryGetValue(drv, out p)) dpc[drv] = p = new PorDriver();
                p.N++; p.TotalUs += us; if (us > p.MaiorUs) p.MaiorUs = us; if (us >= 1000) p.Acima1ms++; if (isr) p.Isr = true;
            }
            catch { }
        }

        static EventRecordCallback cbEvento = AoEvento;            // referência viva: o Windows chama de outra thread
        static BufferCallback cbBuffer = delegate (IntPtr l) { return 1; };

        static IntPtr Propriedades()
        {
            int tam = Marshal.SizeOf(typeof(EVENT_TRACE_PROPERTIES)) + 2 * 1024;
            IntPtr mem = Marshal.AllocHGlobal(tam);
            for (int i = 0; i < tam; i++) Marshal.WriteByte(mem, i, 0);
            var p = new EVENT_TRACE_PROPERTIES();
            p.Wnode.BufferSize = (uint)tam; p.Wnode.Guid = SystemTrace; p.Wnode.Flags = WNODE_FLAG_TRACED_GUID; p.Wnode.ClientContext = 1;
            p.BufferSize = 64; p.MinimumBuffers = 16; p.MaximumBuffers = 64; p.LogFileMode = EVENT_TRACE_REAL_TIME_MODE; p.FlushTimer = 1;
            p.EnableFlags = FLAG_DPC | FLAG_INTERRUPT; p.LoggerNameOffset = (uint)Marshal.SizeOf(typeof(EVENT_TRACE_PROPERTIES));
            Marshal.StructureToPtr(p, mem, false);
            return mem;
        }

        /// <summary>Mede por `segundos` e grava o resultado em JSON. 0 = ok, 2 = sem administrador, 4 = sessão do kernel ocupada, 3 = outro erro.</summary>
        public static int Mede(int segundos, string destino)
        {
            var res = new Dictionary<string, object> { { "quando", K.Iso(DateTime.Now) }, { "segundos", segundos } };
            long f; QueryPerformanceFrequency(out f); usPorTick = 1e6 / f;
            LigaDepuracao(); CarregaDrivers();
            IntPtr props = Propriedades(); ulong h; int cod = 0; bool iniciou = false;
            try
            {
                // marcador: se um teste anterior foi encerrado no meio, a sessão dele ficou ligada; com o marcador, é nossa e pode parar
                string marca = K.Arq("travadas-sessao.txt");
                uint e = StartTraceW(out h, NOME, props);
                if (e == 183 && File.Exists(marca))
                {
                    ControlTraceW(0, NOME, props, EVENT_TRACE_CONTROL_STOP);
                    try { File.Delete(marca); } catch { }
                    Marshal.FreeHGlobal(props); props = Propriedades();
                    e = StartTraceW(out h, NOME, props);
                }
                if (e == 0) try { File.WriteAllText(marca, K.Iso(DateTime.Now)); } catch { }
                if (e == 5) { res["erro"] = "precisa de administrador"; cod = 2; }
                else if (e == 183) { res["erro"] = "outro programa está usando o rastreio do kernel (LatencyMon, xperf, Process Monitor...): feche-o e tente de novo"; cod = 4; }
                else if (e != 0) { res["erro"] = "o Windows recusou o rastreio (código " + e + ")"; cod = 3; }
                iniciou = e == 0;
                if (cod == 0)
                {
                    var log = new EVENT_TRACE_LOGFILE { LoggerName = NOME, ProcessTraceMode = PROCESS_TRACE_MODE_REAL_TIME | PROCESS_TRACE_MODE_EVENT_RECORD | PROCESS_TRACE_MODE_RAW_TIMESTAMP,
                                                        CurrentEvent = new byte[88], LogfileHeader = new byte[280], EventRecordCallback = cbEvento, BufferCallback = cbBuffer };
                    ulong leitor = OpenTraceW(ref log);
                    uint rp = 0;
                    if (leitor == ulong.MaxValue) { res["erro"] = "o Windows não abriu a leitura do rastreio"; cod = 3; }
                    else
                    {
                        var t = new Thread(() => { try { rp = ProcessTrace(new[] { leitor }, 1, IntPtr.Zero, IntPtr.Zero); } catch { rp = 1; } }) { IsBackground = true };
                        t.Start();
                        Thread.Sleep(Math.Max(5, Math.Min(300, segundos)) * 1000);
                        ControlTraceW(0, NOME, props, EVENT_TRACE_CONTROL_STOP);
                        t.Join(5000); CloseTrace(leitor);
                        if (rp != 0 && rp != 1223 && eventos < 100) { res["erro"] = "a leitura do rastreio parou no meio (código " + rp + ")"; cod = 3; }
                    }
                    // sempre para a sessão (mesmo com erro acima): nada fica ligado depois do teste
                    ControlTraceW(0, NOME, props, EVENT_TRACE_CONTROL_STOP);
                    try { File.Delete(K.Arq("travadas-sessao.txt")); } catch { }
                }
            }
            catch (Exception ex) { res["erro"] = ex.Message; cod = 3; if (iniciou) try { ControlTraceW(0, NOME, props, EVENT_TRACE_CONTROL_STOP); } catch { } }
            finally { Marshal.FreeHGlobal(props); }
            res["eventos"] = eventos; res["sem_endereco"] = semEndereco; res["drivers_carregados"] = bases == null ? 0 : bases.Length;
            var lista = new List<object>();
            var ordem = new List<KeyValuePair<string, PorDriver>>(dpc);
            ordem.Sort((x, y) => y.Value.MaiorUs.CompareTo(x.Value.MaiorUs));
            if (ordem.Count > 25) ordem.RemoveRange(25, ordem.Count - 25);
            foreach (var kv in ordem)
                lista.Add(new Dictionary<string, object> { { "driver", kv.Key }, { "n", kv.Value.N }, { "total_ms", Math.Round(kv.Value.TotalUs / 1000, 2) },
                    { "maior_us", Math.Round(kv.Value.MaiorUs, 0) }, { "acima_1ms", kv.Value.Acima1ms }, { "isr", kv.Value.Isr } });
            res["drivers"] = lista;
            try { File.WriteAllText(destino, new JavaScriptSerializer().Serialize(res), new UTF8Encoding(false)); } catch { return 3; }
            return cod;
        }
    }

    static class Programa
    {
        [STAThread]
        static int Main(string[] args)
        {
            var lista = new List<string>(args);
            if (lista.Contains("--teste-fps"))
            {
                try { int i = lista.IndexOf("--teste-fps"); return Testes.TesteFps(i + 1 < lista.Count ? lista[i + 1] : K.Arq("teste-fps.txt")); }
                catch (Exception e) { Log.Escreve("teste fps: " + e); return 3; }
            }
            if (lista.Contains("--travadas"))
            {
                try
                {
                    int i = lista.IndexOf("--travadas"), seg;
                    if (!(i + 1 < lista.Count && int.TryParse(lista[i + 1], out seg))) seg = 60;
                    return Travadas.Mede(seg, i + 2 < lista.Count ? lista[i + 2] : K.Arq("travadas.json"));
                }
                catch (Exception e) { Log.Escreve("travadas: " + e); return 3; }
            }
            if (lista.Contains("--teste-no-pc"))
            {
                try
                {
                    int i = lista.IndexOf("--teste-no-pc");
                    string dest = i + 1 < lista.Count ? lista[i + 1] : K.Arq("teste-no-pc.txt");
                    int c = Testes.TesteNoPc(dest);
                    if (i + 1 >= lista.Count) try { Process.Start(new ProcessStartInfo(dest) { UseShellExecute = true }); } catch { }   // sem destino: abre o relatório no Bloco de Notas
                    return c;
                }
                catch (Exception e) { Log.Escreve("teste no pc: " + e); return 3; }
            }
            if (lista.Contains("--teste-custo"))
            {
                try
                {
                    int i = lista.IndexOf("--teste-custo"), n;
                    string dest = i + 1 < lista.Count ? lista[i + 1] : K.Arq("teste-custo.txt");
                    if (!(i + 2 < lista.Count && int.TryParse(lista[i + 2], out n))) n = 30;
                    return Testes.TesteCusto(dest, Math.Max(5, Math.Min(600, n)));
                }
                catch (Exception e) { Log.Escreve("teste custo: " + e); return 3; }
            }
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
