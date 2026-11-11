using System.Globalization;
using System.Text.Json.Nodes;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Documents;
using Avalonia.Layout;
using Avalonia.Media;
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

    /// <summary>Botão que faz algo assíncrono (conversa com o motor): um erro vira a caixa de erro, nunca fecha o aplicativo.</summary>
    public static Button Botao(string texto, bool primario, Func<Task> acao, bool ativo = true) => Botao(texto, primario, (Action)(async () =>
    {
        try { await acao(); }
        catch (Exception e) { MostraErro(e); }
    }), ativo);

    public static void MostraErro(Exception e)
    {
        Registro.Escreve("erro na tela: " + e);
        var j = Janela.Atual;
        if (j == null) return;
        string texto = e is ErroDoMotor m ? m.Message : "Algo deu errado: " + e.Message;
        j.MostraCaixa(Janela.Caixa("Não deu certo", T(texto + " Nada além disso mudou.", "sub", quebra: true), Botao("Fechar", true, j.FechaCaixa)), true);
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
        var passo = T(texto, null, Tema.Osso, 15);
        var barra = new ProgressBar { IsIndeterminate = true, Height = 3, MinHeight = 3, Foreground = Tema.Ambar, Background = Tema.Linha, CornerRadius = new CornerRadius(0), MaxWidth = 480, HorizontalAlignment = HorizontalAlignment.Left };
        var p = new StackPanel { Spacing = 14, Margin = new Thickness(32, 40), Children = { passo, barra } };
        return (S(p), passo, barra);
    }

    public static Secao Erro(Exception e, Action? tentar = null)
    {
        string texto = e is ErroDoMotor m ? m.Message : "Algo deu errado: " + e.Message;
        return Vazio("Não deu certo", texto + (e is ErroDoMotor { Codigo: "sem_motor" } ? "" : " O detalhe ficou em ~/.katharos/interface.log."),
                     tentar != null ? Botao("Tentar de novo", false, tentar) : null);
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
            Registro.Escreve($"{GetType().Name}: {e}");
            Monta(Corpo.Children.FirstOrDefault() is Secao s && s.Child is Grid ? Corpo.Children[0] : null, Ui.Erro(e, async () => await Recarrega()));
        }
    }

    protected abstract Task Carrega();
}
