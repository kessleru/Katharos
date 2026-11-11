using System.Diagnostics;
using System.Text.Json.Nodes;
using System.Text.RegularExpressions;
using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using static Katharos.App.Ui;

namespace Katharos.App.Telas;

/// <summary>
/// Um lugar para entender cada coisa: o que é, o que eu vi neste PC, por que importa, como resolver (passos numerados, com o botão
/// quando o Katharos resolve, ou o caminho no Windows quando é você) e como desfazer. Abre de qualquer achado, proposta ou resposta.
/// Achado que só se entende lendo (desligamento, tela azul, driver) chega aqui e nunca no Otimizar.
/// </summary>
public class Detalhe : Tela
{
    static JsonNode? pendente;
    static string pendenteSecao = "";
    readonly JsonNode? d;
    readonly string secao;

    /// <summary>Guarda o que abrir; a janela abre com Abre("detalhe") (as telas trocam por texto). secao: "resolver" já rola até os passos.</summary>
    public static void Prepara(JsonNode? dado, string secao = "")
    {
        pendente = dado?.DeepClone();
        pendenteSecao = secao;
    }

    public Detalhe() { d = pendente; secao = pendenteSecao; }

    /// <summary>
    /// Os botões de um achado ou proposta, iguais em toda tela: a ação que resolve (só a correção daquele achado, a tela própria, ou o
    /// passo a passo quando só dá para investigar) e "Entender", que abre este Detalhe. Nunca "Aplicar" em achado que só se lê.
    /// </summary>
    public static Control Botoes(JsonNode x, Action<string> abre, string origem, bool primario = false)
    {
        var p = new StackPanel { Orientation = Orientation.Horizontal, Spacing = 8 };
        string cmd = x.S("comando"), area = Rotas.Cabeca(cmd);
        bool soLer = x.S("tipo") is "leitura" or "info";
        void AbreDetalhe(string secao) { var c = x.DeepClone(); c["origem"] = origem; Prepara(c, secao); abre("detalhe"); }
        if (x.S("resolvido") == "")
        {
            if (Rotas.EhArea(cmd) && !soLer)
                p.Children.Add(area == "inicializacao" ? Botao("Escolher quais abrem", primario, () => abre("inicializacao"))
                                                       : Botao("Aplicar esta correção", primario, async () => await Aplicacao.Correcao(area, Ponto(Primeiro(x.S("evidencia"), x?["explicacao"].S("vi") ?? "", x.S("porque"))), abre)));
            else if (Rotas.Tela(cmd) is string t && !soLer && !(origem == "Raio-x" && t == "raiox"))
                p.Children.Add(Botao(Rotas.Acao(cmd), primario, () => abre(t)));
            else if (cmd != "" || x.S("faz") != "")
                p.Children.Add(Botao(Rotas.EhArea(cmd) ? "Como resolver" : "Como investigar", primario, () => AbreDetalhe("resolver")));
        }
        // "Entender" é discreto (link): a ação é o botão; num achado só de leitura, "Como investigar" já abre o mesmo lugar
        p.Children.Add(Link("Entender", () => AbreDetalhe("")));
        return p;
    }

    protected override Task Carrega()
    {
        string titulo = d.S("titulo", "Detalhe");
        var cab = Cabecalho(Maiuscula(titulo), Subtitulo());
        if (d == null) { Monta(cab, Vazio("Nada para mostrar", "Volte e escolha um achado.", Botao("Ir ao Início", true, () => Abre("inicio")))); return Task.CompletedTask; }

        string cmd = d.S("comando");
        string vi = Primeiro(d.S("evidencia"), d?["explicacao"].S("vi") ?? "", d.S("porque"));
        string importa = Primeiro(d.S("explica"), d.S("impacto_texto"), ImportaPelaGravidade());
        string faz = Primeiro(d.S("faz"), d?["explicacao"].S("faria") ?? "");

        var blocos = new List<Control?>();
        if (d.S("resolvido") != "")
            blocos.Add(S(new StackPanel { Margin = new Thickness(32, 20), Spacing = 6, Children = { Etiqueta("resolvido", Tema.Verde), T(Maiuscula(d.S("resolvido")) + ". Fica aqui só para você ver o que o raio-x tinha visto.", "sub", quebra: true) } }));

        string cat = Rotas.Categoria(d.S("categoria"), titulo, cmd);
        blocos.Add(Bloco("O que é", new Grid { ColumnDefinitions = new ColumnDefinitions("Auto,*"), Children = {
            Icones.De(Icones.DaCategoria(cat), 22, Tema.Ambar).Com(i => { i.VerticalAlignment = VerticalAlignment.Top; i.Margin = new Thickness(0, 1, 14, 0); }),
            T(OQueE(cmd), "sub", quebra: true).Com(t => Grid.SetColumn(t, 1)) } }));
        var viP = new StackPanel { Spacing = 8 };
        if (vi != "") viP.Children.Add(T(Maiuscula(Ponto(vi)), null, Tema.Osso, 15, true));
        if (d.S("evidencia_raiox") != "") viP.Children.Add(T("No raio-x: " + Ponto(d.S("evidencia_raiox")), "rotulo", quebra: true));
        var selos = new WrapPanel();
        if (d.S("certeza") != "") selos.Children.Add(Etiqueta("aconteceu: o Windows registrou", Tema.Ambar).Com(e => e.Margin = new Thickness(0, 0, 8, 6)));
        if (d.S("causa") != "") selos.Children.Add(Etiqueta("causa " + d.S("causa"), Tema.Apagado).Com(e => e.Margin = new Thickness(0, 0, 8, 6)));
        else if (d.S("confianca") != "") selos.Children.Add(Etiqueta("confiança " + d.S("confianca"), d.S("confianca") == "alta" ? Tema.Verde : d.S("confianca") == "média" ? Tema.Ambar : Tema.Apagado).Com(e => e.Margin = new Thickness(0, 0, 8, 6)));
        if (selos.Children.Count > 0) viP.Children.Add(selos);
        if (viP.Children.Count > 0) blocos.Add(Bloco("O que eu vi neste PC", viP));
        blocos.Add(Bloco("Por que importa", T(Maiuscula(Ponto(importa)), "sub", quebra: true)));

        var passos = Passos(cmd, faz);
        var resolver = Bloco(Rotas.EhArea(cmd) ? "Como resolver" : "Como investigar", passos);
        blocos.Add(resolver);

        string desf = d.S("desfazer");
        if (Rotas.EhArea(cmd) || desf != "")
            blocos.Add(Bloco("Como desfazer", T(desf != "" ? Maiuscula(ComoDesfazer(desf)) + "." : "Tudo o que o Katharos aplica aqui volta pela tela Desfazer, a um clique, com o valor de antes.", "sub", quebra: true)));

        Monta(new[] { (Control?)cab }.Concat(blocos).ToArray());
        if (secao == "resolver") Avalonia.Threading.Dispatcher.UIThread.Post(() => resolver.BringIntoView(), Avalonia.Threading.DispatcherPriority.Background);
        return Task.CompletedTask;
    }

    string Subtitulo()
    {
        var (g, _) = Gravidade((int)(d.D("impacto") ?? -1));
        string o = d.S("origem");
        return (o != "" ? o : "Achado do Katharos") + (d.D("impacto") is not null ? " · " + g : "") + (d.S("quando") != "" ? " · " + Quando(d.S("quando")) : "");
    }

    static Control Bloco(string titulo, Control corpo) =>
        S(new StackPanel { Margin = new Thickness(32, 22, 32, 24), Spacing = 10, MaxWidth = 760, HorizontalAlignment = HorizontalAlignment.Left, Children = { T(titulo, "rotulo"), corpo } });

    string ImportaPelaGravidade() => (int)(d.D("impacto") ?? -1) switch
    {
        3 => "É o que mais pesa neste PC agora: resolver tende a ser o maior ganho.",
        2 => "Pesa no dia a dia, mas não é o principal.",
        1 => "Ganho pequeno. Vale quando der.",
        0 => "Só para você saber: não tira ponto da nota.",
        _ => "",
    };

    string OQueE(string cmd) => Rotas.Cabeca(cmd) switch
    {
        "inicializacao" => "Programas que abrem sozinhos quando o Windows liga. Cada um atrasa o boot e fica ocupando memória, mesmo sem você usar.",
        "servicos" => "Serviços são programas do Windows e de fabricantes que rodam sem janela. Alguns não servem para este PC.",
        "privacidade" => "Telemetria, anúncios e recursos que mandam dados para a Microsoft ou ocupam o PC sem você pedir.",
        "energia" => "O plano de energia decide se a CPU acelera quando precisa ou economiza.",
        "limpar" or "disco" => "Arquivos temporários, caches e restos de atualização ocupando o disco.",
        "atualizar" => "Drivers e programas desatualizados, que costumam ter correções de travadas e de segurança.",
        "medir" => "O Windows registrou um evento de hardware ou de energia. O fato é certo; a causa se descobre investigando.",
        "memoria" => "A memória RAM é onde ficam os programas abertos. Cheia demais, o PC passa a usar o disco e engasga.",
        "seguranca" => "A proteção do Windows contra vírus e ameaças.",
        "restaurar" => "O ponto de restauração é uma foto do Windows para voltar se algo der errado.",
        "travadas" => "Travadas curtas costumam vir de um driver que segura o processador por um instante.",
        _ => Maiuscula(Ponto(Primeiro(d.S("explica"), d.S("titulo")))),
    };

    /// <summary>Os passos: os que o Katharos conhece para o comando, ou o "o que fazer" do motor quebrado em frases.</summary>
    Control Passos(string cmd, string faz)
    {
        var p = new StackPanel { Spacing = 16 };
        var lista = new List<(string titulo, string? texto, Control? acao)>();
        string area = Rotas.Cabeca(cmd);
        if (Rotas.EhArea(cmd))
        {
            if (faz != "") lista.Add((Maiuscula(Ponto(faz)), null, null));
            lista.Add(("Aplique com o Katharos", "Você vê cada item com o que ganha e o que perde, tira o que não quiser e aplica. Antes, o Katharos cria um ponto de restauração.",
                       area == "inicializacao" ? Botao("Escolher quais abrem", true, () => Abre("inicializacao"))
                                               : Botao("Aplicar esta correção", true, async () => await Aplicacao.Correcao(area, "", Abre))));
        }
        else
            switch (area)
            {
                case "medir":
                    lista.Add(("Olhe a temperatura com o PC pesado", "Abra Ao vivo e use o PC pesado por 10 minutos (um jogo, uma renderização). CPU acima de 95 °C ou placa de vídeo acima de 88 °C é calor demais: limpeza e pasta térmica resolvem.", Botao("Abrir Ao vivo", false, () => Abre("aovivo"))));
                    lista.Add(("Confira a energia", "Cabo de força bem encaixado e tomada sem régua fraca. No notebook: o carregador original e a bateria.", null));
                    lista.Add(("Teste sem overclock", "Se a CPU, a placa de vídeo ou a memória estão com overclock (ou XMP/EXPO ligado na BIOS), desligue por alguns dias. Se parar, era isso.", null));
                    lista.Add(("Atualize o driver de vídeo e a BIOS", "Pelo site do fabricante da placa de vídeo e da placa-mãe (ou do notebook).", null));
                    lista.Add(("Se repetir, mande um relatório", "Com quando aconteceu (jogando, parado, ligando). Os registros ajudam a achar o padrão.", Botao("Enviar relatório", false, () => Abre("enviar"))));
                    break;
                case "seguranca":
                    lista.Add(("Abra a Segurança do Windows", "Proteção contra vírus e ameaças. Se outro antivírus estiver instalado, é normal o Defender ficar desligado.", AbreNoWindows("Abrir a Segurança do Windows", "windowsdefender://threat")));
                    lista.Add(("Ligue a proteção em tempo real", "Se não houver outro antivírus, ligue em Configurações de proteção.", null));
                    break;
                case "restaurar":
                    lista.Add(("Abra a Proteção do sistema", "Em Proteção do sistema, confira se o disco C: está com a proteção ligada e clique em Criar.", AbreNoWindows("Abrir a Proteção do sistema", "SystemPropertiesProtection.exe")));
                    lista.Add(("Ou deixe com o Katharos", "Ele cria um ponto de restauração sozinho antes de cada mudança.", null));
                    break;
                default:
                    foreach (var f in Frases(faz)) lista.Add((f, null, null));
                    if (lista.Count == 0) lista.Add(("Nada a fazer agora", "Isto só informa. Se mudar, o Katharos avisa.", null));
                    break;
            }
        for (int i = 0; i < lista.Count; i++) p.Children.Add(Passo(i + 1, lista[i].titulo, lista[i].texto, lista[i].acao));
        return p;
    }

    /// <summary>Abre uma página do próprio Windows (Configurações, Segurança, Proteção do sistema). Nunca um programa de terceiros.</summary>
    static Button AbreNoWindows(string texto, string alvo) => Botao(texto, false, () =>
    {
        try { Process.Start(new ProcessStartInfo(alvo) { UseShellExecute = true }); }
        catch (Exception e) { MostraErro(e, "Não deu para abrir", "Abra pelo menu Iniciar do Windows."); }
    });

    static IEnumerable<string> Frases(string s)
    {
        // "faça A; se B, faça C. Depois D." vira três passos, sem quebrar números ("1,5 GB") nem abreviações
        foreach (var f in Regex.Split(s ?? "", @"(?<=[.;])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇa-z])"))
        {
            var t = f.Trim().TrimEnd(';').Trim();
            if (t.Length > 2) yield return Maiuscula(Ponto(t));
        }
    }

    static string Primeiro(params string[] xs) => xs.FirstOrDefault(x => !string.IsNullOrWhiteSpace(x)) ?? "";
    static string Ponto(string s) { s = (s ?? "").Trim(); return s == "" || ".!?:".Contains(s[^1]) ? s : s + "."; }
}
