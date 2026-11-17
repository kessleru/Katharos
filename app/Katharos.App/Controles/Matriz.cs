using Avalonia;
using Avalonia.Controls;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>
/// Número em matriz de pontos 5×7 (referência: Nothing OS e o visor do OP-1 da Teenage Engineering). A assinatura visual da UI 2,
/// usada com parcimônia: a nota do PC e o FPS no jogo. Só desenho; sem animação.
/// </summary>
public class Matriz : Control
{
    // cada caractere: 7 linhas de 5 bits (bit 4 = coluna da esquerda)
    static readonly Dictionary<char, byte[]> Fonte = new()
    {
        ['0'] = new byte[] { 0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E }, ['1'] = new byte[] { 0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E },
        ['2'] = new byte[] { 0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F }, ['3'] = new byte[] { 0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E },
        ['4'] = new byte[] { 0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02 }, ['5'] = new byte[] { 0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E },
        ['6'] = new byte[] { 0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E }, ['7'] = new byte[] { 0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08 },
        ['8'] = new byte[] { 0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E }, ['9'] = new byte[] { 0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C },
        ['-'] = new byte[] { 0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00 }, [' '] = new byte[7],
    };

    string texto = "";
    public string Texto { get => texto; set { texto = value ?? ""; InvalidateMeasure(); InvalidateVisual(); } }
    public IBrush Cor { get; set; } = Tema.Osso;
    /// <summary>Distância entre pontos, em px.</summary>
    public double Passo { get; set; } = 6;

    protected override Size MeasureOverride(Size disponivel)
    {
        int n = Math.Max(1, texto.Length);
        return new Size(n * 6 * Passo - Passo, 7 * Passo);
    }

    public override void Render(DrawingContext g)
    {
        double r = Passo * 0.36;
        var apagado = new SolidColorBrush(Color.FromArgb(28, 255, 255, 255));
        for (int c = 0; c < texto.Length; c++)
        {
            var linhas = Fonte.TryGetValue(texto[c], out var f) ? f : Fonte[' '];
            for (int y = 0; y < 7; y++)
                for (int x = 0; x < 5; x++)
                {
                    bool aceso = (linhas[y] >> (4 - x) & 1) == 1;
                    var p = new Point(c * 6 * Passo + x * Passo + Passo / 2, y * Passo + Passo / 2);
                    g.DrawEllipse(aceso ? Cor : apagado, null, p, r, r);
                }
        }
    }
}
