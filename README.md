# INMET Custom Component

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]](Downloads)
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

Este custom component consulta o site do INMET (Instituto Nacional de Meteorologia) em busca de alertas meteorológicos para sua região e exibe essas informações no Home Assistant.

## Instalação
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sigrist&repository=inmet&category=Integration)

A instalação deste custom component pode ser feita através do HACS, seguindo os seguintes passos:

1. No HACS, vá até "Custom Repositories".
2. Adicione a URL deste repositório como um novo repositório personalizado.
3. Após adicionar, faça o download da última versão disponível.

Após a instalação, reinicie o Home Assistant para que o componente seja reconhecido corretamente.

## Configuração dos Sensores

Os sensores são criados a partir do código da cidade disponível no site do INMET. Para encontrar o código da sua cidade, siga estas etapas:

1. Procure por um alerta meteorológico da sua cidade no site do INMET.
2. Copie o código da cidade (Por exemplo, o código de Campinas/SP é `3509502`).

Com o código da cidade, você pode configurar os sensores no Home Assistant para receber atualizações de alertas meteorológicos específicos da sua região.

## Automação

Para aproveitar ao máximo os alertas meteorológicos fornecidos por este componente, você pode criar automações no Home Assistant que respondem aos alertas.

Passos para Criar uma Automação

1. Configurar uma Zona: Crie uma Zona no Home Assistant com a latitude e longitude informadas pelo sensor da sua cidade.

2. Configurar a Automação:
* Vá até a seção de automações no Home Assistant.
* Escolha o trigger Geo Location e defina como source o valor "inmet".
* Escolha se deseja disparar a automação quando um alerta for criado (enter) ou removido (exit).

Com isso, você poderá, por exemplo, ser notificado sempre que houver um alerta meteorológico severo para sua região ou acionar outros dispositivos, como luzes, para chamar atenção sobre um alerta.


