namespace Katharos.App;

/// <summary>
/// Para onde leva cada comando que o motor manda num achado, numa proposta ou numa resposta (o mesmo nome da linha de comando).
/// Um lugar só para o Início, o Raio-x e a Central: antes cada tela tinha a sua tabela, e um comando sem tela própria (como "medir")
/// caía no Otimizar com o modo inteiro marcado. O teste tests/test_katharos.py confere que todo comando que o motor emite aparece aqui:
/// "atualizar" "conselheiro" "config" "desfazer" "disco" "energia" "grandes" "inicializacao" "jogos" "limpar" "medir" "memoria"
/// "painel" "privacidade" "programas" "raiox" "rede" "reparar" "restaurar" "saude" "segundo-plano" "seguranca" "servicos" "tendencia"
/// "travadas" "turbo" "verificar"
/// </summary>
public static class Rotas
{
    /// <summary>As áreas do Otimizar (os pacotes do motor).</summary>
    public static readonly HashSet<string> Areas = new()
    {
        "ajustes", "apps", "atualizar", "disco", "energia", "ia", "inicializacao", "interface", "jogos", "limpar", "navegador", "privacidade",
        "programas", "rede", "reparar", "servicos", "visual",
    };

    public static string Cabeca(string? cmd) => (cmd ?? "").Trim().Split(' ')[0];

    /// <summary>O comando é uma área que o Katharos aplica (abre "Aplicar esta correção", só com os itens dela).</summary>
    public static bool EhArea(string? cmd) => Areas.Contains(Cabeca(cmd));

    /// <summary>
    /// A tela que resolve, ou null quando o achado só se entende lendo (desligamento, tela azul, driver, RAM): esses abrem o Detalhe,
    /// com o passo a passo, e nunca levam ao Otimizar.
    /// </summary>
    public static string? Tela(string? cmd) => Cabeca(cmd) switch
    {
        "inicializacao" => "inicializacao",
        var a when Areas.Contains(a) => "otimizar:" + a,
        "desfazer" => "desfazer",
        "turbo" => "otimizar",
        "segundo-plano" => "aovivo",
        "painel" or "tendencia" => "historico",
        "conselheiro" => "sugestoes",
        "config" => "config",
        "raiox" or "saude" => "raiox",
        "memoria" => "memoria",
        _ => null,   // medir, travadas, verificar, grandes, seguranca, restaurar e o que vier de novo: o Detalhe
    };

    /// <summary>O nome do botão que leva até lá.</summary>
    public static string Acao(string? cmd) => Cabeca(cmd) switch
    {
        "" => "Entender",
        "inicializacao" => "Escolher quais abrem",
        "atualizar" => "Ver como atualizar",
        "limpar" => "Limpar",
        "segundo-plano" => "Ligar o acompanhamento",
        "desfazer" => "Desfazer",
        "memoria" => "Ver quem usa a RAM",
        "raiox" or "saude" => "Ver no raio-x",
        var a when Areas.Contains(a) => "Aplicar esta correção",
        var a when Tela(a) == null => "Como investigar",
        _ => "Ver",
    };

    /// <summary>A categoria do diagnóstico (o motor manda; raio-x antigo ou exemplo sem ela usa o comando e o título, como o motor).</summary>
    public static string Categoria(string? categoria, string? titulo, string? cmd)
    {
        if (!string.IsNullOrEmpty(categoria)) return categoria!;
        string c = Cabeca(cmd), t = (titulo ?? "").ToLowerInvariant();
        bool Tem(string padrao) => System.Text.RegularExpressions.Regex.IsMatch(t, padrao);
        if (c is "seguranca" or "privacidade" || Tem(@"defender|ameaça|suspeit|bitlocker|segurança|telemetria")) return "segurança";
        if (c == "inicializacao" || Tem(@"inicializa|boot|abr\w* (junto )?com o windows")) return "inicialização";
        if (c == "memoria" || Tem(@"\bram\b|memória")) return "memória";
        if (c is "limpar" or "disco" || Tem(@"disco|espaço|ssd|\bhd\b")) return "disco";
        if (c == "jogos") return "jogos";
        if (c is "atualizar" or "reparar" or "medir" or "travadas" || Tem(@"driver|bios|firmware|tela azul|desligou|erro")) return "saúde";
        return "geral";
    }
}
