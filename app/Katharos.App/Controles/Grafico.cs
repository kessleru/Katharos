using System.Globalization;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Media;
using Avalonia.Threading;

namespace Katharos.App.Controles;

/// <summary>Uma mudança aplicada, marcada no gráfico: onde (0 a 1 na largura) e o que foi ("inicialização e serviços · 12/11").</summary>
public record MarcaGrafico(double X, string Texto);

/// <summary>
/// Linha do tempo de uma métrica, no estilo do gráfico de boot do site: traço âmbar, área com degradê que some embaixo, limite tracejado.
/// Escala fixa (0 a Maximo) para que 90 % sempre pareça 90 %. Ponto sem leitura (NaN) é uma lacuna na linha, nunca zero.
/// Passando o mouse: uma linha vertical e o valor com a data; perto de uma marca, o que foi aplicado ali (clicar avisa a tela).
/// Com Eixos: valores à esquerda e datas embaixo (o gráfico ampliado). Zoom: a roda aproxima e afasta, arrastar escolhe um trecho.
/// </summary>
public class Grafico : Control
{
    public static readonly StyledProperty<IReadOnlyList<double>?> ValoresProperty = AvaloniaProperty.Register<Grafico, IReadOnlyList<double>?>(nameof(Valores));
    public static readonly StyledProperty<IReadOnlyList<double>?> Valores2Property = AvaloniaProperty.Register<Grafico, IReadOnlyList<double>?>(nameof(Valores2));
    public static readonly StyledProperty<double> MaximoProperty = AvaloniaProperty.Register<Grafico, double>(nameof(Maximo), 100);
    public static readonly StyledProperty<double> Maximo2Property = AvaloniaProperty.Register<Grafico, double>(nameof(Maximo2), 100);
    public static readonly StyledProperty<double> LimiteProperty = AvaloniaProperty.Register<Grafico, double>(nameof(Limite), double.NaN);
    public static readonly StyledProperty<IReadOnlyList<MarcaGrafico>?> MarcasProperty = AvaloniaProperty.Register<Grafico, IReadOnlyList<MarcaGrafico>?>(nameof(Marcas));
    /// <summary>A faixa do normal deste PC (p10 a p90 da linha de base), desenhada atrás da linha. NaN = sem faixa.</summary>
    public static readonly StyledProperty<double> FaixaMinProperty = AvaloniaProperty.Register<Grafico, double>(nameof(FaixaMin), double.NaN);
    public static readonly StyledProperty<double> FaixaMaxProperty = AvaloniaProperty.Register<Grafico, double>(nameof(FaixaMax), double.NaN);
    public static readonly StyledProperty<IBrush> CorProperty = AvaloniaProperty.Register<Grafico, IBrush>(nameof(Cor), Tema.Ambar);
    public static readonly StyledProperty<bool> EixosProperty = AvaloniaProperty.Register<Grafico, bool>(nameof(Eixos));
    public static readonly StyledProperty<bool> Mostra1Property = AvaloniaProperty.Register<Grafico, bool>(nameof(Mostra1), true);
    public static readonly StyledProperty<bool> Mostra2Property = AvaloniaProperty.Register<Grafico, bool>(nameof(Mostra2), true);
    static readonly StyledProperty<double> RevelaProperty = AvaloniaProperty.Register<Grafico, double>("Revela", 1);

    public IReadOnlyList<double>? Valores { get => GetValue(ValoresProperty); set => SetValue(ValoresProperty, value); }
    /// <summary>Uma segunda medida para comparar (escala própria, traço verde): "a RAM e as travadas andam juntas?"</summary>
    public IReadOnlyList<double>? Valores2 { get => GetValue(Valores2Property); set => SetValue(Valores2Property, value); }
    public double Maximo { get => GetValue(MaximoProperty); set => SetValue(MaximoProperty, value); }
    public double Maximo2 { get => GetValue(Maximo2Property); set => SetValue(Maximo2Property, value); }
    public double Limite { get => GetValue(LimiteProperty); set => SetValue(LimiteProperty, value); }
    public IReadOnlyList<MarcaGrafico>? Marcas { get => GetValue(MarcasProperty); set => SetValue(MarcasProperty, value); }
    public double FaixaMin { get => GetValue(FaixaMinProperty); set => SetValue(FaixaMinProperty, value); }
    public double FaixaMax { get => GetValue(FaixaMaxProperty); set => SetValue(FaixaMaxProperty, value); }
    public IBrush Cor { get => GetValue(CorProperty); set => SetValue(CorProperty, value); }
    public bool Eixos { get => GetValue(EixosProperty); set => SetValue(EixosProperty, value); }
    public bool Mostra1 { get => GetValue(Mostra1Property); set => SetValue(Mostra1Property, value); }
    public bool Mostra2 { get => GetValue(Mostra2Property); set => SetValue(Mostra2Property, value); }

    /// <summary>A data (ou hora) de cada ponto, para a dica e o eixo: "12/11".</summary>
    public IReadOnlyList<string>? Rotulos { get; set; }
    /// <summary>Como escrever um valor na dica ("46 s", "6,4 GB").</summary>
    public Func<double, string> Formata { get; set; } = v => v.ToString("N0", CultureInfo.GetCultureInfo("pt-BR"));
    public Func<double, string>? Formata2 { get; set; }
    /// <summary>A pessoa clicou numa marca de mudança.</summary>
    public event Action<MarcaGrafico>? MarcaClicada;
    /// <summary>Duplo clique: quem desenhou abre o gráfico ampliado.</summary>
    public event Action? PedeAmpliar;
    /// <summary>Zoom: os pontos visíveis (do primeiro ao último). Muda com a roda e com o arrasto, no gráfico com eixos.</summary>
    public int Inicio { get; private set; }
    public int Fim { get; private set; } = -1;
    public event Action? ZoomMudou;

    double? mouseX; double? arrastoDe;
    bool revelado;
    const double EsqEixo = 52, BaixoEixo = 22;

    static Grafico()
    {
        AffectsRender<Grafico>(ValoresProperty, Valores2Property, MaximoProperty, Maximo2Property, LimiteProperty, CorProperty, MarcasProperty,
                               FaixaMinProperty, FaixaMaxProperty, EixosProperty, Mostra1Property, Mostra2Property, RevelaProperty);
    }

    public Grafico()
    {
        Cursor = new Cursor(StandardCursorType.Cross);
        // a linha se desenha da esquerda para a direita só na primeira vez que aparece (nunca a cada atualização)
        AttachedToVisualTree += (_, _) =>
        {
            if (revelado || Movimento.Reduzido) { revelado = true; return; }
            revelado = true; SetValue(RevelaProperty, 0.0);
            var ini = DateTime.Now; var rel = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(16) };
            rel.Tick += (_, _) => { double f = Math.Min(1, (DateTime.Now - ini).TotalMilliseconds / 240); SetValue(RevelaProperty, 1 - Math.Pow(1 - f, 3)); if (f >= 1) rel.Stop(); };
            rel.Start();
        };
    }

    public void VerTudo() { Inicio = 0; Fim = -1; InvalidateVisual(); ZoomMudou?.Invoke(); }
    public bool ComZoom => Inicio > 0 || (Fim >= 0 && Fim < (Valores?.Count ?? 0) - 1);

    int N => Valores?.Count ?? 0;
    int Ini => Math.Clamp(Inicio, 0, Math.Max(0, N - 2));
    int Fi => Fim < 0 ? N - 1 : Math.Clamp(Fim, Ini + 1, N - 1);
    Rect Area => Eixos ? new Rect(EsqEixo, 6, Math.Max(4, Bounds.Width - EsqEixo - 8), Math.Max(4, Bounds.Height - BaixoEixo - 6)) : new Rect(0, 0, Bounds.Width, Bounds.Height);
    double XDe(int i, Rect a) => a.X + (i - Ini) * (a.Width - 1) / Math.Max(1, Fi - Ini);
    int IndiceEm(double x, Rect a) => Math.Clamp((int)Math.Round(Ini + (x - a.X) / Math.Max(1, a.Width - 1) * (Fi - Ini)), Ini, Fi);
    static double YDe(double v, double max, Rect a) => a.Bottom - 1 - Math.Clamp(v / max, 0, 1) * (a.Height - 2);

    protected override void OnPointerMoved(PointerEventArgs e)
    {
        base.OnPointerMoved(e);
        mouseX = e.GetPosition(this).X;
        InvalidateVisual();
    }

    protected override void OnPointerExited(PointerEventArgs e) { base.OnPointerExited(e); mouseX = null; arrastoDe = null; InvalidateVisual(); }

    protected override void OnPointerPressed(PointerPressedEventArgs e)
    {
        base.OnPointerPressed(e);
        if (e.ClickCount == 2) { PedeAmpliar?.Invoke(); return; }
        var x = e.GetPosition(this).X;
        if (MarcaPerto(x) is MarcaGrafico m) { MarcaClicada?.Invoke(m); return; }
        if (Eixos) arrastoDe = x;
    }

    protected override void OnPointerReleased(PointerReleasedEventArgs e)
    {
        base.OnPointerReleased(e);
        if (arrastoDe is double de && N > 2)
        {
            var a = Area; double ate = e.GetPosition(this).X;
            int i1 = IndiceEm(Math.Min(de, ate), a), i2 = IndiceEm(Math.Max(de, ate), a);
            if (i2 - i1 >= 2) { Inicio = i1; Fim = i2; ZoomMudou?.Invoke(); }
        }
        arrastoDe = null; InvalidateVisual();
    }

    protected override void OnPointerWheelChanged(PointerWheelEventArgs e)
    {
        base.OnPointerWheelChanged(e);
        if (!Eixos || N < 4) return;
        var a = Area; int centro = IndiceEm(e.GetPosition(this).X, a);
        int largura = Fi - Ini;
        int nova = Math.Clamp((int)Math.Round(largura * (e.Delta.Y > 0 ? 0.8 : 1.25)), 3, N - 1);
        int i1 = Math.Clamp(centro - (int)Math.Round((centro - Ini) * (double)nova / Math.Max(1, largura)), 0, N - 1 - nova);
        Inicio = i1; Fim = i1 + nova; e.Handled = true;
        InvalidateVisual(); ZoomMudou?.Invoke();
    }

    MarcaGrafico? MarcaPerto(double x)
    {
        if (Marcas == null || N < 2) return null;
        var a = Area;
        foreach (var m in Marcas)
        {
            double mx = a.X + (m.X * (N - 1) - Ini) / Math.Max(1, Fi - Ini) * (a.Width - 1);
            if (Math.Abs(mx - x) <= 5) return m;
        }
        return null;
    }

    public override void Render(DrawingContext c)
    {
        var v = Valores;
        var a = Area;
        if (v == null || v.Count < 2 || a.Width < 4 || a.Height < 4) return;
        c.FillRectangle(Brushes.Transparent, new Rect(Bounds.Size));   // o mouse "pega" no gráfico inteiro, não só na linha
        double revela = GetValue(RevelaProperty);
        var _clip = c.PushClip(new Rect(0, 0, a.X + a.Width * revela, Bounds.Height));

        if (!double.IsNaN(FaixaMin) && !double.IsNaN(FaixaMax) && FaixaMax > FaixaMin && Mostra1)
        {
            double y1 = YDe(FaixaMax, Maximo, a), y2 = YDe(FaixaMin, Maximo, a);
            c.FillRectangle(new SolidColorBrush(Color.FromArgb(22, 0xEC, 0xE6, 0xD8)), new Rect(a.X, y1, a.Width, Math.Max(1, y2 - y1)));
        }
        if (Eixos) DesenhaEixos(c, a);
        if (!double.IsNaN(Limite))
        {
            double y = Math.Round(YDe(Limite, Maximo, a)) + .5;
            c.DrawLine(new Pen(Tema.LinhaForte, 1, new DashStyle(new double[] { 3, 3 }, 0)), new Point(a.X, y), new Point(a.Right, y));
        }
        // marcas de mudança: um tique discreto embaixo e uma linha bem fraca (antes eram tracejados âmbar fortes, que juntos pareciam pontilhado)
        if (Marcas != null)
            foreach (var m in Marcas)
            {
                double x = a.X + (m.X * (v.Count - 1) - Ini) / Math.Max(1, Fi - Ini) * (a.Width - 1);
                if (x < a.X - 1 || x > a.Right + 1) continue;
                x = Math.Round(x) + .5;
                c.DrawLine(new Pen(new SolidColorBrush(Color.FromArgb(70, Tema.CorAmbar.R, Tema.CorAmbar.G, Tema.CorAmbar.B)), 1), new Point(x, a.Y), new Point(x, a.Bottom));
                c.FillRectangle(Tema.Ambar, new Rect(x - 2.5, a.Bottom - 5, 5, 5));
            }
        if (Mostra1) DesenhaSerie(c, v, Maximo, (Cor as ISolidColorBrush)?.Color ?? Tema.CorAmbar, a, true);
        if (Valores2 is { Count: > 1 } v2 && Mostra2) DesenhaSerie(c, v2, Maximo2, Tema.CorVerde, a, false);
        _clip.Dispose();

        if (arrastoDe is double de && mouseX is double mx2)
            c.FillRectangle(new SolidColorBrush(Color.FromArgb(26, Tema.CorAmbar.R, Tema.CorAmbar.G, Tema.CorAmbar.B)), new Rect(Math.Min(de, mx2), a.Y, Math.Abs(mx2 - de), a.Height));
        if (mouseX is double mx && mx >= a.X - 2 && mx <= a.Right + 2) DesenhaDica(c, a, mx);
    }

    void DesenhaSerie(DrawingContext c, IReadOnlyList<double> v, double max, Color cor, Rect a, bool area)
    {
        // cada trecho com leitura vira uma figura; o dia sem leitura fica em branco
        var linha = new StreamGeometry(); var fundo = new StreamGeometry();
        using (var gl = linha.Open())
        using (var ga = fundo.Open())
        {
            int i = Ini;
            while (i <= Fi)
            {
                while (i <= Fi && (i >= v.Count || double.IsNaN(v[i]))) i++;
                if (i > Fi) break;
                int ini = i;
                gl.BeginFigure(new Point(XDe(i, a), YDe(v[i], max, a)), false);
                ga.BeginFigure(new Point(XDe(i, a), a.Bottom), true);
                ga.LineTo(new Point(XDe(i, a), YDe(v[i], max, a)));
                i++;
                while (i <= Fi && i < v.Count && !double.IsNaN(v[i])) { var p = new Point(XDe(i, a), YDe(v[i], max, a)); gl.LineTo(p); ga.LineTo(p); i++; }
                // ponto sozinho (um dia entre lacunas): um traço curto, para não sumir
                if (i - 1 == ini) gl.LineTo(new Point(XDe(ini, a) + 1.5, YDe(v[ini], max, a)));
                gl.EndFigure(false);
                ga.LineTo(new Point(XDe(i - 1, a), a.Bottom));
                ga.EndFigure(true);
            }
        }
        if (area)
        {
            var degrade = new LinearGradientBrush
            {
                StartPoint = new RelativePoint(0, 0, RelativeUnit.Relative), EndPoint = new RelativePoint(0, 1, RelativeUnit.Relative),
                GradientStops = { new GradientStop(Color.FromArgb(60, cor.R, cor.G, cor.B), 0), new GradientStop(Color.FromArgb(0, cor.R, cor.G, cor.B), 1) }
            };
            c.DrawGeometry(degrade, null, fundo);
        }
        c.DrawGeometry(null, new Pen(new SolidColorBrush(cor), Eixos ? 2 : 1.6, lineJoin: PenLineJoin.Round, lineCap: PenLineCap.Round), linha);
    }

    static FormattedText Texto(string s, double tam, IBrush cor) =>
        new(s, CultureInfo.CurrentCulture, FlowDirection.LeftToRight, new Typeface(Tema.Mono), tam, cor);

    void DesenhaEixos(DrawingContext c, Rect a)
    {
        var fina = new Pen(Tema.Linha, 1);
        for (int k = 0; k <= 4; k++)
        {
            double val = Maximo * k / 4, y = Math.Round(YDe(val, Maximo, a)) + .5;
            c.DrawLine(fina, new Point(a.X, y), new Point(a.Right, y));
            var t = Texto(Formata(val), 11, Tema.Apagado);
            c.DrawText(t, new Point(a.X - t.Width - 8, y - t.Height / 2));
        }
        if (Rotulos is { Count: > 1 } r)
        {
            int passos = Math.Max(1, (int)(a.Width / 90));
            for (int k = 0; k <= passos; k++)
            {
                int i = Ini + (int)Math.Round((Fi - Ini) * k / (double)passos);
                if (i >= r.Count) continue;
                var t = Texto(r[i], 11, Tema.Apagado);
                double x = Math.Clamp(XDe(i, a) - t.Width / 2, a.X, a.Right - t.Width);
                c.DrawText(t, new Point(x, a.Bottom + 6));
            }
        }
    }

    void DesenhaDica(DrawingContext c, Rect a, double mx)
    {
        var v = Valores!;
        int i = IndiceEm(mx, a);
        double x = Math.Round(XDe(i, a)) + .5;
        c.DrawLine(new Pen(Tema.LinhaForte, 1), new Point(x, a.Y), new Point(x, a.Bottom));
        var linhas = new List<(string, IBrush)>();
        if (Rotulos != null && i < Rotulos.Count) linhas.Add((Rotulos[i], Tema.Apagado));
        if (Mostra1) linhas.Add((i < v.Count && !double.IsNaN(v[i]) ? Formata(v[i]) : "sem leitura", Tema.Osso));
        if (Valores2 is { } v2 && Mostra2 && i < v2.Count) linhas.Add((double.IsNaN(v2[i]) ? "sem leitura" : (Formata2 ?? Formata)(v2[i]), Tema.Verde));
        if (MarcaPerto(mx) is MarcaGrafico m) linhas.Add(("aplicado: " + m.Texto, Tema.Ambar));
        if (Mostra1 && i < v.Count && !double.IsNaN(v[i])) c.DrawEllipse(Tema.Fundo, new Pen(Cor, 2), new Point(x, YDe(v[i], Maximo, a)), 3.5, 3.5);
        var ts = linhas.Select(l => Texto(l.Item1, 12, l.Item2)).ToList();
        double w = ts.Max(t => t.Width) + 16, h = ts.Sum(t => t.Height) + 10;
        double bx = x + 10 + w > Bounds.Width ? x - 10 - w : x + 10, by = a.Y + 4;
        c.FillRectangle(Tema.Painel, new Rect(bx, by, w, h));
        c.DrawRectangle(new Pen(Tema.LinhaForte, 1), new Rect(bx + .5, by + .5, w - 1, h - 1));
        double yy = by + 5;
        foreach (var t in ts) { c.DrawText(t, new Point(bx + 8, yy)); yy += t.Height; }
    }
}

/// <summary>O minigráfico de uma linha (24 horas de um programa): só a linha, com lacunas onde não houve leitura.</summary>
public class Minigrafico : Control
{
    public double?[] Valores { get; set; } = Array.Empty<double?>();

    public override void Render(DrawingContext c)
    {
        var v = Valores;
        double w = Bounds.Width, h = Bounds.Height;
        var vs = v.Where(x => x.HasValue).Select(x => x!.Value).ToList();
        c.DrawLine(new Pen(Tema.Linha, 1), new Point(0, h - .5), new Point(w, h - .5));
        if (v.Length < 2 || vs.Count == 0) return;
        double max = Math.Max(1, vs.Max() * 1.1);
        var pen = new Pen(Tema.Ambar, 1.4, lineJoin: PenLineJoin.Round, lineCap: PenLineCap.Round);
        Point P(int i) => new(i * (w - 2) / (v.Length - 1) + 1, h - 2 - v[i]!.Value / max * (h - 4));
        for (int i = 1; i < v.Length; i++)
            if (v[i].HasValue && v[i - 1].HasValue) c.DrawLine(pen, P(i - 1), P(i));
            else if (v[i].HasValue && (i == v.Length - 1 || !v[i + 1].HasValue) && !v[i - 1].HasValue) c.DrawEllipse(Tema.Ambar, null, P(i), 1.2, 1.2);
    }
}
