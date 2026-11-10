# ──────────────────────────────────────────────────────────────────────────────
# O dicionário grande: mais processos conhecidos, por família. Cada linha: (nomes, o que é, o que fazer, comando).
# Os nomes são de processo (minúsculas, sem .exe). Entra aqui o que aparece de verdade no Gerenciador de Tarefas
# de PCs de casa, de jogo e de trabalho. Na dúvida sobre o que um processo é, ele NÃO entra: melhor "não conheço"
# do que explicar errado.
# ──────────────────────────────────────────────────────────────────────────────

_NORMAL = 'faz parte do Windows: normal'
_INI = 'tire da inicialização se não usa todo dia'
_ABAS = 'feche abas e veja as extensões'

FAMILIAS = [
    # ── Windows: núcleo e sessão ──
    ('smss wininit winlogon services lsaiso dllhost conhost sihost backgroundtaskhost applicationframehost '
     'systemsettings systemsettingsbroker useroobebroker lockapp logonui userinit dashost wudfhost unsecapp '
     'securityhealthsystray securityhealthhost sgrmbroker msdtc vds vssvc wlanext wmiapsrv wmiadap smartscreen '
     'crossdeviceservice crossdeviceresume mobsync taskmgr mmc regedit notepad calculatorapp snippingtool '
     'screenclippinghost aggregatorhost dataexchangehost easeofaccessdialog magnify narrator osk tabtip '
     'openwith pickerhost credentialuibroker consent rundll32 msiexec werfault wermgr winstore.app',
     'parte do Windows', _NORMAL, ''),
    ('ntoskrnl secure system', 'o núcleo do Windows', 'se gasta muito parado, é driver: veja "saude"', 'saude'),
    ('idle', 'o tempo em que o processador está livre', 'quanto maior, melhor: não é um programa', ''),
    ('wsl wslhost wslservice wslrelay', 'o Linux dentro do Windows (WSL)', 'rode "wsl --shutdown" quando não usa', ''),
    ('vmcompute vmms vmwp', 'máquinas virtuais do Hyper-V', 'a memória é da máquina virtual', ''),
    ('windowsterminal openconsole cmd powershell pwsh powershell_ise', 'um terminal aberto', 'é o que você (ou um script) está rodando nele', ''),
    ('werfault wermgr', 'o relatório de erros do Windows', 'aparece quando um programa trava: veja "saude"', 'saude'),
    ('msiexec', 'um instalador do Windows trabalhando', 'espere a instalação terminar', ''),
    ('tiworker trustedinstaller musnotification musnotifyicon updatenotificationmgr usocoreworker wuaucltcore sihclient',
     'o Windows Update', 'espere terminar e reinicie', 'atualizar'),
    ('defrag dfrgui', 'a otimização de unidades', 'passa sozinho; em SSD é só o TRIM', ''),
    ('chkdsk autochk', 'a verificação de disco', 'espere terminar', ''),
    ('sfc', 'a verificação de arquivos do Windows', 'espere terminar', ''),
    ('searchfilterhost searchui', 'a busca do Windows', 'passa sozinho', ''),
    ('ngen ngentask mscorsvw', 'o .NET recompilando programas depois de uma atualização', 'passa sozinho em alguns minutos', ''),
    ('mpcmdrun mpsigstub msseces', 'o antivírus do Windows (Defender)', 'passa sozinho', 'disco'),
    ('sdxhelper officeclicktorun officec2rclient appvshnotify msoia', 'o instalador e atualizador do Office', 'normal; pesa só enquanto atualiza', ''),
    ('msteamsupdate squirrel update', 'um atualizador de programa', 'passa sozinho', ''),
    ('gameinputsvc gamingservicesnet xboxgamebarwidgets xboxappservices xgamehelper', 'serviços de jogos do Xbox',
     'necessários para jogos da Microsoft Store', ''),
    ('gamebarpresencewriter bcastdvr broadcastdvrserver', 'a gravação de jogos do Xbox', 'o pacote de jogos desliga a gravação em segundo plano', 'jogos'),
    ('microsoft.photos photos video.ui microsoft.media.player wmplayer', 'fotos e vídeo do Windows', 'normal enquanto está aberto', ''),
    ('hxtsr hxoutlook hxcalendarappimm', 'o app Email e Calendário', 'pode ser removido se você não usa', 'apps'),
    ('m365copilot copilotnative microsoft.copilot aihost aixhost windowsaifoundry', 'a IA do Windows (Copilot)', 'o pacote de privacidade desliga', 'privacidade'),
    ('msedgeupdate microsoftedgeupdate', 'o atualizador do Edge', 'passa sozinho', ''),
    ('identity_helper elevation_service notification_helper', 'um auxiliar do navegador', 'normal', ''),
    ('onedrivesetup onedriveupdater filecoauth filesynchelper', 'o OneDrive', 'muita CPU quer dizer muitos arquivos pequenos sincronizando', 'privacidade'),
    ('peopleexperiencehost', 'os contatos do Windows', 'normal', ''),
    ('msfeedssync newsandinterests', 'notícias e interesses', 'o pacote de privacidade desliga', 'privacidade'),
    ('printisolationhost splwow64', 'a impressão', 'normal enquanto imprime', ''),
    ('wlrmdr', 'avisos de login do Windows', _NORMAL, ''),
    ('quickassist msra', 'a assistência remota', 'feche se você não abriu: alguém pode estar vendo sua tela', ''),
    ('mstsc rdpclip', 'a área de trabalho remota', 'normal durante uma conexão remota', ''),
    # ── navegadores ──
    ('vivaldi opera_gx operagx arc zen librewolf waterfox thorium chromium tor iexplore', 'um navegador', _ABAS, ''),
    ('brave bravebrowser', 'o Brave', _ABAS, ''),
    ('browser_broker crashpad_handler chrome_crashpad_handler', 'um auxiliar de navegador', 'normal', ''),
    # ── comunicação e escritório ──
    ('telegram signal element thunderbird mailbird', 'um programa de mensagens ou e-mail', _INI, 'inicializacao'),
    ('teamviewer teamviewer_service anydesk rustdesk parsecd parsec', 'acesso remoto', 'deixe aberto só quando precisa: ele aceita conexões de fora', 'inicializacao'),
    ('winword excel powerpnt onenote onenotem msaccess mspub visio lync', 'o Microsoft Office', 'normal enquanto está aberto', ''),
    ('soffice soffice.bin wps wpp et', 'um pacote de escritório', 'normal enquanto está aberto', ''),
    ('acrobat acrord32 acrocef rdrcef adobearm armsvc', 'o Adobe Acrobat', 'o atualizador pode sair da inicialização', 'inicializacao'),
    ('notion obsidian evernote todoist trello', 'um app de notas ou tarefas', _INI, 'inicializacao'),
    ('webexmta atmgr ciscocollabhost gotomeeting', 'um app de reunião', _INI, 'inicializacao'),
    # ── criação ──
    ('creative cloud ccxprocess cclibrary coresync adobeipcbroker adobe desktop service adobeupdateservice agsservice agmservice adobegcclient adobenotificationclient',
     'a Adobe Creative Cloud em segundo plano', 'gasta parada: tire da inicialização e abra só com os programas da Adobe', 'inicializacao'),
    ('photoshop illustrator afterfx premiere pro adobe premiere pro lightroom indesign adobe media encoder',
     'um programa da Adobe', 'normal enquanto trabalha; usa muita RAM de propósito', ''),
    ('resolve blender obs64 obs32 streamlabs obs vegas handbrake audacity gimp-2.10 gimp inkscape krita figma figma_agent canva',
     'um programa de criação ou gravação', 'normal enquanto trabalha', ''),
    ('vlc mpc-hc64 mpc-be64 mpv potplayermini64 itunes applemobiledeviceservice', 'um player de mídia', 'normal enquanto toca', ''),
    # ── nuvem e backup ──
    ('dropbox dropboxupdate googledrivefs googledrivesync megasync icloudservices iclouddrive icloudphotos pcloud nextcloud backblaze bztransmit',
     'sincronização de arquivos na nuvem', 'gasta CPU enquanto sincroniza; os arquivos só sobem com ele aberto', 'inicializacao'),
    ('veeam.endpoint.tray acronistrueimage macriumservice reflectmonitor', 'um programa de backup', 'deixe: é o seu backup', ''),
    # ── jogos: lojas e auxiliares ──
    ('steamservice gameoverlayui steamerrorreporter', 'a Steam', 'a sobreposição pode ser desligada nas configurações dela', ''),
    ('epicgameslauncher unrealcefsubprocess epiconlineservices epiconlineservicesuserhelper eosoverlayrenderer-win64-shipping',
     'a loja da Epic', 'feche depois de abrir o jogo; tire da inicialização', 'inicializacao'),
    ('agent battle.net blizzardbrowser blizzarderror', 'a Battle.net', 'tire da inicialização', 'inicializacao'),
    ('origin originwebhelperservice eadesktop ealauncher eaconnect_microsoft ealocalhostsvc eaanticheat.gameservice', 'o EA app',
     'tire da inicialização', 'inicializacao'),
    ('ubisoftgamelauncher upc uplaywebcore ubisoftconnect uplayservice', 'a Ubisoft Connect', 'tire da inicialização', 'inicializacao'),
    ('riotclientux riotclientuxrender riotclientcrashhandler leagueclient leagueclientux', 'o cliente da Riot', 'tire da inicialização', 'inicializacao'),
    ('galaxyclient galaxyclienthelper galaxycommunication gogalaxy', 'o GOG Galaxy', 'tire da inicialização', 'inicializacao'),
    ('rockstarservice launcher socialclubhelper', 'o launcher da Rockstar', 'abre só com o jogo', ''),
    ('amazon games itch playnite heroic lutris prismlauncher curseforge overwolf overwolfbrowser overwolfhelper',
     'um launcher ou gerenciador de jogos', _INI, 'inicializacao'),
    ('minecraftlauncher minecraft tlauncher', 'o launcher do Minecraft', 'pode fechar depois que o jogo abre', ''),
    ('medal medalencoder outplayed', 'gravador de jogadas', 'grava o tempo todo: desligue se não usa', 'inicializacao'),
    ('wallpaper32 wallpaper64 wallpaperservice32 rainmeter lively', 'papel de parede animado ou widgets', 'gasta GPU o tempo todo: pause quando joga', 'inicializacao'),
    ('rtss msiafterburner hwinfo64 hwinfo32 hwmonitor coretemp aida64 cpuz gpu-z fancontrol', 'monitor de hardware',
     'cada um deles lê os sensores o tempo todo: deixe só um aberto', 'inicializacao'),
    ('vgc vgtray vanguard', 'o anti-cheat Vanguard (Valorant)', 'o Katharos não mexe em anti-cheat', ''),
    ('easyanticheat easyanticheat_eos beservice beservice_x64 faceit faceitservice esportal', 'um anti-cheat', 'o Katharos não mexe em anti-cheat', ''),
    # ── placas de vídeo e chips ──
    ('nvidia overlay nvsphelper64 nvcplui nvtelemetrycontainer nvbroadcast nvidia broadcast nvoawrappercache',
     'programas da NVIDIA', 'a sobreposição e a telemetria podem ser desligadas no app da NVIDIA', ''),
    ('amdrsserv amdow atieclxx atiesrxx amdfendrsr cncmd amddvr radeonsoftware amdryzenmasterdriver',
     'o driver e o painel da AMD', 'normal; a gravação (ReLive) pode ser desligada no painel', ''),
    ('igfxtray igfxhk igfxcuiservice igfxext intelgraphicssoftware arccontrol intelcphdcpsvc oneapp.igcc.winservice',
     'o driver e o painel de vídeo da Intel', 'normal', ''),
    ('lms jhi_service ipf_helper ipf_uf esif_uf dptf intelcphecisvc heciserver', 'serviços do chipset Intel (gerenciamento e controle térmico)',
     'deixe: o controle térmico do notebook depende deles', ''),
    ('rtkngui64 rtkauduservice64 rtkbtmanserv ravbg64 ravcpl64 nahimicsvc64 nahimicsvc32 nahimic3 waves maxxaudiopro wavessvc64 dolbydax2api dax3api',
     'o áudio do fabricante', 'os efeitos de som pesam pouco; o Nahimic é conhecido por atrapalhar jogos', ''),
    ('syntpenh syntphelper etdctrl etdservice apoint elantechservice', 'o driver do touchpad', 'deixe: os gestos dependem dele', ''),
    ('ibtsiva btwdins', 'o Bluetooth do fabricante', 'normal', ''),
    ('killerservice killernetworkservice killeranalyticsservice xtuservice', 'software de rede ou ajuste da Intel/Killer',
     'o Killer é conhecido por pesar na rede: dá para usar só o driver', 'servicos'),
    # ── fabricantes de PC ──
    ('asus_framework asusoptimization asussoftwaremanager asussystemanalysis asussystemdiagnosis asuslinknear asuslinkremote asusswitch asuscertservice '
     'armourysocketserver armouryswagent armourycrate armouryhtmldebugserver asusupdatecheck atkexcomsvc rogliveservice aura auraservice aurawallpaperservice',
     'programas da ASUS', 'são vários e somam: use o perfil silencioso ou remova o que não usa', 'programas'),
    ('myasus glidex screenxpert', 'o MyASUS', 'pode sair da inicialização', 'inicializacao'),
    ('dellsupportassistremedationservice supportassist supportassistagent dell.techhub dell.d3.winsvc dell.coreservices.client delldatavault '
     'dellclientmanagementservice dellupdate dellpair ddvdatacollector ddvrulesprocessor ddvcollectorsvcapi dcu-cli',
     'programas de suporte da Dell', 'conhecidos por pesar parados: podem ser removidos', 'programas'),
    ('awcc awcc.service awccservice alienfxsubagent gamelibrarysvc', 'a central da Alienware', 'costuma pesar: atualize ou use o perfil equilibrado', 'servicos'),
    ('hpsupportassistant hpsa_service hpsysteminfocap hpdiagscap hpnetworkcap hpappheliercap hpanalyticscomp hpcommrecovery hpaudioanalytics '
     'hpprintscandoctorservice hpomencap omencommandcenterbackground hpsmartexperiences sysinfocap networkcap apphelpercap diagscap',
     'programas e telemetria da HP', 'são muitos serviços que consultam o PC o tempo todo: podem ser removidos', 'programas'),
    ('lenovovantage lenovovantageservice lenovo.modern.imcontroller imcontrollerservice lenovonow lenovoutilityservice lenovofnandfunctionkeys '
     'utility lnbitssvc systeminterfacefoundation legionzone lzservice legionfancontrol',
     'programas da Lenovo', 'o Vantage pode ficar em manual; as teclas de função dependem do "Utility"', 'servicos'),
    ('acersysmonitorservice acerccagent acercentralservice acerqaagent quickaccess nitrosense predatorsense acerservice aasvc',
     'programas da Acer', 'a central de ventoinha pode ficar; o resto pode sair da inicialização', 'inicializacao'),
    ('msi.centralserver msi.terminalserver msi_central_service mystic_light_service dragoncenter msiservice lightkeeperservice ledkeeper2 msiapservice',
     'programas da MSI', 'costumam pesar: atualize ou tire da inicialização', 'servicos'),
    ('samsungsystemsupportengine samsungsettings samsungdex smartthings galaxybookexperience', 'programas da Samsung', _INI, 'inicializacao'),
    ('gigabyte control center gcc easytuneengineservice sivservice rgbfusion gamingotservice', 'programas da Gigabyte',
     'conhecidos por pesar: deixe só se usa RGB ou controle de ventoinha', 'servicos'),
    # ── periféricos e RGB ──
    ('lghub lghub_agent lghub_updater lghub_system_tray lcore logioptionsplus logioptionsplus_agent logioptions logi_lamparray_service setpoint',
     'programas da Logitech', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    ('razer synapse 3 razer synapse service razer central razercentralservice rzsdkservice rzsdkserver razer cortex gamemanagerservice rzchromastreamserver',
     'programas da Razer', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    ('icue corsair.service corsair.service.cpuidremote corsair.service.displayadapter corsairgamingaudiocfgservice64 cuellaccessservice',
     'o iCUE da Corsair', 'conhecido por gastar CPU: atualize ou feche quando não precisa', 'inicializacao'),
    ('steelseriesgg steelseriesengine steelseriesggclient steelseriessonar steelseriesprismsync', 'o SteelSeries GG', _INI, 'inicializacao'),
    ('hyperx ngenuity ngenuity2 openrgb signalrgb signalrgblauncher nzxt cam nzxt cam roccat_swarm_monitor wootility', 'software de periférico ou RGB',
     'RGB sincronizado gasta CPU o tempo todo: feche se não faz questão', 'inicializacao'),
    ('wacom_tablet wacomhost wtabletserviceisd pen_tablet', 'o driver da mesa digitalizadora', 'deixe: a caneta depende dele', ''),
    ('epson status monitor 3 e_yatiave canonmydeviceservice hpstatusbl brmfcmon', 'o monitor da impressora', 'pode sair da inicialização: a impressora continua funcionando', 'inicializacao'),
    # ── antivírus e segurança de terceiros ──
    ('avastui avastsvc aswidsagent aswenginesrv wsc_proxy afwserv avgui avgsvc avgidsagent', 'o antivírus Avast/AVG',
     'o Defender pesa menos; se quer manter, é escolha sua', 'programas'),
    ('mcuicnt mcshield mfemms mfevtps mfefire mcapexe mccspservicehost modulecoreservice mcafee.truekey pefservice mmsshost servicehost',
     'o McAfee', 'costuma vir de fábrica e pesar: remova se não pagou por ele', 'programas'),
    ('nortonsecurity ns nortonui nortonsvc nllclientsvc', 'o Norton', 'costuma vir de fábrica: remova se não pagou por ele', 'programas'),
    ('avp avpui ksde kavfs', 'o Kaspersky', 'é o seu antivírus: o Katharos não mexe', ''),
    ('bdagent bdservicehost vsserv bdredline epsecurityservice', 'o Bitdefender', 'é o seu antivírus: o Katharos não mexe', ''),
    ('ekrn egui eguiproxy', 'o ESET', 'é o seu antivírus: o Katharos não mexe', ''),
    ('mbam mbamservice mbamtray', 'o Malwarebytes', 'a versão grátis não precisa abrir com o Windows', 'inicializacao'),
    ('avguard avira.servicehost avira.systray avira.spotlight.service', 'o Avira', 'o Defender pesa menos', 'programas'),
    ('csfalconservice csfalconcontainer sentinelagent sentinelone cbdefense repmgr cylancesvc taniumclient ccmexec nessusd qualysagent zsatunnel '
     'zsatray vpnagent vpnui globalprotect pangps pangpa forticlient fortitray nxtray netskope stagentsvc',
     'segurança ou gestão da empresa', 'é do TI da sua empresa: não mexa (e use o modo seguro neste PC)', ''),
    ('1password bitwarden keepass keepassxc lastpass dashlane nordpass protonpass', 'um gerenciador de senhas', 'deixe aberto: é ele que preenche as senhas', ''),
    ('nordvpn nordvpn-service expressvpn expressvpnd protonvpn protonvpnservice surfshark openvpn openvpn-gui wireguard tailscale tailscaled tailscale-ipn '
     'cloudflare warp warp-svc mullvad-daemon windscribe hamachi-2 zerotier-one_x64 radminvpn',
     'uma VPN', 'ligada, deixa a internet e os jogos com mais atraso: ligue só quando precisa', 'inicializacao'),
    # ── utilitários ──
    ('powertoys powertoys.runner powertoys.awake powertoys.fancyzones powertoys.powerlauncher powertoys.colorpickerui powertoys.keyboardmanagerengine',
     'o PowerToys', 'desligue dentro dele os módulos que não usa', ''),
    ('everything sharex lightshot greenshot flameshot ditto f.lux flux autohotkey autohotkeyu64 espanso keypirinha listary flow.launcher '
     'translucenttb startallbackcfg explorerpatcher eartrumpet twinkletray quicklook nilesoft.shell', 'um utilitário que fica na bandeja',
     'leve; deixe se você usa', ''),
    ('7zfm 7zg 7z winrar rar peazip bandizip', 'um compactador trabalhando', 'gasta CPU só enquanto compacta', ''),
    ('qbittorrent utorrent bittorrent transmission-qt deluge tixati fdm idman iemonitor jdownloader2', 'um programa de download',
     'usa disco e rede o tempo todo enquanto baixa ou semeia', 'inicializacao'),
    ('ccleaner ccleaner64 ccleanerbrowser iobit advancedsystemcare asc driverbooster iobituninstaler glaryutilities wisecare365 pcappstore '
     'driver easy drivereasy smartdefrag auslogics reimage restoro outbyte avastcleanup avgtuneup',
     'um "otimizador" que fica rodando', 'fica residente e vende limpeza: não precisa abrir com o Windows, e pode ser removido', 'programas'),
    ('java javaw javaws jusched jucheck jp2launcher', 'o Java', 'o atualizador (jusched) pode sair da inicialização', 'inicializacao'),
    ('virtualbox virtualboxvm vboxsvc vboxheadless vmware vmware-vmx vmware-tray vmware-authd vmnat vmnetdhcp qemu-system-x86_64 bluestacks hd-player '
     'hd-agent ldplayer dnplayer nox noxvmhandle memu msiplayer androidemulator',
     'uma máquina virtual ou emulador de Android', 'usa muita RAM de propósito: feche quando não usa', ''),
    # ── programação ──
    ('code code - insiders cursor windsurf devenv rider64 idea64 pycharm64 webstorm64 clion64 goland64 phpstorm64 datagrip64 studio64 '
     'sublime_text notepad++ atom zed fleet', 'um editor de código', 'extensões e indexação pesam: normal ao abrir um projeto grande', ''),
    ('node deno bun npm yarn pnpm tsserver esbuild vite webpack', 'JavaScript rodando (um servidor ou build seu)', 'feche o terminal ou o editor que abriu', ''),
    ('python python3 pythonw py jupyter-lab jupyter-notebook conda', 'um programa em Python', 'é algo que você ou outro programa abriu', ''),
    ('git git-remote-https ssh ssh-agent gpg-agent github desktop githubdesktop sourcetree gitkraken fork', 'o Git ou um cliente dele', 'normal durante clone, pull e push', ''),
    ('docker dockerd com.docker.service com.docker.build docker desktop backend vpnkit docker-desktop', 'o Docker Desktop',
     'feche quando não usa: ele mantém uma máquina virtual ligada', ''),
    ('msbuild cl link vbcscompiler dotnet cargo rustc rust-analyzer gopls go gradle java gcc g++ clang cmake ninja make',
     'um compilador ou servidor de linguagem', 'normal enquanto compila ou analisa o projeto', ''),
    ('postgres mysqld mongod redis-server sqlservr sqlwriter sqlbrowser sqlceip mariadbd elasticsearch', 'um banco de dados local',
     'fica ligado o tempo todo: ponha em manual se só usa de vez em quando', 'servicos'),
    ('ollama ollama app lm studio lmstudio koboldcpp', 'um modelo de IA local', 'usa muita RAM e placa de vídeo de propósito: feche quando não usa', ''),
    ('adb emulator qemu-system-x86_64-headless', 'ferramentas do Android', 'normal com o Android Studio aberto', ''),
    ('postman insomnia dbeaver heidisql ssms azuredatastudio wireshark fiddler', 'uma ferramenta de desenvolvimento', 'normal enquanto está aberta', ''),
]

for _nomes, _oque, _faz, _cmd in FAMILIAS:
    # nomes com espaço vêm juntos na mesma string; os conhecidos de duas palavras são reconhecidos pela lista abaixo
    for _n in _nomes.split():
        PROCESSOS.setdefault(_n, (_oque, _faz, _cmd))

# nomes de processo com espaço (o split acima os quebraria): entram inteiros
for _n, _v in {
    'creative cloud': ('a Adobe Creative Cloud em segundo plano', 'tire da inicialização e abra só com os programas da Adobe', 'inicializacao'),
    'adobe desktop service': ('a Adobe Creative Cloud em segundo plano', 'tire da inicialização e abra só com os programas da Adobe', 'inicializacao'),
    'adobe premiere pro': ('o Adobe Premiere', 'normal enquanto trabalha; usa muita RAM de propósito', ''),
    'adobe media encoder': ('o Adobe Media Encoder', 'normal enquanto exporta', ''),
    'streamlabs obs': ('o Streamlabs', 'normal enquanto transmite', ''),
    'razer synapse 3': ('o Razer Synapse', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    'razer synapse service': ('o Razer Synapse', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    'razer central': ('o Razer Central', 'tire da inicialização', 'inicializacao'),
    'razer cortex': ('o Razer Cortex', 'é um "otimizador" residente: não precisa abrir com o Windows', 'inicializacao'),
    'nvidia overlay': ('a sobreposição da NVIDIA', 'desligue no app da NVIDIA se não grava', ''),
    'nvidia broadcast': ('o NVIDIA Broadcast', 'usa a placa de vídeo o tempo todo: feche quando não está em chamada', 'inicializacao'),
    'docker desktop backend': ('o Docker Desktop', 'feche quando não usa: ele mantém uma máquina virtual ligada', ''),
    'github desktop': ('o GitHub Desktop', 'normal enquanto está aberto', ''),
    'lm studio': ('um modelo de IA local (LM Studio)', 'usa muita RAM e placa de vídeo de propósito', ''),
    'ollama app': ('um modelo de IA local (Ollama)', 'usa muita RAM e placa de vídeo de propósito', ''),
    'amazon games': ('o launcher da Amazon Games', _INI, 'inicializacao'),
    'nzxt cam': ('o NZXT CAM', 'conhecido por gastar CPU: feche se não precisa do controle de ventoinha', 'inicializacao'),
    'epson status monitor 3': ('o monitor da impressora Epson', 'pode sair da inicialização', 'inicializacao'),
    'gigabyte control center': ('o Gigabyte Control Center', 'conhecido por pesar: deixe só se usa RGB ou ventoinha', 'servicos'),
    'cloudflare warp': ('a VPN da Cloudflare (WARP)', 'ligada, pode aumentar o atraso nos jogos', 'inicializacao'),
    'driver easy': ('um "atualizador de drivers"', 'instala drivers de origem duvidosa: prefira o Windows Update e o site do fabricante', 'programas'),
    'code - insiders': ('o Visual Studio Code', 'extensões pesam: veja "Developer: Show Running Extensions"', ''),
}.items():
    PROCESSOS[_n] = _v

# pedaços soltos dos nomes com espaço (o split os deixou para trás) não querem dizer nada sozinhos
_MULTI = [k for k in PROCESSOS if ' ' in k]
for _n in {tok for k in _MULTI for tok in k.split()} - {'code', 'ollama', 'docker', 'update', 'launcher', 'agent', 'system'}:
    PROCESSOS.pop(_n, None)

# o começo do nome já diz de quem é (para o que não está listado um a um)
PREFIXOS = [
    ('asus', 'um programa da ASUS', 'veja se você usa; a ASUS instala vários', 'programas'),
    ('armoury', 'a central da ASUS (Armoury Crate)', 'costuma pesar: use o perfil silencioso ou atualize', 'servicos'),
    ('dell', 'um programa da Dell', 'os de suporte podem ser removidos', 'programas'),
    ('hpsupport', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpomen', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpsa_', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpdiag', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpprint', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpaudio', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpnetwork', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpsystem', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpsmart', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpq', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hptouchpoint', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpanalytics', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('hpcomm', 'um programa da HP', 'os de suporte e telemetria podem ser removidos', 'programas'),
    ('lenovo', 'um programa da Lenovo', 'pode ficar em manual', 'servicos'),
    ('acer', 'um programa da Acer', 'pode sair da inicialização', 'inicializacao'),
    ('msi.', 'um programa da MSI', 'costuma pesar: atualize ou tire da inicialização', 'servicos'),
    ('samsung', 'um programa da Samsung', _INI, 'inicializacao'),
    ('nvidia', 'um componente da NVIDIA', 'normal', ''),
    ('amd', 'um componente da AMD', 'normal', ''),
    ('radeon', 'um componente da AMD', 'normal', ''),
    ('igfx', 'um componente de vídeo da Intel', 'normal', ''),
    ('intel', 'um componente da Intel', 'normal', ''),
    ('rtk', 'um componente da Realtek (som ou rede)', 'normal', ''),
    ('razer', 'um programa da Razer', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    ('logi', 'um programa da Logitech', 'tire da inicialização se o perfil já está salvo no mouse', 'inicializacao'),
    ('corsair', 'um programa da Corsair', 'conhecido por gastar CPU: feche quando não precisa', 'inicializacao'),
    ('steelseries', 'um programa da SteelSeries', _INI, 'inicializacao'),
    ('steam', 'a Steam', 'tire da inicialização se não joga todo dia', 'inicializacao'),
    ('epic', 'a loja da Epic', 'tire da inicialização', 'inicializacao'),
    ('riot', 'o cliente da Riot', 'tire da inicialização', 'inicializacao'),
    ('ubisoft', 'a Ubisoft Connect', 'tire da inicialização', 'inicializacao'),
    ('adobe', 'um programa da Adobe', 'os que ficam em segundo plano podem sair da inicialização', 'inicializacao'),
    ('microsoft.', 'um app da Microsoft', 'normal', ''),
    ('windows.', 'parte do Windows', _NORMAL, ''),
    ('powertoys', 'o PowerToys', 'desligue dentro dele os módulos que não usa', ''),
    ('mcafee', 'o McAfee', 'costuma vir de fábrica: remova se não pagou por ele', 'programas'),
    ('norton', 'o Norton', 'costuma vir de fábrica: remova se não pagou por ele', 'programas'),
    ('avast', 'o antivírus Avast', 'o Defender pesa menos', 'programas'),
    ('avg', 'o antivírus AVG', 'o Defender pesa menos', 'programas'),
    ('vmware', 'o VMware', 'a memória é da máquina virtual', ''),
    ('vbox', 'o VirtualBox', 'a memória é da máquina virtual', ''),
    ('jetbrains', 'um editor da JetBrains', 'indexação pesa ao abrir um projeto', ''),
]
# o fim do nome diz o que o programa está fazendo, mesmo sem saber de quem é
SUFIXOS = [
    ('-win64-shipping', 'um jogo feito na Unreal Engine', 'é o jogo em si: o pacote "jogos" ajusta o Windows para ele', 'jogos'),
    ('-wingdk-shipping', 'um jogo da Microsoft Store feito na Unreal Engine', 'é o jogo em si', 'jogos'),
    ('crashhandler', 'o relator de erros de um programa', 'normal', ''),
    ('crashreporter', 'o relator de erros de um programa', 'normal', ''),
    ('webhelper', 'as páginas embutidas de um programa', 'fecha junto com o programa', ''),
    ('updater', 'o atualizador de um programa', 'passa sozinho; pode sair da inicialização', 'inicializacao'),
    ('update', 'o atualizador de um programa', 'passa sozinho; pode sair da inicialização', 'inicializacao'),
    ('setup', 'um instalador rodando', 'espere terminar', ''),
    ('installer', 'um instalador rodando', 'espere terminar', ''),
    ('tray', 'o ícone de um programa na bandeja', 'pode sair da inicialização se você não usa', 'inicializacao'),
    ('launcher', 'o abridor de um programa ou jogo', 'pode fechar depois que o programa abre', ''),
]


def quem_e(nome):
    """(o que é, o que fazer, comando) para um nome de processo, ou None se o Katharos não conhece.
    Primeiro o nome exato, depois o jogo do catálogo, depois de quem é (começo do nome) e o que faz (fim do nome)."""
    n = str(nome or '').strip().lower()
    if n.endswith('.exe'):
        n = n[:-4]
    n = re.sub(r'#\d+$', '', n)
    if not n:
        return None
    if n in PROCESSOS:
        return PROCESSOS[n]
    for sufixo, oque, faz, cmd in SUFIXOS:
        if n.endswith(sufixo) and len(n) > len(sufixo):
            return (oque, faz, cmd)
    for prefixo, oque, faz, cmd in sorted(PREFIXOS, key=lambda x: -len(x[0])):
        if n.startswith(prefixo) and len(n) > len(prefixo):
            return (oque, faz, cmd)
    return None
