using Avalonia;
using Avalonia.Controls;
using Avalonia.Layout;
using static Katharos.App.Ui;

namespace Katharos.App;

/// <summary>
/// Os conceitos que o Katharos usa, explicados numa janelinha à parte (o "Saiba mais"/"?" de cada lugar). A lista e o botão ficam com
/// uma linha só; quem quer entender abre a janela, que separa: o que é, um jeito de pensar, o que o Katharos faz e se é seguro mexer.
/// Os nomes seguem os do próprio Windows em português (Aplicativos de inicialização, Dados de diagnóstico, Memória virtual), para a
/// pessoa reconhecer quando abrir as Configurações.
/// </summary>
public static class Conceitos
{
    public record Conceito(string Titulo, string Icone, string OQueE, string PenseAssim, string NoKatharos, string Seguro, string? NoWindows = null);

    public static readonly Dictionary<string, Conceito> Todos = new()
    {
        ["nota"] = new("Como a nota é feita", "raiox",
            "Começa em 100 e cada problema que o raio-x acha tira pontos: grave tira 15, atenção tira 7, dica tira 2. Informação não tira nada.",
            "Cada parte do PC tem um limite: cinco problemas de disco contam como um problema grande de disco (no máximo 20), e não como cinco. Segurança e saúde podem tirar mais (até 30), porque são o que estraga o PC ou os seus arquivos.",
            "O que você resolve depois do raio-x sai da conta na hora: a nota sobe sem precisar fazer o raio-x de novo. O que não dá para saber vira \"não sei\", nunca um chute.",
            "A nota só lê: nada muda no PC para calcular."),
        ["inicializacao"] = new("Aplicativos de inicialização", "inicializacao",
            "Programas que abrem sozinhos quando o Windows liga, sem você clicar. Ficam rodando escondidos, perto do relógio.",
            "É como cada programa entrar na fila do café da manhã antes de você: cada um atrasa um pouco o PC ficar pronto e fica ocupando memória o dia todo.",
            "Mostra quanto o Windows mediu de atraso de cada um e sugere desligar só o que não faz falta (antivírus, drivers e o que é do Windows ficam sempre). Até 5 que dá para desligar é normal num PC comum.",
            "Desligar não desinstala: o programa só deixa de abrir sozinho e abre normal quando você quiser. Volta com um clique.",
            "Configurações > Aplicativos > Inicialização"),
        ["servicos"] = new("Serviços do Windows", "camadas",
            "Programas sem janela que o Windows e os fabricantes deixam rodando por trás: impressão, fax, Xbox, atualizadores, telemetria de fabricante.",
            "São funcionários de plantão: alguns são essenciais, outros ficam esperando um trabalho que neste PC nunca chega (fax num PC sem fax).",
            "Só mexe nos que não servem para este PC, e prefere \"manual\" (o Windows liga quando algo pede) a desligar de vez. Os essenciais nunca entram na lista.",
            "Volta pelo Desfazer, com o valor exato de antes.",
            "Ferramenta \"Serviços\" (services.msc)"),
        ["telemetria"] = new("Dados de diagnóstico e anúncios", "privacidade",
            "Informações que o Windows manda para a Microsoft sobre como você usa o PC, mais as sugestões e anúncios no menu Iniciar e na tela de bloqueio.",
            "É uma pesquisa de satisfação que roda o tempo todo, mesmo quando você não respondeu nada.",
            "Desliga pelas mesmas políticas que as empresas usam, sem apagar nada do Windows. O Windows Update e a Microsoft Store continuam funcionando.",
            "Seguro e reversível pelo Desfazer.",
            "Configurações > Privacidade e segurança > Diagnóstico e comentários"),
        ["tarefas"] = new("Tarefas agendadas", "tempo",
            "Coisas que o Windows ou um programa programou para rodar sozinhas: ao ligar, de hora em hora, quando o PC está parado.",
            "É o despertador dos programas: cada um põe o seu, e alguns tocam a cada poucos minutos.",
            "Avisa quando uma tarefa roda um programa de uma pasta incomum (AppData, Temp) sem assinatura digital, que é o padrão de vírus. As do próprio Katharos e as de programas assinados não viram alarme.",
            "O Katharos só avisa; desativar uma tarefa é com você, no Agendador de Tarefas.",
            "Agendador de Tarefas (taskschd.msc)"),
        ["memoria_virtual"] = new("Memória virtual (arquivo de paginação)", "memoria",
            "Um pedaço do disco que o Windows usa como se fosse RAM quando a memória de verdade enche.",
            "É a mesa de apoio ao lado da mesa principal: dá para continuar trabalhando, mas buscar coisa lá é bem mais lento.",
            "Recomenda deixar no automático (tamanho gerenciado pelo Windows). Tamanho fixo pequeno faz programas fecharem sozinhos quando a RAM enche.",
            "Nunca desligue: sem ela, programas e jogos fecham do nada.",
            "Sistema > Configurações avançadas do sistema > Desempenho > Avançado > Memória virtual"),
        ["memoria_prometida"] = new("Memória prometida", "memoria",
            "O quanto da memória total (RAM + memória virtual) o Windows já prometeu aos programas abertos.",
            "É o limite do cartão de crédito: perto de 100 %, o próximo programa que pedir memória é recusado e fecha.",
            "É o número que diz se a RAM está cheia de verdade. Acima de 90 % é \"cheia\"; RAM \"em uso\" alta sozinha não é problema, porque o Windows usa RAM livre de cache de propósito.",
            "Só leitura."),
        ["compressao"] = new("Memória compactada", "memoria",
            "Quando a RAM aperta, o Windows comprime o que está parado na memória em vez de mandar para o disco.",
            "É fazer a mala sentando em cima: cabe mais, mas tirar algo de lá leva um instante.",
            "Muita memória comprimida (mais de 15 % da RAM) é sinal de que a RAM está cheia de verdade.",
            "O Katharos deixa a compactação ligada: ela é mais rápida que usar o disco."),
        ["plano_energia"] = new("Modo de energia", "energia",
            "Decide se o processador acelera assim que precisa (desempenho) ou segura para gastar menos (economia).",
            "É o câmbio do carro: na economia ele demora a reduzir a marcha quando você pisa.",
            "Na tomada, usa o modo de desempenho; na bateria, pode voltar sozinho para o equilibrado (opção nas Configurações).",
            "Seguro: só muda quanto o PC gasta de energia e esquenta.",
            "Configurações > Sistema > Energia e bateria > Modo de energia"),
        ["ponto_restauracao"] = new("Ponto de restauração", "desfazer",
            "Uma foto das configurações do Windows num momento. Se algo der errado, o Windows volta para como estava na foto.",
            "É salvar o jogo antes do chefe.",
            "Antes de aplicar qualquer mudança, o Katharos cria um. É a segunda rede de proteção: a primeira é o Desfazer, item por item.",
            "Não mexe nos seus arquivos (fotos, documentos): só nas configurações e programas.",
            "Painel de Controle > Recuperação > Configurar a Restauração do Sistema"),
        ["desfazer"] = new("Desfazer", "desfazer",
            "Tudo o que o Katharos muda guarda antes o valor que estava. O Desfazer põe esse valor de volta, exatamente como era.",
            "É o Ctrl+Z das otimizações.",
            "Dá para voltar uma área inteira ou só alguns itens; o resto continua aplicado. O que foi aplicado antes da versão 4.3.0 só volta com a área inteira.",
            "Remoções (apps da Microsoft desinstalados) não voltam pelo Desfazer: a tela avisa antes de aplicar."),
        ["driver"] = new("Driver", "atualizar",
            "O programa que ensina o Windows a usar uma peça: placa de vídeo, Wi-Fi, som, chipset.",
            "É o tradutor entre o Windows e a peça. Tradutor desatualizado entende errado e o resultado são travadas e telas azuis.",
            "Mostra os drivers velhos e onde baixar o novo (sempre no site do fabricante). Não instala driver sozinho.",
            "Baixe só do fabricante (NVIDIA, AMD, Intel ou o do seu notebook)."),
        ["travadas"] = new("Travadas por driver (DPC)", "aovivo",
            "Às vezes um driver segura o processador por alguns milissegundos para atender a peça dele. Se demora, o jogo e o som engasgam.",
            "É alguém parando no meio da faixa: dura pouco, mas todo mundo atrás freia.",
            "O teste de travadas (1 minuto) mede qual driver segura mais e por quanto tempo.",
            "Só leitura."),
        ["cache"] = new("Caches e temporários", "limpar",
            "Arquivos que programas e o Windows guardam para abrir mais rápido depois ou que sobraram de instalações e atualizações.",
            "É o rascunho: útil por um tempo, depois só ocupa a gaveta.",
            "Limpa só o que se recria sozinho (caches de navegador, temporários, restos de atualização). Arquivos seus nunca entram.",
            "Seguro: na primeira vez, um site ou programa pode abrir um pouco mais devagar enquanto refaz o cache.",
            "Configurações > Sistema > Armazenamento"),
        ["modos"] = new("Os três modos", "otimizar",
            "Seguro, equilibrado e extremo são o quanto o Katharos mexe: cada modo marca mais itens que o anterior.",
            "Seguro só tira o que ninguém usa. Equilibrado tira o que quase ninguém usa. Extremo vai além, trocando recursos por desempenho.",
            "O botão de cada modo mostra quantas mudanças ele faria agora neste PC (o que já está feito não conta). Você confere e tira o que quiser antes de aplicar.",
            "Tudo volta pelo Desfazer, menos as remoções, que a tela marca em vermelho."),
        ["ja_feito"] = new("\"Já está assim\"", "ok",
            "Antes de mostrar a lista, o Katharos confere no Windows quais ajustes já estão como ele faria (por você, por outro programa ou por ele mesmo).",
            "É olhar a casa antes de arrumar: não adianta guardar o que já está guardado.",
            "A conferência fica guardada e vale até você aplicar ou desfazer, o Windows atualizar ou passar um dia. Quando precisa ler de novo, lê por trás, sem travar a tela.",
            "Só leitura: conferir roda cada ajuste em modo teste, sem mudar nada."),
        ["gargalo"] = new("Gargalo", "jogos",
            "A peça que chega no limite primeiro e segura as outras: num jogo, ou a placa de vídeo está a 100 %, ou o processador não entrega quadros rápido o bastante.",
            "É o funil: não adianta despejar mais rápido se a boca é estreita.",
            "O acompanhamento mede, durante o jogo, qual peça ficou no limite e por quanto tempo. Placa de vídeo no limite é o normal (é ela que desenha); processador no limite é onde o Katharos ajuda.",
            "Só leitura."),
    };

    /// <summary>O conceito de uma área do Otimizar ou de um comando do motor (null se não tem).</summary>
    public static string? DoComando(string? cmd) => Rotas.Cabeca(cmd) switch
    {
        "inicializacao" => "inicializacao",
        "servicos" => "servicos",
        "privacidade" => "telemetria",
        "limpar" or "disco" => "cache",
        "energia" => "plano_energia",
        "atualizar" => "driver",
        "travadas" => "travadas",
        "memoria" => "memoria_prometida",
        "restaurar" => "ponto_restauracao",
        "desfazer" => "desfazer",
        _ => null,
    };

    /// <summary>O "?" pequeno ao lado de um título: abre o conceito.</summary>
    public static Button Interrogacao(string chave)
    {
        var b = new Button { Classes = { "link" }, Padding = new Thickness(4), Content = T("?", null, Tema.Ambar, 13).Com(t => t.FontFamily = Tema.Mono), VerticalAlignment = VerticalAlignment.Center };
        if (Todos.TryGetValue(chave, out var c)) ToolTip.SetTip(b, "O que é " + c.Titulo.ToLowerInvariant().Trim('"') + "?");
        b.Click += (_, _) => Abre(chave);
        return b;
    }

    /// <summary>A janelinha do conceito: título com ícone e quatro blocos separados por linha.</summary>
    public static void Abre(string chave)
    {
        var j = Janela.Atual;
        if (j == null || !Todos.TryGetValue(chave, out var c)) return;
        var corpo = new StackPanel { MaxWidth = 600 };
        Control Bloco(string rotulo, string texto, bool primeiro = false) => new Border
        {
            BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, primeiro ? 0 : 1, 0, 0), Padding = new Thickness(0, primeiro ? 0 : 16, 0, 16),
            Child = new StackPanel { Spacing = 6, Children = { T(rotulo, "rotulo"), T(texto, "sub", quebra: true) } },
        };
        corpo.Children.Add(Bloco("O que é", c.OQueE, true));
        corpo.Children.Add(Bloco("Pense assim", c.PenseAssim));
        corpo.Children.Add(Bloco("O que o Katharos faz", c.NoKatharos));
        corpo.Children.Add(new Border
        {
            BorderBrush = Tema.Linha, BorderThickness = new Thickness(0, 1, 0, 0), Padding = new Thickness(0, 16, 0, 0),
            Child = new StackPanel { Spacing = 6, Children = { T("É seguro?", "rotulo"), Item(c.Seguro, Tema.Verde) } },
        });
        if (c.NoWindows != null)
            corpo.Children.Add(new StackPanel { Spacing = 4, Margin = new Thickness(0, 16, 0, 0), Children = { T("No Windows", "rotulo"), T(c.NoWindows, null, Tema.Texto, 13).Com(t => { t.FontFamily = Tema.Mono; t.TextWrapping = Avalonia.Media.TextWrapping.Wrap; }) } });
        var titulo = c.Titulo;
        j.MostraCaixa(Janela.Caixa(titulo, new StackPanel { Spacing = 18, Children = {
                new StackPanel { Orientation = Orientation.Horizontal, Spacing = 10, Children = { Icones.De(c.Icone, 20, Tema.Ambar), T("Conceito", "rotulo").Com(t => t.VerticalAlignment = VerticalAlignment.Center) } },
                corpo } },
            Botao("Entendi", true, j.FechaCaixa).Com(b => { b.HorizontalAlignment = HorizontalAlignment.Right; b.Margin = new Thickness(0, 16, 0, 0); })), true);
    }
}
