using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>
/// Uma faixa da tela, como as seções do site: ocupa a largura toda, o conteúdo fica entre as duas linhas verticais, uma linha embaixo
/// de ponta a ponta e um "+" onde as linhas se cruzam.
/// </summary>
public class Secao : Decorator
{
    public static readonly StyledProperty<bool> LinhaEmbaixoProperty = AvaloniaProperty.Register<Secao, bool>(nameof(LinhaEmbaixo), true);
    public static readonly StyledProperty<bool> CruzesProperty = AvaloniaProperty.Register<Secao, bool>(nameof(Cruzes), true);

    public bool LinhaEmbaixo { get => GetValue(LinhaEmbaixoProperty); set => SetValue(LinhaEmbaixoProperty, value); }
    public bool Cruzes { get => GetValue(CruzesProperty); set => SetValue(CruzesProperty, value); }

    static readonly IPen Fina = new Pen(Tema.Linha, 1);
    static readonly IPen Cruz = new Pen(Tema.LinhaForte, 1);

    static Secao() { AffectsRender<Secao>(LinhaEmbaixoProperty, CruzesProperty); }

    protected override Size MeasureOverride(Size disponivel)
    {
        var dentro = new Size(Math.Max(0, disponivel.Width - 2 * Tema.Margem), disponivel.Height);
        Child?.Measure(dentro);
        var d = Child?.DesiredSize ?? default;
        return new Size(d.Width + 2 * Tema.Margem, d.Height + (LinhaEmbaixo ? 1 : 0));
    }

    protected override Size ArrangeOverride(Size final)
    {
        Child?.Arrange(new Rect(Tema.Margem, 0, Math.Max(0, final.Width - 2 * Tema.Margem), Math.Max(0, final.Height - (LinhaEmbaixo ? 1 : 0))));
        return final;
    }

    public override void Render(DrawingContext c)
    {
        double w = Bounds.Width, h = Bounds.Height, e = Tema.Margem + .5, d = w - Tema.Margem - .5;
        c.DrawLine(Fina, new Point(e, 0), new Point(e, h));
        c.DrawLine(Fina, new Point(d, 0), new Point(d, h));
        if (!LinhaEmbaixo) return;
        c.DrawLine(Fina, new Point(0, h - .5), new Point(w, h - .5));
        if (!Cruzes) return;
        foreach (var x in new[] { e, d })
        {
            c.DrawLine(Cruz, new Point(x - 4, h - .5), new Point(x + 4, h - .5));
            c.DrawLine(Cruz, new Point(x, h - 4.5), new Point(x, h + 3.5));
        }
    }
}
