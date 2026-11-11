using System.Text.Json.Nodes;
using Avalonia.Platform;

namespace Katharos.App;

/// <summary>
/// O caminho único das telas até o motor. Leitura vai para o motor comum (como o usuário); mudança vai para o motor elevado (um pedido
/// de permissão do Windows por sessão). No modo exemplo (fotos e testes da interface) devolve dados fixos, no mesmo formato da API.
/// </summary>
public static class Servico
{
    public static bool Exemplo;
    /// <summary>No modo exemplo, quem grava os vídeos pode responder no lugar do motor (com eventos de progresso no tempo do vídeo).</summary>
    public static Func<string, object?, Action<string, JsonNode?>?, Task<JsonNode?>>? Simulador;
    public static Func<JsonNode?>? AgoraSimulado;
    static MotorComum? comum;
    static MotorElevado? elevado;
    static readonly SemaphoreSlim abrindo = new(1, 1);

    public static async Task<JsonNode?> Le(string metodo, object? p = null, Action<string, JsonNode?>? evento = null)
    {
        if (Exemplo) return Simulador != null ? await Simulador(metodo, p, evento) : DadosDeExemplo.Para(metodo);
        await abrindo.WaitAsync();
        try { comum ??= await MotorComum.Abre(); comum.Caiu += _ => comum = null; }
        finally { abrindo.Release(); }
        return await comum.Pede(metodo, p, evento);
    }

    /// <summary>Muda o PC: abre o motor elevado na primeira vez (o Windows pergunta se pode).</summary>
    public static async Task<JsonNode?> Muda(string metodo, object? p = null, Action<string, JsonNode?>? evento = null)
    {
        if (Exemplo) return Simulador != null ? await Simulador(metodo, p, evento) : DadosDeExemplo.Para(metodo);
        await abrindo.WaitAsync();
        try { elevado ??= await MotorElevado.Abre(); elevado.Caiu += _ => elevado = null; }
        finally { abrindo.Release(); }
        Atualizacao.Ocupado = true;   // nada de trocar de versão no meio de uma mudança
        try { return await elevado.Pede(metodo, p, evento); }
        finally { Atualizacao.Ocupado = false; }
    }

    public static async Task Fecha()
    {
        if (comum != null) await comum.DisposeAsync();
        if (elevado != null) await elevado.DisposeAsync();
    }

    /// <summary>A leitura de agora do segundo plano, direto do arquivo (sem motor: atualiza a cada segundo sem custo).</summary>
    public static JsonNode? Agora()
    {
        if (Exemplo) return AgoraSimulado?.Invoke() ?? DadosDeExemplo.Para("agora");
        try
        {
            var arq = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".katharos", "agora.json");
            if (!File.Exists(arq) || (DateTime.Now - File.GetLastWriteTime(arq)).TotalSeconds > 20) return null;
            using var f = new FileStream(arq, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            return JsonNode.Parse(f);
        }
        catch { return null; }
    }
}

/// <summary>Os dados de exemplo das fotos: os mesmos números do site, no formato exato da API (tests/api/contrato.json).</summary>
public static class DadosDeExemplo
{
    static JsonNode? itens;

    public static JsonNode? Para(string metodo) => metodo switch
    {
        "inicio" => JsonNode.Parse("""
            {"raiox": {"quando": "2026-11-10T09:12:00", "nota": 72, "total": 3, "achados": [
               {"titulo": "Driver da placa de vídeo de março", "impacto": 3, "evidencia": "NVIDIA 551.86. O novo corrige travadas em jogos DirectX 12.", "faz": "Baixe pelo app da NVIDIA ou pelo site.", "comando": "atualizar"},
               {"titulo": "11 programas abrem junto com o Windows", "impacto": 2, "evidencia": "O PC leva 41 s para ficar pronto; sem eles, uns 25 s.", "faz": "", "comando": "inicializacao"},
               {"titulo": "Memória em canal único", "impacto": 1, "evidencia": "Um pente de 16 GB. Dois de 8 GB rendem até 15 % mais em jogos.", "faz": "", "comando": ""}]},
             "pc": {"disco_livre_gb": 182, "disco_total_gb": 476},
             "temperatura": {"cpu": 47, "cpu_fonte": "MSI Afterburner", "gpu": 44, "gpu_fonte": "driver de vídeo"},
             "ultima_mudanca": {"pacote": "privacidade", "titulo": "privacidade", "quando": "2026-11-08T21:40", "itens": 96},
             "segundo_plano": {"rodando": true, "ligado": true, "cpu_pct": 0.1, "ram_mb": 52, "intervalo_s": 1},
             "aviso_aceito": true}
            """),
        "itens" => itens ??= Carrega("exemplo-itens.json"),
        "agora" => JsonNode.Parse("""
            {"cpu": 38, "nucleo_max": 71, "gpu": 97, "vram_gb": 7.9, "vram_total_gb": 8, "ram_pct": 61, "ram_gb": 9.8, "ram_total_gb": 16,
             "disco": 6, "disco_le_mbs": 2.1, "temp_cpu": 72, "temp_cpu_fonte": "MSI Afterburner", "temp_gpu": 71, "temp_gpu_fonte": "driver de vídeo",
             "intervalo_s": 1, "segundo_plano": {"cpu_pct": 0.1, "ram_mb": 52},
             "jogo": {"nome": "eldenring", "min": 47, "principal": "gpu", "fps": 118, "fps_med": 118, "fps_1low": 74, "travadas_por_min": 2},
             "conclusoes": [{"id": "vram", "nivel": 1, "titulo": "Memória da placa de vídeo quase cheia", "texto": "7,9 de 8 GB. Baixe a qualidade das texturas no jogo: acima disso ele engasga."},
                            {"id": "gpu", "nivel": 0, "titulo": "A placa de vídeo é o limite", "texto": "Isso é o esperado num jogo pesado. Mais FPS vem de baixar resolução ou qualidade, não de otimizar o Windows."}]}
            """),
        "aviso" => Carrega("exemplo-aviso.json"),
        "historico" => Historico(),
        "config_ler" => Carrega("exemplo-config.json"),
        "raiox_guardado" => JsonNode.Parse("""
            {"quando": "2026-11-10T09:12:00", "nota": 72,
             "pesa": [{"titulo": "Driver da placa de vídeo de março", "pontos": 14}, {"titulo": "11 programas abrem junto com o Windows", "pontos": 6}],
             "pc": {"modelo": "ASUS TUF Gaming A15", "windows": "Windows 11 25H2 Pro", "cpu": "AMD Ryzen 7 7735HS · 8 núcleos", "ram": "16 GB DDR5 · 1 pente", "disco": "NVMe 512 GB · 182 GB livres", "video": "NVIDIA GeForce RTX 4060 Laptop"},
             "achados": [
               {"titulo": "Driver da placa de vídeo de março", "impacto": 3, "evidencia": "NVIDIA 551.86, de março. O novo corrige travadas em jogos DirectX 12.", "faz": "Baixe pelo app da NVIDIA ou em nvidia.com/drivers.", "comando": "atualizar"},
               {"titulo": "11 programas abrem junto com o Windows", "impacto": 2, "evidencia": "O PC leva 41 s para ficar pronto; sem eles, uns 25 s.", "faz": "Tire o que você não usa logo ao ligar.", "comando": "inicializacao"},
               {"titulo": "Memória em canal único", "impacto": 1, "evidencia": "Um pente de 16 GB. Dois de 8 GB rendem até 15 % mais em jogos.", "faz": "Ao comprar memória, prefira dois pentes iguais.", "comando": ""},
               {"titulo": "Telemetria, anúncios e IA do Windows", "impacto": 0, "evidencia": "Ligados por padrão em toda instalação.", "faz": "Desligar por políticas oficiais (reversível).", "comando": "privacidade"}]}
            """),
        "sessoes" => JsonNode.Parse("""
            {"resumo": {"sessoes": 14, "horas": 21.5, "principal": "gpu", "temp_cpu_max": 84},
             "comparacoes": [{"jogo": "eldenring", "rotulo": "1% mais lento", "antes": 61, "depois": 74, "veredito": "melhor", "nome_pacote": "jogos", "quando": "2026-11-02T20:10"},
                             {"jogo": "eldenring", "rotulo": "FPS médio", "antes": 116, "depois": 118, "veredito": "sem diferença", "nome_pacote": "jogos", "quando": "2026-11-02T20:10"}],
             "sessoes": [{"jogo": "cs2", "inicio": "2026-11-08T22:05:00", "min": 64, "principal": "cpu", "fps_med": 287, "fps_1low": 142, "temp_cpu_max": 81},
                         {"jogo": "eldenring", "inicio": "2026-11-09T20:31:00", "min": 112, "principal": "gpu", "fps_med": 117, "fps_1low": 73, "temp_cpu_max": 76},
                         {"jogo": "eldenring", "inicio": "2026-11-10T19:02:00", "min": 47, "principal": "gpu", "fps_med": 118, "fps_1low": 74, "temp_cpu_max": 77}]}
            """),
        "sugestoes" => JsonNode.Parse("""
            {"propostas": [{"id": "inicializacao-lenta", "titulo": "Tirar 3 programas da inicialização", "porque": "Nos últimos 14 dias o PC levou 41 s em média para ficar pronto; Teams, OneDrive e Steam somam 14 s.", "comando": "inicializacao", "confianca": "alta", "tipo": "acao"},
                           {"id": "calor-tarde", "titulo": "Limpar a ventilação do notebook", "porque": "A CPU passa de 85 °C em 30 % das sessões de jogo à noite, com a mesma carga de antes.", "comando": "", "confianca": "media", "tipo": "info"}],
             "resultados": [{"id": "jogos", "titulo": "Itens de jogo (02/11)", "texto": "Eu previ 1% mais lento melhor em Elden Ring: foi de 61 para 74 FPS (margem de ±4).", "veredito": "melhorou"}]}
            """),
        "aplicado" => JsonNode.Parse("""
            {"ponto": "2026-11-08T21:38:00", "pacotes": [
              {"pacote": "privacidade", "titulo": "privacidade", "quando": "2026-11-08T21:40", "itens": ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r"], "desfaz": true},
              {"pacote": "jogos", "titulo": "jogos", "quando": "2026-11-02T20:10", "itens": ["a","b","c","d","e","f","g"], "desfaz": true},
              {"pacote": "apps", "titulo": "apps da Loja", "quando": "2026-11-02T20:05", "itens": ["a","b","c","d"], "desfaz": false}]}
            """),
        _ => null,
    };

    // 45 dias de medidas de exemplo: o boot cai no dia em que "inicialização" foi aplicada (dia 28)
    static JsonNode Historico()
    {
        var r = new Random(5); var hoje = DateTime.Today; var series = new JsonArray();
        (string chave, string rot, string un, int casas, Func<int, double> f)[] ms = {
            ("boot_s", "o tempo de boot", "s", 0, i => i < 28 ? 46 + r.NextDouble() * 6 : 24 + r.NextDouble() * 3),
            ("ram_usada", "a RAM em uso", "GB", 1, i => 6.4 + r.NextDouble() * .6 - (i >= 28 ? .5 : 0)),
            ("livre_c", "o espaço livre em C:", "GB", 0, i => 196 - i * .4 + (i >= 28 ? 9 : 0)),
            ("processos", "o número de processos", "", 0, i => 214 - (i >= 28 ? 31 : 0) + r.Next(0, 9)) };
        foreach (var m in ms)
        {
            var pts = new JsonArray();
            for (int i = 0; i < 45; i++) pts.Add(new JsonObject { ["dia"] = hoje.AddDays(i - 44).ToString("yyyy-MM-dd"), ["v"] = Math.Round(m.f(i), m.casas) });
            series.Add(new JsonObject { ["chave"] = m.chave, ["rotulo"] = m.rot, ["unidade"] = m.un, ["casas"] = m.casas, ["pontos"] = pts });
        }
        string q = hoje.AddDays(28 - 44).ToString("yyyy-MM-dd") + "T21:40";
        return new JsonObject
        {
            ["series"] = series, ["marcas"] = new JsonArray(new JsonObject { ["quando"] = q, ["titulo"] = "inicialização" }), ["tendencia"] = new JsonArray(),
            ["efeitos"] = new JsonArray(new JsonObject { ["titulo"] = "inicialização", ["quando"] = q, ["medidas"] = new JsonArray(
                new JsonObject { ["rotulo"] = "o tempo de boot", ["veredito"] = "melhorou", ["antes"] = 49, ["depois"] = 25, ["casas"] = 0, ["unidade"] = "s" },
                new JsonObject { ["rotulo"] = "o número de processos", ["veredito"] = "melhorou", ["antes"] = 218, ["depois"] = 187, ["casas"] = 0, ["unidade"] = "" },
                new JsonObject { ["rotulo"] = "a RAM em uso", ["veredito"] = "sem diferença mensurável", ["antes"] = 6.7, ["depois"] = 6.3, ["casas"] = 1, ["unidade"] = "GB" }) }),
        };
    }

    static JsonNode? Carrega(string nome)
    {
        using var s = AssetLoader.Open(new Uri("avares://Katharos/Assets/" + nome));
        return JsonNode.Parse(s);
    }
}
