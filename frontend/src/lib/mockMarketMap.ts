import type { MarketMap } from '@/components/quick-chat/types'

/** Mock market map for Quick Chat dev — U.S. AI chip export restrictions / Nvidia. */
export const MOCK_MARKET_MAP: MarketMap = {
  nodes: [
    {
      id: 'event_1',
      type: 'main_event',
      label: 'U.S. AI chip export restrictions',
      description:
        'New U.S. restrictions may limit sales of advanced AI chips to China, tightening prior rules on high-end GPU exports.',
      linkedSection: 'summary',
      confidence: 'high',
    },
    {
      id: 'company_nvda',
      type: 'company',
      label: 'Nvidia',
      description:
        'Most directly affected due to dominant share in AI accelerators and meaningful China revenue exposure.',
      linkedSection: 'market_impact',
      confidence: 'high',
    },
    {
      id: 'company_amd',
      type: 'company',
      label: 'AMD',
      description:
        'Competitor in data-center GPUs; may gain share if Nvidia faces China sales constraints.',
      linkedSection: 'market_impact',
      confidence: 'medium',
    },
    {
      id: 'company_tsmc',
      type: 'company',
      label: 'TSMC',
      description:
        'Key foundry for advanced AI chips; demand and utilization tied to Nvidia and peers.',
      linkedSection: 'market_impact',
      confidence: 'medium',
    },
    {
      id: 'sector_semis',
      type: 'sector_theme',
      label: 'Semiconductors',
      description:
        'Sector sensitive to export controls, supply chains, and geopolitical policy shifts.',
      linkedSection: 'market_impact',
      confidence: 'high',
    },
    {
      id: 'sector_ai_infra',
      type: 'sector_theme',
      label: 'AI infrastructure',
      description:
        'Broader theme covering data-center buildout, cloud capex, and AI chip demand.',
      linkedSection: 'why_it_matters',
      confidence: 'high',
    },
    {
      id: 'impact_china_revenue',
      type: 'market_impact',
      label: 'China revenue exposure',
      description:
        'Potential revenue pressure if high-end AI chip sales to Chinese customers are restricted or delayed.',
      linkedSection: 'risks_and_uncertainties',
      confidence: 'medium',
    },
    {
      id: 'impact_earnings',
      type: 'market_impact',
      label: 'Earnings guidance risk',
      description:
        'Management may need to adjust forward guidance if China restrictions reduce near-term sales.',
      linkedSection: 'risks_and_uncertainties',
      confidence: 'medium',
    },
    {
      id: 'impact_datacenter',
      type: 'market_impact',
      label: 'Data center demand offset',
      description:
        'Strong global cloud and AI capex could partially offset lost China revenue.',
      linkedSection: 'reasoning',
      confidence: 'medium',
    },
    {
      id: 'risk_geo',
      type: 'risk_uncertainty',
      label: 'U.S.–China geopolitical risk',
      description:
        'Escalating tech rivalry increases policy uncertainty for cross-border chip trade.',
      linkedSection: 'risks_and_uncertainties',
      confidence: 'high',
    },
    {
      id: 'risk_retaliation',
      type: 'risk_uncertainty',
      label: 'China retaliation risk',
      description:
        'China could respond with counter-measures affecting U.S. chip firms or supply chains.',
      linkedSection: 'risks_and_uncertainties',
      confidence: 'low',
    },
    {
      id: 'watch_earnings',
      type: 'watch_next',
      label: 'Nvidia earnings guidance',
      description:
        'Next earnings call for management commentary on China demand and export rule impact.',
      linkedSection: 'watch_next',
      confidence: 'high',
    },
    {
      id: 'watch_policy',
      type: 'watch_next',
      label: 'Further U.S. policy updates',
      description:
        'Additional rule clarifications or expanded entity lists could shift the impact timeline.',
      linkedSection: 'watch_next',
      confidence: 'medium',
    },
  ],
  edges: [
    {
      id: 'edge_1',
      source: 'event_1',
      target: 'company_nvda',
      label: 'affects',
      description:
        'Export restrictions directly affect Nvidia because of its AI chip sales exposure to China.',
      confidence: 'high',
    },
    {
      id: 'edge_2',
      source: 'company_nvda',
      target: 'impact_china_revenue',
      label: 'creates risk for',
      description: 'Nvidia may face revenue pressure if China sales are restricted.',
      confidence: 'medium',
    },
    {
      id: 'edge_3',
      source: 'impact_china_revenue',
      target: 'impact_earnings',
      label: 'may pressure',
      description: 'China revenue weakness could flow through to earnings guidance.',
      confidence: 'medium',
    },
    {
      id: 'edge_4',
      source: 'event_1',
      target: 'risk_geo',
      label: 'linked to',
      description: 'The restrictions are part of broader U.S.–China tech competition.',
      confidence: 'high',
    },
    {
      id: 'edge_5',
      source: 'risk_geo',
      target: 'risk_retaliation',
      label: 'increases risk for',
      description: 'Geopolitical tension raises the chance of Chinese counter-measures.',
      confidence: 'low',
    },
    {
      id: 'edge_6',
      source: 'event_1',
      target: 'company_amd',
      label: 'may benefit',
      description: 'AMD could pick up share if Nvidia faces China constraints.',
      confidence: 'medium',
    },
    {
      id: 'edge_7',
      source: 'company_nvda',
      target: 'company_tsmc',
      label: 'depends on',
      description: 'Nvidia advanced GPUs rely on TSMC manufacturing capacity.',
      confidence: 'high',
    },
    {
      id: 'edge_8',
      source: 'event_1',
      target: 'sector_semis',
      label: 'affects',
      description: 'Export controls ripple through the broader semiconductor supply chain.',
      confidence: 'high',
    },
    {
      id: 'edge_9',
      source: 'sector_semis',
      target: 'sector_ai_infra',
      label: 'linked to',
      description: 'Semiconductor policy shapes the pace of AI infrastructure buildout.',
      confidence: 'medium',
    },
    {
      id: 'edge_10',
      source: 'impact_datacenter',
      target: 'impact_china_revenue',
      label: 'may offset',
      description: 'Strong data-center demand could partially offset China weakness.',
      confidence: 'medium',
    },
    {
      id: 'edge_11',
      source: 'sector_ai_infra',
      target: 'impact_datacenter',
      label: 'supports',
      description: 'AI infrastructure capex underpins data-center chip demand.',
      confidence: 'medium',
    },
    {
      id: 'edge_12',
      source: 'impact_earnings',
      target: 'watch_earnings',
      label: 'watch next',
      description: 'Earnings risk makes the next guidance update a key signal.',
      confidence: 'high',
    },
    {
      id: 'edge_13',
      source: 'event_1',
      target: 'watch_policy',
      label: 'watch next',
      description: 'Policy evolution will clarify scope and enforcement of restrictions.',
      confidence: 'medium',
    },
    {
      id: 'edge_14',
      source: 'company_nvda',
      target: 'watch_earnings',
      label: 'watch next',
      description: 'Investors will look to Nvidia for China exposure commentary.',
      confidence: 'high',
    },
  ],
}
