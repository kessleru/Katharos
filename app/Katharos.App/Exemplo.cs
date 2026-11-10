using Avalonia.Media;

namespace Katharos.App;

// Modelos das telas. No protótipo vêm com dados de exemplo (os mesmos números do site); na fase 2 vêm do motor (`katharos api`).

public record Achado(string Gravidade, string Titulo, string Explica, string Acao)
{
    public IBrush Cor => Gravidade switch { "grave" => Tema.Vermelho, "atenção" => Tema.Ambar, _ => Tema.Apagado };
}

public class ItemOtim
{
    public required string Titulo { get; init; }
    public required string Ganho { get; init; }
    public string? Aviso { get; init; }
    public bool JaFeito { get; init; }
    public bool Marcado { get; set; }
    public string Estado => JaFeito ? "já está assim" : Marcado ? "vai mudar" : "não marcado";
    public IBrush CorEstado => JaFeito ? Tema.Verde : Marcado ? Tema.Ambar : Tema.Apagado;
    public bool TemAviso => Aviso != null;
}

public class Area
{
    public required string Nome { get; init; }
    public required string Descricao { get; init; }
    public List<ItemOtim> Itens { get; init; } = new();
    public bool Aberta { get; set; }
    public string Conta => $"{Itens.Count(i => i.Marcado && !i.JaFeito)} mudam · {Itens.Count(i => i.JaFeito)} já feitos · {Itens.Count} itens";
}

public record Modo(string Nome, string Explica, int Itens, int JaFeitos, bool Escolhido)
{
    public string Conta => $"marca {Itens} itens · {JaFeitos} já feitos";
    public IBrush Borda => Escolhido ? Tema.Ambar : Tema.Linha;
    public IBrush Fundo => Escolhido ? Tema.AmbarFraco : Brushes.Transparent;
}

public record Metrica(string Rotulo, string Valor, string Unidade, string Contexto, IBrush CorContexto, double[] Valores, double Maximo = 100, double Limite = double.NaN);

public static class Exemplo
{
    public static readonly List<Achado> Achados = new()
    {
        new("grave", "Driver da placa de vídeo de março", "NVIDIA 551.86. O novo corrige travadas em jogos DirectX 12.", "Atualizar o driver"),
        new("atenção", "11 programas abrem junto com o Windows", "O PC leva 41 s para ficar pronto; sem eles, uns 25 s.", "Escolher quais abrem"),
        new("dica", "Memória em canal único", "Um pente de 16 GB. Dois de 8 GB rendem até 15 % mais em jogos.", "Entender"),
    };

    public static readonly List<Modo> Modos = new()
    {
        new("Seguro", "Só o que não tem contrapartida: telemetria, anúncios e lixo.", 40, 12, false),
        new("Equilibrado", "O seguro mais o que quase ninguém usa.", 96, 42, true),
        new("Extremo", "Tudo o que ajuda neste PC. Cada item diz o que você perde.", 130, 42, false),
    };

    public static readonly List<Area> Areas = new()
    {
        new() { Nome = "Limpeza", Descricao = "temporários, caches e restos", Itens = Gera(13, 3) },
        new()
        {
            Nome = "Inicialização", Descricao = "o que abre junto com o Windows", Aberta = true,
            Itens = new()
            {
                new() { Titulo = "Tirar o Teams da inicialização", Ganho = "o PC fica pronto uns 4 s antes", Marcado = true },
                new() { Titulo = "Tirar o OneDrive da inicialização", Ganho = "uns 2 s; ele abre quando você abrir uma pasta dele", Marcado = true, Aviso = "para de sincronizar até você abrir" },
                new() { Titulo = "Desligar a inicialização rápida", Ganho = "reinício limpo; menos erro de driver depois de atualizar", JaFeito = true, Marcado = true },
                new() { Titulo = "Atrasar o Steam em 30 s", Ganho = "o Windows termina de ligar antes", Marcado = false },
            }
        },
        new() { Nome = "Serviços", Descricao = "serviços que este PC não usa", Itens = Gera(10, 6) },
        new() { Nome = "Privacidade", Descricao = "telemetria, anúncios e sugestões", Itens = Gera(18, 11) },
        new() { Nome = "Jogos", Descricao = "Modo de Jogo, gravação de fundo, mouse", Itens = Gera(7, 2) },
    };

    static List<ItemOtim> Gera(int n, int feitos) =>
        Enumerable.Range(0, n).Select(i => new ItemOtim { Titulo = "item " + i, Ganho = "", JaFeito = i < feitos, Marcado = true }).ToList();

    static double[] Onda(double baseV, double amp, double ruido, int seed)
    {
        var r = new Random(seed);
        return Enumerable.Range(0, 120).Select(i => Math.Clamp(baseV + amp * Math.Sin(i / 9.0) + r.NextDouble() * ruido, 0, 100)).ToArray();
    }

    public static readonly List<Metrica> Metricas = new()
    {
        new("Placa de vídeo", "97", "%", "no limite: é ela que segura o FPS", Tema.Ambar, Onda(90, 3, 6, 1), 100, 95),
        new("CPU", "38", "%", "sobra: núcleo mais usado em 71 %", Tema.Verde, Onda(36, 10, 8, 2)),
        new("Memória RAM", "61", "%", "9,8 de 16 GB", Tema.Verde, Onda(60, 1, 2, 3)),
        new("Temperatura", "72", "°C", "CPU 72 · placa de vídeo 71 · normal", Tema.Verde, Onda(70, 2, 3, 4), 100, 90),
        new("Memória da placa", "7,9", "GB", "de 8 GB: quase cheia", Tema.Ambar, Onda(92, 2, 4, 5), 100, 95),
        new("Disco", "6", "%", "lendo 2,1 MB/s", Tema.Verde, Onda(5, 3, 8, 6)),
    };
}
