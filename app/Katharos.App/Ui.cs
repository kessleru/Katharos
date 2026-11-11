using System.Globalization;
using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Documents;
using Avalonia.Layout;
using Avalonia.Media;
using Avalonia.Threading;
using Katharos.App.Controles;

namespace Katharos.App;

/// <summary>
/// As peças de todas as telas, num lugar só: título com o ponto âmbar, seções com as linhas e os "+", números grandes, linhas de
/// lista, etiquetas, botões e os estados de carregando, vazio e erro. Toda tela é feita com estas; assim todas falam igual.
/// </summary>
public static class Ui
{
    public static readonly CultureInfo Br = CultureInfo.GetCultureInfo("pt-BR");

    public static TextBlock T(string texto, string? classes = null, IBrush? cor = null, double tamanho = 0, bool quebra = false)
    {
        var t = new TextBlock { Text = texto };
        if (classes != null) foreach (var c in classes.Split(' ')) t.Classes.Add(c);
        if (cor != null) t.Foreground = cor;
        if (tamanho > 0) t.FontSize = tamanho;
        if (quebra) t.TextWrapping = TextWrapping.Wrap;
        return t;
    }

    public static Secao S(Control filho, bool linha = true) => new() { Child = filho, LinhaEmbaixo = linha };

    public static Secao Cabecalho(string titulo, string sub, Control? direita = null)
    {
        var t = new TextBlock();
        t.Classes.Add("titulo");
        t.Inlines = new InlineCollection { new Run(titulo), new Run(".") { Foreground = Tema.Ambar } };
        var esq = new StackPanel { Spacing = 8, Children = { t, T(sub, "sub") } };
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions("*,Auto"), Margin = new Thickness(32, 36, 32, 30) };
        g.Children.Add(esq);
        if (direita != null) { Grid.SetColumn(direita, 1); direita.VerticalAlignment = VerticalAlignment.Bottom; g.Children.Add(direita); }
        return S(g);
    }

    /// <summary>Um subtítulo de bloco ("O que o raio-x achou").</summary>
    public static Control Subtitulo(string texto, string? explica = null)
    {
        var p = new StackPanel { Spacing = 4, Margin = new Thickness(32, 22, 32, 12) };
        p.Children.Add(T(texto, "forte"));
        if (explica != null) p.Children.Add(T(explica, "rotulo", quebra: true));
        return p;
    }

    public static Control Numero(string rotulo, string valor, string unidade, string contexto, IBrush corContexto, Control? extra = null)
    {
        var num = new StackPanel { Orientation = Orientation.Horizontal, Children = { T(valor, "numero"), T(unidade, "unidade") } };
        var p = new StackPanel { Spacing = 4, Children = { T(rotulo, "rotulo"), num, T(contexto, null, corContexto, 13) } };
        if (extra != null) p.Children.Add(extra);
        return new Border { Padding = new Thickness(32, 24), Child = p };
    }

    /// <summary>Células lado a lado, separadas pela linha vertical fina (como os números do site).</summary>
    public static Grid Celulas(params Control[] cels)
    {
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions(string.Join(",", cels.Select(_ => "*"))) };
        for (int i = 0; i < cels.Length; i++)
        {
            var b = new Border { Child = cels[i], BorderBrush = Tema.Linha, BorderThickness = new Thickness(i == 0 ? 0 : 1, 0, 0, 0) };
            Grid.SetColumn(b, i);
            g.Children.Add(b);
        }
        return g;
    }

    public static Button Botao(string texto, bool primario, Action acao, bool ativo = true)
    {
        var b = new Button { Content = texto, IsEnabled = ativo, VerticalAlignment = VerticalAlignment.Center };
        b.Classes.Add(primario ? "primario" : "contorno");
        b.Click += (_, _) => acao();
        return b;
    }

    static readonly HashSet<Button> ocupados = new();

    /// <summary>Botão que faz algo assíncrono (conversa com o motor): enquanto trabalha, fica desligado com "…" no texto e a barra
    /// lateral diz que está trabalhando (sem isso, uma ação lenta parecia bug e convidava a clicar de novo); um segundo clique no
    /// meio não roda de novo; um erro vira a caixa de erro, nunca fecha o aplicativo.</summary>
    public static Button Botao(string texto, bool primario, Func<Task> acao, bool ativo = true)
    {
        Button? b = null;
        b = Botao(texto, primario, (Action)(async () =>
        {
            if (!ocupados.Add(b!)) return;
            var conteudo = b!.Content; bool estava = b.IsEnabled, marcou = false;
            // o "…" só aparece se demorar: numa ação rápida (gravar uma preferência) o botão não pisca
            DispatcherTimer.RunOnce(() => { if (ocupados.Contains(b)) { marcou = true; b.Content = texto + "…"; b.IsEnabled = false; } }, TimeSpan.FromMilliseconds(250));
            Trabalho.Comeca();
            try { await acao(); }
            catch (Exception e) { MostraErro(e); }
            finally { Trabalho.Termina(); ocupados.Remove(b); if (marcou) { b.Content = conteudo; b.IsEnabled = estava; } }
        }), ativo);
        return b;
    }

    /// <summary>A caixa de erro: o que houve em palavras simples, o que fazer, e os detalhes para pedir ajuda. <paramref name="depois"/>
    /// diz o que aconteceu com o PC (ex.: "o que chegou a mudar volta pelo Desfazer"); sem ele, vale "nada além disso mudou".</summary>
    public static void MostraErro(Exception e, string? titulo = null, string? depois = null)
    {
        string refe = Referencia(e, "caixa");
        var j = Janela.Atual;
        if (j == null) return;
        var (t, texto) = Explica(e);
        var corpo = new StackPanel { Spacing = 10, MaxWidth = 560, HorizontalAlignment = HorizontalAlignment.Left };
        corpo.Children.Add(T(texto, "sub", quebra: true));
        corpo.Children.Add(T(depois ?? "Nada além disso mudou no PC.", "rotulo", quebra: true));
        corpo.Children.Add(Detalhes(e, refe));
        j.MostraCaixa(Janela.Caixa(titulo ?? t, corpo, new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 8, 0, 0),
            Children = { Botao("Fechar", true, j.FechaCaixa) } }), true);
    }

    /// <summary>O erro em palavras de quem usa: um título curto e o que fazer. O texto técnico fica nos detalhes.</summary>
    public static (string titulo, string texto) Explica(Exception e)
    {
        if (e is ErroDoMotor m)
            return m.Codigo switch
            {
                "caiu" or "sem_resposta" => ("O motor do Katharos fechou", "Ele parou no meio do pedido. Tente de novo: ele abre sozinho. Se repetir, copie os detalhes abaixo e mande junto com os registros."),
                "demorou" => ("Demorou demais", m.Message),
                "recusado" => ("Sem permissão de administrador", m.Message),
                "sem_motor" => ("Instalação incompleta", m.Message),
                "motor_alterado" => ("Arquivos do Katharos alterados", m.Message),
                "interno" => ("Erro interno do Katharos", "Algo inesperado aconteceu no motor. Tente de novo; se repetir, copie os detalhes abaixo e mande junto com os registros."),
                "nao_ligou" or "sem_exe" => ("O acompanhamento não abriu", m.Message),
                "so_windows" => ("Só no Windows", m.Message),
                "sem_texto" => ("Falta o texto", m.Message),
                "sem_secoes" => ("Nada marcado", m.Message),
                "sem_internet" => ("Sem conexão", m.Message),
                "envio_fora" => ("O envio ainda não está no ar", "O servidor que recebe os relatórios ainda não foi ligado pelo criador do Katharos."),
                "envio_limite" => ("Muitos envios seguidos", m.Message),
                "envio_recusado" => ("O servidor não aceitou", m.Message + " Tente de novo mais tarde; se repetir, mande só o feedback contando isso."),
                _ => ("Não deu certo", m.Message),
            };
        return e switch
        {
            UnauthorizedAccessException => ("Sem permissão para um arquivo", "O Windows não deixou ler ou gravar um arquivo do Katharos. Feche programas que possam estar usando a pasta .katharos (antivírus, sincronização de nuvem) e tente de novo."),
            IOException => ("Arquivo em uso", "Um arquivo do Katharos estava em uso por outro programa, ou o disco demorou a responder. Tente de novo em alguns segundos."),
            TimeoutException => ("Demorou demais", "Uma etapa passou do tempo. Tente de novo; num PC ocupado pode levar mais."),
            System.Text.Json.JsonException => ("Resposta ilegível", "O motor respondeu algo que a janela não entendeu. Tente de novo; se repetir, mande os registros."),
            _ => ("Não deu certo", "Algo inesperado aconteceu na janela. Tente de novo; se repetir, copie os detalhes abaixo e mande junto com os registros."),
        };
    }

    /// <summary>Grava o erro inteiro no registro com um número curto, que aparece na tela: com ele, o registro certo é achado na hora.</summary>
    public static string Referencia(Exception e, string onde)
    {
        string refe = DateTime.Now.ToString("HHmmss") + "-" + (Math.Abs(e.GetHashCode()) % 1000).ToString("000");
        Registro.Escreve($"erro {refe} ({onde}): {(e is ErroDoMotor m ? m.Codigo + ": " : "")}{e}");
        return refe;
    }

    /// <summary>A linha de detalhes: o texto técnico curto, "Copiar detalhes" (versão, número, erro) e "Abrir os registros".</summary>
    public static Control Detalhes(Exception e, string refe)
    {
        string codigo = e is ErroDoMotor m ? m.Codigo : e.GetType().Name;
        string versao = typeof(Ui).Assembly.GetName().Version?.ToString(3) ?? "";
        string tecnico = $"Katharos {versao} · {Environment.OSVersion.VersionString} · erro {refe} · {codigo}: {e.Message}";
        var copiar = Botao("Copiar detalhes", false, async () => await Copia(tecnico));
        var abrir = Botao("Abrir os registros", false, () =>
        {
            try
            {
                var d = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos");
                Directory.CreateDirectory(d);
                if (OperatingSystem.IsWindows()) System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo("explorer.exe", "\"" + d + "\"") { UseShellExecute = true });
            }
            catch (Exception x) { Registro.Escreve("abrir os registros: " + x.Message); }
        });
        var botoes = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8, Children = { copiar, abrir } };
        // erro de envio não oferece "enviar relatório" (seria o mesmo caminho que acabou de falhar)
        if (!(e is ErroDoMotor { Codigo: "sem_internet" or "envio_fora" or "envio_limite" or "envio_recusado" or "sem_texto" or "sem_secoes" }))
            botoes.Children.Add(Botao("Enviar relatório", false, () => { var j = Janela.Atual; j?.FechaCaixa(); j?.Mostra("enviar:" + refe); }));
        return new StackPanel { Spacing = 8, Children = {
            T($"Referência {refe} · {codigo}", "rotulo", tamanho: 12.5, quebra: true).Com(t => t.FontFamily = Tema.Mono), botoes } };
    }

    /// <summary>Copia um texto para a área de transferência (o código de um envio, os detalhes de um erro).</summary>
    public static async Task Copia(string texto)
    {
        var cb = TopLevel.GetTopLevel(Janela.Atual)?.Clipboard;
        if (cb != null) await cb.SetTextAsync(texto);
    }

    public static Border Etiqueta(string texto, IBrush cor) =>
        new() { Classes = { "etiqueta" }, BorderBrush = cor, HorizontalAlignment = HorizontalAlignment.Left, Child = T(texto, null, cor) };

    public static (string texto, IBrush cor) Gravidade(int impacto) => impacto switch
    {
        3 => ("grave", Tema.Vermelho), 2 => ("atenção", Tema.Ambar), 1 => ("dica", Tema.Apagado), _ => ("info", Tema.Apagado),
    };

    /// <summary>Uma linha de lista: etiqueta à esquerda (opcional), título e explicação, ação à direita.</summary>
    public static Control Linha(string titulo, string? explica, Border? etiqueta = null, Control? direita = null)
    {
        var g = new Grid { ColumnDefinitions = new ColumnDefinitions(etiqueta != null ? "136,*,Auto" : "*,Auto") };
        int c = 0;
        if (etiqueta != null) { etiqueta.VerticalAlignment = VerticalAlignment.Top; etiqueta.Margin = new Thickness(0, 2, 0, 0); g.Children.Add(etiqueta); c = 1; }
        var meio = new StackPanel { Spacing = 3, VerticalAlignment = VerticalAlignment.Center };
        meio.Children.Add(T(titulo, null, Tema.Osso, 15, true).Com(t => t.FontWeight = FontWeight.SemiBold));
        if (!string.IsNullOrWhiteSpace(explica)) meio.Children.Add(T(explica!, "rotulo", tamanho: 13.5, quebra: true));
        Grid.SetColumn(meio, c); g.Children.Add(meio);
        if (direita != null) { direita.Margin = new Thickness(16, 0, 0, 0); direita.VerticalAlignment = VerticalAlignment.Center; Grid.SetColumn(direita, c + 1); g.Children.Add(direita); }
        return new Border { Padding = new Thickness(32, 16), BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Child = g };
    }

    /// <summary>Estado vazio: diz o que falta e o que fazer, com a ação.</summary>
    public static Secao Vazio(string titulo, string texto, Button? acao = null)
    {
        var p = new StackPanel { Spacing = 8, Margin = new Thickness(32, 40), MaxWidth = 640, HorizontalAlignment = HorizontalAlignment.Left };
        p.Children.Add(T(titulo, "forte", tamanho: 19));
        p.Children.Add(T(texto, "sub"));
        if (acao != null) { acao.HorizontalAlignment = HorizontalAlignment.Left; acao.Margin = new Thickness(0, 10, 0, 0); p.Children.Add(acao); }
        return S(p);
    }

    /// <summary>Carregando: o que está acontecendo, com a barra que anda (e o passo, quando o motor manda).</summary>
    public static (Secao secao, TextBlock passo, ProgressBar barra) Carregando(string texto)
    {
        var (p, passo, barra) = Andamento(texto);
        p.Margin = new Thickness(32, 40);
        barra.MaxWidth = 480; barra.HorizontalAlignment = HorizontalAlignment.Left;
        return (S(p), passo, barra);
    }

    /// <summary>O que está acontecendo agora: o passo, a barra que anda e, depois de 3 s, há quanto tempo (uma espera longa nunca parece
    /// tela parada). Opcional: uma dica embaixo (ex.: onde aparece o pedido de permissão do Windows).</summary>
    public static (StackPanel painel, TextBlock passo, ProgressBar barra) Andamento(string texto, string? dica = null)
    {
        var passo = T(texto, null, Tema.Osso, 15, true);
        var barra = new ProgressBar { IsIndeterminate = true, Height = 3, MinHeight = 3, Foreground = Tema.Ambar, Background = Tema.Linha, CornerRadius = new CornerRadius(0) };
        var tempo = T("", "rotulo");
        var p = new StackPanel { Spacing = 12, Children = { passo, barra, tempo } };
        if (dica != null) p.Children.Add(T(dica, "rotulo", quebra: true));
        var inicio = DateTime.Now;
        var rel = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
        rel.Tick += (_, _) => { int s = (int)(DateTime.Now - inicio).TotalSeconds; tempo.Text = s < 3 ? "" : $"trabalhando há {s} s"; };
        p.AttachedToVisualTree += (_, _) => rel.Start();
        p.DetachedFromVisualTree += (_, _) => rel.Stop();
        return (p, passo, barra);
    }

    /// <summary>O erro no lugar da tela: o que houve, o que fazer, "Tentar de novo" e os detalhes para pedir ajuda.</summary>
    public static Secao Erro(Exception e, Action? tentar = null)
    {
        string refe = Referencia(e, "tela");
        var (titulo, texto) = Explica(e);
        var s = Vazio(titulo, texto, tentar != null ? Botao("Tentar de novo", true, tentar) : null);
        if (s.Child is StackPanel p) p.Children.Add(Detalhes(e, refe).Com(d => d.Margin = new Thickness(0, 14, 0, 0)));
        return s;
    }

    // ───── leitura dos dados da API (JsonNode) sem estourar: o que faltar vira o padrão ─────
    public static string S(this JsonNode? n, string chave, string padrao = "") => n?[chave] is JsonValue v && v.TryGetValue(out string? s) ? s ?? padrao : (n?[chave]?.ToString() ?? padrao);
    public static double? D(this JsonNode? n, string chave)
    {
        if (n?[chave] is not JsonValue v) return null;
        if (v.TryGetValue(out double d)) return d;
        if (v.TryGetValue(out int i)) return i;
        if (v.TryGetValue(out long l)) return l;
        if (v.TryGetValue(out decimal m)) return (double)m;
        return double.TryParse(v.ToString(), NumberStyles.Float, CultureInfo.InvariantCulture, out d) ? d : null;
    }
    public static bool B(this JsonNode? n, string chave) => n?[chave] is JsonValue v && v.TryGetValue(out bool b) && b;
    public static IEnumerable<JsonNode> A(this JsonNode? n, string chave) => (n?[chave] as JsonArray)?.Where(x => x != null).Select(x => x!) ?? Enumerable.Empty<JsonNode>();

    /// <summary>O "como desfazer" do motor vem no jeito do terminal; nas janelas, é a tela Desfazer.</summary>
    public static string ComoDesfazer(string s) => s.StartsWith("katharos desfazer") ? "a um clique, na tela Desfazer" : s;

    public static string Num(double? v, int casas = 0) => v.HasValue ? v.Value.ToString("N" + casas, Br) : "-";

    public static string Quando(string iso)
    {
        if (!DateTime.TryParse(iso, CultureInfo.InvariantCulture, DateTimeStyles.AssumeLocal, out var d)) return iso;
        var hoje = DateTime.Today;
        string dia = d.Date == hoje ? "hoje" : d.Date == hoje.AddDays(-1) ? "ontem" : d.ToString("dd/MM", Br);
        return $"{dia}, {d:HH:mm}";
    }

    /// <summary>Primeira letra maiúscula, sem quebrar com texto vazio.</summary>
    public static string Maiuscula(string? s) => string.IsNullOrEmpty(s) ? "" : char.ToUpper(s[0]) + s[1..];

    public static T Com<T>(this T c, Action<T> f) { f(c); return c; }
}

/// <summary>Base das telas: rolagem, montagem e a carga assíncrona com os estados de carregando e erro.</summary>
public abstract class Tela : UserControl
{
    protected readonly StackPanel Corpo = new();
    public event Action<string>? Pede;
    protected void Abre(string tela) => Pede?.Invoke(tela);

    protected Tela()
    {
        Content = new ScrollViewer { HorizontalScrollBarVisibility = Avalonia.Controls.Primitives.ScrollBarVisibility.Disabled, Content = Corpo };
        AttachedToVisualTree += async (_, _) => await Recarrega();
    }

    protected void Monta(params Control?[] partes)
    {
        Corpo.Children.Clear();
        foreach (var p in partes) if (p != null) Corpo.Children.Add(p);
    }

    public async Task Recarrega()
    {
        try { await Carrega(); }
        catch (Exception e)
        {
            Registro.Escreve($"{GetType().Name}: não carregou (o erro inteiro vem na linha seguinte)");
            Monta(Corpo.Children.FirstOrDefault() is Secao s && s.Child is Grid ? Corpo.Children[0] : null, Ui.Erro(e, async () => await Recarrega()));
        }
    }

    protected abstract Task Carrega();
}

/// <summary>Se a janela está fazendo algo agora (a barra lateral mostra, em âmbar, no lugar do estado do acompanhamento).</summary>
public static class Trabalho
{
    static int n;
    static string? texto;
    static DateTime desde;
    /// <summary>Só conta depois de 300 ms: uma ação rápida não acende a barra lateral à toa.</summary>
    public static bool Ativo => n > 0 && (DateTime.Now - desde).TotalMilliseconds >= 300;
    public static string Texto => texto ?? "Trabalhando…";
    public static void Comeca(string? oQue = null)
    {
        if (n++ == 0) desde = DateTime.Now;
        if (oQue != null) texto = oQue;
        DispatcherTimer.RunOnce(() => Janela.Atual?.AtualizaEstado(), TimeSpan.FromMilliseconds(320));
    }
    public static void Termina() { n = Math.Max(0, n - 1); if (n == 0) texto = null; Janela.Atual?.AtualizaEstado(); }
}
