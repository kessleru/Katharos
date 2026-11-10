# ──────────────────────────────────────────────────────────────────────────────
# Quem é quem: o que é cada processo que aparece gastando CPU, memória ou disco, e o que dá para fazer.
# Só nomes de processo (sem .exe, minúsculas). O raio-x usa isto para explicar em vez de só listar.
# Cada entrada: (o que é, o que fazer, comando do Katharos que ajuda ou '').
# ──────────────────────────────────────────────────────────────────────────────

PROCESSOS = {
    # Windows
    'system': ('o núcleo do Windows e os drivers', 'se gasta muito parado, é driver: veja "saude"', 'saude'),
    'system interrupts': ('interrupções de hardware', 'alto parado indica driver ou dispositivo com defeito', 'saude'),
    'registry': ('o registro do Windows na memória', 'normal', ''),
    'memory compression': ('memória comprimida pelo Windows', 'muito alta quer dizer RAM faltando', 'inicializacao'),
    'memcompression': ('memória comprimida pelo Windows', 'muito alta quer dizer RAM faltando', 'inicializacao'),
    'svchost': ('serviços do Windows agrupados', 'normal; se um deles gasta muito, o Gerenciador de Tarefas diz qual', 'servicos'),
    'dwm': ('desenha as janelas (Gerenciador de Janelas)', 'alto quer dizer efeitos visuais pesando ou driver de vídeo', 'visual'),
    'explorer': ('a área de trabalho e as pastas', 'se gasta muito, uma extensão de menu ou miniatura travou: reinicie o Explorer', ''),
    'msmpeng': ('o antivírus do Windows (Defender) verificando arquivos', 'passa sozinho; o pacote de disco deixa as varreduras mais leves', 'disco'),
    'nissrv': ('a inspeção de rede do Defender', 'normal', ''),
    'mpdefendercoreservice': ('o núcleo do Defender', 'normal', ''),
    'tiworker': ('o Windows Update instalando', 'espere terminar e reinicie', 'atualizar'),
    'trustedinstaller': ('o instalador de componentes do Windows', 'espere terminar e reinicie', 'atualizar'),
    'mousocoreworker': ('o Windows Update procurando atualizações', 'passa sozinho', 'atualizar'),
    'wuauclt': ('o Windows Update', 'passa sozinho', 'atualizar'),
    'usoclient': ('o Windows Update', 'passa sozinho', 'atualizar'),
    'searchindexer': ('o índice da busca do Windows', 'depois de muita cópia de arquivo ele trabalha; se nunca para, reduza as pastas indexadas', 'servicos'),
    'searchhost': ('a busca do menu Iniciar', 'normal', ''),
    'searchapp': ('a busca do menu Iniciar', 'normal', ''),
    'searchprotocolhost': ('o índice da busca lendo arquivos', 'passa sozinho', ''),
    'compattelrunner': ('a telemetria de compatibilidade da Microsoft', 'o pacote de privacidade desliga', 'privacidade'),
    'diagtrack': ('a telemetria do Windows', 'o pacote de privacidade desliga', 'privacidade'),
    'wmiprvse': ('consultas WMI que outros programas fazem', 'quase sempre é programa de fabricante perguntando sem parar', 'servicos'),
    'wsappx': ('a Microsoft Store instalando ou atualizando apps', 'passa sozinho', ''),
    'runtimebroker': ('permissões dos apps da Store', 'normal', ''),
    'audiodg': ('o áudio do Windows', 'alto indica efeito de áudio do driver: desligue os aprimoramentos de som', ''),
    'spoolsv': ('a fila de impressão', 'se gasta muito, há impressão presa', 'servicos'),
    'widgets': ('os Widgets do Windows 11', 'o pacote de privacidade desliga', 'privacidade'),
    'widgetservice': ('os Widgets do Windows 11', 'o pacote de privacidade desliga', 'privacidade'),
    'phoneexperiencehost': ('o Vincular ao Celular', 'tire da inicialização se não usa', 'inicializacao'),
    'yourphone': ('o Vincular ao Celular', 'tire da inicialização se não usa', 'inicializacao'),
    'gamebar': ('a Barra de Jogos do Xbox', 'o pacote de jogos desliga a gravação em segundo plano', 'jogos'),
    'gamebarftserver': ('a Barra de Jogos do Xbox', 'o pacote de jogos desliga a gravação em segundo plano', 'jogos'),
    'copilot': ('o Copilot', 'o pacote de privacidade desliga', 'privacidade'),
    'msedgewebview2': ('páginas embutidas em outros programas (WebView2)', 'quem usa é o programa que abriu: Teams, Widgets, Outlook novo', ''),
    'smartscreen': ('a checagem de programas baixados', 'proteção: deixe ligada', ''),
    'securityhealthservice': ('a Segurança do Windows', 'normal', ''),
    'lsass': ('logins e senhas do Windows', 'normal', ''),
    'csrss': ('parte do núcleo do Windows', 'normal', ''),
    'fontdrvhost': ('fontes do Windows', 'normal', ''),
    'ctfmon': ('teclado e idiomas', 'normal', ''),
    'taskhostw': ('tarefas agendadas do Windows', 'normal', ''),
    'sihost': ('a interface do Windows', 'normal', ''),
    'startmenuexperiencehost': ('o menu Iniciar', 'normal', ''),
    'shellexperiencehost': ('a barra de tarefas e as notificações', 'normal', ''),
    'textinputhost': ('o teclado virtual e os emojis', 'normal', ''),
    'vmmem': ('uma máquina virtual (WSL, Docker ou Hyper-V)', 'a memória é da máquina virtual: limite no .wslconfig ou feche-a', ''),
    'vmmemwsl': ('o Linux do WSL', 'limite a memória no arquivo .wslconfig ou rode "wsl --shutdown"', ''),
    'vmwp': ('uma máquina virtual do Hyper-V', 'a memória é da máquina virtual', ''),
    'onedrive': ('o OneDrive sincronizando', 'muita CPU quer dizer muitos arquivos pequenos na pasta sincronizada', 'privacidade'),
    'cleanmgr': ('a Limpeza de Disco', 'passa sozinho', ''),
    'dism': ('reparo ou limpeza de componentes do Windows', 'espere terminar', ''),
    'dismhost': ('reparo ou limpeza de componentes do Windows', 'espere terminar', ''),
    'sppsvc': ('a ativação do Windows e do Office', 'passa sozinho', ''),
    'mrt': ('a Ferramenta de Remoção de Software Mal-Intencionado', 'roda uma vez por mês', ''),
    'software_reporter_tool': ('o verificador do Chrome', 'passa sozinho', ''),
    # navegadores e comunicação
    'chrome': ('o Google Chrome', 'cada aba e extensão é um processo: feche abas e veja as extensões', ''),
    'msedge': ('o Microsoft Edge', 'cada aba e extensão é um processo; desligue o "início rápido" dele', 'privacidade'),
    'firefox': ('o Firefox', 'feche abas e veja as extensões', ''),
    'brave': ('o Brave', 'feche abas e veja as extensões', ''),
    'opera': ('o Opera', 'feche abas e veja as extensões', ''),
    'teams': ('o Microsoft Teams', 'tire da inicialização se não usa todo dia', 'inicializacao'),
    'ms-teams': ('o Microsoft Teams', 'tire da inicialização se não usa todo dia', 'inicializacao'),
    'discord': ('o Discord', 'desligue a aceleração por hardware e a sobreposição se pesa no jogo', 'inicializacao'),
    'slack': ('o Slack', 'tire da inicialização se não usa todo dia', 'inicializacao'),
    'whatsapp': ('o WhatsApp', 'tire da inicialização se não usa todo dia', 'inicializacao'),
    'spotify': ('o Spotify', 'tire da inicialização', 'inicializacao'),
    'zoom': ('o Zoom', 'tire da inicialização', 'inicializacao'),
    'skype': ('o Skype', 'tire da inicialização', 'inicializacao'),
    'outlook': ('o Outlook', 'normal enquanto sincroniza', ''),
    'olk': ('o Outlook novo', 'normal enquanto sincroniza', ''),
    # jogos e lojas
    'steam': ('a Steam', 'tire da inicialização se não joga todo dia', 'inicializacao'),
    'steamwebhelper': ('as páginas dentro da Steam', 'o modo "pouco desempenho" da Steam reduz', ''),
    'epicgameslauncher': ('a loja da Epic', 'tire da inicialização', 'inicializacao'),
    'epicwebhelper': ('as páginas dentro da loja da Epic', 'feche a loja depois de abrir o jogo', ''),
    'battle.net': ('a Battle.net', 'tire da inicialização', 'inicializacao'),
    'eadesktop': ('o EA app', 'tire da inicialização', 'inicializacao'),
    'eabackgroundservice': ('o serviço do EA app', 'pode ficar em manual', 'servicos'),
    'upc': ('a Ubisoft Connect', 'tire da inicialização', 'inicializacao'),
    'ubisoftconnect': ('a Ubisoft Connect', 'tire da inicialização', 'inicializacao'),
    'riotclientservices': ('o cliente da Riot', 'tire da inicialização', 'inicializacao'),
    'galaxyclient': ('o GOG Galaxy', 'tire da inicialização', 'inicializacao'),
    'xboxpcapp': ('o app Xbox', 'normal enquanto baixa jogos', ''),
    'gamingservices': ('os serviços de jogos do Xbox', 'necessário para jogos da Microsoft Store', ''),
    # placas de vídeo e fabricantes
    'nvcontainer': ('serviços da NVIDIA', 'normal', ''),
    'nvdisplay.container': ('o driver de vídeo da NVIDIA', 'normal', ''),
    'nvidia app': ('o app da NVIDIA', 'a sobreposição pode ser desligada nele', ''),
    'nvidia share': ('a sobreposição da NVIDIA', 'desligue a sobreposição no app da NVIDIA se não grava', ''),
    'nvidia web helper': ('o GeForce Experience', 'pode ser desinstalado se você não usa', 'programas'),
    'radeonsoftware': ('o painel da AMD', 'normal; a sobreposição pode ser desligada nele', ''),
    'amdrsserv': ('o serviço do painel da AMD', 'normal', ''),
    'igfxem': ('o driver de vídeo da Intel', 'normal', ''),
    'armourycrate.service': ('a central da ASUS (Armoury Crate)', 'costuma pesar: use o perfil silencioso ou atualize', 'servicos'),
    'armourycrate.usersessionhelper': ('a central da ASUS (Armoury Crate)', 'costuma pesar: use o perfil silencioso ou atualize', 'servicos'),
    'lightingservice': ('as luzes RGB da ASUS', 'conhecido por gastar CPU: desligue se não usa RGB', 'servicos'),
    'awcc': ('a central da Alienware', 'costuma pesar: atualize ou use o perfil equilibrado', 'servicos'),
    'lenovovantageservice': ('o Lenovo Vantage', 'pode ficar em manual', 'servicos'),
    'supportassistagent': ('o Dell SupportAssist', 'conhecido por pesar: pode ser removido', 'programas'),
    'hpsupportsolutionsframeworkservice': ('o HP Support Assistant', 'pode ser removido', 'programas'),
    'touchpointanalyticsclientservice': ('a telemetria da HP', 'pode ser removida', 'programas'),
    'msi.centralserver': ('o MSI Center', 'costuma pesar: atualize ou tire da inicialização', 'servicos'),
    'icue': ('o iCUE da Corsair', 'conhecido por gastar CPU: atualize ou feche quando não precisa', 'inicializacao'),
    'lghub': ('o Logitech G HUB', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    'razer synapse': ('o Razer Synapse', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    'rtkauduservice64': ('o áudio da Realtek', 'normal', ''),
    # antivírus de terceiros
    'mcshield': ('o antivírus McAfee', 'o Defender pesa menos: remova se não pagou por ele', 'programas'),
    'mfemms': ('o antivírus McAfee', 'o Defender pesa menos: remova se não pagou por ele', 'programas'),
    'avastsvc': ('o antivírus Avast', 'o Defender pesa menos', 'programas'),
    'avgsvc': ('o antivírus AVG', 'o Defender pesa menos', 'programas'),
    'nortonsecurity': ('o antivírus Norton', 'o Defender pesa menos: remova se não pagou por ele', 'programas'),
    # programação
    'node': ('o Node.js (um programa seu ou de um editor)', 'feche o servidor ou o editor que abriu', ''),
    'code': ('o Visual Studio Code', 'extensões pesam: veja "Developer: Show Running Extensions"', ''),
    'python': ('um programa em Python', 'é algo que você ou outro programa abriu', ''),
    'java': ('um programa em Java', 'é algo que você ou outro programa abriu', ''),
    'javaw': ('um programa em Java (o Minecraft, por exemplo)', 'ajuste a memória no launcher', ''),
    'docker desktop': ('o Docker Desktop', 'feche quando não usa: ele mantém uma máquina virtual ligada', ''),
    'com.docker.backend': ('o Docker Desktop', 'feche quando não usa: ele mantém uma máquina virtual ligada', ''),
    'devenv': ('o Visual Studio', 'normal enquanto compila ou indexa', ''),
}


def o_que_e(x):
    """O que é um processo do raio-x: o que o Katharos conhece; se não conhece, o que o próprio arquivo declara (descrição e empresa)."""
    q = quem_e(x.get('n'))
    if q:
        return q[0]
    desc, emp = str(x.get('desc') or '').strip(), str(x.get('emp') or '').strip()
    if desc and emp and emp.lower() not in desc.lower():
        return f'{desc}, de {emp}'
    if desc or emp:
        return desc or f'um programa de {emp}'
    return 'não conheço este'


def explica_processos(lista_proc, campo, unidade, limite=3):
    """'chrome 12% (o Google Chrome), xyz 4%': os primeiros de uma lista do raio-x, com o que cada um é."""
    partes = []
    for x in lista_proc[:limite]:
        q = o_que_e(x)
        valor = f'{br(x.get(campo), 1 if unidade == "%" else 0)}{" " if unidade != "%" else ""}{unidade}'
        partes.append(f'{x.get("n")} {valor}' + (f' ({q})' if q != 'não conheço este' else ''))
    return ', '.join(partes)
