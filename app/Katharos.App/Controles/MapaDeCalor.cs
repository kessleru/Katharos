using Avalonia;
using Avalonia.Controls;
using Avalonia.Input;
using Avalonia.Media;

namespace Katharos.App.Controles;

/// <summary>
/// Calendário das últimas semanas, um quadrado por dia (colunas = semanas, linhas = dias da semana), mais forte quanto maior o valor.
/// UI 2: as horas de jogo de cada dia no Histórico. Dia sem dado fica só com o contorno. A dica mostra o dia e o valor.
/// </summary>
public class MapaDeCalor : Control
{
    public Dictionary<DateTime, double> Valores { get; set; } = new();
    public int Semanas { get; set; } = 12;
    public Func<double, string> Formata { get; set; } = v => v.ToString("0.#");
    const double Lado = 13, Vao = 3;

    protected override Size MeasureOverride(Size d) => new(Semanas * (Lado + Vao) + 30, 7 * (Lado + Vao) + 18);

    DateTime Inicio() { var hoje = DateTime.Today; int dow = ((int)hoje.DayOfWeek + 6) % 7; return hoje.AddDays(-dow - 7 * (Semanas - 1)); }

    public override void Render(DrawingContext g)
    {
        double max = Valores.Count > 0 ? Math.Max(0.01, Valores.Values.Max()) : 1;
        var ini = Inicio();
        var contorno = new Pen(Tema.Linha, 1);
        var rotulos = new[] { "seg", "", "qua", "", "sex", "", "dom" };
        for (int l = 0; l < 7; l++)
            if (rotulos[l] != "")
                g.DrawText(new FormattedText(rotulos[l], System.Globalization.CultureInfo.CurrentCulture, FlowDirection.LeftToRight, new Typeface(Tema.Mono), 9.5, Tema.Apagado),
                           new Point(0, 18 + l * (Lado + Vao)));
        for (int s = 0; s < Semanas; s++)
        {
            var dia = ini.AddDays(s * 7);
            if (dia.Day <= 7)
                g.DrawText(new FormattedText(dia.ToString("MMM").TrimEnd('.'), System.Globalization.CultureInfo.CurrentCulture, FlowDirection.LeftToRight, new Typeface(Tema.Mono), 9.5, Tema.Apagado),
                           new Point(30 + s * (Lado + Vao), 0));
            for (int l = 0; l < 7; l++)
            {
                var d = ini.AddDays(s * 7 + l);
                if (d > DateTime.Today) continue;
                var r = new Rect(30 + s * (Lado + Vao), 16 + l * (Lado + Vao), Lado, Lado);
                if (Valores.TryGetValue(d, out var v) && v > 0)
                {
                    byte a = (byte)(60 + 195 * Math.Clamp(v / max, 0, 1));
                    g.FillRectangle(new SolidColorBrush(Color.FromArgb(a, Tema.CorAmbar.R, Tema.CorAmbar.G, Tema.CorAmbar.B)), r);
                }
                else g.DrawRectangle(null, contorno, r.Deflate(0.5));
            }
        }
    }

    protected override void OnPointerMoved(PointerEventArgs e)
    {
        base.OnPointerMoved(e);
        var p = e.GetPosition(this);
        int s = (int)((p.X - 30) / (Lado + Vao)), l = (int)((p.Y - 16) / (Lado + Vao));
        if (p.X < 30 || p.Y < 16 || s < 0 || s >= Semanas || l < 0 || l > 6) { ToolTip.SetTip(this, null); return; }
        var d = Inicio().AddDays(s * 7 + l);
        ToolTip.SetTip(this, d > DateTime.Today ? null : d.ToString("dd/MM") + ": " + (Valores.TryGetValue(d, out var v) && v > 0 ? Formata(v) : "nada"));
    }
}
