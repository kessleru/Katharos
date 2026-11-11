using Avalonia;
using Avalonia.Controls;
using Avalonia.Controls.Shapes;
using Avalonia.Media;

namespace Katharos.App;

/// <summary>
/// Ícones de traço, leves: só o desenho vetorial (sem fonte de ícones nem imagem). Desenhos do Lucide (lucide.dev, licença ISC,
/// Copyright (c) 2026 Lucide Icons and Contributors), convertidos para caminhos. Um por categoria e por ação; nada além.
/// </summary>
public static class Icones
{
    static readonly Dictionary<string, string> desenhos = new()
    {
        ["seguranca"] = "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z m9 12 2 2 4-4",
        ["inicializacao"] = "M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5 M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09 M9 12a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.4 22.4 0 0 1-4 2z M9 12H4s.55-3.03 2-4c1.62-1.08 5 .05 5 .05",
        ["memoria"] = "M12 12v-2 M12 18v-2 M16 12v-2 M16 18v-2 M2 11h1.5 M20 18v-2 M20.5 11H22 M4 18v-2 M8 12v-2 M8 18v-2 M4 6h16a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-6a2 2 0 0 1 2 -2z",
        ["disco"] = "M10 16h.01 M2.212 11.577a2 2 0 0 0-.212.896V18a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-5.527a2 2 0 0 0-.212-.896L18.55 5.11A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z M21.946 12.013H2.054 M6 16h.01",
        ["jogos"] = "M6 11L10 11 M8 9L8 13 M15 12L15.01 12 M18 10L18.01 10 M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z",
        ["saude"] = "M2 9.5a5.5 5.5 0 0 1 9.591-3.676.56.56 0 0 0 .818 0A5.49 5.49 0 0 1 22 9.5c0 2.29-1.5 4-3 5.5l-5.492 5.313a2 2 0 0 1-3 .019L5 15c-1.5-1.5-3-3.2-3-5.5 M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27",
        ["geral"] = "m12 14 4-4 M3.34 19a10 10 0 1 1 17.32 0",
        ["cpu"] = "M12 20v2 M12 2v2 M17 20v2 M17 2v2 M2 12h2 M2 17h2 M2 7h2 M20 12h2 M20 17h2 M20 7h2 M7 20v2 M7 2v2 M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z M9 8h6a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-6a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1z",
        ["rede"] = "M12 20h.01 M2 8.82a15 15 0 0 1 20 0 M5 12.859a10 10 0 0 1 14 0 M8.5 16.429a5 5 0 0 1 7 0",
        ["temperatura"] = "M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z",
        ["aovivo"] = "M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2",
        ["energia"] = "M15.914 4a1.5 1.5 0 00-2.474-1.561l-9 9A1.5 1.5 0 005.5 14h4.002a.5.5 0 01.471.666L8.086 20a1.5 1.5 0 002.475 1.56l9-9A1.5 1.5 0 0018.5 10h-3.997a.5.5 0 01-.472-.667z",
        ["ok"] = "M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 m16 9-5.5 5.5L8 12",
        ["alerta"] = "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3 M12 9v4 M12 17h.01",
        ["info"] = "M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 16v-4 M12 8h.01",
        ["tempo"] = "M2 12a10 10 0 1 0 20 0a10 10 0 1 0 -20 0 M12 6v6l4 2",
        ["desfazer"] = "M9 14 4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11",
        ["buscar"] = "m21 21-4.34-4.34 M3 11a8 8 0 1 0 16 0a8 8 0 1 0 -16 0",
        ["central"] = "M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z M20 2v4 M22 4h-4 M2 20a2 2 0 1 0 4 0a2 2 0 1 0 -4 0",
        ["desligar"] = "M12 2v10 M18.4 6.6a9 9 0 1 1-12.77.04",
        ["camadas"] = "M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12 M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17",
        ["historico"] = "M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8 M3 3v5h5 M12 7v5l4 2",
        ["inicio"] = "M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8 M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
        ["enviar"] = "M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z m21.854 2.147-10.94 10.939",
        ["config"] = "M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915 M9 12a3 3 0 1 0 6 0a3 3 0 1 0 -6 0",
        ["otimizar"] = "M10 5H3 M12 19H3 M14 3v4 M16 17v4 M21 12h-9 M21 19h-5 M21 5h-7 M8 10v4 M8 12H3",
        ["raiox"] = "M3 7V5a2 2 0 0 1 2-2h2 M17 3h2a2 2 0 0 1 2 2v2 M21 17v2a2 2 0 0 1-2 2h-2 M7 21H5a2 2 0 0 1-2-2v-2 M9 12a3 3 0 1 0 6 0a3 3 0 1 0 -6 0 m16 16-1.9-1.9",
        ["limpar"] = "m16 22-1-4 M19 14a1 1 0 0 0 1-1v-1a2 2 0 0 0-2-2h-3a1 1 0 0 1-1-1V4a2 2 0 0 0-4 0v5a1 1 0 0 1-1 1H6a2 2 0 0 0-2 2v1a1 1 0 0 0 1 1 M19 14H5l-1.973 6.767A1 1 0 0 0 4 22h16a1 1 0 0 0 .973-1.233z m8 22 1-4",
        ["programa"] = "M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z M10 4v4 M2 8h20 M6 4v4",
        ["video"] = "M4 3h16a2 2 0 0 1 2 2v10a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-10a2 2 0 0 1 2 -2z M8 21L16 21 M12 17L12 21",
        ["privacidade"] = "M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49 M14.084 14.158a3 3 0 0 1-4.242-4.242 M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143 m2 2 20 20",
        ["atualizar"] = "M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8 M21 3v5h-5 M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16 M8 16H3v5",
        ["seta"] = "m9 18 6-6-6-6",
        ["ampliar"] = "M15 3h6v6 m21 3-7 7 m3 21 7-7 M9 21H3v-6",
        ["fechar"] = "M18 6 6 18 m6 6 12 12",
        ["janela"] = "M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-16a2 2 0 0 1 -2 -2v-12a2 2 0 0 1 2 -2z M10 4v4 M2 8h20 M6 4v4",
    };
    static readonly Dictionary<string, Geometry> prontos = new();

    public static bool Tem(string nome) => desenhos.ContainsKey(nome);

    /// <summary>O ícone no tamanho pedido (24 de base), com o traço na cor dada.</summary>
    public static Control De(string nome, double tamanho = 18, IBrush? cor = null)
    {
        if (!desenhos.TryGetValue(nome, out var d)) d = desenhos["info"];
        if (!prontos.TryGetValue(nome, out var g)) prontos[nome] = g = Geometry.Parse(d);
        var p = new Avalonia.Controls.Shapes.Path { Data = g, Stroke = cor ?? Tema.Texto, StrokeThickness = 2, StrokeLineCap = PenLineCap.Round, StrokeJoin = PenLineJoin.Round, Width = 24, Height = 24 };
        return new Viewbox { Width = tamanho, Height = tamanho, Child = p, IsHitTestVisible = false };
    }

    /// <summary>O ícone de cada categoria do diagnóstico (as mesmas do motor).</summary>
    public static string DaCategoria(string c) => c switch
    {
        "segurança" => "seguranca", "inicialização" => "inicializacao", "memória" => "memoria", "disco" => "disco",
        "jogos" => "jogos", "saúde" => "saude", _ => "geral",
    };
}
