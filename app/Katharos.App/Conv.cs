using Avalonia.Data.Converters;

namespace Katharos.App;

public static class Conv
{
    /// <summary>Área aberta ou fechada: a seta que diz o que o clique faz.</summary>
    public static readonly IValueConverter Seta = new FuncValueConverter<bool, string>(a => a ? "−" : "+");
}
