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
        try { if (comum == null) { var c = await MotorComum.Abre(); c.Caiu += _ => { if (comum == c) comum = null; }; comum = c; } }
        finally { abrindo.Release(); }
        return await comum.Pede(metodo, p, evento);
    }

    /// <summary>Muda o PC: abre o motor elevado na primeira vez (o Windows pergunta se pode).</summary>
    public static async Task<JsonNode?> Muda(string metodo, object? p = null, Action<string, JsonNode?>? evento = null)
    {
        if (Exemplo) return Simulador != null ? await Simulador(metodo, p, evento) : DadosDeExemplo.Para(metodo);
        await abrindo.WaitAsync();
        try { if (elevado == null) { var e = await MotorElevado.Abre(); e.Caiu += _ => { if (elevado == e) elevado = null; }; elevado = e; } }
        finally { abrindo.Release(); }
        Interlocked.Increment(ref Atualizacao.EmUso);   // nada de trocar de versão no meio de uma mudança (contador: podem ser duas)
        try { return await elevado!.Pede(metodo, p, evento); }
        finally { Interlocked.Decrement(ref Atualizacao.EmUso); }
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
            if (!File.Exists(arq)) return null;
            double idade = (DateTime.Now - File.GetLastWriteTime(arq)).TotalSeconds;
            if (idade > 600) return null;
            JsonNode? a;
            using (var f = new FileStream(arq, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete)) a = JsonNode.Parse(f);
            // num PC lento o segundo plano espaça as leituras (até 30 s): o limite acompanha o ritmo que ele mesmo informa; senão a
            // janela dizia "desligado" com o acompanhamento rodando, e "ligar" parecia não fazer nada
            double limite = Math.Max(20, 3 * (a.D("espera_s") ?? 0) + 5);
            return idade > limite ? null : a;
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
             "aviso_aceito": true, "primeira_vez": false,
             "motor": {"frase": "O que segura os seus jogos: a CPU freando.", "quando": "2026-11-10T09:30:00",
                       "acao": {"id": "causa-economia", "titulo": "Plano de energia de desempenho na tomada", "comando": "energia", "area": "energia",
                                "porque": "Em 14 sessões de jogo (21,5 h), a CPU rodou abaixo de 75 % da velocidade em 31 % do tempo, sem calor.",
                                "previsao": "plano de energia de desempenho na tomada.", "desfazer": "katharos desfazer energia", "confianca": "alta"}}}
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
               {"titulo": "Telemetria, anúncios e IA do Windows", "impacto": 0, "evidencia": "Ligados por padrão em toda instalação.", "faz": "Desligar por políticas oficiais (reversível).", "comando": "privacidade"}],
             "motor": {"ainda_nao_sei": false, "achados": [{"titulo": "CPU freando nos jogos", "vi": "em 14 sessões de jogo (21,5 h), CPU freando em 31 % do tempo", "confianca": "alta", "fonte": "sessões do segundo plano", "tipo": "limite"}]}}
            """),

        "sugestoes" => JsonNode.Parse("""
            {"diagnosticos": [{"problema": "jogos", "titulo": "O que segura os seus jogos", "causa": "economia", "nome": "economia de energia", "confianca": "alta",
                               "evidencias": ["em 14 sessões de jogo (21,5 h), CPU freando em 31 % do tempo", "parte das leituras recentes foi na bateria"],
                               "descartadas": [{"causa": "calor", "motivo": "descartada: a temperatura ficou abaixo do limite em todas as sessões"}],
                               "faria": "plano de energia de desempenho na tomada (no notebook, ligar a troca automática)",
                               "mudaria": "se aparecer calor acima do seguro, a causa passa a ser calor"}],
             "propostas": [{"id": "causa-economia", "titulo": "Plano de energia de desempenho na tomada", "porque": "x", "comando": "energia", "confianca": "alta", "tipo": "acao",
                            "explicacao": {"vi": "Em 14 sessões de jogo (21,5 h), a CPU rodou abaixo de 75 % da velocidade em 31 % do tempo.", "faria": "plano de desempenho na tomada; na bateria continua economizando."},
                            "previsao": {"texto": "a CPU deixa de frear com carga"}, "risco": "mais consumo de energia na tomada", "desfazer": "katharos desfazer energia"},
                           {"id": "inicializacao-lenta", "titulo": "Tirar 3 programas da inicialização", "porque": "Nos últimos 14 dias o PC levou 41 s em média para ficar pronto; Teams, OneDrive e Steam somam 14 s.", "comando": "inicializacao", "confianca": "média", "tipo": "acao",
                            "previsao": {"texto": "boot uns 14 s mais rápido"}, "risco": "baixo: o programa continua instalado", "desfazer": "katharos desfazer inicializacao"}],
             "linha_do_tempo": [{"id": "jogos", "titulo": "Itens de jogo", "quando": "2026-11-02T20:10", "previsto": "1% mais lento melhor", "veredito": "como previsto", "cor": "verde", "antes": 61, "depois": 74, "un": "FPS", "respondido": "sim"},
                                {"id": "servicos", "titulo": "Serviços que este PC não usa", "quando": "2026-10-28T19:00", "previsto": "menos RAM em uso", "veredito": "sem diferença", "cor": "cinza", "antes": 6.6, "depois": 6.5, "un": "GB"}]}
            """),
        "sessoes" => Sessoes(),
        "linha_de_base" => JsonNode.Parse("""{"metricas": {"cpu": {"jogo": {"p10": 22, "p90": 58, "dias": 12}}, "ram": {"jogo": {"p10": 52, "p90": 66, "dias": 12}}, "temp_cpu": {"jogo": {"p10": 61, "p90": 78, "dias": 12}}, "disco": {"jogo": {"p10": 1, "p90": 12, "dias": 12}}}}"""),
        "memoria" => JsonNode.Parse("""{"contagens": {"minutos": 41230, "horas": 0, "sessoes": 14, "resultados": 3}, "desde": "2026-09-30T18:02:00", "bytes": 9400000}"""),
        "perguntar" => JsonNode.Parse("""
            {"resposta": "O que segura os seus jogos: economia de energia. O que eu vi: CPU freando em 31 % do tempo nas sessões de jogo. Plano de energia de desempenho na tomada.",
             "comandos": [{"tipo": "comando", "area": "energia", "id": "energia", "titulo": "plano de energia"}, {"tipo": "comando", "area": "travadas", "id": "travadas", "titulo": "qual driver trava o PC"}]}
            """),
        "aplicado" => JsonNode.Parse("""
            {"ponto": "2026-11-08T21:38:00", "pacotes": [
              {"pacote": "privacidade", "titulo": "privacidade", "quando": "2026-11-08T21:40", "itens": ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r"], "desfaz": true},
              {"pacote": "jogos", "titulo": "jogos", "quando": "2026-11-02T20:10", "itens": ["a","b","c","d","e","f","g"], "desfaz": true},
              {"pacote": "apps", "titulo": "apps da Loja", "quando": "2026-11-02T20:05", "itens": ["a","b","c","d"], "desfaz": false}]}
            """),
        _ => null,
    };

    static JsonNode Sessoes()
    {
        var d = JsonNode.Parse("""
            {"resumo": {"sessoes": 14, "horas": 21.5, "principal": "gpu", "temp_cpu_max": 84},
             "comparacoes": [{"jogo": "eldenring", "rotulo": "1% mais lento", "antes": 61, "depois": 74, "veredito": "melhor", "nome_pacote": "jogos", "quando": "2026-11-02T20:10"},
                             {"jogo": "eldenring", "rotulo": "FPS médio", "antes": 116, "depois": 118, "veredito": "sem diferença", "nome_pacote": "jogos", "quando": "2026-11-02T20:10"}],
             "sessoes": [{"jogo": "cs2", "inicio": "2026-11-08T22:05:00", "min": 64, "principal": "cpu", "fps_med": 287, "fps_1low": 142, "temp_cpu_max": 81},
                         {"jogo": "eldenring", "inicio": "2026-11-09T20:31:00", "min": 112, "principal": "gpu", "fps_med": 117, "fps_1low": 73, "temp_cpu_max": 76},
                         {"jogo": "eldenring", "inicio": "2026-11-10T19:02:00", "min": 47, "principal": "gpu", "fps_med": 118, "fps_1low": 74, "temp_cpu_max": 77}]}
            """)!;
        var ev = new JsonArray();
        double[] low = { 61, 63, 60, 64, 72, 74, 73, 75 };
        for (int i = 0; i < low.Length; i++) ev.Add(new JsonObject { ["inicio"] = DateTime.Today.AddDays(i - 12).ToString("yyyy-MM-dd") + "T20:00:00", ["fps_med"] = 116 + i % 3, ["fps_1low"] = low[i], ["travadas_por_min"] = i < 4 ? 2.1 : 0.6 });
        d["por_jogo"] = new JsonArray(
            new JsonObject { ["jogo"] = "eldenring", ["sessoes"] = 8, ["horas"] = 14.2, ["segura"] = new JsonArray(new JsonObject { ["nome"] = "placa de vídeo no limite", ["pct"] = 64 }, new JsonObject { ["nome"] = "CPU abaixo da velocidade", ["pct"] = 18 }),
                             ["evolucao"] = ev, ["recomendacao"] = new JsonObject { ["titulo"] = "O que segura os seus jogos", ["nome"] = "economia de energia", ["faria"] = "plano de energia de desempenho na tomada" } },
            new JsonObject { ["jogo"] = "cs2", ["sessoes"] = 6, ["horas"] = 7.3, ["segura"] = new JsonArray(new JsonObject { ["nome"] = "CPU segurando o jogo", ["pct"] = 41 }), ["evolucao"] = new JsonArray() });
        return d;
    }

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
            var vs = pts.Take(28).Select(x => (double)x!["v"]!).OrderBy(x => x).ToList();
            series.Add(new JsonObject { ["chave"] = m.chave, ["rotulo"] = m.rot, ["unidade"] = m.un, ["casas"] = m.casas, ["pontos"] = pts,
                                        ["faixa"] = new JsonObject { ["p10"] = vs[(int)(vs.Count * .1)], ["p90"] = vs[(int)(vs.Count * .9)] } });
        }
        string q = hoje.AddDays(28 - 44).ToString("yyyy-MM-dd") + "T21:40";
        return new JsonObject
        {
            ["anomalias"] = new JsonArray(new JsonObject { ["dia"] = hoje.AddDays(-3).ToString("yyyy-MM-dd"), ["titulo"] = "A RAM dos serviços do Windows está acima do normal deste PC", ["tipo"] = "anomalia", ["confianca"] = "média", ["dias"] = 2,
                ["vi"] = "nas últimas 24 horas, sem jogo aberto, a RAM dos serviços do Windows ficou em 3,1 GB (mediana de 820 minutos). O normal deste PC nos 14 dias antes era 2,4 GB (entre 2,2 e 2,6)" }),
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
