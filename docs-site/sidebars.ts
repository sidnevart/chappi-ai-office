import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  ownerManual: [
    {
      type: 'category',
      label: 'Руководство владельца',
      collapsible: false,
      items: [
        'owner-manual/intro',
        'owner-manual/dashboards',
        'owner-manual/kb-guide',
        'owner-manual/openclaw-guide',
        'owner-manual/multi-agent',
        'owner-manual/voice-guide',
        'owner-manual/notifications',
        'owner-manual/troubleshooting',
      ],
    },
  ],
  setupGuide: [
    {
      type: 'category',
      label: 'Руководство по настройке',
      collapsible: false,
      items: [
        'setup-guide/prerequisites',
        'setup-guide/vps-setup',
        'setup-guide/mac-setup',
        'setup-guide/openclaw-config',
        'setup-guide/kb-setup',
        'setup-guide/mempalace',
        'setup-guide/voice',
        'setup-guide/claude-code',
        'setup-guide/google',
        'setup-guide/star-office-ui',
        'setup-guide/daily-usage',
      ],
    },
  ],
};

export default sidebars;
