# INMET Custom Component

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


## Dashboard

Você pode criar um card no dashboard do Home Assistant para visualizar os alertas meteorológicos de forma prática. Aqui está um exemplo de código YAML para criar um card utilizando o componente auto-entities:

```yaml
type: custom:auto-entities
card:
  type: grid
  columns: 1
  square: false
  cards_gap: medium
  style: |
    ha-card {
      padding: 16px;
    }
card_param: cards
filter:
  include:
    - domain: geo_location
      attributes:
        source: inmet
      options:
        type: custom:button-card
        entity: this.entity_id
        show_icon: false
        show_name: false
        show_label: false
        styles:
          grid:
            - grid-template-areas: >-
                "icon desc desc" "icon severity severity" "icon dates dates" ". risks-header risks-header" ". risks risks" ". instructions-header instructions-header" ". instructions instructions" ". link link"
            - grid-template-columns: auto 1fr
            - grid-template-rows: auto auto auto auto auto auto
          card:
            - padding: 24px
            - width: 100%
            - min-width: 300px
            - max-width: 500px
            - margin: 10px
          custom_fields:
            icon:
              - justify-self: start
              - align-self: start
              - margin-right: 8px
            desc:
              - justify-self: start
              - text-align: left
              - font-size: 2em
              - font-weight: 500
              - line-height: 1em
            severity:
              - justify-self: start
              - text-align: left
              - font-size: 1.2em
              - font-weight: 500
            dates:
              - justify-self: start
              - text-align: left
              - font-size: 0.9em
              - display: flex
              - align-items: center
              - color: var(--primary-text-color)
            risks-header:
              - justify-self: start
              - font-size: 1.0em
              - font-weight: 600
              - text-align: left
              - margin-top: 10px
              - margin-bottom: 5px
              - color: var(--primary-text-color)
            instructions-header:
              - justify-self: start
              - font-size: 1.0em
              - font-weight: 600
              - text-align: left
              - margin-top: 10px
              - margin-bottom: 5px
              - color: var(--primary-text-color)
            risks:
              - justify-self: start
              - text-align: left
              - word-break: break-word
              - white-space: normal
              - font-size: 0.8em
              - margin-top: 10px
              - margin-bottom: 10px
              - max-width: 400px
              - overflow-wrap: break-word
            instructions:
              - justify-self: start
              - text-align: left
              - word-break: break-word
              - white-space: normal
              - font-size: 0.8em
              - margin-top: 10px
              - margin-bottom: 10px
              - max-width: 400px
              - overflow-wrap: break-word
            link:
              - justify-self: start
              - font-size: 0.9em
              - margin-top: 10px
              - margin-bottom: 10px
        custom_fields:
          icon: |
            [[[ 
              const severityColor = entity.attributes.color || '#FFFFFF';  
              return `<ha-icon icon="${entity.attributes.icon}" style="color:${severityColor}; --mdc-icon-size: 48px;"></ha-icon>` 
            ]]]
          desc: |
            [[[ 
              const severityColor = entity.attributes.color || '#FFFFFF';  
              return `<span style="color:${severityColor};">` + entity.attributes.description  + `</span>`;
            ]]]
          severity: |
            [[[ 
              const severityColor = entity.attributes.color || '#FFFFFF';  
              return `<span style="color:${severityColor};">` + entity.attributes.severity + `</span>`;
            ]]]
          dates: |
            [[[ 
              const startDate = new Date(entity.attributes.start_date).toLocaleString();
              const endDate = new Date(entity.attributes.end_date).toLocaleString();
              return `<ha-icon icon="mdi:calendar" style="--mdc-icon-size: 16px; margin-right: 8px;"></ha-icon>` + `De ` + startDate + ` até ` + endDate;
            ]]]
          risks-header: |
            [[[ 
              return `<div style="display: flex; align-items: center; justify-content: flex-start;">
                        <span>Riscos</span>
                        <div style="flex-grow: 1; height: 1px; background-color: var(--primary-text-color); margin-left: 10px;"></div>
                      </div>`;
            ]]]
          risks: |
            [[[ 
              const risks = entity.attributes.risks.filter(risk => risk.trim() !== ''); 
              return risks.length ? `<ul style='margin: 0; padding-left: 20px; max-width: 400px; white-space: normal; overflow-wrap: break-word;'>` + risks.map(risk => risk ? `<li style='margin-bottom: 8px;'>` + risk + `</li>` : '').join('') + `</ul>` : 'Sem riscos informados.'; 
            ]]]
          instructions-header: |
            [[[ 
              return `<div style="display: flex; align-items: center; justify-content: flex-start;">
                        <span>Instruções</span>
                        <div style="flex-grow: 1; height: 1px; background-color: var(--primary-text-color); margin-left: 10px;"></div>`;
            ]]]
          instructions: |
            [[[ 
              const instructions = entity.attributes.instructions.filter(instruction => instruction.trim() !== '');  
              return instructions.length ? `<ul style='margin: 0; padding-left: 20px; max-width: 400px; white-space: normal; overflow-wrap: break-word;'>` + instructions.map(instruction => instruction ? `<li style='margin-bottom: 8px;'>` + instruction + `</li>` : '').join('') + `</ul>` : 'Sem instruções adicionais.'; 
            ]]]
          link: |
            [[[ 
              const url = entity.attributes.url || '#';  
              return `<a href="${url}" target="_blank" style="text-decoration: underline; color: var(--primary-color);">Mais informações</a>`; 
            ]]]

```