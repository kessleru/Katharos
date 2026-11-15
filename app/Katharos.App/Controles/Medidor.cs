using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>
/// Barra fina segmentada, como um VU (referência: Teenage Engineering): quanto do máximo está em uso agora. Os segmentos acesos ficam
/// verdes; do limite para cima, todos âmbar; o último, cheio, vermelho. Só redesenha quando o valor muda.
/// </summary>
public class Medidor : Control
{
    double valor;
    public double Maximo { get; set; } = 100;
    public double Limite { get; set; } = 85;
    public int Segmentos { get; set; } = 20;

    public double Valor
    {
        get => valor;
        set { if (Math.Abs(value - valor) < 0.01) return; valor = value; InvalidateVisual(); }
    }

    public Medidor() { Height = 6; }

    public override void Render(DrawingContext g)
    {
        if (Bounds.Width <= 0 || Maximo <= 0) return;
        double vao = 2, w = (Bounds.Width - vao * (Segmentos - 1)) / Segmentos;
        int acesos = (int)Math.Round(Math.Clamp(valor / Maximo, 0, 1) * Segmentos);
        IBrush aceso = valor >= Limite ? Tema.Ambar : Tema.Verde;   // a barra inteira diz o estado: verde folgado, âmbar no limite
        for (int i = 0; i < Segmentos; i++)
        {
            IBrush cor = i >= acesos ? Tema.Linha : i == Segmentos - 1 ? Tema.Vermelho : aceso;
            g.FillRectangle(cor, new Rect(i * (w + vao), 0, w, Bounds.Height));
        }
    }
}
