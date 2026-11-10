using Avalonia.Media;

namespace Katharos.App;

/// <summary>
/// As cores e as fontes do site (arte/site.html, :root), num lugar só. A interface usa exatamente estas; nada de cor solta numa tela.
/// </summary>
public static class Tema
{
    public static readonly Color CorFundo = Color.Parse("#0c0c0d");
    public static readonly Color CorPainel = Color.Parse("#121214");
    public static readonly Color CorLinha = Color.Parse("#242428");
    public static readonly Color CorLinhaForte = Color.Parse("#38383e");
    public static readonly Color CorApagado = Color.Parse("#86837c");
    public static readonly Color CorTexto = Color.Parse("#cdc8be");
    public static readonly Color CorOsso = Color.Parse("#efe9de");
    public static readonly Color CorAmbar = Color.Parse("#e2a85c");
    public static readonly Color CorVerde = Color.Parse("#9ccf8c");
    public static readonly Color CorVermelho = Color.Parse("#e5737a");

    public static readonly IBrush Fundo = new SolidColorBrush(CorFundo);
    public static readonly IBrush Painel = new SolidColorBrush(CorPainel);
    public static readonly IBrush Linha = new SolidColorBrush(CorLinha);
    public static readonly IBrush LinhaForte = new SolidColorBrush(CorLinhaForte);
    public static readonly IBrush Apagado = new SolidColorBrush(CorApagado);
    public static readonly IBrush Texto = new SolidColorBrush(CorTexto);
    public static readonly IBrush Osso = new SolidColorBrush(CorOsso);
    public static readonly IBrush Ambar = new SolidColorBrush(CorAmbar);
    public static readonly IBrush AmbarFraco = new SolidColorBrush(Color.FromArgb(28, 226, 168, 92));
    public static readonly IBrush Verde = new SolidColorBrush(CorVerde);
    public static readonly IBrush Vermelho = new SolidColorBrush(CorVermelho);

    // títulos, números e rótulos em JetBrains Mono; texto corrido em Archivo (as duas fontes do site, licença OFL, dentro do app)
    public static readonly FontFamily Mono = new("avares://Katharos/Assets/Fontes#JetBrains Mono");
    public static readonly FontFamily Sans = new("avares://Katharos/Assets/Fontes#Archivo");

    /// <summary>Margem lateral do conteúdo: onde ficam as linhas verticais e os "+".</summary>
    public const double Margem = 40;
}
