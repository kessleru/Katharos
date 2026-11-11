---
title: Pesquisa de personalização do Windows (Windhawk, PowerToys e outros)
date: 2026-11-11
tags: [pesquisa, katharos, personalizacao, windhawk, powertoys]
---
# Pesquisa de personalização do Windows

Base do plano [Personalização, otimização e relatório](../2026-11-personalizacao-otimizacao-relatorio.md).

## O que o catálogo do Windhawk mostra
- **898 mods**, soma de **7,48 milhões** de instalações, lido do catálogo oficial (`mods.windhawk.net/catalog.json`) em 11 nov 2026.
- Os quatro mais usados são estilizadores: barra de tarefas (1,12 mi), menu Iniciar (1,01 mi), central de notificações (624 mil) e
  Explorador (357 mil). O que a maioria quer é **mudar a aparência do shell**, não trocar o Windows por outro.
- Depois vêm ajustes de uso do dia a dia: tamanho da barra, tamanho das pastas no Explorador, volume rolando o mouse na barra, relógio
  com mais informação, barra que some só com janela maximizada, clique do meio fechando o programa.
- Alguns mods entram em **todos os processos** (`*`) ou no **compositor de tela** (`dwm.exe`): animações de janela, janelas translúcidas,
  bordas e cantos. Esses ficam fora das receitas do Katharos (anti-cheat e risco de falha na imagem).
- O Windhawk entra em todos os processos por padrão, menos exclusões; já exclui jogos nas pastas comuns de Steam, Epic, Riot, Ubisoft e EA,
  e aceita lista de exclusão e de inclusão
  ([wiki](https://github.com/ramensoftware/windhawk/wiki/Injection-targets-and-critical-system-processes)). Sobre banimento, não há
  posição oficial de Valve nem do Windhawk; só relatos de uso sem problema
  ([Steam](https://steamcommunity.com/discussions/forum/9/601891467285283647/?l=swedish)).

## Os 60 mods mais usados
| # | mod (id) | usuários | entra em | risco para o Katharos |
|---|---|---|---|---|
| 1 | Windows 11 Taskbar Styler (`windows-11-taskbar-styler`) | 1.12 mi | explorer.exe | só no shell do Windows |
| 2 | Windows 11 Start Menu Styler (`windows-11-start-menu-styler`) | 1.01 mi | StartMenuExperienceHost.exe, SearchHost.exe, SearchApp.exe | só no shell do Windows |
| 3 | Windows 11 Notification Center Styler (`windows-11-notification-center-styler`) | 624 mil | ShellExperienceHost.exe, ShellHost.exe | só no shell do Windows |
| 4 | Taskbar Dock Animation (`taskbar-dock-animation`) | 526 mil | explorer.exe | só no shell do Windows |
| 5 | Windows 11 File Explorer Styler (`windows-11-file-explorer-styler`) | 357 mil | explorer.exe | só no shell do Windows |
| 6 | Taskbar height and icon size (`taskbar-icon-size`) | 336 mil | explorer.exe | só no shell do Windows |
| 7 | Better file sizes in Explorer details (`explorer-details-better-file-sizes`) | 240 mil | * | atenção: entra em todos os processos |
| 8 | Translucent Windows (`translucent-windows`) | 180 mil | * | atenção: entra em todos os processos |
| 9 | Taskbar Volume Control (`taskbar-volume-control`) | 178 mil | explorer.exe, ShellExperienceHost.exe, SndVol.exe | só no shell do Windows |
| 10 | Windows Animations (`windows-animations`) | 133 mil | * | atenção: entra em todos os processos |
| 11 | Taskbar Clock Customization (`taskbar-clock-customization`) | 123 mil | explorer.exe | só no shell do Windows |
| 12 | Taskbar auto-hide when maximized (`taskbar-auto-hide-when-maximized`) | 121 mil | explorer.exe | só no shell do Windows |
| 13 | Invisible Window Borders (`invisible-borders`) | 102 mil | * | atenção: entra em todos os processos |
| 14 | MacOS Minimize Animation (`macos-minimize-animation`) | 96 mil | * | atenção: entra em todos os processos |
| 15 | Windows 11 Settings Styler (`windows-11-settings-styler`) | 88 mil | SystemSettings.exe | só no shell do Windows |
| 16 | Taskbar tray system icon tweaks (`taskbar-tray-system-icon-tweaks`) | 86 mil | explorer.exe | só no shell do Windows |
| 17 | Resource Redirect (`icon-resource-redirect`) | 84 mil | * | atenção: entra em todos os processos |
| 18 | Dark mode context menus (`dark-menus`) | 82 mil | * | atenção: entra em todos os processos |
| 19 | Slick Window Arrangement (`slick-window-arrangement`) | 76 mil | * | atenção: entra em todos os processos |
| 20 | Dynamic Island for Windows (`dynamic-island-for-windows`) | 73 mil | windhawk.exe | só no shell do Windows |
| 21 | Middle click to close on the taskbar (`taskbar-button-click`) | 63 mil | explorer.exe | só no shell do Windows |
| 22 | Classic context menu on Windows 11 (`explorer-context-menu-classic`) | 52 mil | explorer.exe | só no shell do Windows |
| 23 | Taskbar Volume Control Per-App (`taskbar-volume-control-per-app`) | 49 mil | explorer.exe | só no shell do Windows |
| 24 | Taskbar tray icon spacing and grid (`taskbar-notification-icon-spacing`) | 49 mil | explorer.exe | só no shell do Windows |
| 25 | Taskbar Dock Animation Plus (`taskbar-dock-animation-plus`) | 45 mil | explorer.exe | só no shell do Windows |
| 26 | Taskbar auto-hide speed (`taskbar-auto-hide-speed`) | 42 mil | explorer.exe | só no shell do Windows |
| 27 | UXTheme hook (`uxtheme-hook`) | 39 mil | winlogon.exe, explorer.exe, systemsettings.exe… | só no shell do Windows |
| 28 | Modernize Folder Picker Dialog (`modernize-folder-picker-dialog`) | 38 mil | * | atenção: entra em todos os processos |
| 29 | Taskbar Labels for Windows 11 (`taskbar-labels`) | 38 mil | explorer.exe | só no shell do Windows |
| 30 | Start Menu Size (`start-menu-size`) | 35 mil | StartMenuExperienceHost.exe, explorer.exe | só no shell do Windows |
| 31 | Taskbar Auto-Hide Instant Show (`taskbar-autohide-instant-show`) | 34 mil | explorer.exe | só no shell do Windows |
| 32 | Island Media Controls (`island-media-controls`) | 34 mil | explorer.exe | só no shell do Windows |
| 33 | Taskbar Fluent Media Player (`taskbar-fluent-media-player`) | 33 mil | explorer.exe | só no shell do Windows |
| 34 | Chrome/Edge scroll tabs with mouse wheel (`chrome-wheel-scroll-tabs`) | 31 mil | chrome.exe, msedge.exe, opera.exe… | só no programa citado |
| 35 | Disable grouping on the taskbar (`taskbar-grouping`) | 31 mil | explorer.exe | só no shell do Windows |
| 36 | WinUI Context Menu Animation (`winui-context-menu-animation`) | 30 mil | * | atenção: entra em todos os processos |
| 37 | File Explorer WinUI-Like Content Animation (`file-explorer-content-animation`) | 29 mil | explorer.exe | só no shell do Windows |
| 38 | Alt+Tab per monitor (`alt-tab-per-monitor`) | 29 mil | explorer.exe | só no shell do Windows |
| 39 | Taskbar Thumbnail Reorder (`taskbar-thumbnail-reorder`) | 26 mil | explorer.exe | só no shell do Windows |
| 40 | Alt+Tab window delayer (`alt-tab-delayer`) | 24 mil | explorer.exe | só no shell do Windows |
| 41 | Taskbar on top for Windows 11 (`taskbar-on-top`) | 23 mil | explorer.exe, StartMenuExperienceHost.exe, ShellExperienceHost.exe… | só no shell do Windows |
| 42 | Custom Window Corner Radius (`custom-corner-radius`) | 23 mil | dwm.exe | atenção: mexe no compositor de tela (dwm) |
| 43 | Dark Mode for Notepad (`notepad-dark-mode`) | 22 mil | notepad.exe | só no programa citado |
| 44 | Windows 11 Start Menu Power Buttons (`win11-power-buttons`) | 22 mil | StartMenuExperienceHost.exe, explorer.exe | só no shell do Windows |
| 45 | No Focus Rectangle (`no-focus-rectangle`) | 22 mil | explorer.exe | só no shell do Windows |
| 46 | Taskbar Background Helper (`taskbar-background-helper`) | 20 mil | explorer.exe | só no shell do Windows |
| 47 | Mac Island & Dock (`mac-island-dock`) | 20 mil | windhawk.exe, explorer.exe | só no shell do Windows |
| 48 | Start button colorizer (`taskbar-start-button-colorizer`) | 19 mil | explorer.exe | só no shell do Windows |
| 49 | Start button always on the left (`taskbar-start-button-position`) | 19 mil | StartMenuExperienceHost.exe, explorer.exe | só no shell do Windows |
| 50 | Vertical Taskbar for Windows 11 (`taskbar-vertical`) | 18 mil | explorer.exe, StartMenuExperienceHost.exe, ShellExperienceHost.exe… | só no shell do Windows |
| 51 | Customize Windows notifications placement (`notifications-placement`) | 18 mil | explorer.exe, ShellExperienceHost.exe | só no shell do Windows |
| 52 | File Operation Styler (`file-operation-styler`) | 17 mil | explorer.exe | só no shell do Windows |
| 53 | Turn off change file extension warning (`extension-change-no-warning`) | 16 mil | explorer.exe | só no shell do Windows |
| 54 | Dynamic Taskbar Transparency (`dynamic-taskbar-transparency`) | 14 mil | explorer.exe | só no shell do Windows |
| 55 | Open With - Remove Microsoft Store Menu Item (`remove-ms-store-open-with`) | 13 mil | * | atenção: entra em todos os processos |
| 56 | Alt+Tab Flip 3D (Vista Style) (`alt-tab-flip-3d`) | 13 mil | windhawk.exe, explorer.exe | só no shell do Windows |
| 57 | CEF/Spotify Tweaks (`cef-titlebar-enabler-universal`) | 13 mil | spotify.exe, cefclient.exe | só no programa citado |
| 58 | Remove Taskbar Window Suffixes (`file-explorer-remove-suffixes`) | 13 mil | explorer.exe | só no shell do Windows |
| 59 | Shell Flyout Positions (`shell-flyout-positions`) | 12 mil | explorer.exe, ShellExperienceHost.exe, ShellHost.exe… | só no shell do Windows |
| 60 | Disable Taskbar Thumbnails (`taskbar-thumbnails`) | 11 mil | explorer.exe | só no shell do Windows |
## Outros fatos que pesaram no plano
- O Windows 11 24H2 chegou a barrar a atualização em PCs com StartAllBack e ExplorerPatcher, e a impedir instalar o ExplorerPatcher; o
  Start11, assinado, não foi barrado ([Pureinfotech](https://pureinfotech.com/windows-11-24h2-blocks-customization-apps)). Por isso o
  Katharos não instala esses programas.
- O 26H2 ainda não saiu: o plano não conta com ele (barra em qualquer lado só pelo Windhawk, se a pessoa tiver).
  ([Windows Central](https://www.windowscentral.com/microsoft/windows-11/windows-11-2026-update-26h2-changes-for-start-menu-taskbar-and-search)).
  Quando o Windows tiver o nativo, o Katharos usa o nativo e deixa o mod de lado.
- PowerToys 0.98: Command Palette com Dock, Light Switch (tema por horário), Keyboard Manager novo
  ([Windows Central](https://www.windowscentral.com/software-apps/my-favorite-free-windows-11-app-just-got-another-great-update-whats-new-in-powertoys-v0-98)).
- WinUtil (Chris Titus) em 2026: instala programas pelo winget, ajustes padrão e avançados com ponto de restauração, reparos e um criador
  de imagem do Windows ([christitus.com](https://christitus.com/winutil-in-2026/)).
- GitHub Pages: site de até 1 GB e 100 GB/mês de banda (limite flexível)
  ([docs](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)).

Related: [Um programa só](2026-11-11-um-programa-so.md), [Segurança de GPU e limpeza](2026-11-11-seguranca-de-gpu-e-limpeza.md)
