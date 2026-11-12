using Avalonia;
using Avalonia.Controls;

namespace Katharos.App.Controles;

/// <summary>
/// Uma linha que se ajusta à largura: [esquerda] [meio] [direita]. Com espaço, tudo lado a lado; quando o meio ficaria com menos de
/// MinMeio pixels (janela estreita, texto longo, botão largo), a parte da direita desce para baixo do meio, alinhada com ele. Assim o
/// texto nunca é espremido nem invade o botão, e o botão nunca sai da tela.
/// </summary>
public class Fileira : Panel
{
    public Control? Esquerda { get; init; }
    public required Control Meio { get; init; }
    public Control? Direita { get; init; }
    public double MinMeio { get; init; } = 300;
    public double Espaco { get; init; } = 16;
    bool empilhado;

    protected override void OnInitialized()
    {
        base.OnInitialized();
        foreach (var c in new[] { Esquerda, Meio, Direita }) if (c != null && !Children.Contains(c)) Children.Add(c);
    }

    protected override Size MeasureOverride(Size disp)
    {
        double w = double.IsInfinity(disp.Width) ? 1200 : disp.Width;
        Esquerda?.Measure(new Size(w, double.PositiveInfinity));
        Direita?.Measure(new Size(w, double.PositiveInfinity));
        double we = Esquerda?.DesiredSize.Width ?? 0, wd = Direita?.DesiredSize.Width ?? 0;
        double resto = w - we - (Direita != null ? wd + Espaco : 0);
        empilhado = Direita != null && resto < MinMeio;
        double wm = Math.Max(0, empilhado ? w - we : resto);
        Meio.Measure(new Size(wm, double.PositiveInfinity));
        double hm = Meio.DesiredSize.Height, he = Esquerda?.DesiredSize.Height ?? 0, hd = Direita?.DesiredSize.Height ?? 0;
        double h = empilhado ? Math.Max(he, hm + Espaco * 0.75 + hd) : Math.Max(he, Math.Max(hm, hd));
        return new Size(double.IsInfinity(disp.Width) ? we + wm + (empilhado ? 0 : wd + Espaco) : w, h);
    }

    protected override Size ArrangeOverride(Size final)
    {
        double we = Esquerda?.DesiredSize.Width ?? 0, wd = Direita?.DesiredSize.Width ?? 0;
        Esquerda?.Arrange(new Rect(0, 0, we, Esquerda.DesiredSize.Height));
        if (empilhado)
        {
            double hm = Meio.DesiredSize.Height;
            Meio.Arrange(new Rect(we, 0, Math.Max(0, final.Width - we), hm));
            Direita!.Arrange(new Rect(we, hm + Espaco * 0.75, Math.Min(wd, Math.Max(0, final.Width - we)), Direita.DesiredSize.Height));
        }
        else
        {
            double wm = Math.Max(0, final.Width - we - (Direita != null ? wd + Espaco : 0));
            // o meio no centro da altura quando a linha é mais alta que ele (botão alto ao lado de uma linha de texto)
            double ym = Math.Max(0, (final.Height - Meio.DesiredSize.Height) / 2);
            Meio.Arrange(new Rect(we, Esquerda != null ? 0 : ym, wm, Meio.DesiredSize.Height));
            if (Direita != null) Direita.Arrange(new Rect(final.Width - wd, Math.Max(0, (final.Height - Direita.DesiredSize.Height) / 2), wd, Direita.DesiredSize.Height));
        }
        return final;
    }
}
