using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>
/// Linha do tempo de uma métrica, no estilo do gráfico de boot do site: traço âmbar, área com degradê que some embaixo, limite tracejado.
/// Escala fixa (0 a Maximo) para que 90 % sempre pareça 90 %.
/// </summary>
public class Grafico : Control
{
    public static readonly StyledProperty<IReadOnlyList<double>?> ValoresProperty = AvaloniaProperty.Register<Grafico, IReadOnlyList<double>?>(nameof(Valores));
    public static readonly StyledProperty<double> MaximoProperty = AvaloniaProperty.Register<Grafico, double>(nameof(Maximo), 100);
    public static readonly StyledProperty<double> LimiteProperty = AvaloniaProperty.Register<Grafico, double>(nameof(Limite), double.NaN);
    /// <summary>Marcas verticais (0 a 1 na largura): quando cada mudança entrou.</summary>
    public static readonly StyledProperty<IReadOnlyList<double>?> MarcasProperty = AvaloniaProperty.Register<Grafico, IReadOnlyList<double>?>(nameof(Marcas));
    public IReadOnlyList<double>? Marcas { get => GetValue(MarcasProperty); set => SetValue(MarcasProperty, value); }
    public static readonly StyledProperty<IBrush> CorProperty = AvaloniaProperty.Register<Grafico, IBrush>(nameof(Cor), Tema.Ambar);

    public IReadOnlyList<double>? Valores { get => GetValue(ValoresProperty); set => SetValue(ValoresProperty, value); }
    public double Maximo { get => GetValue(MaximoProperty); set => SetValue(MaximoProperty, value); }
    public double Limite { get => GetValue(LimiteProperty); set => SetValue(LimiteProperty, value); }
    public IBrush Cor { get => GetValue(CorProperty); set => SetValue(CorProperty, value); }

    static Grafico() { AffectsRender<Grafico>(ValoresProperty, MaximoProperty, LimiteProperty, CorProperty, MarcasProperty); }

    public override void Render(DrawingContext c)
    {
        var v = Valores;
        double w = Bounds.Width, h = Bounds.Height;
        if (v == null || v.Count < 2 || w < 4 || h < 4) return;
        Point P(int i) => new(i * (w - 1) / (v.Count - 1), h - 1 - Math.Clamp(v[i] / Maximo, 0, 1) * (h - 2));
        var linha = new StreamGeometry();
        using (var g = linha.Open())
        {
            g.BeginFigure(P(0), false);
            for (int i = 1; i < v.Count; i++) g.LineTo(P(i));
            g.EndFigure(false);
        }
        var area = new StreamGeometry();
        using (var g = area.Open())
        {
            g.BeginFigure(new Point(0, h), true);
            for (int i = 0; i < v.Count; i++) g.LineTo(P(i));
            g.LineTo(new Point(w, h));
            g.EndFigure(true);
        }
        var cor = (Cor as ISolidColorBrush)?.Color ?? Tema.CorAmbar;
        var degrade = new LinearGradientBrush
        {
            StartPoint = new RelativePoint(0, 0, RelativeUnit.Relative), EndPoint = new RelativePoint(0, 1, RelativeUnit.Relative),
            GradientStops = { new GradientStop(Color.FromArgb(60, cor.R, cor.G, cor.B), 0), new GradientStop(Color.FromArgb(0, cor.R, cor.G, cor.B), 1) }
        };
        c.DrawGeometry(degrade, null, area);
        if (!double.IsNaN(Limite))
        {
            double y = Math.Round(h - 1 - Math.Clamp(Limite / Maximo, 0, 1) * (h - 2)) + .5;
            c.DrawLine(new Pen(Tema.LinhaForte, 1, new DashStyle(new double[] { 3, 3 }, 0)), new Point(0, y), new Point(w, y));
        }
        if (Marcas != null)
            foreach (var m in Marcas)
            {
                double x = Math.Round(Math.Clamp(m, 0, 1) * (w - 1)) + .5;
                c.DrawLine(new Pen(Tema.Ambar, 1, new DashStyle(new double[] { 2, 3 }, 0)), new Point(x, 0), new Point(x, h));
            }
        c.DrawGeometry(null, new Pen(Cor, 1.6, lineJoin: PenLineJoin.Round), linha);
    }
}
