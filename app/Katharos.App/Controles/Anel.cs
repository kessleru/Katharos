using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>Um anel fino que enche de 0 a 100 (a nota do PC, a bateria). Só desenho: nenhuma animação, nada roda em segundo plano.</summary>
public class Anel : Control
{
    public double Valor { get; set; }
    public IBrush Cor { get; set; } = Tema.Ambar;
    public double Espessura { get; set; } = 5;

    public override void Render(DrawingContext g)
    {
        double lado = Math.Min(Bounds.Width, Bounds.Height), r = lado / 2 - Espessura / 2;
        var c = new Point(Bounds.Width / 2, Bounds.Height / 2);
        g.DrawEllipse(null, new Pen(Tema.Linha, Espessura), c, r, r);
        double f = Math.Clamp(Valor / 100.0, 0, 1);
        if (f <= 0) return;
        if (f >= 0.999) { g.DrawEllipse(null, new Pen(Cor, Espessura), c, r, r); return; }
        double a0 = -Math.PI / 2, a1 = a0 + f * 2 * Math.PI;
        var geo = new StreamGeometry();
        using (var ctx = geo.Open())
        {
            ctx.BeginFigure(new Point(c.X + r * Math.Cos(a0), c.Y + r * Math.Sin(a0)), false);
            ctx.ArcTo(new Point(c.X + r * Math.Cos(a1), c.Y + r * Math.Sin(a1)), new Size(r, r), 0, f > 0.5, SweepDirection.Clockwise);
            ctx.EndFigure(false);
        }
        g.DrawGeometry(null, new Pen(Cor, Espessura, lineCap: PenLineCap.Flat), geo);
    }
}
